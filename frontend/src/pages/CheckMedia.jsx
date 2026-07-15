import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, ArrowRight } from 'lucide-react';
import { analyzeClipUrl, analyzeFile } from '../api';

export default function CheckMedia() {
  const navigate = useNavigate();
  const [analyzing, setAnalyzing] = useState(false);
  const [pipelineState, setPipelineState] = useState(0); // 0: none, 1: prov, 2: meas, 3: for, 4: jud
  const [url, setUrl] = useState('');
  const [strictClipMode, setStrictClipMode] = useState(false);
  const [inputError, setInputError] = useState('');
  const fileInputRef = useRef(null);

  const startAnalysis = async (file) => {
    if (!file?.type?.startsWith('image/')) {
      setInputError('Only still images are supported right now.');
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setInputError('Choose an image smaller than 25 MB.');
      return;
    }

    setInputError('');
    setAnalyzing(true);
    setPipelineState(1);

    const timers = [
      setTimeout(() => setPipelineState(2), 500),
      setTimeout(() => setPipelineState(3), 1000),
    ];

    try {
      const analysis = await analyzeFile(file, false);
      timers.forEach(clearTimeout);
      setPipelineState(4);

      try {
        sessionStorage.setItem('peachcheck:last-analysis', JSON.stringify(analysis));
      } catch {
        // The navigation state below still carries the report if browser storage is full.
      }

      const reportId = analysis.trust_report?.identity?.sha256?.slice(0, 12) || 'analysis';
      navigate(`/report/${reportId}`, { state: { analysis } });
    } catch (error) {
      timers.forEach(clearTimeout);
      setAnalyzing(false);
      setPipelineState(0);
      setInputError(
        error instanceof TypeError || error?.message === 'Failed to fetch' || /^Request failed \(5\d\d\)$/.test(error?.message || '')
          ? 'Analysis is unavailable because the backend is not running. Start the FastAPI server and try again.'
          : error?.message || 'The backend could not analyze this image.',
      );
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];

    if (!file) {
      setInputError('Choose a media file before starting the check.');
      return;
    }

    startAnalysis(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleFileSelect = (e) => {
    if (e.target.files?.[0]) startAnalysis(e.target.files[0]);
    e.target.value = '';
  };

  const handleUrlCheck = async () => {
    const value = url.trim();

    if (!value) {
      setInputError('Paste a media URL before clicking Check.');
      return;
    }

    try {
      const parsedUrl = new URL(value);
      if (!['http:', 'https:'].includes(parsedUrl.protocol)) throw new Error('Unsupported protocol');
    } catch {
      setInputError('Enter a valid URL beginning with http:// or https://.');
      return;
    }

    setInputError('');
    setAnalyzing(true);
    setPipelineState(1);

    const timers = [
      setTimeout(() => setPipelineState(2), 500),
      setTimeout(() => setPipelineState(3), 1000),
    ];

    try {
      const clip = await analyzeClipUrl(value, false, strictClipMode ? 7 : 5, strictClipMode);
      timers.forEach(clearTimeout);
      setPipelineState(4);

      try {
        sessionStorage.setItem('peachcheck:last-clip-analysis', JSON.stringify(clip));
      } catch {
        // Navigation state still carries the result when the frame previews exceed storage quota.
      }

      navigate(`/report/clip-${Date.now()}`, { state: { clip } });
    } catch (error) {
      timers.forEach(clearTimeout);
      setAnalyzing(false);
      setPipelineState(0);
      setInputError(error?.message || 'The backend could not analyze this clip URL.');
    }
  };

  return (
    <div className="grid-12">
      <div className="col-10 col-start-2">
        <p className="text-xs font-mono text-lo mb-2 uppercase tracking-wide">Check a photo or short video</p>
        <h1 className="text-2xl mb-4">See what we can verify.</h1>
        <p className="text-base text-lo mb-8">Upload a photo or paste a video link. We will show what we found, what looks unusual, and what we could not prove.</p>

        {!analyzing ? (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="sr-only"
              onChange={handleFileSelect}
              aria-label="Choose a media file"
            />
            <button
              type="button"
              className="upload-zone mb-6"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
              aria-label="Drop a file here or browse to upload a still image up to 25MB"
            >
              <UploadCloud size={48} className="mx-auto mb-4" aria-hidden="true" />
              <p className="font-display text-lg mb-2 text-hi">[ Drop a file here or browse ]</p>
              <p className="text-sm font-mono text-lo">still image · max 25 MB</p>
            </button>

            <div className="flex gap-4 items-center flex-wrap">
              <span className="text-lo font-mono text-sm whitespace-nowrap" id="url-label">Or paste a clip URL</span>
              <input
                type="url"
                className="flex-1"
                placeholder="YouTube, TikTok, Instagram, or a direct clip link"
                aria-labelledby="url-label"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);
                  if (inputError) setInputError('');
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleUrlCheck();
                }}
                aria-invalid={Boolean(inputError)}
                aria-describedby={inputError ? 'media-input-error' : undefined}
              />
              <button type="button" className="btn btn-secondary" onClick={handleUrlCheck}>
                Check <ArrowRight size={16} />
              </button>
            </div>
            <label className="clip-options text-sm text-lo mt-2">
              <input
                type="checkbox"
                checked={strictClipMode}
                onChange={(e) => setStrictClipMode(e.target.checked)}
              />
              Strict clip mode — sample more frames for a more cautious result
            </label>
            {inputError && (
              <p id="media-input-error" className="form-error mt-2" role="alert">
                {inputError}
              </p>
            )}
          </>
        ) : (
          <div className="card mb-6" role="status" aria-live="polite">
            <h3 className="font-display text-lg mb-4 text-clay">Checking your media...</h3>
            <div className="flex gap-4 flex-wrap">
              <div className={`pipeline-step ${pipelineState >= 1 ? 'active' : ''}`}>
                <span className="font-mono text-xs">01</span>
                <span className="font-display">Source</span>
                {pipelineState >= 1 && <span className="font-mono text-xs text-lo mt-2">looking for a trusted source record...</span>}
              </div>
              <div className={`pipeline-step ${pipelineState >= 2 ? 'active' : ''}`}>
                <span className="font-mono text-xs">02</span>
                <span className="font-display">AI label</span>
                {pipelineState >= 2 ? <span className="font-mono text-xs text-lo mt-2">looking for a clear AI warning...</span> : <span className="font-mono text-xs text-ink-500 mt-2">waiting</span>}
              </div>
              <div className={`pipeline-step ${pipelineState >= 3 ? 'active' : ''}`}>
                <span className="font-mono text-xs">03</span>
                <span className="font-display">Image checks</span>
                {pipelineState >= 3 ? <span className="font-mono text-xs text-lo mt-2">looking for signs of AI or editing...</span> : <span className="font-mono text-xs text-ink-500 mt-2">waiting</span>}
              </div>
              <div className={`pipeline-step ${pipelineState >= 4 ? 'active' : ''}`}>
                <span className="font-mono text-xs">04</span>
                <span className="font-display">Result</span>
                {pipelineState >= 4 ? <span className="font-mono text-xs text-lo mt-2">putting the results together...</span> : <span className="font-mono text-xs text-ink-500 mt-2">waiting</span>}
              </div>
            </div>
          </div>
        )}

        <div className="mt-12">
          <h3 className="font-display text-lg mb-4 pb-2 border-b">What we check</h3>
          <div className="info-cols text-sm text-lo">
            <div className="flex-1"><strong className="text-hi font-display">Source</strong><br/>Does the file include a trusted camera or creator record?</div>
            <div className="flex-1"><strong className="text-hi font-display">AI warning</strong><br/>Does the post or file say that AI was used?</div>
            <div className="flex-1"><strong className="text-hi font-display">Visual clues</strong><br/>Do the image checks find anything unusual?</div>
            <div className="flex-1"><strong className="text-hi font-display">Answer</strong><br/>How strong is the evidence, and what is still unknown?</div>
          </div>
        </div>
      </div>
    </div>
  );
}
