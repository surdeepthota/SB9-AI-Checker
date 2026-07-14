import React from 'react';

const BAND_META = {
  leans_authentic: { label: 'Leans Authentic', badge: 'success' },
  abstain: { label: 'Abstain — No Verdict', badge: '' },
  moderate_signal: { label: 'Moderate Signal', badge: 'warning' },
  strong_signal: { label: 'Strong Signal', badge: 'danger' },
};

export default function JudgmentCard({ judgment, embedded = false }) {
  if (!judgment) return null;
  const meta = BAND_META[judgment.band] || { label: judgment.band, badge: '' };
  const score = judgment.calibrated_score ?? 0;
  const containerClassName = embedded ? 'layer-card' : 'glass-card layer-card';

  return (
    <div className={containerClassName}>
      <div className="layer-head">
        <span className="layer-title">Overall Confidence</span>
        <span className="chip probabilistic">probabilistic</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem', flexWrap: 'wrap' }}>
        <span className={`badge ${meta.badge}`} style={{ fontSize: '0.95rem', padding: '0.45rem 1rem' }}>
          {meta.label}
        </span>
      </div>

      <details className="collapse">
        <summary>Advanced Details</summary>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem', flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'var(--mono)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              score {score.toFixed(2)}
            </span>
          </div>

          <div className="band-strip">
            <div className="band-pointer" style={{ left: `${Math.min(Math.max(score, 0), 1) * 100}%` }}>
              {score.toFixed(2)}
            </div>
            <div className="bands">
              <div className="band leans">leans authentic</div>
              <div className="band abstain">abstain</div>
              <div className="band moderate">moderate</div>
              <div className="band strong">strong</div>
            </div>
            <div className="band-scale"><span>0.0</span><span>0.3</span><span>0.7</span><span>0.9</span><span>1.0</span></div>
          </div>

          {judgment.band === 'abstain' && (
            <p className="inset" style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Abstaining is a real answer, not a failure.</strong>{' '}
              This score falls in the region where detectors of this kind cannot reliably beat a coin
              flip, so PeachCheck declines to lean either way. It does <em>not</em> mean “probably AI.”
            </p>
          )}

          {judgment.rationale && <p className="note-text">{judgment.rationale}</p>}

          {judgment.calibration_version === 'v0-identity' && (
            <p className="note-text">
              Calibration version <span style={{ fontFamily: 'var(--mono)' }}>v0-identity</span>: the score is the raw fused panel
              output, not yet fit to a labeled corpus — treat the band, not the number, as the takeaway.
            </p>
          )}
        </div>
      </details>
    </div>
  );
}
