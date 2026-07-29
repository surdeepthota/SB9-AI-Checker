import React from 'react';

const STEPS = [
  {
    number: '1',
    title: 'Where did the file come from?',
    text: 'Some cameras and editing apps attach a signed source record. If the record is present and valid, we can check whether the file still matches it. If there is no record, we say the source is unknown. We do not treat a missing record as proof of AI use.',
  },
  {
    number: '2',
    title: 'Does it say AI was used?',
    text: 'We look for AI labels in the file and in the original post. For campaign ads, we also check whether the warning is easy to see. A clear AI label is stronger evidence than a visual guess.',
  },
  {
    number: '3',
    title: 'Do the image checks find anything unusual?',
    text: 'If the source is unknown, we check file details, editing patterns, image patterns, and an AI detector. These checks can be wrong, especially after a social media site compresses the file, so we show them as clues instead of facts.',
  },
  {
    number: '4',
    title: 'How strong is the evidence?',
    text: 'The final result can lean toward a normal camera image, say there is not enough evidence, or show moderate or strong signs of AI or editing. A high score is still not proof unless the file or post directly says AI was used.',
  },
];

export default function Methodology() {
  return (
    <div className="grid-12">
      <div className="col-8 col-start-3">
        <p className="text-xs font-mono text-lo mb-2 uppercase tracking-wide">Plain-language guide</p>
        <h1 className="font-display text-xl mb-4">How PeachCheck works</h1>
        <p className="text-base text-lo mb-8">
          PeachCheck checks the strongest evidence first. It says when something is unknown instead of forcing a yes-or-no answer.
        </p>

        <div className="flex flex-col gap-6">
          {STEPS.map((step) => (
            <section className="card" key={step.number}>
              <p className="font-mono text-xs text-clay mb-2">Step {step.number}</p>
              <h2 className="font-display text-lg mb-3">{step.title}</h2>
              <p className="text-sm text-lo leading-relaxed">{step.text}</p>
            </section>
          ))}
        </div>

        <div className="card mt-8">
          <h2 className="font-display text-lg mb-3">About Georgia SB 9</h2>
          <p className="text-sm text-lo leading-relaxed">
            SB 9 is a proposed Georgia standard, not an active law. PeachCheck uses its AI-warning rules as a test. The app does not decide whether someone broke the law.
          </p>
        </div>
      </div>
    </div>
  );
}
