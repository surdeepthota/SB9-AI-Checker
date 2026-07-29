import React from 'react';
import { Link } from 'react-router-dom';

function Home() {
  return (
    <>
      <style>{`
        .material-symbols-outlined {
          font-family: 'Material Symbols Outlined';
          font-weight: normal;
          font-style: normal;
          display: inline-block;
          line-height: 1;
          text-transform: none;
          letter-spacing: normal;
          word-wrap: normal;
          white-space: nowrap;
          direction: ltr;
        }
        
        @keyframes subtleFloat {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-6px); }
        }
        .animate-subtle-float {
          animation: subtleFloat 4s ease-in-out infinite;
        }
        
        /* Glassmorphism utility removed for clinical look */
    `}</style>
      <main className="flex-grow flex flex-col gap-[64px] px-margin-mobile">
{/* Hero Section */}
<section className="flex flex-col items-center text-center mt-[40px]">
<div className="mb-8 relative w-full aspect-square max-w-[280px] mx-auto rounded-full bg-surface-container-low flex items-center justify-center border border-outline-variant">
{/* Abstract scanning visualization */}
<div className="absolute inset-4 rounded-full border border-outline-variant/50"></div>
<div className="z-10 flex flex-col items-center">
<span className="material-symbols-outlined text-[96px] text-primary animate-subtle-float" style={{ fontVariationSettings: "'FILL' 1" }}>gpp_good</span>
<div className="h-1 w-[120px] bg-primary mt-4 rounded-full"></div>
</div>
</div>
<h1 className="font-headline-lg-mobile text-headline-lg-mobile text-on-background mb-4">
                Verify the Truth in a World of Fakes.
            </h1>
<p className="font-body-lg text-body-lg text-on-surface-variant mb-8 max-w-md">
                Professional-grade deepfake detection and forensic media analysis powered by blockchain provenance.
            </p>
<Link to="/check" className="bg-primary text-on-primary font-headline-sm text-headline-sm px-8 py-3 rounded-lg hover:bg-primary-fixed-dim transition-colors active:scale-95 w-full max-w-[280px] inline-flex justify-center items-center no-underline">
                Start Analyzing
            </Link>
</section>
{/* Features Bento Grid */}
<section className="flex flex-col gap-4">
{/* Deepfake Detection Card */}
<div className="bg-surface-container rounded-lg p-6 flex flex-col gap-4 border border-outline-variant">
<div className="flex items-center gap-3">
<div className="bg-surface-container-high p-2 rounded-lg border border-outline-variant">
<span className="material-symbols-outlined text-primary">face</span>
</div>
<h3 className="font-headline-sm text-headline-sm leading-tight text-on-surface">Deepfake Detection</h3>
</div>
<p className="font-body-md text-on-surface-variant">AI-powered scan for facial manipulation, inconsistencies, and synthetic generation artifacts.</p>
<div className="mt-2 flex items-center gap-2 font-label-mono text-label-mono text-primary">
<span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                    SCAN.READY
                </div>
</div>
{/* Forensic Analysis Card */}
<div className="bg-surface-container rounded-lg p-6 flex flex-col gap-4 border border-outline-variant">
<div className="flex items-center gap-3">
<div className="bg-surface-container-high p-2 rounded-lg border border-outline-variant">
<span className="material-symbols-outlined text-secondary">analytics</span>
</div>
<h3 className="font-headline-sm text-headline-sm leading-tight text-on-surface">Forensic Analysis</h3>
</div>
<p className="font-body-md text-on-surface-variant">Frame-by-frame metadata extraction and deep artifact inspection for media integrity.</p>
</div>
{/* Blockchain Provenance Card */}
<div className="bg-surface-container rounded-lg p-6 flex flex-col gap-4 border border-outline-variant">
<div className="flex items-center gap-3">
<div className="bg-surface-container-high p-2 rounded-lg border border-outline-variant">
<span className="material-symbols-outlined text-tertiary">link</span>
</div>
<h3 className="font-headline-sm text-headline-sm leading-tight text-on-surface">Blockchain Provenance</h3>
</div>
<p className="font-body-md text-on-surface-variant">Immutable cryptographic verification of content origin and modification history.</p>
</div>
</section>
{/* How it Works (Interactive Process) */}
<section className="flex flex-col gap-6">
<h2 className="font-headline-md text-headline-md text-on-background text-center">Verification Protocol</h2>
<div className="flex flex-col gap-2 relative">
{/* Connecting Line */}
<div className="absolute left-[27px] top-8 bottom-8 w-[2px] bg-outline-variant z-0"></div>
{/* Step 1 */}
<div className="flex gap-4 items-start relative z-10">
<div className="w-14 h-14 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center shrink-0">
<span className="material-symbols-outlined text-on-surface-variant">upload_file</span>
</div>
<div className="pt-2 pb-6">
<h4 className="font-label-mono text-label-mono text-on-surface">01. UPLOAD</h4>
<p className="font-body-md text-on-surface-variant mt-1">Submit media file to the secure forensic locker.</p>
</div>
</div>
{/* Step 2 */}
<div className="flex gap-4 items-start relative z-10">
<div className="w-14 h-14 rounded-full bg-surface-container-high border border-primary flex items-center justify-center shrink-0">
<span className="material-symbols-outlined text-primary">radar</span>
</div>
<div className="pt-2 pb-6">
<h4 className="font-label-mono text-label-mono text-primary">02. SCAN</h4>
<p className="font-body-md text-on-surface-variant mt-1">Multi-layer analysis for synthetic manipulation.</p>
</div>
</div>
{/* Step 3 */}
<div className="flex gap-4 items-start relative z-10">
<div className="w-14 h-14 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center shrink-0">
<span className="material-symbols-outlined text-secondary">verified</span>
</div>
<div className="pt-2">
<h4 className="font-label-mono text-label-mono text-on-surface">03. VERIFY</h4>
<p className="font-body-md text-on-surface-variant mt-1">Receive immutable provenance certificate.</p>
</div>
</div>
</div>
</section>
{/* Social Proof */}
<section className="bg-surface-container-low rounded-lg p-6 text-center border border-outline-variant">
<span className="material-symbols-outlined text-secondary text-[32px] mb-2 opacity-80">security</span>
<p className="font-label-mono text-label-mono text-on-surface-variant">
                "Trusted by global newsrooms and forensic investigators."
            </p>
</section>
</main>
    </>
  );
}

export default Home;
