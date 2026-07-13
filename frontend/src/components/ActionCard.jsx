import React, { useState } from 'react';
import { buildPacket } from '../api';

const QUESTIONS = [
  ['satire', 'Is this media satire?'],
  ['parody', 'Is it parody?'],
  ['artistic_expression', 'Is it a work of artistic expression?'],
  ['journalism', 'Is it journalism by a bona fide news organization?'],
];

export default function ActionCard({ action, trustReport }) {
  const [answers, setAnswers] = useState({});
  const [publisher, setPublisher] = useState('');
  const [packet, setPacket] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  if (!action) return null;
  const complete = QUESTIONS.every(([key]) => answers[key] !== undefined);

  const assemble = async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await buildPacket(trustReport, answers, publisher.trim());
      setPacket(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const download = () => {
    const blob = new Blob([JSON.stringify(packet, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `peachcheck-evidence-packet-${(packet.file_sha256 || 'report').slice(0, 12)}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="glass-card layer-card">
      <div className="layer-head">
        <span className="layer-title">Civic Action — SB 9 evidence packet</span>
        <span className="chip human">human decision</span>
      </div>

      <div className="kv-grid">
        <div className="kv">
          <span className="k">Next Georgia election</span>
          <span className="v">{action.next_election_name} · {action.next_election_date}</span>
        </div>
        <div className="kv">
          <span className="k">90-day statutory window</span>
          <span className="v" style={{ color: action.within_90_day_window ? '#34d399' : undefined }}>
            {action.within_90_day_window
              ? `open — ${action.days_until_election} days to the election`
              : `not open${action.window_opens ? ` (opens ${action.window_opens})` : ''}`}
          </span>
        </div>
        <div className="kv">
          <span className="k">Deterministic gate</span>
          <span className="v" style={{ color: action.gate_passed ? '#34d399' : undefined }}>
            {action.gate_passed ? 'passed' : 'closed'}
          </span>
        </div>
      </div>

      {action.deterministic_corroboration?.length > 0 && (
        <div className="inset">
          <span className="k" style={{ fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-tertiary)' }}>
            Deterministic corroboration
          </span>
          <ul style={{ marginTop: '0.4rem', marginLeft: '1.2rem', fontFamily: 'var(--mono)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            {action.deterministic_corroboration.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      )}

      <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)' }}>{action.guidance}</p>

      {action.gate_passed && !packet && (
        <>
          <hr className="divider" />
          <div>
            <h4 style={{ fontSize: '0.95rem', marginBottom: '0.2rem' }}>Exemption questionnaire — §21-2-605(d)</h4>
            <p className="note-text">
              Georgia’s statute exempts First Amendment–protected media entirely. Answer honestly:
              an exemption means no filing is appropriate, and PeachCheck will say so.
            </p>
            {QUESTIONS.map(([key, question]) => (
              <div key={key} className="question-row">
                <span className="q">{question}</span>
                <span className="seg">
                  <button
                    type="button"
                    className={answers[key] === true ? 'on-yes' : ''}
                    onClick={() => setAnswers((a) => ({ ...a, [key]: true }))}
                  >
                    Yes
                  </button>
                  <button
                    type="button"
                    className={answers[key] === false ? 'on-no' : ''}
                    onClick={() => setAnswers((a) => ({ ...a, [key]: false }))}
                  >
                    No
                  </button>
                </span>
              </div>
            ))}
            <div style={{ marginTop: '0.9rem' }}>
              <label className="note-text" htmlFor="publisher-field" style={{ display: 'block', marginBottom: '0.35rem' }}>
                Who published this media? The statute reaches campaign-affiliated actors, so the
                packet must capture the publisher.
              </label>
              <input
                id="publisher-field"
                className="text-field"
                value={publisher}
                onChange={(e) => setPublisher(e.target.value)}
                placeholder="e.g. the sponsoring committee, campaign account, or page that posted it"
              />
            </div>
            <button className="btn" style={{ marginTop: '1rem' }} disabled={!complete || busy} onClick={assemble}>
              {busy ? 'Assembling…' : 'Assemble evidence packet'}
            </button>
            {error && <p style={{ color: 'var(--danger)', fontSize: '0.85rem', marginTop: '0.5rem' }}>{error}</p>}
          </div>
        </>
      )}

      {packet && (
        <div className="inset" style={{ borderLeft: `3px solid ${packet.packet_eligible ? 'var(--success)' : 'var(--warning)'}` }}>
          <h4 style={{ fontSize: '0.95rem', marginBottom: '0.4rem' }}>
            {packet.packet_eligible
              ? 'Packet assembled — eligible for a State Election Board complaint'
              : 'Packet assembled for your records — not eligible for filing'}
          </h4>
          <p className="note-text" style={{ marginBottom: '0.8rem' }}>{packet.submission_instructions || ''}</p>
          <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
            <button className="btn" onClick={download}>Download packet (JSON)</button>
            <button className="btn ghost" onClick={() => setPacket(null)}>Edit answers</button>
          </div>
        </div>
      )}

      <p className="note-text">
        There is no “submit” button by design: no API into the State Election Board exists, and
        pretending otherwise would be dishonest. Under §21-2-33.1(a.1) the Board must publish
        findings of completed investigations — that publication closes the civic loop.
      </p>
    </div>
  );
}
