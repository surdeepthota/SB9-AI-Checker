import React from 'react';
import RouteMap from './RouteMap';
import ProvenanceCard from './ProvenanceCard';
import MeasurementCard from './MeasurementCard';
import ForensicsCard from './ForensicsCard';
import JudgmentCard from './JudgmentCard';
import ActionCard from './ActionCard';
import IdentityPanel from './IdentityPanel';

// Renders the trust report and nothing else: every fact shown here was written by a
// pipeline layer server-side. The UI never re-derives a verdict.
export default function ReportCard({ data, previewUrl, onReset, title = null, showReset = true }) {
  const report = data.trust_report;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.4rem' }}>
      <div className="glass-card headline-banner" style={{ display: 'flex', gap: '1.4rem', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <div style={{ flex: '1 1 380px' }}>
          {title && <div className="frame-label">{title}</div>}
          {report.headline}
          <div className="filename">{report.identity.filename}</div>
        </div>
        <div style={{ display: 'flex', gap: '0.9rem', alignItems: 'center' }}>
          {previewUrl && (
            <img
              src={previewUrl}
              alt="Analyzed media preview"
              style={{ width: '96px', height: '96px', objectFit: 'cover', borderRadius: '10px', border: '1px solid var(--card-border)' }}
            />
          )}
          {showReset && <button className="btn ghost" onClick={onReset}>Analyze another</button>}
        </div>
      </div>

      <RouteMap route={report.route} />
      <ProvenanceCard provenance={report.provenance} />
      <MeasurementCard measurement={report.measurement} />
      <ForensicsCard forensics={report.forensics} />
      <JudgmentCard judgment={report.judgment} />
      <ActionCard action={report.action} trustReport={report} />
      <IdentityPanel identity={report.identity} exif={data.exif_data} />
    </div>
  );
}
