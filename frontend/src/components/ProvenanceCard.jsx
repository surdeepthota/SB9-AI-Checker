import React from 'react';

const STATE_META = {
  valid_capture: { label: 'Verified Content Credentials', badge: 'success' },
  valid_ai_asserted: { label: 'Signed AI Disclosure', badge: 'warning' },
  tampered: { label: 'Altered After Signing', badge: 'danger' },
  untrusted: { label: 'Unknown Provenance', badge: 'info' },
};

export default function ProvenanceCard({ provenance }) {
  if (!provenance) return null;
  const meta = STATE_META[provenance.state] || { label: provenance.state, badge: '' };

  return (
    <div className="glass-card layer-card">
      <div className="layer-head">
        <span className="layer-title">Provenance — C2PA validation</span>
        <span className="chip deterministic">deterministic</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem', flexWrap: 'wrap' }}>
        <span className={`badge ${meta.badge}`} style={{ fontSize: '0.95rem', padding: '0.45rem 1rem' }}>
          {meta.label}
        </span>
        {provenance.signer && (
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Signed by <strong style={{ color: 'var(--text-primary)' }}>{provenance.signer}</strong>
            {provenance.trust_list_result === false && ' (signer not on the C2PA trust list)'}
          </span>
        )}
      </div>

      {provenance.explanation && <p className="inset" style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{provenance.explanation}</p>}

      {(provenance.claim_generator || provenance.digital_source_type || provenance.failed_assertion) && (
        <div className="kv-grid">
          {provenance.claim_generator && (
            <div className="kv"><span className="k">Claim generator</span><span className="v" title={provenance.claim_generator}>{provenance.claim_generator}</span></div>
          )}
          {provenance.digital_source_type && (
            <div className="kv"><span className="k">digitalSourceType</span><span className="v">{provenance.digital_source_type}</span></div>
          )}
          {provenance.failed_assertion && (
            <div className="kv"><span className="k">Failed check</span><span className="v" style={{ color: '#f87171' }}>{provenance.failed_assertion}</span></div>
          )}
        </div>
      )}

      <p className="note-text">
        Content Credentials confirm manifest <em>integrity</em>, not truthfulness — and platforms
        routinely strip them on re-encode, so their absence proves nothing by itself. Statistical
        watermarks like Google&nbsp;SynthID have no public detection API, so PeachCheck claims only
        what it can cryptographically verify.{' '}
        <a href="https://deepmind.google/science/synthid/" target="_blank" rel="noreferrer" style={{ color: 'var(--text-secondary)' }}>
          Learn about SynthID
        </a>
      </p>
    </div>
  );
}
