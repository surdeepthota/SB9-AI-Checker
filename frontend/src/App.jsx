import React, { useEffect, useRef, useState } from 'react';
import Uploader from './components/Uploader';
import ReportCard from './components/ReportCard';
import { LightboxProvider } from './components/Lightbox';
import { analyzeFile, analyzeSample, listSamples } from './api';

function App() {
  const [reportData, setReportData] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [samples, setSamples] = useState([]);
  const objectUrlRef = useRef(null);

  useEffect(() => {
    listSamples()
      .then((body) => setSamples(body.samples || []))
      .catch(() => setSamples([])); // demo gallery is optional; the uploader still works
  }, []);

  const releasePreview = () => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
  };

  const run = async (task, preview) => {
    setLoading(true);
    setError(null);
    setReportData(null);
    releasePreview();
    setPreviewUrl(preview || null);
    try {
      setReportData(await task());
    } catch (err) {
      setError(err.message || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = (file, isCampaignAd) => {
    const url = URL.createObjectURL(file);
    objectUrlRef.current = url;
    run(() => analyzeFile(file, isCampaignAd), url);
  };

  const handleSample = (filename, isCampaignAd) => {
    run(() => analyzeSample(filename, isCampaignAd), null);
  };

  const handleReset = () => {
    setReportData(null);
    setError(null);
    releasePreview();
    setPreviewUrl(null);
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

          {!reportData && !error && (
            <Uploader onUpload={handleUpload} onSample={handleSample} samples={samples} loading={loading} />
          )}

          {reportData && !error && (
            <ReportCard data={reportData} previewUrl={previewUrl} onReset={handleReset} />
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
