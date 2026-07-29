import React from 'react';
import { useLightbox } from '../lightbox-context';

const SIGNAL_META = {
  metadata: { label: 'EXIF / Metadata', kind: 'deterministic read' },
  error_level_analysis: { label: 'Error Level Analysis', kind: 'team-written' },
  fft_frequency_domain: { label: 'FFT Frequency Domain', kind: 'team-written' },
  ml_classifier: { label: 'Pretrained ML Classifier', kind: 'least reliable' },
};

export default function ForensicsCard({ forensics }) {
  const zoom = useLightbox();
  if (!forensics) return null;
  const available = forensics.signals.filter((s) => s.available);
  const triggered = available.filter((s) => s.triggered);

  return (
    <div className="premium-card layer-card">
      <div className="layer-head">
        <span className="layer-title">Image Analysis</span>
        <span className="chip probabilistic">probabilistic</span>
      </div>

      <p style={{ fontSize: '0.95rem' }}>
        We checked the image for signs of manipulation and found <strong>{triggered.length}</strong> unusual pattern{triggered.length === 1 ? '' : 's'}.
      </p>

      <details className="collapse">
        <summary>Advanced Details</summary>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.5rem' }}>
          <p style={{ fontSize: '0.95rem' }}>
            These are suggestive signals, never verdicts — the panel runs only because this file
            offered nothing cryptographic to verify.
          </p>

          <div className="signal-grid">
            {forensics.signals.map((signal) => {
              const meta = SIGNAL_META[signal.name] || { label: signal.name, kind: '' };
              const cls = !signal.available ? 'unavailable' : signal.triggered ? 'triggered' : '';
              return (
                <div key={signal.name} className={`signal-card ${cls}`}>
                  <div className="signal-name">
                    {meta.label}
                    <span className={`badge ${!signal.available ? '' : signal.triggered ? 'warning' : 'success'}`} style={{ fontSize: '0.7rem' }}>
                      {!signal.available ? 'not run' : signal.triggered ? 'triggered' : 'quiet'}
                    </span>
                  </div>
                  {signal.available && (
                    <span className="signal-value">
                      value {signal.raw_value} · threshold {signal.threshold}
                    </span>
                  )}
                  <p className="signal-explain">{signal.explanation}</p>
                  {signal.evidence_ref && (
                    <img
                      src={signal.evidence_ref}
                      alt={`${meta.label} evidence visualization`}
                      onClick={() => zoom(signal.evidence_ref)}
                    />
                  )}
                </div>
              );
            })}
          </div>

          {forensics.fusion_rule && (
            <p className="note-text">
              Fused score <strong style={{ fontFamily: 'var(--mono)' }}>{forensics.fused_score}</strong> — {forensics.fusion_rule}
            </p>
          )}
        </div>
      </details>
    </div>
  );
}
