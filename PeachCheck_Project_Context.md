# PeachCheck / AdCheck — Master Project Context

**Congressional App Challenge 2026 · AI-Generated Media, Provenance & Election Integrity in Georgia**

*Compiled: July 12, 2026 (day before Week 1 begins). This is the single source of truth for the team, mentors, and future planning sessions. Items are tagged **[LOCKED]** (decided) or **[PROPOSED]** (recommended in planning, not yet committed).*

---

## 1. Project identity

- **Working names:** PeachCheck (public-facing candidate) / AdCheck (the disclosure-measurement module; original spine name). Final name not yet decided.
- **One-line pitch:** A web app that analyzes political media for cryptographic provenance and disclosure compliance against Georgia's proposed SB 9 standard, reports calibrated confidence instead of verdicts, and converts strong findings into ready-to-file civic evidence packets for the State Election Board.
- **Design thesis:** Build a **layered trust system** where each layer catches what the previous one misses, **uncertainty is a first-class output**, and the final layer converts analysis into **civic action under SB 9**.
- **Core positioning [LOCKED]:** Pure deepfake *detection* is the weakest possible foundation — the gap between lab benchmarks and in-the-wild accuracy makes detection-only apps unreliable and indefensible in front of judges. PeachCheck therefore **leads with deterministic, cryptographically verifiable signals** (C2PA provenance, measurable SB 9 disclosure compliance) and treats probabilistic ML forensics as a clearly-labeled last resort.
- **Cardinal output rule [LOCKED]:** The app **never says "fake."** Canonical phrasing: *"No provenance found + 4 of 6 forensic indicators triggered — inconclusive; here is the evidence."* Media without credentials is labeled **"unknown provenance."** Rationale: C2PA absence is not proof of synthesis (messaging apps strip manifests on re-encode), and a false accusation against real media is the worst failure mode — it feeds the "liar's dividend."

## 2. Competition constraints — CAC 2026

| Constraint | Value |
|---|---|
| Submission deadline | **October 26, 2026, 12:00 PM (noon) ET** |
| Team size | Up to 4 students |
| Code authorship | All coding student-originated; open-source libraries allowed but **must be documented** |
| Code eligibility window | Code created **after October 30, 2025** |
| Demo video | **1–3 minutes**, public YouTube or Vimeo |
| Judging | Per congressional district; video + written answers are the primary evaluation (idea quality, implementation/UX, demonstrated coding excellence) |

**Internal hard deadline [LOCKED]: feature freeze October 12, 2026.** Final two weeks are video and write-ups only.

## 3. Rubric strategy (CAC Rubric Guide — 30 pts: Concept /15 + Technology /15)

Six rows, each scored 1–5. What the top score requires (paraphrased) and the project's explicit answer:

| Row | 5/5 bar | PeachCheck answer |
|---|---|---|
| **Ideology** (Concept) | Issue is extremely relevant | Live Georgia legislation (SB 9) + the 2026 Georgia U.S. Senate race (Ossoff–Collins) deepfake-ad controversy; the gap between SB 9's stalled status and current reality *is* the civic argument |
| **Impact** (Concept) | Immense creativity in explaining impact | The closable civic loop: evidence packet → State Election Board (which under §21-2-33.1(a.1) must publish findings) → community page. Plus stakeholder quote + user comprehension-test results |
| **Structure** (Concept) | Video is innovative, engaging, explains all aspects | Tight row-by-row script inside 3 minutes; budget for two full re-shoots |
| **Function** (Technology) | Fully functional with complex features | Full pipeline demo on the curated corpus; four milestone demos across the build |
| **Code** (Technology) | Explanation indicates immense understanding | Walk through the three **team-written** functions — ELA, calibration, C2PA verification — plus the calibration-curve reading. Honesty about ML limits is explicitly what "separates a 3/5 from a 5/5" here |
| **UI** (Technology) | Highly innovative design and interface | Report design + abstention language, validated by three rounds of non-technical user testing |

## 4. Legal foundation — Georgia SB 9 (House Committee on Rules substitute, LC 56 0401S)

**Status (verified via web search): stalled January 2026; never became law.** Framing [LOCKED]: the app is built to SB 9 as a **proposed legislative standard**, not enforceable law. Never claim the app enforces or detects violations of an active statute.

### 4.1 Part I — Legislative findings
AI advances pose a unique danger to Georgia's free and fair elections; AI now lets people (good faith and bad) create media falsely depicting conduct that appears real; the state and citizens hold rights to both free/fair elections and free speech; the Act is narrowly tailored against **bad-faith deceptive media** used to reduce candidates' election chances or suppress turnout through mass confusion.

### 4.2 Part II, §21-2-605 — Criminal offense: fraudulent election interference
- **"Materially deceptive media"** (two prongs): a video/audio/still-image file that (A) appears to depict a real individual's speech or conduct **that did not occur in reality**, and (B) **would appear authentic to a reasonable observer**.
- **"Person"**: employees/staff/affiliates of a political party, political body, candidate, campaign committee, PAC, or other political committee. **Explicitly excludes** broadcasters, cable providers, online services, ISPs, and streaming platforms (except in their role selling advertising to covered persons). → *The statute reaches campaign-affiliated actors, not platforms or random citizens — the evidence packet must capture who published the media.*
- **Offense elements** (§21-2-605(b)) — all must hold:
  1. Knowledge of the media's falsity;
  2. Publishes, broadcasts, streams, or uploads it;
  3. **Within 90 days of an election**;
  4. With intent to deceive one or more electors;
  5. For the purpose of (1) significantly influencing a candidate's chance of election, (2) creating confusion about election administration, or (3) otherwise influencing a referendum result.
- **Solicitation** (§21-2-605(c)): commanding, encouraging, or requesting someone to commit the above, with intent that it be committed.
- **Exemptions** (§21-2-605(d)): First Amendment–protected activity, including **satire, parody, works of artistic expression, and journalism by bona fide news organizations**. → *This is why the evidence packet includes a guided exemption questionnaire.*
- **Penalties** (§21-2-605(e)): first offense = misdemeanor; second/subsequent = **felony, 2–5 years imprisonment + fine up to $50,000**.
- **Venue** (§21-2-605(f)): any Georgia county where an act in furtherance occurred, the affected candidate resides, the defendant resided, or **the media is received**.
- **Enforcement path** (§21-2-605(g)): Attorney General has concurrent jurisdiction, but prosecution may only begin **upon the AG receiving a recommendation from the State Election Board**. → *The SEB is the gateway; the app's packet targets the SEB.*
- **Injunctive relief** (§21-2-605(h)): may be sought by (1) the individual depicted, (2) the AG, or (3) a candidate injured or likely to be injured.
- **§21-2-33.1(a.1) (new):** for any §21-2-605 investigation, **the State Election Board shall publicly release the findings of any completed investigation**. → *This is the app's feedback loop: packet out → published finding back → community page updated.*

### 4.3 Part II, Article 5 (§§21-5-90 through 21-5-94) — Civil disclosure regime for AI in campaign ads
- **"AI generated media"** (§21-5-90(1), three prongs): (A) created through an AI system, (B) depicts a real individual's speech/conduct that did not occur in reality, (C) appears authentic to a reasonable observer.
- **"Artificial intelligence system"** (§21-5-90(2)): an engineered/machine-based system emulating human cognitive processes (learning, generalizing, reasoning, planning, predicting, acting, communicating) from audio/visual/text/other inputs.
- **"Campaign advertisement"** (§21-5-90(3)): any material/commercial/media designed to bring about nomination or election, recall (or opposition to recall), or approval/rejection of ballot questions, amendments, or referenda — state, county, or municipal.
- **Safe-harbor rule** (§21-5-91(a)): AI-generated content **is permitted** in campaign ads if the ad discloses:
  1. The name of the candidate(s)/committee(s) that created, sponsored, and paid for it;
  2. The name of **each person being impersonated**;
  3. That events depicted **may not have actually occurred**;
  4. That **AI was used** to make part or all of the content.
- **Minor-editing exemption** (§21-5-91(b)): no disclosure needed for minor edits that would not substantially change an observer's understanding. → *A judgment call the app flags and explains rather than rules on.*
- **Disclosure format thresholds (§21-5-92) — the measurable spec the app tests against [core of the AdCheck module]:**
  - **Visual media:** written disclosure, in **every written language** used in the ad, and "clearly readable," defined as:
    - (i) text **≥ 30% of the vertical picture height**;
    - (ii) visible for **≥ 30% of the media's duration** (moving images/video);
    - (iii) **reasonable color contrast** — safe harbor is black text on white; otherwise contrast must be no less than that between the background and the largest type size in the communication.
  - **Audio-only media:** disclosure spoken at the **same volume**, the **same speaking rate (words per minute)**, and in **each spoken language** used in the ad.
- **Penalties** (§21-5-93): fine **≥ $10,000 per violation** (per §21-5-6 mechanics); violations involving AI media in a **fundraising solicitation** → **disgorgement of funds raised within 10 days** of the solicitation; the commission may investigate complaints within 90 days of an election.
- **§21-5-94:** commission rulemaking authority. **Part III:** effective upon Governor's approval (which never happened — see status above).

### 4.4 Statute → measurable check mapping [LOCKED design intent]

| SB 9 provision | App check |
|---|---|
| §21-5-90(1) "AI generated media" | C2PA manifest assertion `digitalSourceType: trainedAlgorithmicMedia` — the file's own **signed self-declaration** |
| §21-5-92(1)(B)(i) 30% text height | OCR bounding-box height ÷ frame height |
| §21-5-92(1)(B)(ii) 30% duration | Frame sampling → disclosure-presence ratio |
| §21-5-92(1)(B)(iii) contrast | WCAG-style contrast ratio as the measurement proxy |
| §21-5-92(2) audio parity | LUFS loudness comparison + words-per-minute rate comparison (video/audio phase) |
| §21-2-605(b) 90-day window | Date check against Georgia election calendar, computed in the evidence packet |
| §21-2-605(d) exemptions | Guided satire/parody/art/journalism questionnaire before packet assembly |
| §21-2-605(a)(3) "person" scope | Packet field capturing **who published** the media (statute reaches only campaign-affiliated actors) |

**Constitutional awareness point (for video/Q&A):** a comparable California law was partially struck down on First Amendment grounds — SB 9's satire/journalism carve-outs and the app's flag-and-explain posture (rather than rule-and-accuse) show the team understands that tightrope.

---

## 5. Architecture — the layered trust pipeline

**Pipeline order [LOCKED]:** provenance gate (C2PA) → disclosure measurement (SB 9 thresholds) → forensics panel → calibrated confidence → civic action.

**Naming rule [LOCKED]:** refer to layers by **function** — *provenance, measurement, forensics, judgment, action* — never by number, so the narrative survives any reordering.

**Scope [LOCKED]:** still images first; video/audio later. The **trust-report JSON schema is the foundational contract** — every layer writes into it, the UI only reads from it. Schema v0 is a Week 1 deliverable.

**Epistemic ranking (the story of the whole app):** deterministic measurement > cryptographic provenance > probabilistic forensics > human judgment. The UI is honest about which layer each claim comes from.

### 5.1 Provenance gate — C2PA (deterministic)

**What C2PA is:** a tamper-evident, cryptographically signed record of where a file came from and what was done to it — "a nutrition label for content that breaks visibly if altered."

**Lifecycle:** Create (tool writes a manifest: tools used + actions taken such as captured/cropped/AI-generated/composited, plus cryptographic hashes of the content) → Sign (with the tool's private key; certificate chains to an authority on the C2PA trust list) → Embed (signed manifest travels inside the file in a **JUMBF** container) → Verify (a validator checks the **COSE signature** against the trust list and recomputes hashes; any change breaks the hashes, and legitimate edits append new manifests → a full edit history).

**PeachCheck's role: the app *is* a C2PA validator.** c2pa-python (backend) / c2pa-js WebAssembly (in-browser) reads the JUMBF container, verifies the COSE signature against the trust list, and recomputes hashes.

**Four-state routing [LOCKED]:**

| C2PA state | Meaning | Route |
|---|---|---|
| **Valid + AI assertion** (`digitalSourceType: trainedAlgorithmicMedia`) | The file has "confessed" to being AI generated media under §21-5-90 **by its own signed testimony** | → Disclosure measurement (the §21-5-91 compliance question) |
| **Valid camera capture** | Verified origin | → **Early exit — no ML runs at all** |
| **Tampered** | **Highest-signal state**: cryptographic proof of post-signing alteration, naming the exact failed assertion | → Straight into the SB 9 evidence packet (with SHA-256 + timestamp) |
| **Untrusted / No credentials** | Nothing verifiable either way | → Forensics panel, labeled **"unknown provenance," never "fake"** |

**Honest caveat taught in the UI:** C2PA confirms **manifest integrity, not truthfulness**; messaging apps and screenshots strip manifests on re-encode, so absence of credentials means nothing on its own. The provenance layer has essentially no statistical error rate — its only failure mode is a UI that overstates what absence means.

**SynthID decision [LOCKED — demoted]:** No public detection API exists for image/video/audio (detection needs Google's watermarking keys). Therefore SynthID is an **educational link-out plus explanatory copy** in the report UI, not a programmatic check. Framing: *"we claim only what we can cryptographically verify"* — a rubric strength, not a gap. Even if an API opened tomorrow, statistical watermark detection would still rank below C2PA's determinism, so C2PA anchoring this layer is the correct design, not a workaround.
*Background retained for the write-up:* SynthID pipeline = Generate → Embed → Transform → Detect (Detected / Uncertain / Not found); two neural networks — one imperceptibly shifts pixel values, the second detects the pattern surviving crop/compression/filter/rotation; for text it weaves the watermark into token-probability sampling; Bayesian detector with tunable false-positive/false-negative thresholds; Google embeds **both** SynthID and C2PA in its outputs; NVIDIA Cosmos videos also carry SynthID.

### 5.2 Disclosure measurement — the AdCheck module (deterministic)

For AI-declared media (or a user-asserted campaign ad): OCR the disclosure text; measure text height as a fraction of vertical picture height against the **30% bar**; frame-sample video for the **≥30% duration** requirement; compute a WCAG-style **contrast ratio** against the statute's contrast rule; check that disclosure appears in **every language** used; (audio phase) compare **LUFS loudness** and **words-per-minute** between disclosure and ad body. Outputs are **reproducible numbers with visual proof** — bounding boxes drawn on frames, per-threshold pass/fail with the measurements attached. No ML opinions in this layer.

### 5.3 Forensics panel (runs only on "unknown provenance"; a panel of independent signals, not a chain)

| # | Signal | Type | Mechanism | Trigger | Known weakness | Cost |
|---|---|---|---|---|---|---|
| 1 | **EXIF / metadata** | Deterministic read, soft signal | Reads facts baked into the file: real photos carry camera make/model/lens/GPS/timestamp; AI outputs usually carry none; flags generator software tags (Midjourney, DALL·E, Stable Diffusion, etc.) | No camera data **OR** an AI-tool tag present | Screenshots/re-uploads strip metadata → "none found" is weak alone | Free, instant |
| 2 | **Error Level Analysis (ELA)** | Probabilistic | Re-save the image at a known JPEG quality, subtract from the original; regions edited separately compress differently and "light up" | Residual error above threshold | Catches **splices** (a pasted face), not "is this AI" directly | Free, fast — **team-written, video centerpiece** |
| 3 | **FFT / frequency domain** | Probabilistic | Fourier transform of the image; cameras leave natural sensor noise, many generators leave periodic/grid fingerprints from upscaling | Excess energy in the high-frequency ring | Newer generators hide it — catches cheaper/older fakes best | Free, fast |
| 4 | **Pretrained ML classifier** | Probabilistic — **least reliable** | Pretrained weights from Hugging Face; **never train our own**. Outputs a fake-likelihood score treated as one indicator, never a fact | Score above threshold, reported as an indicator | Real-world SOTA ≈ **80% accurate** — the layer we must be most honest about | Heaviest compute → where GCP credits / Cloud Run matter |

- **Fusion [LOCKED]:** transparent **rules-based fusion** (indicator counting/weighting readable directly in the code), *not* a learned meta-model — chosen for explainability on the Code rubric row.
- **[PROPOSED, optional]:** Reality Defender's free developer tier (50 image/audio scans/month, Python + TypeScript SDKs) as a supplementary API signal, with the local open-source model as fallback so demos never die on a rate limit. Not part of the locked panel.
- **Stretch:** Grad-CAM heatmaps showing where the ML model looked.

### 5.4 Calibrated confidence — the judgment layer

**Purpose:** the honesty mechanism that makes a probabilistic detector safe in front of a voter. Exists because ML detectors overfit and overclaim.

**Calibration, video-ready definition:** a model is *calibrated* when its scores mean what they say — among all files it scores around 0.8, roughly 80% actually turn out to be synthetic.

**Four bands [LOCKED] (working boundaries from the Layer-3 design, pending Week 10 tuning):**

| Score range | Band |
|---|---|
| 0.00 – 0.30 | **Leans authentic** |
| 0.30 – 0.70 | **Abstain / no verdict** — deliberately the **widest** band; covers the whole region where calibration data shows the detector can't beat a coin flip |
| 0.70 – 0.90 | **Moderate signal** |
| 0.90 – 1.00 | **Strong signal** |

**Three jobs of the bands:**
1. Convert detector output from vibe to **auditable claim** — a measured statistic with evidence behind it.
2. **Operationalize abstention** — "insufficient evidence" is a legitimate verdict line; a point-score UI would force a verdict on every file, bands let the app decline.
3. **Gate the pipeline** — the band structure is literally the interface contract between the probabilistic layer and the civic-action layer.

**Gate rule [LOCKED]:** only a **"strong signal" band corroborated by something deterministic** (tampered C2PA hash, hard metadata contradiction, or a failed disclosure measurement) may ever nudge the app toward the SB 9 reporting path. An abstain contributes **nothing**, no matter how suspicious a user feels. Forensics alone never files.

**Build recipe (~20 lines of Python + a JSON of band definitions the UI reads) [team-written]:** hold out part of the ground-truth corpus → bin detector scores into deciles → compute per-bin accuracy → fit Platt scaling or use the empirical bins → pick band edges where measured precision crosses chosen thresholds. Deliverables: reliability diagram + band strip (one video frame: *"we measured our detector's honesty and built the interface around it"* — the cleanest proof of the rubric's "immense understanding" bar).

**Threshold philosophy [LOCKED]:** tune for **precision over recall**. A false accusation against real media is the worst failure — it feeds the liar's dividend.

### 5.5 Civic action — evidence packet + community layer

**Evidence packet (exportable PDF + JSON) contents:**
- **SHA-256** of the file **plus a perceptual hash** (so re-encoded copies still match);
- Timestamp of analysis;
- Full trust-report JSON: C2PA state + named assertions, disclosure measurements, per-signal forensic outputs, calibrated band;
- **90-day-window calculation** against Georgia's election calendar;
- **Guided exemption questionnaire** (satire / parody / artistic expression / journalism — mirrors §21-2-605(d)) that the user completes before packet assembly;
- A field capturing **who published** the media (SB 9's "person" definition only reaches campaign-affiliated actors).

**Filing realism [LOCKED]:** there is no API into the State Election Board — the app generates a **complete packet with submission instructions**, not a fake "submit" button. The SEB is the correct target because §21-2-605(g) makes it the prosecution gateway and §21-2-33.1(a.1) forces it to **publish findings of completed investigations** — the app's closable feedback loop.

**Community page:** driven by the perceptual hash — when **multiple distinct users** upload matching media, surface the evidence report (never the word "fake") on a district-facing information page, **gated behind team review** so the feature can't become a defamation machine.

## 6. Trust-report JSON schema — the foundational contract

**Status:** schema **v0 is a Week 1 deliverable** [LOCKED as the first artifact]. Every layer appends; the UI only reads. **[PROPOSED sections]** for v0: file identity (name, MIME, SHA-256, perceptual hash, analysis timestamp, schema version) · provenance block (C2PA state, signer, trust-list result, assertions incl. `digitalSourceType`, failed assertion if tampered) · measurement block (per-threshold value / bar / pass-fail / evidence image refs) · forensics block (per-signal: triggered?, raw value, threshold, one-line explanation) · judgment block (raw score, calibrated score, band, calibration version) · action block (90-day calc, exemption answers, publisher field, packet-eligible boolean).

## 7. Report language rules

- Never "fake"; always "unknown provenance," indicator counts, and evidence.
- Abstention is a first-class verdict, not an error state.
- **Comprehension test [PROPOSED cadence]:** show five non-technical people a report and ask what they think it means, in three rounds — mockups (~Week 2), live app (~Week 8), final (~Week 13). **If anyone reads "abstain" as "probably fake," rewrite the copy.** That test is the honesty mechanism actually working, and its results are Impact-row evidence.

## 8. Evaluation plan

**Labeled test corpus — a core artifact, not an afterthought [LOCKED]:** target **80–120 files** with a ground-truth CSV; start with the first ~50 in Week 1. It underpins every claim in the video, settles every threshold argument (*"the corpus settles arguments"* — run pytest against ground truth), and the regression suite doubles as rubric evidence of rigor.

**Corpus mix [PROPOSED]:** C2PA-signed AI outputs · C2PA camera captures · tampered-credential files · credential-stripped copies · known AI images across multiple generators · authentic photos · authentic-but-weird "torture" media (old camcorder footage, heavy Instagram filters) · disclosure-bearing ad mockups at varying compliance levels.

**Metrics reported in the video:** precision, recall, confusion matrix, calibration curve / reliability diagram.

**Stress suites (Weeks 13–14, run as regression gates):**
1. **Adversarial laundering sweep:** screenshot → re-compress at multiple JPEG qualities → crop → resize → format-convert. Expected result to *show*: C2PA breaks **gracefully** (reports credential loss, not "fake") while forensic signals **degrade measurably**.
2. **Out-of-distribution:** generators absent from any pretrained model's training data.
3. **Edge cases:** multi-face, low-light; non-English audio (video/audio phase).
4. **Real-media torture test:** authentic-but-weird content to measure false positives.
5. **Failure injection** (broken files, timeouts) + **human-factors testing** — 5–10 classmates interpret reports; measure whether they understand "abstain."

## 9. Tech stack

| Component | Choice |
|---|---|
| Frontend | React (Flutter was the alternative); **c2pa-js** (WebAssembly) for in-browser verification |
| Backend | **Python + FastAPI** |
| Provenance | **c2pa-python** SDK (C2PA core tooling is MIT-licensed) |
| Imaging/forensics | EXIF/container metadata parsing; ELA + FFT (team-written on standard imaging libs); OCR for disclosure text; Hugging Face pretrained classifier; frame sampling + LUFS loudness (later phase); Grad-CAM (stretch) |
| Calibration | Reliability diagrams; Platt scaling or empirical binning |
| Deployment | **Google Cloud Run** (GCP credits cover the ML layer's compute) |
| Hashing | SHA-256 + perceptual hash |
| Standards touched | C2PA, COSE signatures, X.509 certificate chains, JUMBF, WCAG-style contrast |
| Compliance | Every open-source dependency documented vs. what the team wrote (CAC rule); **ELA, calibration, and C2PA verification written by the team** because they're the video's centerpiece demonstrations |

## 10. 15-week build plan (July 13 → October 26, 2026)

| Phase | Weeks | Dates | Deliverable |
|---|---|---|---|
| 1. Foundations | W1 | Jul 13–19 | Repo + board, corpus spreadsheet started (~50 items + ground-truth CSV), trust-report schema v0, de-risk spikes, stakeholder email |
| 2. Walking skeleton | W2–3 | Jul 20–Aug 2 | Upload → EXIF → report JSON → UI card, **deployed to Cloud Run**; first language mockup test |
| 3. Provenance gate | W4–5 | Aug 3–16 | c2pa-python verification, four-state routing live |
| 4. Disclosure measurement | W6–7 | Aug 17–30 | OCR, height %, duration %, contrast vs. SB 9 thresholds |
| 5. Forensics panel | W8–9 | Aug 31–Sep 13 | EXIF rules, ELA, FFT, pretrained model wired as indicators; live-app language test |
| 6. Calibration | W10 | Sep 14–20 | Reliability diagram, band edges fit, confusion matrix |
| 7. Civic action | W11–12 | Sep 21–Oct 4 | Evidence packet (PDF/JSON), exemption questionnaire, community page |
| 8. Hardening | W13–14 | Oct 5–18 | Stress suites, threshold re-tuning, final metrics; **FEATURE FREEZE MON OCT 12**; final language test |
| 9. Ship | W15 | Oct 19–26 | Video (two re-shoots budgeted), written answers, exit questionnaire, dependency documentation, **submit before Oct 26 noon ET** |

**Operating rules [LOCKED]:**
- **Walking skeleton:** always maintain a demoable thin vertical slice end-to-end; never build horizontal layers where nothing works.
- **Scope ladder:** under time pressure, cut stretch features from the bottom — **never cut polish or testing first**. [PROPOSED cut order, last-cut-first]: video/audio modality → Grad-CAM → community page → in-app filing polish → FFT/ML extras. Never cut: schema, C2PA gate, disclosure measurement, bands, corpus, user testing.
- **Iteration engine [PROPOSED]:** weekly cadence (planning at week start, internal demo at week end — app demoable every single week); small pull requests reviewed by teammates (doubles as proof all coding was student-done); one decision-log paragraph after every phase (those paragraphs become the written submission answers almost verbatim).

## 11. Week 1 — the three de-risking tasks [LOCKED]

1. **Create the repo and the corpus spreadsheet.** [PROPOSED columns]: filename · source URL · generator or camera · C2PA state · ground-truth label · laundering applied · notes.
2. **Verify one Content Credentials sample file with c2pa-python** — the "hello world" for the riskiest dependency. (Spike A: prove the four states are reachable. Spike B: one Hugging Face detector inference.)
3. **Stand up a FastAPI upload endpoint returning EXIF as JSON** — the seed of the walking skeleton.

*If both spikes work by next Sunday, everything downstream is execution, not risk.*

## 12. Team structure (≤4, [PROPOSED] split)

Pipeline/backend · Frontend/UI · Evaluation (corpus, calibration, stress tests) · Civic layer + video production — **with everyone touching code** so each member can speak to it on camera.

## 13. Open items & risks

- [ ] **Stakeholder outreach by ~July 26** (Week 1–2): one email to a county elections office, a civics teacher, or the Member's congressional office. A single quote/feedback exchange is a genuine Impact-row differentiator and costs thirty minutes. (Brainstorm notes float **Rep. Todd Jones** as a potential approval/endorsement contact.)
- [ ] Three rounds of non-technical user testing on report language (Weeks ~2, ~8, ~13).
- [ ] Final name decision: PeachCheck vs. AdCheck.
- [ ] **Citation check** before any video use: the brainstorm's claim that AI scam calls/deepfakes account for ~90–95% of AI-related crime is currently **unsourced** — verify or drop.
- Risk: pretrained detector underperforming in the wild → mitigated by the abstention band and by never resting claims on it.
- Risk: corpus assembly stalling → it's a Week-1 start and every later phase depends on it.

## 14. Video plan (1–3 minutes)

**Opening hook [PROPOSED, established in planning]:** the 2026 Georgia U.S. Senate race (Ossoff–Collins) deepfake-ad controversy — a campaign-released AI-generated video with a minimal disclaimer — then SB 9's stalled status showing the gap the app fills.

**Beat sheet, scripted row-by-row against the rubric:** hook (Ideology) → the layered-honesty story + who the packet serves + comprehension-test results (Impact) → live demo through the four provenance states (Function) → the calibration curve walkthrough + the three hand-written functions (Code — the designated "immense understanding" moment) → clean report/UI tour with abstention language (UI) → future-improvements slide → tight edit inside three minutes with two full re-shoots budgeted (Structure).

## 15. Decision log — principles [LOCKED]

1. Pure deepfake detection is the weakest foundation; lead with deterministic and cryptographically verifiable signals.
2. Walking skeleton: never be in a state where nothing works end-to-end.
3. The labeled test corpus is the product's foundational evidence, not an afterthought.
4. Scope ladder: cut stretch features from the bottom; never cut polish or testing first.
5. A wide abstention band is honest engineering — more defensible than any forced binary.
6. Name layers by function (provenance, measurement, forensics, judgment, action), never by number.
7. SB 9 is a **proposed standard**, not law — the gap is part of the civic argument.
8. Only strong-band findings **with deterministic corroboration** touch the SB 9 reporting path.
9. Rules-based fusion over learned meta-models, for explainability.
10. The app never says "fake"; absence of credentials is "unknown provenance."
11. Precision over recall; false accusations feed the liar's dividend.
12. Team hand-writes ELA, calibration, and C2PA verification — the video's stars.

## 16. Origin notes (initial brainstorm, retained)

- **Pros listed:** abundant real-world stories of lives damaged by fake representations; potential approval from Todd Jones; access to Claude Code; available AI models.
- **Problem framing:** AI is growing and beneficial, but bad actors exploit it; people unfamiliar with the technology fall for fakes because they look real; the app "streamlines the truth" — minimizing AI's harms to maximize its positives.
- **Con flagged:** "too broad" → answered by narrowing to **Georgia political media measured against the SB 9 standard**.
- **Requirement noted:** the submission should include **future-improvement suggestions**.
- Early planning session: https://claude.ai/share/08ac0548-8970-4588-9044-5ac2742554dc

---

## Appendix — SB 9 quick-reference card

**90 days** (criminal window + commission investigation window) · **30% / 30%** (disclosure text height / on-screen duration) · **contrast**: black-on-white safe harbor or ≥ largest-type contrast · **4 disclosure items**: sponsor, impersonated persons, "may not have occurred," "AI was used" · **$10,000** minimum civil fine · **10-day** fundraising disgorgement · misdemeanor → felony **2–5 yrs / $50,000** on repeat · exemptions: **satire, parody, art, bona fide journalism** · SEB gates prosecution **and must publish completed-investigation findings**.

*End of context document — v1.0, July 12, 2026.*
