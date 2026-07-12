import React, { useCallback, useState } from 'react';

export default function Uploader({ onUpload, loading }) {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onUpload(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0]);
    }
  };

  const style = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '4rem 2rem',
    border: `2px dashed ${dragActive ? 'var(--accent-primary)' : 'var(--card-border)'}`,
    borderRadius: '16px',
    textAlign: 'center',
    background: dragActive ? 'rgba(249, 115, 22, 0.05)' : 'transparent',
    transition: 'all 0.2s ease',
    cursor: 'pointer'
  };

  if (loading) {
    return (
      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', padding: '4rem' }}>
        <div style={{
          width: '40px', height: '40px', 
          border: '4px solid rgba(249, 115, 22, 0.2)',
          borderTop: '4px solid var(--accent-primary)',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
        <h3 style={{ margin: 0 }}>Running Provenance Check...</h3>
        <p style={{ color: 'var(--text-secondary)' }}>Extracting C2PA manifests and signatures</p>
        <style>{`
          @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        `}</style>
      </div>
    );
  }

  return (
    <div className="glass-card">
      <form 
        style={style} 
        onDragEnter={handleDrag} 
        onDragLeave={handleDrag} 
        onDragOver={handleDrag} 
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-upload').click()}
      >
        <input 
          id="file-upload" 
          type="file" 
          multiple={false} 
          accept="image/*" 
          onChange={handleChange} 
          style={{ display: 'none' }} 
        />
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: '1rem', color: 'var(--accent-primary)' }}>
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
        <h3 style={{ marginBottom: '0.5rem', fontSize: '1.25rem' }}>Upload Media for Analysis</h3>
        <p style={{ color: 'var(--text-secondary)' }}>Drag and drop an image here, or click to browse</p>
      </form>
    </div>
  );
}
