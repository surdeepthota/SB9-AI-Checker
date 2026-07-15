import React, { useState } from 'react';

const STATE_BADGES = {
  valid_capture: ['success', 'verified capture'],
  valid_ai_asserted: ['warning', 'signed AI'],
  tampered: ['danger', 'tampered'],
  untrusted: ['info', 'unknown provenance'],
};

export default function Uploader({ onUpload, onSample, samples, loading }) {
  const [dragActive, setDragActive] = useState(false);
  const [isCampaignAd, setIsCampaignAd] = useState(false);
  const [clipUrl, setClipUrl] = useState('');
  const [strictClipMode, setStrictClipMode] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) onUpload(e.dataTransfer.files[0], isCampaignAd);
  };

  if (loading) {
    return (
      <div className="premium-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', padding: '4rem' }}>
        <div className="spinner" />
        <h3 style={{ margin: 0 }}>Running the trust pipeline…</h3>
        <p style={{ color: 'var(--text-secondary)', textAlign: 'center', maxWidth: '30rem' }}>
          Verifying Content Credentials, then routing to disclosure measurement or the forensic
          panel. First analysis loads model weights and can take a little longer.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="premium-card">
        <form
          className={`dropzone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-upload').click()}
          onSubmit={(e) => e.preventDefault()}
        >
          <input
            id="file-upload"
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={(e) => {
              if (e.target.files?.[0]) onUpload(e.target.files[0], isCampaignAd);
              e.target.value = '';
            }}
          />
          <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: '0.9rem', color: 'var(--accent-primary)' }}>
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <h3 style={{ marginBottom: '0.4rem', fontSize: '1.2rem' }}>Analyze a still image</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
            Drag &amp; drop or click to browse. Nothing you upload is stored.
          </p>
        </form>
        <label className="toggle-row">
          <input
            type="checkbox"
            checked={isCampaignAd}
            onChange={(e) => setIsCampaignAd(e.target.checked)}
          />
          This is a campaign advertisement — also measure its SB 9 disclosure
        </label>
      </div>

      <div className="glass-card layer-card">
        <div className="layer-head">
          <span className="layer-title">Short Clip Link</span>
          <span className="layer-sub">paste a normal TikTok, YouTube, Instagram, or direct clip link</span>
        </div>
        <div className="url-uploader">
          <input
            type="url"
            value={clipUrl}
            placeholder="https://www.tiktok.com/... or https://www.youtube.com/watch?v=..."
            onChange={(e) => setClipUrl(e.target.value)}
          />
          <button
            type="button"
            className="btn"
            onClick={() => onUpload({ clipUrl: clipUrl.trim(), strictClipMode }, isCampaignAd)}
            disabled={!clipUrl.trim()}
          >
            Analyze clip
          </button>
        </div>
        <label className="toggle-row" style={{ justifyContent: 'flex-start', marginTop: 0 }}>
          <input
            type="checkbox"
            checked={strictClipMode}
            onChange={(e) => setStrictClipMode(e.target.checked)}
          />
          Strict clip mode — sample more frames and weigh repeated suspicious frames more aggressively
        </label>
        <p className="note-text">
          The server resolves the clip, samples a few frames, and runs the still-image trust pipeline on
          each one. No raw `.mp4` link is required anymore.
        </p>
      </div>

      {samples?.length > 0 && (
        <div className="premium-card layer-card">
          <div className="layer-head">
            <span className="layer-title">Or try the demo corpus</span>
            <span className="layer-sub">real C2PA test files + fictional ad mockups, ground truth known</span>
          </div>
          <div className="sample-gallery">
            {samples.map((sample) => {
              const [badge, label] = STATE_BADGES[sample.expected_state] || ['', sample.expected_state];
              return (
                <button
                  key={sample.filename}
                  type="button"
                  className="sample-tile"
                  onClick={() => onSample(sample.filename, isCampaignAd)}
                >
                  <span className={`badge ${badge}`} style={{ fontSize: '0.7rem', alignSelf: 'flex-start' }}>{label}</span>
                  <span className="name">{sample.filename}</span>
                  {sample.notes && <span className="note">{sample.notes}</span>}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
}
