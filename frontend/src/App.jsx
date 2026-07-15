import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, Link } from 'react-router-dom';
import { ShieldCheck, Info } from 'lucide-react';
import CheckMedia from './pages/CheckMedia';
import TrustReport from './pages/TrustReport';
import EvidenceLibrary from './pages/EvidenceLibrary';
import Community from './pages/Community';
import Methodology from './pages/Methodology';
import FileReport from './pages/FileReport';

function TopNav() {
  return (
    <header className="top-nav">
      <Link to="/" className="logo nav-brand">
        <span className="flex items-center gap-2">
          <ShieldCheck size={28} />
          PeachCheck
        </span>
      </Link>
      <nav className="nav-links" aria-label="Primary">
        <NavLink to="/" end>Check media</NavLink>
        <NavLink to="/library">Examples</NavLink>
        <NavLink to="/community">Community</NavLink>
        <NavLink to="/methodology">How it works</NavLink>
      </nav>
      <div className="nav-about flex items-center gap-4">
        <a href="https://github.com/alienec/CongressionalAppChallenge" target="_blank" rel="noreferrer" className="text-lo flex items-center gap-2 text-sm" style={{ textDecoration: 'none' }}>
          <Info size={16} />
          About
        </a>
      </div>
    </header>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <a href="#main-content" className="skip-link">Skip to main content</a>
        <TopNav />
        <main className="main-content" id="main-content">
          <Routes>
            <Route path="/" element={<CheckMedia />} />
            <Route path="/report/:id" element={<TrustReport />} />
            <Route path="/report/:id/file" element={<FileReport />} />
            <Route path="/library" element={<EvidenceLibrary />} />
            <Route path="/community" element={<Community />} />
            <Route path="/methodology" element={<Methodology />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
