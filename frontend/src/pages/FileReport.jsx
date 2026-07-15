import React from 'react';
import { Link } from 'react-router-dom';
import { Download, AlertTriangle } from 'lucide-react';

function readStoredAnalysis() {
  try {
    const stored = sessionStorage.getItem('peachcheck:last-analysis');
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

export default function FileReport() {
  const analysis = readStoredAnalysis();
  const report = analysis?.trust_report;

  if (!report?.identity) {
    return (
      <div className="grid-12">
        <div className="col-8 col-start-3 card">
          <h1 className="text-xl mb-4">No saved report</h1>
          <p className="text-lo mb-6">Check an image first. Then you can view and download its details here.</p>
          <Link className="btn btn-primary" to="/">Analyze an image</Link>
        </div>
      </div>
    );
  }

  const score = report.judgment?.calibrated_score;
  const availableSignals = report.forensics?.signals?.filter((signal) => signal.available) || [];
  const triggeredSignals = availableSignals.filter((signal) => signal.triggered);

  const downloadAnalysis = () => {
    const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `peachcheck-analysis-${report.identity.sha256.slice(0, 12)}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="grid-12">
      <div className="col-8 col-start-3">
        <h1 className="font-display text-xl mb-6 border-b border-ink-500 pb-4">Saved check details</h1>

        <div className="card mb-6">
          <h2 className="text-lg mb-4">What PeachCheck found</h2>
          <div className="text-sm font-mono text-lo flex-col gap-4">
            <p className="break-all"><strong className="text-hi">File:</strong> {report.identity.filename}</p>
            <p><strong className="text-hi">Checked:</strong> {new Date(report.identity.analyzed_at).toLocaleString()}</p>
            <p><strong className="text-hi">Source result:</strong> {report.provenance?.state?.replaceAll('_', ' ') || 'not available'}</p>
            <p>
              <strong className="text-hi">Image checks:</strong>{' '}
              {report.forensics ? `${triggeredSignals.length} of ${availableSignals.length} found something unusual` : 'not needed'}
            </p>
            <p>
              <strong className="text-hi">Score:</strong>{' '}
              {typeof score === 'number' ? `${(score * 100).toFixed(1)}/100` : 'no score needed'}
            </p>
            <details>
              <summary className="cursor-pointer text-hi">Technical file fingerprint</summary>
              <p className="break-all mt-2">{report.identity.sha256}</p>
            </details>
          </div>
        </div>

        <div className="bg-ink-900 border border-ink-500 p-4 rounded flex gap-3 text-sm text-lo mb-6">
          <AlertTriangle size={20} className="text-clay flex-shrink-0" />
          <p className="leading-relaxed">
            {report.action?.gate_passed
              ? 'This result has enough supporting evidence to continue to the report questionnaire.'
              : 'This result does not have enough supporting evidence for an election complaint.'}
          </p>
        </div>

        <div className="flex gap-4 stack-sm">
          <button type="button" className="btn btn-secondary flex-1" onClick={downloadAnalysis}>
            <Download size={18} /> Download technical details
          </button>
          <Link className="btn btn-primary flex-1" to="/">Analyze another image</Link>
        </div>
      </div>
    </div>
  );
}
