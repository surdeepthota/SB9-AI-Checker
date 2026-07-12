import React, { useState } from 'react';
import Uploader from './components/Uploader';
import ReportCard from './components/ReportCard';

function App() {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async (file) => {
    setLoading(true);
    setError(null);
    setReportData(null);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Analysis failed on the server');
      }
      
      const data = await response.json();
      setReportData(data);
    } catch (err) {
      setError(err.message || 'An error occurred during upload.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setReportData(null);
    setError(null);
  };

  return (
    <div className="app-container">
      <header>
        <h1>PeachCheck</h1>
        <p>A layered trust system for measuring political media compliance against Georgia's proposed SB 9 standard.</p>
      </header>

      <main>
        {error && (
          <div className="glass-card" style={{ borderLeft: '4px solid var(--danger)' }}>
            <h3 style={{ color: 'var(--danger)', marginBottom: '0.5rem' }}>Error</h3>
            <p>{error}</p>
            <button className="btn" style={{ marginTop: '1rem' }} onClick={handleReset}>Try Again</button>
          </div>
        )}

        {!reportData && !error && (
          <Uploader onUpload={handleUpload} loading={loading} />
        )}

        {reportData && !error && (
          <ReportCard data={reportData} onReset={handleReset} />
        )}
      </main>
    </div>
  );
}

export default App;
