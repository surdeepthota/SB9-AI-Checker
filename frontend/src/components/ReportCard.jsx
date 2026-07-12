import React from 'react';

export default function ReportCard({ data, onReset }) {
  const report = data.trust_report;
  const exif = data.exif_data;
  
  const prov = report?.provenance || {};
  const isAI = prov.state === 'valid_ai_asserted';
  const isCapture = prov.state === 'valid_capture';
  const isUntrusted = prov.state === 'untrusted';
  const isTampered = prov.state === 'tampered';

  let statusColor = 'var(--text-secondary)';
  let statusText = 'Unknown State';
  let badgeClass = '';

  if (isAI) {
    statusColor = 'var(--warning)';
    statusText = 'AI-Generated Media (Signed)';
    badgeClass = 'warning';
  } else if (isCapture) {
    statusColor = 'var(--success)';
    statusText = 'Verified Camera Capture';
    badgeClass = 'success';
  } else if (isTampered) {
    statusColor = 'var(--danger)';
    statusText = 'Tampered Content';
    badgeClass = 'danger';
  } else if (isUntrusted) {
    statusColor = 'var(--info)';
    statusText = 'Unknown Provenance';
    badgeClass = 'info';
  }

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* Header Section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--card-border)', paddingBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>Analysis Complete</h2>
          <p style={{ color: 'var(--text-secondary)', fontFamily: 'monospace', fontSize: '0.875rem' }}>
            {report.identity.filename}
          </p>
        </div>
        <button className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={onReset}>
          Analyze Another
        </button>
      </div>

      {/* Provenance Verdict */}
      <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '12px' }}>
        <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1rem' }}>
          Layer 1: Cryptographic Provenance (C2PA)
        </h3>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <span className={`badge ${badgeClass}`} style={{ fontSize: '1rem', padding: '0.5rem 1rem' }}>
            {statusText}
          </span>
          {prov.signer && (
            <span style={{ color: 'var(--text-secondary)' }}>Signed by: <strong style={{ color: 'var(--text-primary)' }}>{prov.signer}</strong></span>
          )}
        </div>

        {isUntrusted && (
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
            <strong>Note:</strong> This media contains no C2PA cryptographic signature. This is common when images are shared on social media or messaging apps, as they often strip metadata. We cannot verify its origin cryptographically.
          </p>
        )}
        
        {isAI && (
          <p style={{ color: 'var(--warning)', fontSize: '0.9rem', lineHeight: '1.6' }}>
            This file carries a valid cryptographic signature asserting it was generated using an AI model. Under Georgia's proposed SB 9 standard, this media requires explicit disclosure if used in a political campaign context.
          </p>
        )}
      </div>

      {/* EXIF Data Panel */}
      <div>
        <h3 style={{ fontSize: '1.125rem', marginBottom: '1rem' }}>Raw EXIF Metadata</h3>
        {Object.keys(exif).length === 0 ? (
          <p style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>No EXIF metadata found.</p>
        ) : (
          <div style={{ 
            display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', 
            gap: '0.75rem', 
            background: 'rgba(0,0,0,0.1)', 
            padding: '1rem', 
            borderRadius: '8px' 
          }}>
            {Object.entries(exif).map(([key, value]) => (
              <div key={key} style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>{key}</span>
                <span style={{ fontSize: '0.875rem', fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={value}>{value}</span>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
