import React from 'react';
import { useLightbox } from '../lightbox-context';

const CHECK_LABELS = {
  content_ai_use_stated: 'States AI was used',
  content_events_caveat_stated: '"Events may not have occurred" stated',
  content_sponsor_named: 'Sponsor / "paid for by" named',
  text_height_ratio: 'Text size is large enough',
  visible_duration_ratio: 'Visible for long enough',
  contrast_ratio: 'Text contrast is readable',
};

function formatValue(check) {
  if (check.name.startsWith('content_')) return check.passed ? 'found' : 'not found';
  if (check.name.includes('ratio') && check.required_bar <= 1.0) {
    return `${(check.measured_value * 100).toFixed(1)}% / ${(check.required_bar * 100).toFixed(0)}%`;
  }
  return `${check.measured_value} / ${check.required_bar}`;
}

export default function MeasurementCard({ measurement }) {
  const zoom = useLightbox();
  if (!measurement) return null;
  const evidence = measurement.checks?.find((c) => c.evidence_ref)?.evidence_ref;

  return (
    <div className="glass-card layer-card">
      <div className="layer-head">
        <span className="layer-title">Disclosure Check</span>
        <span className="chip deterministic">deterministic</span>
      </div>

      <p style={{ fontSize: '0.95rem' }}>
        {measurement.checks?.length > 0
          ? (measurement.checks.every(c => c.passed) ? "This image meets all the disclosure requirements." : "This image does not meet all the required disclosure rules.")
          : (measurement.note || 'No measurements produced.')}
      </p>

      {measurement.checks?.length > 0 && (
        <details className="collapse">
          <summary>Advanced Details</summary>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.5rem' }}>
            <div className="table-scroll">
              <table className="check-table">
                <thead>
                  <tr><th>Requirement</th><th>Measured / Required</th><th>Result</th></tr>
                </thead>
                <tbody>
                  {measurement.checks.map((check) => (
                    <React.Fragment key={check.name}>
                      <tr>
                        <td>{CHECK_LABELS[check.name] || check.name}</td>
                        <td className="mono">{formatValue(check)}</td>
                        <td>
                          <span className={`badge ${check.passed ? 'success' : 'danger'}`}>
                            {check.passed ? 'meets bar' : 'below bar'}
                          </span>
                        </td>
                      </tr>
                      {check.detail && (
                        <tr><td colSpan={3} className="detail">{check.detail}</td></tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>

            {measurement.disclosure_text && (
              <div className="inset">
                <div className="kv"><span className="k">Disclosure text as read (OCR)</span></div>
                <p style={{ fontFamily: 'var(--mono)', fontSize: '0.82rem', marginTop: '0.35rem', color: 'var(--text-secondary)' }}>
                  “{measurement.disclosure_text}”
                </p>
              </div>
            )}

            {evidence && (
              <figure className="evidence-figure">
                <img src={evidence} alt="Frame with the measured disclosure bounding box drawn on it" onClick={() => zoom(evidence)} />
                <figcaption>
                  Visual proof: the exact box the height percentage was computed from. Redo the arithmetic
                  by hand and you get the same number.
                </figcaption>
              </figure>
            )}

            {measurement.note && (
              <p className="note-text">{measurement.note}</p>
            )}
          </div>
        </details>
      )}
    </div>
  );
}
