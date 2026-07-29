import React from 'react';

export default function IdentityPanel({ identity, exif }) {
  if (!identity) return null;
  const exifEntries = Object.entries(exif || {});

  return (
    <div className="premium-card layer-card">
      <div className="layer-head">
        <span className="layer-title">File Identity</span>
        <span className="layer-sub">schema v{identity.schema_version}</span>
      </div>
      <div className="kv-grid">
        <div className="kv"><span className="k">SHA-256</span><span className="v" title={identity.sha256}>{identity.sha256}</span></div>
        <div className="kv">
          <span className="k">Perceptual hash (dHash)</span>
          <span className="v">{identity.perceptual_hash || '—'}</span>
        </div>
        <div className="kv"><span className="k">Analyzed at (UTC)</span><span className="v">{identity.analyzed_at?.replace('T', ' ').slice(0, 19)}</span></div>
        <div className="kv"><span className="k">MIME type</span><span className="v">{identity.mime_type}</span></div>
      </div>
      <p className="note-text">
        SHA-256 proves this exact file was analyzed; the perceptual hash still matches after a
        screenshot or re-compression, so laundered copies of the same picture can be recognized.
      </p>
      <details className="collapse">
        <summary>Raw EXIF metadata ({exifEntries.length} tags)</summary>
        {exifEntries.length === 0 ? (
          <p className="note-text" style={{ fontStyle: 'italic' }}>No EXIF metadata found in this file.</p>
        ) : (
          <div className="kv-grid">
            {exifEntries.map(([key, value]) => (
              <div key={key} className="kv">
                <span className="k">{key}</span>
                <span className="v" title={value}>{value}</span>
              </div>
            ))}
          </div>
        )}
      </details>
    </div>
  );
}
