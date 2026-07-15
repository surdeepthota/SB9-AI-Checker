import React, { useEffect, useState } from 'react';
import { listSamples } from '../api';

const GUIDED_EXAMPLES = [
  {
    filename: 'truepic-20230212-camera.jpg',
    title: 'A photo with a verified camera record',
    badge: 'valid',
    badgeText: 'Camera record verified',
    lesson: 'This file has a trusted record showing that it came from a camera. PeachCheck does not need to guess from visual clues.',
  },
  {
    filename: 'peachcheck-ad-compliant.jpg',
    title: 'An AI test ad with a clear label',
    badge: 'untrusted',
    badgeText: 'AI use declared',
    lesson: 'This fictional test ad says it was made with AI and includes the required warning. It tests whether PeachCheck can read and measure that warning.',
  },
  {
    filename: 'adobe-20220124-XCA.jpg',
    title: 'A file changed after it was signed',
    badge: 'tampered',
    badgeText: 'File changed',
    lesson: 'The file had a trusted record, but its contents no longer match that record. This proves the file changed after signing. It does not explain why it changed.',
  },
  {
    filename: 'adobe-20220124-A.jpg',
    title: 'A photo with no source record',
    badge: 'abstain',
    badgeText: 'Source unknown',
    lesson: 'PeachCheck cannot verify where this file came from. Missing source information does not mean the image was made by AI.',
  },
  {
    filename: 'peachcheck-ad-no-disclosure.png',
    title: 'An AI test ad with no warning',
    badge: 'tampered',
    badgeText: 'Warning missing',
    lesson: 'The team created this fictional AI test ad without a warning. It checks whether PeachCheck notices that the disclosure is missing.',
  },
];

function ExampleImage({ filename, title }) {
  const [status, setStatus] = useState('loading');
  const [attempt, setAttempt] = useState(0);
  const imageUrl = `/sample-file/${encodeURIComponent(filename)}?attempt=${attempt}`;

  return (
    <div className="example-image-wrap">
      {status === 'loading' && <p className="example-image-message">Loading picture…</p>}
      {status === 'error' && (
        <div className="example-image-message" role="alert">
          <p>We could not load this picture.</p>
          <button
            className="btn btn-secondary mt-2"
            type="button"
            onClick={() => {
              setStatus('loading');
              setAttempt((value) => value + 1);
            }}
          >
            Try again
          </button>
        </div>
      )}
      <img
        className={`example-image${status === 'loaded' ? '' : ' is-hidden'}`}
        src={imageUrl}
        alt={title}
        onLoad={() => setStatus('loaded')}
        onError={() => setStatus('error')}
      />
    </div>
  );
}

export default function EvidenceLibrary() {
  const [samplesByName, setSamplesByName] = useState({});
  const [error, setError] = useState('');

  useEffect(() => {
    listSamples()
      .then((body) => {
        const indexed = Object.fromEntries((body.samples || []).map((sample) => [sample.filename, sample]));
        setSamplesByName(indexed);
      })
      .catch((requestError) => setError(requestError.message || 'The examples could not be loaded.'));
  }, []);

  return (
    <div className="grid-12">
      <div className="col-10 col-start-2">
        <p className="text-xs font-mono text-lo mb-2 uppercase tracking-wide">Learn by example</p>
        <h1 className="font-display text-xl mb-4">What can PeachCheck find?</h1>
        <p className="text-lo mb-8 max-w-2xl">
          These are test files, not community reports. Each one shows a different result the app can give.
          They help us make sure the app behaves correctly.
        </p>

        {error && <div className="card form-error" role="alert">{error}</div>}

        <div className="flex flex-col gap-6">
          {GUIDED_EXAMPLES.map((example) => {
            const sample = samplesByName[example.filename];
            return (
              <article className="card example-card" key={example.filename}>
                <ExampleImage filename={example.filename} title={example.title} />
                <div className="example-copy">
                  <span className={`badge badge-${example.badge}`} style={{ alignSelf: 'flex-start' }}>{example.badgeText}</span>
                  <h2 className="font-display text-lg">{example.title}</h2>
                  <p className="text-sm text-lo leading-relaxed">{example.lesson}</p>

                  <details className="text-sm text-lo">
                    <summary className="cursor-pointer text-hi">More details</summary>
                    <div className="mt-2 flex flex-col gap-2">
                      <p><strong>Test file:</strong> {example.filename}</p>
                      {sample?.notes && <p>{sample.notes}</p>}
                      {sample?.source_url?.startsWith('http') && (
                        <a className="text-clay hover:underline" href={sample.source_url} target="_blank" rel="noreferrer">
                          Open the original test-file source
                        </a>
                      )}
                    </div>
                  </details>
                </div>
              </article>
            );
          })}
        </div>

        <div className="card mt-12">
          <h2 className="font-display text-lg mb-2">What these examples do not show</h2>
          <p className="text-sm text-lo">
            Five examples cannot prove that an AI detector is accurate. We will publish accuracy numbers only after
            testing a much larger set of known real and AI-made media.
          </p>
        </div>
      </div>
    </div>
  );
}
