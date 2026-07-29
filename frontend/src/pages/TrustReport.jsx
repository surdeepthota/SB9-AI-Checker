import React, { useEffect, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { Download } from 'lucide-react';
import { ConfidenceBand, LayerRow } from '../components/Shared';
import { loadReport } from '../lib/reportCache';

const PROVENANCE_META = {
  valid_capture: ['valid', 'Source verified'],
  valid_ai_asserted: ['untrusted', 'AI use declared'],
  tampered: ['tampered', 'File changed'],
  untrusted: ['untrusted', 'Source unknown'],
};

const BAND_META = {
  leans_authentic: ['valid', 'Looks like a normal camera image'],
  abstain: ['abstain', 'Not enough evidence'],
  moderate_signal: ['untrusted', 'Some signs found'],
  strong_signal: ['tampered', 'Strong signs found'],
};

const SIGNAL_LABELS = {
  metadata: 'Camera details',
  error_level_analysis: 'Signs of pasted-in edits',
  fft_frequency_domain: 'Unusual image patterns',
  ml_classifier: 'AI image checker',
};

const CHECK_LABELS = {
  content_ai_use_stated: 'Says AI was used',
  content_events_caveat_stated: 'Warns that events may not be real',
  content_sponsor_named: 'Names who paid for the ad',
  text_height_ratio: 'Warning is large enough',
  visible_duration_ratio: 'Warning stays visible long enough',
  contrast_ratio: 'Warning is easy to read',
};

function formatSignalName(name) {
  return String(name || '').replaceAll('_', ' ');
}

function ClipTrustReport({ clip }) {
  const summary = clip.clip_summary;
  const judgment = summary?.judgment;
  const score = judgment?.calibrated_score ?? summary?.clip_decision_score;
  const bandMeta = BAND_META[judgment?.band] || ['abstain', 'No clip judgment produced'];

  const downloadReport = () => {
    const blob = new Blob([JSON.stringify(clip, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'peachcheck-clip-report.json';
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="grid-12">
      <div className="col-10 col-start-2">
        <p className="text-xs font-mono text-lo mb-2 uppercase tracking-wide">Video check finished</p>
        <h1 className="text-xl mb-4">Overall result: {bandMeta[1]}</h1>
        <p className="text-lo mb-8 break-all">{clip.clip_url}</p>

        {clip.source_ai_disclosure && (
          <div className="card mb-6" style={{ borderColor: 'var(--state-tampered)' }}>
            <p className="text-xs font-mono text-state-tampered mb-2 uppercase tracking-wide">This post says it uses AI</p>
            <p className="text-base">"{clip.source_ai_disclosure}"</p>
            <p className="text-sm text-lo mt-2">The post's own description says the video was made with AI. That is stronger evidence than a visual guess.</p>
          </div>
        )}

        <div className="card mb-6">
          <div className="flex justify-between items-center gap-4 flex-wrap mb-6">
            <div>
              <p className="text-sm text-lo mb-2">Based on {summary?.sampled_frames || clip.reports?.length || 0} moments from the video</p>
              <span className={`badge badge-${bandMeta[0]}`}>{bandMeta[1]}</span>
            </div>
            <div className="font-mono text-lg">
              {typeof score === 'number' ? `${(score * 100).toFixed(1)}/100` : 'No score'}
            </div>
          </div>

          {typeof score === 'number' && <ConfidenceBand score={score * 100} size="full" />}

          <div className="info-cols text-sm text-lo mt-8">
            <div><strong className="text-hi">Duration</strong><br />{Math.round(clip.duration_seconds || 0)} seconds</div>
            <div><strong className="text-hi">Moments checked</strong><br />{clip.reports?.length || 0}</div>
            <div><strong className="text-hi">Highest single score</strong><br />{typeof summary?.strongest_frame_score === 'number' ? `${(summary.strongest_frame_score * 100).toFixed(1)}/100` : 'Not available'}</div>
            <div><strong className="text-hi">Check type</strong><br />{summary?.strict_mode ? 'Extra careful' : 'Standard'}</div>
          </div>

          <p className="mt-6 text-sm text-lo">
            {clip.source_ai_disclosure
              ? 'The post directly says AI was used. The visual checks are shown below as extra information.'
              : `We checked ${clip.reports?.length || 0} moments from the video. The highest visual-check score was ${typeof summary?.strongest_frame_score === 'number' ? `${(summary.strongest_frame_score * 100).toFixed(1)}/100` : 'not available'}.`}
          </p>
        </div>

        <h2 className="text-lg mb-4">Moments we checked</h2>
        <div className="clip-frame-grid mb-8">
          {clip.reports?.map((frame) => {
            const frameReport = frame.analysis?.trust_report;
            const frameScore = frameReport?.judgment?.calibrated_score;
            return (
              <article className="card" key={`${frame.frame_number}-${frame.seconds}`}>
                {frame.preview_data_url && (
                  <img className="clip-frame-preview mb-4" src={frame.preview_data_url} alt={`Sampled clip frame at ${frame.label}`} />
                )}
                <p className="font-mono text-xs text-clay mb-2">Moment {frame.frame_number} · {frame.label}</p>
                <p className="text-sm mb-2">{frameReport?.headline || 'No frame report produced.'}</p>
                <p className="font-mono text-xs text-lo">
                  {typeof frameScore === 'number' ? `Visual-check score ${(frameScore * 100).toFixed(1)}/100` : 'No visual-check score'}
                </p>
              </article>
            );
          })}
        </div>

        <div className="flex gap-4 stack-sm">
          <button type="button" className="btn btn-secondary flex-1" onClick={downloadReport}>
            <Download size={18} /> Download technical details
          </button>
          <Link className="btn btn-primary flex-1" to="/">Analyze another</Link>
        </div>
      </div>
    </div>
  );
}

export default function TrustReport() {
  const location = useLocation();
  const { id } = useParams();
  const hasNavState = Boolean(location.state?.clip || location.state?.analysis);
  const [cached, setCached] = useState(null);
  const [loading, setLoading] = useState(!hasNavState);

  useEffect(() => {
    // Navigation state (set right after an analysis completes) is already in memory
    // and always wins. It's only absent after a reload, in which case this pulls the
    // same report back out of IndexedDB — the whole reason this cache exists.
    if (hasNavState) {
      setLoading(false);
      return undefined;
    }
    let cancelled = false;
    const key = id?.startsWith('clip-') ? 'last-clip-analysis' : 'last-analysis';
    loadReport(key).then((value) => {
      if (!cancelled) {
        setCached(value);
        setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, hasNavState]);

  if (loading) {
    return (
      <div className="grid-12">
        <div className="col-8 col-start-3 card">
          <p className="text-lo">Loading your last result…</p>
        </div>
      </div>
    );
  }

  const clip = location.state?.clip || (id?.startsWith('clip-') ? cached : null);
  if (clip?.reports) return <ClipTrustReport clip={clip} />;

  const analysis = location.state?.analysis || (!id?.startsWith('clip-') ? cached : null);
  const report = analysis?.trust_report;

  if (!report?.identity) {
    return (
      <div className="grid-12">
        <div className="col-8 col-start-3 card">
          <h1 className="text-xl mb-4">No completed analysis</h1>
          <p className="text-lo mb-6">
            PeachCheck did not receive a real report from the backend, so there is no result to display.
          </p>
          <Link className="btn btn-primary" to="/">Choose an image</Link>
        </div>
      </div>
    );
  }

  const provenanceMeta = PROVENANCE_META[report.provenance?.state] || ['abstain', 'Not available'];
  const judgmentMeta = BAND_META[report.judgment?.band] || ['abstain', 'No score produced'];
  const availableSignals = report.forensics?.signals?.filter((signal) => signal.available) || [];
  const triggeredSignals = availableSignals.filter((signal) => signal.triggered);
  const score = report.judgment?.calibrated_score;

  const downloadReport = () => {
    const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `peachcheck-report-${report.identity.sha256.slice(0, 12)}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="grid-12">
      <div className="col-5 flex-col gap-4 report-rail">
        <div className="mb-4">
          <p className="text-xs font-mono text-lo mb-2 uppercase tracking-wide">Photo check finished</p>
          <h2 className="font-display text-lg break-all">{report.identity.filename}</h2>
        </div>

        <LayerRow title="Source check" badgeState={provenanceMeta[0]} badgeLabel={provenanceMeta[1]} defaultOpen>
          <div className="bg-ink-900 p-3 rounded text-xs">
            <p className="mb-2">
              {report.provenance?.state === 'valid_capture' && 'This file includes a trusted camera record.'}
              {report.provenance?.state === 'valid_ai_asserted' && 'This file includes a trusted record saying AI was used.'}
              {report.provenance?.state === 'tampered' && 'The trusted source record no longer matches this file, so the file changed after it was signed.'}
              {report.provenance?.state === 'untrusted' && 'This file has no source record PeachCheck can verify. That does not prove AI was used.'}
            </p>
            <details className="text-lo mt-2">
              <summary className="cursor-pointer">Technical details</summary>
              {report.provenance?.signer && <p className="mt-2"><strong>Signed by:</strong> {report.provenance.signer}</p>}
              <p className="mt-2 break-all"><strong>File fingerprint:</strong> {report.identity.sha256}</p>
            </details>
          </div>
        </LayerRow>

        <LayerRow
          title="AI warning"
          badgeState={report.measurement ? (report.measurement.checks?.every((check) => check.passed) ? 'valid' : 'tampered') : 'abstain'}
          badgeLabel={report.measurement ? `${report.measurement.checks?.filter((check) => check.passed).length || 0}/${report.measurement.checks?.length || 0} passed` : 'Not run'}
        >
          <div className="bg-ink-900 p-3 rounded text-xs flex-col gap-2">
            {report.measurement?.checks?.map((check) => (
              <div key={check.name} className="flex justify-between gap-4 pb-1" style={{ borderBottom: '1px solid var(--ink-500)' }}>
                <span>{CHECK_LABELS[check.name] || formatSignalName(check.name)}</span>
                <span className={check.passed ? 'text-state-valid' : 'text-state-tampered'}>
                  {check.passed ? 'Passed' : 'Failed'}
                </span>
              </div>
            )) || <p className="text-lo">This check was not needed.</p>}
          </div>
        </LayerRow>

        <LayerRow
          title="Image checks"
          badgeState={report.forensics ? (triggeredSignals.length ? 'untrusted' : 'valid') : 'abstain'}
          badgeLabel={report.forensics ? `${triggeredSignals.length} of ${availableSignals.length} triggered` : 'Not run'}
        >
          <div className="bg-ink-900 p-3 rounded text-xs flex-col gap-2">
            {report.forensics?.signals?.map((signal) => (
              <div key={signal.name} className="flex justify-between gap-4 pb-1" style={{ borderBottom: '1px solid var(--ink-500)' }}>
                <span>{SIGNAL_LABELS[signal.name] || formatSignalName(signal.name)}</span>
                <span className={!signal.available ? 'text-lo' : signal.triggered ? 'text-state-tampered' : 'text-state-valid'}>
                  {!signal.available ? 'Could not run' : signal.triggered ? 'Found something' : 'Nothing unusual'}
                </span>
              </div>
            )) || <p className="text-lo">This check was not needed.</p>}
          </div>
        </LayerRow>

        <LayerRow title="Overall result" badgeState={judgmentMeta[0]} badgeLabel={judgmentMeta[1]}>
          <div className="bg-ink-900 p-3 rounded text-xs">
            {typeof score === 'number' ? (
              <>
                <p><strong>Visual-check score:</strong> {(score * 100).toFixed(1)}/100</p>
                <p className="mt-2 text-lo">This score is a clue, not proof by itself.</p>
              </>
            ) : (
              <p className="text-lo">No visual-check score was needed for this file.</p>
            )}
          </div>
        </LayerRow>
      </div>

      <div className="col-7 report-main">
        <div className="card mb-8">
          <h1 className="font-display text-xl mb-6">{report.headline || 'Analysis complete'}</h1>

          {typeof score === 'number' ? (
            <ConfidenceBand score={score * 100} size="full" />
          ) : (
            <div className="p-4 bg-ink-900 rounded border border-ink-500 text-sm text-lo">
              No score was needed because the source record already answered the question.
            </div>
          )}

          <div className="mt-8 p-4 bg-ink-900 rounded border border-ink-500 text-sm">
            <p><strong>Checked:</strong> {new Date(report.identity.analyzed_at).toLocaleString()}</p>
          </div>
        </div>

        <div className="flex gap-4 stack-sm">
          <button type="button" className="btn btn-secondary flex-1" onClick={downloadReport}>
            <Download size={18} />
            Download technical details
          </button>
          <Link className="btn btn-primary flex-1" to="/">Analyze another image</Link>
        </div>
      </div>
    </div>
  );
}
