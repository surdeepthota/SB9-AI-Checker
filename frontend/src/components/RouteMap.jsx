import React from 'react';

const LAYER_ORDER = ['provenance', 'measurement', 'forensics', 'judgment', 'action'];
const LAYER_LABELS = {
  provenance: 'Provenance',
  measurement: 'Measurement',
  forensics: 'Forensics',
  judgment: 'Judgment',
  action: 'Civic Action',
};

// "Which layers ran, and why" is itself a finding — a verified capture proudly
// skipping the ML panel is the layered-trust story in one glance.
export default function RouteMap({ route }) {
  const byLayer = Object.fromEntries((route || []).map((step) => [step.layer, step]));
  return (
    <div className="premium-card layer-card">
      <div className="layer-head">
        <span className="layer-title">Pipeline Route</span>
        <span className="layer-sub">each layer catches what the previous one misses</span>
      </div>
      <div className="route-map">
        {LAYER_ORDER.map((layer) => {
          const step = byLayer[layer];
          const ran = step?.ran;
          return (
            <div key={layer} className={`route-step ${ran ? 'ran' : 'skipped'}`}>
              <span className="step-name">
                {ran ? '●' : '○'} {LAYER_LABELS[layer]}
              </span>
              <div className="step-reason">{step?.reason || 'No routing decision recorded.'}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
