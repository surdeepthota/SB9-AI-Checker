import React from 'react';

export function ProvenanceBadge({ state, label }) {
  let badgeClass = '';
  switch (state) {
    case 'valid': badgeClass = 'badge-valid'; break;
    case 'tampered': badgeClass = 'badge-tampered'; break;
    case 'untrusted': badgeClass = 'badge-untrusted'; break;
    case 'abstain': badgeClass = 'badge-abstain'; break;
    default: badgeClass = 'badge-abstain'; break;
  }

  return (
    <span className={`badge ${badgeClass}`}>
      {label}
    </span>
  );
}

export function ConfidenceBand({ score, size = 'full' }) {
  // score is 0 to 100 for visual marker placement.
  // Band widths mirror the backend: Leans 30%, Abstain 40%, Moderate 20%, Strong 10%.

  const markerPosition = Math.max(0, Math.min(100, score));

  return (
    <div className={`confidence-band-container ${size === 'sparkline' ? 'sparkline' : ''}`}>
      <div className="confidence-band">
        <div className="band-segment band-leans">Looks normal</div>
        <div className="band-segment band-abstain" style={{
          backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,0.05) 10px, rgba(255,255,255,0.05) 20px)'
        }}>Not enough evidence</div>
        <div className="band-segment band-moderate">Some signs</div>
        <div className="band-segment band-strong">Strong signs</div>

        {/* Marker */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            bottom: 0,
            left: `${markerPosition}%`,
            width: '2px',
            background: 'var(--text-hi)',
            transform: 'translateX(-50%)',
            boxShadow: '0 0 4px rgba(0,0,0,0.5)',
            zIndex: 10
          }}
        >
          <div style={{
            position: 'absolute',
            top: '-12px',
            left: '50%',
            transform: 'translateX(-50%)',
            width: 0,
            height: 0,
            borderLeft: '6px solid transparent',
            borderRight: '6px solid transparent',
            borderTop: '8px solid var(--text-hi)'
          }} />
        </div>
      </div>
      {size === 'full' && (
        <div className="flex justify-between mt-2 font-mono text-xs text-lo">
          <span>0%</span>
          <span>50%</span>
          <span>100%</span>
        </div>
      )}
    </div>
  );
}

export function LayerRow({ title, badgeState, badgeLabel, children, defaultOpen = false }) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen);

  return (
    <div className="timeline-row">
      <button
        type="button"
        className="timeline-header"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-4">
          <span className="font-display text-base">{title}</span>
        </div>
        <div className="flex items-center gap-2">
          <ProvenanceBadge state={badgeState} label={badgeLabel} />
          <span className="text-lo font-mono text-xs ml-2" aria-hidden="true">{isOpen ? '▲' : '▼'}</span>
        </div>
      </button>
      {isOpen && (
        <div className="timeline-content">
          {children}
        </div>
      )}
    </div>
  );
}
