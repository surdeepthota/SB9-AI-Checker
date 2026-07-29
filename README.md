# PeachCheck

**Cryptographic provenance and SB 9 disclosure analysis for Georgia political media — evidence and calibrated confidence, never verdicts.**

Congressional App Challenge 2026 · Georgia

PeachCheck analyzes political media for cryptographic provenance (C2PA Content
Credentials) and disclosure compliance against Georgia's proposed **SB 9** standard,
reports calibrated confidence instead of verdicts, and converts strong findings into
ready-to-file civic evidence packets for the State Election Board.

> **The cardinal rule: this app never says "fake."** Media without credentials is
> "unknown provenance." A canonical report reads: *"No provenance found + 2 of 4
> forensic indicators triggered — inconclusive; here is the evidence."* A false
> accusation against real media is the worst possible failure mode — it feeds the
> "liar's dividend."

---

## Why this exists

Georgia's SB 9 (LC 56 0401S) would have required AI-generated campaign ads to carry
specific, *measurable* disclosures — text at least 30% of the frame height, visible
30% of the runtime, with real contrast — and made bad-faith deceptive election media
a crime within 90 days of an election. The bill **stalled in January 2026 and never
became law**. PeachCheck is built against SB 9 as a *proposed standard*: the gap
between what the law would require and what circulates today **is** the civic
argument.

Pure deepfake *detection* is the weakest possible foundation for a tool like this —
real-world detector accuracy (~80%) can't responsibly power accusations. PeachCheck
therefore leads with **deterministic, verifiable signals** and treats ML forensics as
a clearly-labeled last resort:

```
deterministic measurement > cryptographic provenance > probabilistic forensics > human judgment
```

## The five-layer trust pipeline

Each layer catches what the previous one misses; every layer writes into one
trust-report JSON contract (`peachcheck/schema.py`) and the UI only ever *reads* it.

| Layer | Type | What it does |
|---|---|---|
| **Provenance** (`layers/provenance.py`) | deterministic | Validates the C2PA manifest: COSE signature, trust list, recomputed content hashes. Routes to one of four states — see below. |
| **Measurement** (`layers/measurement.py`) | deterministic | OCRs the ad and measures its disclosure against SB 9 §21-5-91/92: content items present, text ≥ 30% of frame height, contrast vs the ad's own text. Outputs numbers + an annotated evidence image, never opinions. |
| **Forensics** (`layers/forensics.py`) | probabilistic | Four independent indicators, run only on "unknown provenance": EXIF/metadata rules, team-written Error Level Analysis, team-written FFT frequency analysis, and an ensemble of two pretrained Hugging Face classifiers (the higher reading is used — they miss different generators). Fused with fixed, readable weights — no learned meta-model. |
| **Judgment** (`layers/judgment.py`) | probabilistic | Maps the fused score into four calibrated-confidence bands. **Abstain (0.30–0.70) is deliberately the widest band** — "insufficient evidence" is a legitimate verdict. |
| **Action** (`layers/action.py`) | human decision | Computes the 90-day statutory window against Georgia's election calendar, walks the user through the §21-2-605(d) exemption questionnaire (satire/parody/art/journalism), captures the publisher, and assembles an evidence packet for the State Election Board. There is deliberately **no "submit" button** — no SEB API exists, and pretending otherwise would be dishonest. |

### The four provenance states

| State | Meaning | Route |
|---|---|---|
| **Valid capture** | Intact signed manifest, no AI assertion | Early exit — no ML runs at all |
| **Valid + AI assertion** | The file's own signed manifest declares it AI-generated (`digitalSourceType: trainedAlgorithmicMedia`) | → disclosure measurement |
| **Tampered** | Signature valid but content hashes broken — cryptographic proof of post-signing alteration | → straight to the evidence packet |
| **Untrusted** | No manifest, or unverifiable signature | → forensics panel, labeled **"unknown provenance," never "fake"** |

### The reporting gate

Only a **strong-signal band corroborated by something deterministic** (a tampered
C2PA hash, an explicit AI-tool metadata tag, or a failed disclosure measurement) ever
opens the SB 9 reporting path. Forensics alone never files, no matter the score.

---

## Running locally

Prereqs: Python 3.11+, Node 20+.

```bash
# 1. Backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/make_demo_corpus.py   # builds the demo corpus (one-time)
.venv/bin/uvicorn app:app --port 8000

# 2. Frontend (second terminal)
cd frontend
npm ci
npm run dev        # http://localhost:5173 (proxies API calls to :8000)
```

The first analysis of an "unknown provenance" file downloads the classifier weights
(~350 MB, one-time) and the OCR model; subsequent runs are fast. Both degrade
gracefully — if a model can't load, the report says so honestly instead of failing.

### Docker (mirrors the Cloud Run deployment)

```bash
docker build -t peachcheck .
docker run -p 8080:8080 peachcheck    # http://localhost:8080
```

### Tests

```bash
.venv/bin/python -m pytest              # fast unit suite (~3 s, no model loads)
.venv/bin/python -m pytest -m corpus    # regression gate over the demo corpus (slow)
```

The corpus suite asserts every bundled sample lands in its ground-truth provenance
state — *"the corpus settles arguments."*

---

## Demo script (three minutes)

The demo gallery on the home page covers all four states with known ground truth:

1. **`truepic-20230212-camera.jpg`** — verified capture. Watch the route map: the
   forensic panel proudly *doesn't run*. No ML touches a verified file.
2. **`adobe-20220124-XCA.jpg`** — tampered. Cryptographic proof of post-signing
   alteration, naming the exact failed check (`assertion.dataHash.mismatch`). Gate
   passes on this alone.
3. **`peachcheck-ad-tiny-disclosure.jpg`** — a fictional campaign ad whose signed
   manifest admits it's AI-generated. Measurement finds the disclosure *content* but
   fails it on the 30% height bar (measured: ~2%) and contrast — with the bounding
   box drawn on the frame as visual proof. Complete the exemption questionnaire and
   assemble the evidence packet.
4. **`peachcheck-ad-stripped.jpg`** — the same compliant ad after credential
   stripping (what messaging apps do). Provenance: unknown. The forensic panel runs,
   the judgment lands in **abstain**, and the app declines to lean either way — while
   the perceptual hash still matches the signed original.

## What the team wrote vs. what libraries do

Per CAC rules, all open-source dependencies are documented in `requirements.txt`.
The load-bearing analysis logic is team-written:

- **Four-state provenance routing** (`provenance.route`) — pure decision logic over
  the validator's raw output; unit-tested against hand-built fixtures.
- **Error Level Analysis** (`forensics.compute_ela`) — re-save, diff, and heatmap.
- **FFT frequency analysis** (`forensics.compute_fft_high_freq_energy`) — radial
  high-frequency energy ratio.
- **SB 9 threshold arithmetic** (`measurement.py`) — height/duration/contrast checks,
  WCAG contrast math, disclosure-content detection rules (auditable regexes, not a
  classifier).
- **Rules-based fusion** (`forensics.fuse_signals`) — a fixed weighted panel with a
  direct-evidence floor, so strong classifier evidence is not diluted by unrelated
  quiet splice checks; the arithmetic remains readable directly in the code and can
  be recomputed by hand from any report.
- **Calibration banding + the reporting gate** (`judgment.py`).
- **Perceptual dHash** (`pipeline.compute_dhash`) — 64-bit difference hash that
  survives re-encoding.
- The pipeline routing, the election calendar, evidence packet assembly, the API, and
  the entire React UI.

Libraries do what libraries should: `c2pa-python` verifies COSE signatures,
`Pillow`/`numpy` move pixels, `easyocr`/`pytesseract` read text, `transformers` runs
two pretrained classifiers — `umm-maybe/AI-image-detector` and
`haywoodsloan/ai-image-detector-deploy` (never trained in-house) — `FastAPI`/`React`
serve it all.

## Honest limits (current phase)

- **Still images only.** Video/audio (duration %, LUFS loudness parity, words-per-
  minute) are designed into the schema and statute mapping but not yet ingested.
- **Calibration is `v0-identity`** — band edges are the design values, not yet fit to
  a held-out labeled corpus (that's the Week 10 milestone; the UI says so on every
  judgment card).
- **The ML classifier is the panel's weakest signal** and is capped at 40% of the
  fused score by design. Its ~80% real-world accuracy is stated in the report itself.
  Running two pretrained models and taking the higher reading catches more than
  either alone, but both were benchmarked against a real Gemini-generated image and
  still scored it under 10% "artificial" — recent, photorealistic generators remain a
  known blind spot for open pretrained detectors, which is exactly why this signal is
  capped and gated rather than trusted on its own.
- **Impersonated-person disclosure** (§21-5-91(a)(2)) can't be measured automatically
  — it requires knowing who appears in the ad. Flagged for the human filer.
- **The demo AI-asserted ads are signed with the standard C2PA test certificate**, so
  validators report "signer not on the trust list" — which the app displays honestly.
  The verification mechanism is identical to production-signed media.
- The election calendar covers Georgia's statewide 2026 dates; county/municipal
  specials are out of scope.

## Repository map

```
app.py                        FastAPI app: /analyze, /analyze-sample, /samples, /packet, /api/health
peachcheck/
  schema.py                   Trust-report contract (v0.2.0) — every layer writes, the UI reads
  pipeline.py                 Routing between layers + headline language + dHash
  election_calendar.py        Georgia 2026 election dates + 90-day window math
  layers/
    provenance.py             C2PA validation + four-state routing
    measurement.py            SB 9 disclosure measurement (OCR + geometry + WCAG contrast)
    forensics.py              Metadata / ELA / FFT / ML classifier + rules-based fusion
    judgment.py               Calibrated bands + the reporting gate
    action.py                 90-day window, exemption questionnaire, evidence packet
frontend/                     React + Vite UI (layer cards, band strip, packet builder)
corpus/                       metadata.csv ground truth + samples/ demo corpus
scripts/make_demo_corpus.py   Rebuilds the demo corpus (downloads C2PA test files,
                              renders + signs fictional ad mockups)
tests/                        Unit suite + `-m corpus` regression gate
```

All candidates and committees in the demo ads are fictional.
