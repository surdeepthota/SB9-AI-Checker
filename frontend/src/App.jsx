import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, Link } from 'react-router-dom';
import { ShieldCheck, Info, Search, ImageIcon, Users, BookOpen } from 'lucide-react';
import Home from './pages/Home';
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
      <nav className="nav-links desktop-only" aria-label="Primary">
        <NavLink to="/check">Check media</NavLink>
        <NavLink to="/library">Examples</NavLink>
        <NavLink to="/community">Community</NavLink>
        <NavLink to="/methodology">How it works</NavLink>
      </nav>
      <div className="nav-about flex items-center gap-4 desktop-only">
        <a href="https://github.com/alienec/CongressionalAppChallenge" target="_blank" rel="noreferrer" className="text-lo flex items-center gap-2 text-sm" style={{ textDecoration: 'none' }}>
          <Info size={16} />
          About
        </a>
      </div>
    </header>
  );
}

function BottomNav() {
  return (
    <nav className="bottom-nav mobile-only" aria-label="Mobile">
      <NavLink to="/check" className="bottom-nav-item">
        <Search size={20} />
        <span>Check</span>
      </NavLink>
      <NavLink to="/library" className="bottom-nav-item">
        <ImageIcon size={20} />
        <span>Examples</span>
      </NavLink>
      <NavLink to="/community" className="bottom-nav-item">
        <Users size={20} />
        <span>Community</span>
      </NavLink>
      <NavLink to="/methodology" className="bottom-nav-item">
        <BookOpen size={20} />
        <span>Method</span>
      </NavLink>
    </nav>
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
            <Route path="/" element={<Home />} />
            <Route path="/check" element={<CheckMedia />} />
            <Route path="/report/:id" element={<TrustReport />} />
            <Route path="/report/:id/file" element={<FileReport />} />
            <Route path="/library" element={<EvidenceLibrary />} />
            <Route path="/community" element={<Community />} />
            <Route path="/methodology" element={<Methodology />} />
          </Routes>
        </main>
        <BottomNav />
      </div>
    </BrowserRouter>
  );
}

export default App;
