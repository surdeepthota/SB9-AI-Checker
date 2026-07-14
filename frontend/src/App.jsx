import React, { useEffect, useRef, useState } from 'react';
import Uploader from './components/Uploader';
import ReportCard from './components/ReportCard';
import JudgmentCard from './components/JudgmentCard';
import { LightboxProvider } from './components/Lightbox';
import { analyzeClipUrl, analyzeFile, analyzeSample, listSamples } from './api';

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
        const clip = await analyzeClipUrl(upload.clipUrl, isCampaignAd, 5, Boolean(upload.strictClipMode));
        const reports = clip.reports.map((frame) => ({
          frameNumber: frame.frame_number,
          seconds: frame.seconds,
          label: frame.label,
          previewUrl: frame.preview_data_url,
          data: frame.analysis,
        }));
        return {
          kind: 'clip',
          clipUrl: upload.clipUrl,
          strictClipMode: Boolean(upload.strictClipMode),
          durationSeconds: clip.duration_seconds,
          clipSummary: clip.clip_summary,
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
                  PeachCheck now aggregates the sampled frames into one clip-level judgment first, then shows the
                  individual frame reports underneath as supporting evidence.
                </p>
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button className="btn ghost" onClick={handleReset}>Analyze another</button>
                </div>
              </div>

              {analysisResult.clipSummary?.judgment && (
                <div className="glass-card layer-card">
                  {(() => {
                    const clipDecisionScore =
                      analysisResult.clipSummary.clip_decision_score ?? analysisResult.clipSummary.average_frame_score ?? 0;
                    return (
                      <>
                        <div className="layer-head">
                          <span className="layer-title">Clip Summary</span>
                          <span className="layer-sub">
                            aggregate over {analysisResult.clipSummary.sampled_frames} frames
                          </span>
                        </div>
                        <JudgmentCard judgment={analysisResult.clipSummary.judgment} embedded />
                        <div className="kv-grid">
                          <div className="kv"><span className="k">Clip decision score</span><span className="v">{clipDecisionScore.toFixed(2)}</span></div>
                          <div className="kv"><span className="k">Average sampled frame</span><span className="v">{analysisResult.clipSummary.average_frame_score.toFixed(2)}</span></div>
                          <div className="kv"><span className="k">Strongest frame</span><span className="v">{analysisResult.clipSummary.strongest_frame_score.toFixed(2)}</span></div>
                          <div className="kv"><span className="k">Moderate/strong frames</span><span className="v">{analysisResult.clipSummary.suspicious_frames}</span></div>
                          <div className="kv"><span className="k">Analysis mode</span><span className="v">{analysisResult.clipSummary.strict_mode ? 'strict' : 'standard'}</span></div>
                        </div>
                        <p className="note-text">
                          The clip decision score is the decisive aggregate. The average sampled frame score is shown only as supporting context.
                        </p>
                      </>
                    );
                  })()}
                </div>
              )}

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
