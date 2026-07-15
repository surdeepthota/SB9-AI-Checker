import React from 'react';

const ICONS = {
  calendar: 'M7 3v3M17 3v3M4 8h16M5.5 5h13A1.5 1.5 0 0 1 20 6.5v13a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 19.5v-13A1.5 1.5 0 0 1 5.5 5Z',
  mask: 'M4 9c1.6-1.3 3.4-2 5.5-2 1 0 1.9.15 2.5.5.6-.35 1.5-.5 2.5-.5 2.1 0 3.9.7 5.5 2-.3 3.7-1.7 8-5 8-1.2 0-2.1-.5-3-1.4-.9.9-1.8 1.4-3 1.4-3.3 0-4.7-4.3-5-8Z M8.5 10.5h.01M15.5 10.5h.01',
  megaphone: 'M3 10v4a1 1 0 0 0 1 1h2l4.4 3.2a.6.6 0 0 0 .95-.48V6.28a.6.6 0 0 0-.95-.48L6 9H4a1 1 0 0 0-1 1Z M15 8.5c1 .8 1 6.2 0 7 M18 6.5c2 1.6 2 9.4 0 11',
  landmark: 'M4 21h16M5 21V10M9 21V10M15 21V10M19 21V10M2.5 10 12 4l9.5 6M4 10h16',
  check: 'M5 13l4 4L19 7',
  download: 'M12 4v11m0 0-4-4m4 4 4-4M5 19h14',
  arrow: 'M5 12h13m0 0-5-5m5 5-5 5',
};

function Icon({ name, size = 20, strokeWidth = 1.8 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={ICONS[name]} />
    </svg>
  );
}

function IconBadge({ name, tone = 'accent', size = 44 }) {
  return (
    <div className={`icon-badge ${tone}`} style={{ width: size, height: size }}>
      <Icon name={name} size={size * 0.5} />
    </div>
  );
}

function ExemptionCard({ icon, title, children }) {
  return (
    <div className="premium-card exemption-card">
      <div className="exemption-head">
        <IconBadge name={icon} tone="neutral" size={40} />
        <h3 className="card-title">{title}</h3>
      </div>
      <p className="note-text">{children}</p>
    </div>
  );
}

export default function PlatformPage({ onAnalyze }) {
  return (
    <>
      <header className="page-header">
        <div className="page-eyebrow badge accent">
          <Icon name="landmark" size={13} strokeWidth={2.2} />
          Compliance framework
        </div>
        <h1>Georgia SB 9 disclosure framework</h1>
        <p>
          A plain-language guide to the State of Georgia&rsquo;s Senate Bill 9 requirements for
          AI-generated and heavily manipulated political media — when disclosure is required, who is
          exempt, and how the State Election Board reviews reports.
        </p>
      </header>

      <div className="premium-card mandate-card">
        <IconBadge name="calendar" tone="warning" size={56} />
        <div>
          <span className="layer-title" style={{ color: 'var(--warning)' }}>Key mandate</span>
          <h2 className="card-title" style={{ fontSize: '1.3rem', marginTop: '0.35rem' }}>The 90-day window</h2>
          <p className="note-text" style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
            Disclosure requirements are triggered for any materially deceptive audio or visual media
            published, broadcast, or distributed within the <strong style={{ color: 'var(--text-primary)' }}>90 days
            immediately preceding an election</strong>. Content inside this window carries the highest
            compliance risk and the shortest runway to correct it.
          </p>
        </div>
      </div>

      <div>
        <div className="section-heading">
          <h2>Recognized legal exemptions</h2>
        </div>
        <div className="two-col">
          <ExemptionCard icon="mask" title="Satire &amp; parody">
            Content primarily designed for comedic effect, satire, or parody is structurally exempt
            from the disclosure mandate. The comedic nature must be clearly evident to a reasonable
            viewer, or carry a standard disclaimer, to avoid classification as deceptive media.
          </ExemptionCard>
          <ExemptionCard icon="megaphone" title="Journalism &amp; reporting">
            Bona fide news organizations, broadcasters, and registered journalistic entities are
            exempt when publishing manipulated media strictly to report on it. Objective reporting in
            the public interest nullifies the creator&rsquo;s disclosure requirement.
          </ExemptionCard>
        </div>
      </div>

      <div className="feedback-grid">
        <div className="premium-card">
          <div className="exemption-head">
            <IconBadge name="landmark" tone="neutral" size={40} />
            <h3 className="card-title">The feedback loop</h3>
          </div>
          <p className="note-text" style={{ marginTop: '0.5rem' }}>
            The State Election Board (SEB) operates a structured feedback loop for citizen and
            organizational reports of undeclared synthetic media.
          </p>
          <ul className="check-list">
            <li><Icon name="check" size={16} /><span>Expedited review process during the 90-day window.</span></li>
            <li><Icon name="check" size={16} /><span>Authority to issue immediate takedown requests to platforms.</span></li>
          </ul>
        </div>

        <div className="premium-card cta-card">
          <h3 className="card-title" style={{ color: '#fff' }}>Need direct assistance?</h3>
          <p style={{ color: 'rgba(255,255,255,0.72)', fontSize: '0.85rem', lineHeight: 1.55, marginTop: '0.4rem' }}>
            Run a specific media asset through PeachCheck&rsquo;s five-layer pipeline before you file
            or respond to a report.
          </p>
          <button className="btn" style={{ marginTop: '1.25rem', background: '#fff', color: 'var(--accent-primary)', borderColor: '#fff' }} onClick={onAnalyze}>
            Analyze media now <Icon name="arrow" size={16} />
          </button>
        </div>
      </div>

      <footer className="platform-footer">
        <div>
          <h4 className="card-title">Ensure full compliance today</h4>
          <p className="note-text">Download the checklist to verify your media assets against SB 9 criteria.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <a className="btn ghost" href="mailto:compliance@peachcheck.example">Contact legal counsel</a>
          <button className="btn">
            <Icon name="download" size={16} /> Download checklist
          </button>
        </div>
      </footer>
    </>
  );
}
