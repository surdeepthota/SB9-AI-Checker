import React, { useEffect, useRef, useState } from 'react';
import Uploader from './components/Uploader';
import ReportCard from './components/ReportCard';
import { LightboxProvider } from './components/Lightbox';
import { analyzeFile, analyzeSample, listSamples } from './api';
import { extractFramesFromClipUrl } from './media-url';

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [samples, setSamples] = useState([]);
  const objectUrlsRef = useRef([]);

  useEffect(() => {
    listSamples()
      .then((body) => setSamples(body.samples || []))
      .catch(() => setSamples([])); // demo gallery is optional; the uploader still works
    return () => {
      objectUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
      objectUrlsRef.current = [];
    };
  }, []);

  const trackObjectUrl = (url) => {
    if (url) {
      objectUrlsRef.current.push(url);
    }
  };

  const releasePreviews = () => {
    objectUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    objectUrlsRef.current = [];
  };

  const run = async (task) => {
    setLoading(true);
    setError(null);
    setAnalysisResult(null);
    releasePreviews();
    try {
      setAnalysisResult(await task());
    } catch (err) {
      setError(err.message || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = (upload, isCampaignAd) => {
    if (upload?.clipUrl) {
      run(async () => {
        const clip = await extractFramesFromClipUrl(upload.clipUrl);
        clip.frames.forEach((frame) => trackObjectUrl(frame.previewUrl));
        const reports = await Promise.all(
          clip.frames.map(async (frame, index) => ({
            frameNumber: index + 1,
            seconds: frame.seconds,
            label: frame.label,
            previewUrl: frame.previewUrl,
            data: await analyzeFile(frame.file, isCampaignAd),
          })),
        );
        return {
          kind: 'clip',
          clipUrl: upload.clipUrl,
          durationSeconds: clip.durationSeconds,
          reports,
        };
      });
      return;
    }

    run(async () => {
      const previewUrl = URL.createObjectURL(upload);
      trackObjectUrl(previewUrl);
      return {
        kind: 'single',
        previewUrl,
        data: await analyzeFile(upload, isCampaignAd),
      };
    });
  };

  const handleSample = (filename, isCampaignAd) => {
    run(async () => ({
      kind: 'single',
      previewUrl: null,
      data: await analyzeSample(filename, isCampaignAd),
    }));
  };

  const handleReset = () => {
    setAnalysisResult(null);
    setError(null);
    releasePreviews();
  };

  return (
    <LightboxProvider>
      <div className="app-container">
        <header className="masthead">
          <h1>PeachCheck</h1>
          <p className="tagline">
            Cryptographic provenance and SB 9 disclosure analysis for Georgia political media —
            evidence and calibrated confidence, never verdicts.
          </p>
          <span className="principle">This tool never labels media “fake.” Absence of credentials means unknown, not guilty.</span>
        </header>

        <main style={{ display: 'flex', flexDirection: 'column', gap: '1.4rem' }}>
          {error && (
            <div className="glass-card" style={{ borderLeft: '4px solid var(--danger)' }}>
              <h3 style={{ color: 'var(--danger)', marginBottom: '0.5rem' }}>Analysis error</h3>
              <p style={{ color: 'var(--text-secondary)' }}>{error}</p>
              <button className="btn" style={{ marginTop: '1rem' }} onClick={handleReset}>Try again</button>
            </div>
          )}

          {!analysisResult && !error && (
            <Uploader onUpload={handleUpload} onSample={handleSample} samples={samples} loading={loading} />
          )}

          {analysisResult?.kind === 'single' && !error && (
            <ReportCard data={analysisResult.data} previewUrl={analysisResult.previewUrl} onReset={handleReset} />
          )}

          {analysisResult?.kind === 'clip' && !error && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.4rem' }}>
              <div className="glass-card layer-card">
                <div className="layer-head">
                  <span className="layer-title">Clip Analysis</span>
                  <span className="layer-sub">{analysisResult.reports.length} sampled frames from a {Math.round(analysisResult.durationSeconds)} second clip</span>
                </div>
                <div className="kv-grid">
                  <div className="kv"><span className="k">Source URL</span><span className="v" title={analysisResult.clipUrl}>{analysisResult.clipUrl}</span></div>
                  <div className="kv"><span className="k">Frames analyzed</span><span className="v">{analysisResult.reports.length}</span></div>
                </div>
                <p className="note-text">
                  Each frame below was analyzed independently with the existing still-image trust pipeline.
                  Re-encoded clips and screenshots often strip provenance, so frame-level results should be read
                  as evidence snapshots, not as proof about the full video.
                </p>
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button className="btn ghost" onClick={handleReset}>Analyze another</button>
                </div>
              </div>

              {analysisResult.reports.map((frame) => (
                <ReportCard
                  key={`${frame.frameNumber}-${frame.label}`}
                  data={frame.data}
                  previewUrl={frame.previewUrl}
                  onReset={handleReset}
                  title={`Frame ${frame.frameNumber} · ${frame.label}`}
                  showReset={false}
                />
              ))}
            </div>
          )}
        </main>

        <footer className="colophon">
          PeachCheck analyzes media against Georgia SB 9 (LC 56 0401S) as a <em>proposed</em> legislative
          standard — the bill stalled in January 2026 and is not enforceable law. Provenance checks
          use the open C2PA standard. Forensic indicators are probabilistic and clearly labeled as
          such. Built for the Congressional App Challenge 2026.
        </footer>
      </div>
    </LightboxProvider>
  );
}

export default App;
