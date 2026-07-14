"""PeachCheck API — FastAPI wrapper around the five-layer trust pipeline.

Endpoints:
    POST /analyze            multipart upload -> full trust report JSON
    POST /analyze-clip-url   social/video page URL -> sampled frame reports
    POST /analyze-sample     run the pipeline on a bundled demo-corpus file by name
    GET  /samples            list the bundled demo corpus (for the UI's demo picker)
    POST /packet             exemption questionnaire + publisher -> evidence packet JSON
    GET  /api/health         which optional capabilities are live in this environment

Endpoints are plain `def` (not `async def`) on purpose: the pipeline is CPU-bound
(hashing, FFT, model inference), so FastAPI's threadpool execution keeps the event
loop free instead of blocking it.
"""

import csv
import os
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from peachcheck.clip_analysis import clip_support_available, resolve_and_sample_clip
from peachcheck.layers import action as action_layer
from peachcheck.layers.forensics import extract_metadata_text
from peachcheck.layers.judgment import build_judgment
from peachcheck.pipeline import run_pipeline
from peachcheck.schema import ActionBlock, ConfidenceBand, report_to_dict

app = FastAPI(title="PeachCheck API", version="0.2.0")

# Allow the Vite dev server to connect during local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, "corpus", "samples")
CORPUS_CSV = os.path.join(BASE_DIR, "corpus", "metadata.csv")

ALLOWED_MIME_PREFIXES = ("image/",)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def _analyze_path(file_path: str, mime_type: str, is_campaign_ad: bool) -> dict:
    """Shared analysis body for uploads and bundled samples."""
    analyzed_at_iso = datetime.now(timezone.utc).isoformat()
    report = run_pipeline(file_path, mime_type, analyzed_at_iso, is_campaign_ad=is_campaign_ad)
    exif, _ = extract_metadata_text(file_path)
    return {"exif_data": exif, "trust_report": report_to_dict(report)}


def _judgment_to_dict(judgment) -> dict:
    return {
        "raw_score": judgment.raw_score,
        "calibrated_score": judgment.calibrated_score,
        "band": judgment.band.value if judgment.band else None,
        "calibration_version": judgment.calibration_version,
        "rationale": judgment.rationale,
    }


def _clip_band_for_score(score: float, strict_mode: bool) -> ConfidenceBand:
    if not strict_mode:
        if score < 0.30:
            return ConfidenceBand.LEANS_AUTHENTIC
        if score < 0.70:
            return ConfidenceBand.ABSTAIN
        if score < 0.90:
            return ConfidenceBand.MODERATE_SIGNAL
        return ConfidenceBand.STRONG_SIGNAL

    if score < 0.24:
        return ConfidenceBand.LEANS_AUTHENTIC
    if score < 0.58:
        return ConfidenceBand.ABSTAIN
    if score < 0.84:
        return ConfidenceBand.MODERATE_SIGNAL
    return ConfidenceBand.STRONG_SIGNAL


def _summarize_clip_reports(reports: list[dict], strict_mode: bool = False) -> dict | None:
    trust_reports = [item["analysis"]["trust_report"] for item in reports]
    judgments = [report.get("judgment") for report in trust_reports if report.get("judgment")]
    if not judgments:
        return None

    scores = [float(j["calibrated_score"]) for j in judgments if j.get("calibrated_score") is not None]
    if not scores:
        return None

    bands = [j["band"] for j in judgments if j.get("band")]
    band_counts = Counter(bands)
    sorted_scores = sorted(scores, reverse=True)
    top_window = sorted_scores[: max(2, min(4 if strict_mode else 3, len(sorted_scores)))]
    average_score = sum(scores) / len(scores)
    top_window_score = sum(top_window) / len(top_window)
    suspicious_frames = band_counts.get("moderate_signal", 0) + band_counts.get("strong_signal", 0)
    suspicious_ratio = suspicious_frames / len(judgments)
    strongest = max(scores)

    aggregated_score = top_window_score
    if suspicious_ratio >= 0.6:
        aggregated_score += 0.08
    if suspicious_ratio >= 0.8 and average_score >= 0.65:
        aggregated_score += 0.05
    if strict_mode:
        consistency_score = (0.5 * strongest) + (0.3 * top_window_score) + (0.2 * average_score)
        aggregated_score = max(aggregated_score, consistency_score)
        if suspicious_ratio >= 0.4:
            aggregated_score += 0.08
        if suspicious_ratio >= 0.6:
            aggregated_score += 0.08
        if band_counts.get("strong_signal", 0) >= 2:
            aggregated_score += 0.08
        elif band_counts.get("strong_signal", 0) >= 1:
            aggregated_score += 0.05
        if strongest >= 0.85 and average_score >= 0.5:
            aggregated_score += 0.04
    aggregated_score = max(0.0, min(1.0, round(aggregated_score, 4)))

    judgment = build_judgment(
        raw_score=aggregated_score,
        rationale=(
            f"Clip-level aggregation across {len(judgments)} sampled frames: "
            f"average frame score {average_score:.2f}, strongest frame {strongest:.2f}, "
            f"{suspicious_frames} frame(s) landed in moderate-or-strong signal. "
            + (
                "Strict clip mode is on, so repeated suspicious frames and multiple strong frames are weighted more aggressively."
                if strict_mode
                else "The clip summary weights the strongest consistent frames more heavily than any one frame."
            )
        ),
    )
    judgment.band = _clip_band_for_score(judgment.calibrated_score or 0.0, strict_mode)
    return {
        "sampled_frames": len(reports),
        "frames_with_judgment": len(judgments),
        "strict_mode": strict_mode,
        "average_frame_score": round(average_score, 4),
        "strongest_frame_score": round(strongest, 4),
        "clip_decision_score": round(judgment.calibrated_score or 0.0, 4),
        "suspicious_frames": suspicious_frames,
        "band_counts": dict(band_counts),
        "judgment": _judgment_to_dict(judgment),
    }


@app.post("/analyze")
def analyze_file(file: UploadFile = File(...), is_campaign_ad: bool = Form(False)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    mime_type = file.content_type or "application/octet-stream"
    if not mime_type.startswith(ALLOWED_MIME_PREFIXES):
        raise HTTPException(
            status_code=415,
            detail="Only still images are supported in this phase (video/audio are future work).",
        )

    temp_dir = tempfile.mkdtemp()
    # Basename only — never trust a client-supplied path.
    file_path = os.path.join(temp_dir, os.path.basename(file.filename))
    try:
        size = 0
        with open(file_path, "wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="File exceeds the 25 MB upload limit.")
                buffer.write(chunk)
        return _analyze_path(file_path, mime_type, is_campaign_ad)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/samples")
def list_samples():
    """The bundled demo corpus, joined with its ground-truth notes from metadata.csv,
    so the UI can offer one-click demo files covering all four provenance states.
    """
    notes: dict[str, dict] = {}
    if os.path.exists(CORPUS_CSV):
        with open(CORPUS_CSV, newline="") as f:
            for row in csv.DictReader(f):
                notes[row["filename"]] = row
    samples = []
    if os.path.isdir(SAMPLES_DIR):
        for name in sorted(os.listdir(SAMPLES_DIR)):
            if name.lower().endswith((".jpg", ".jpeg", ".png")):
                meta = notes.get(name, {})
                samples.append(
                    {
                        "filename": name,
                        "expected_state": meta.get("c2pa_state", ""),
                        "notes": meta.get("notes", ""),
                    }
                )
    return {"samples": samples}


class SampleRequest(BaseModel):
    filename: str
    is_campaign_ad: bool = False


class ClipUrlRequest(BaseModel):
    url: str
    is_campaign_ad: bool = False
    frame_count: int = 5
    strict_mode: bool = False


@app.post("/analyze-clip-url")
def analyze_clip_url(request: ClipUrlRequest):
    requested_floor = 7 if request.strict_mode else 3
    requested_ceiling = 9 if request.strict_mode else 7
    frame_count = max(requested_floor, min(request.frame_count, requested_ceiling))
    temp_dir = tempfile.mkdtemp()
    try:
        sampled = resolve_and_sample_clip(
            request.url,
            temp_dir=temp_dir,
            frame_count=frame_count,
        )
        reports = []
        for frame in sampled.frames:
            reports.append(
                {
                    "frame_number": frame.frame_number,
                    "seconds": frame.seconds,
                    "label": frame.label,
                    "preview_data_url": frame.preview_data_url,
                    "analysis": _analyze_path(
                        frame.image_path,
                        "image/png",
                        request.is_campaign_ad,
                    ),
                }
            )
        return {
            "clip_url": sampled.source_url,
            "duration_seconds": sampled.duration_seconds,
            "clip_summary": _summarize_clip_reports(reports, strict_mode=request.strict_mode),
            "reports": reports,
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Clip analysis failed: {exc}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/analyze-sample")
def analyze_sample(request: SampleRequest):
    # Resolve strictly inside the samples dir — no client-controlled traversal.
    safe_name = os.path.basename(request.filename)
    file_path = os.path.join(SAMPLES_DIR, safe_name)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"No bundled sample named {safe_name!r}.")
    mime = "image/png" if safe_name.lower().endswith(".png") else "image/jpeg"
    try:
        return _analyze_path(file_path, mime, request.is_campaign_ad)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")


class PacketRequest(BaseModel):
    """Phase-2 civic action: the user's questionnaire answers plus the trust report
    the packet should wrap. The report is echoed back from the client because the
    server keeps no per-analysis state (nothing is stored server-side by design).
    """

    trust_report: dict
    exemption_answers: dict[str, bool]
    publisher: str | None = None


@app.post("/packet")
def build_packet(request: PacketRequest):
    action_dict = request.trust_report.get("action") or {}
    base = ActionBlock(
        within_90_day_window=action_dict.get("within_90_day_window"),
        next_election_date=action_dict.get("next_election_date"),
        next_election_name=action_dict.get("next_election_name"),
        window_opens=action_dict.get("window_opens"),
        days_until_election=action_dict.get("days_until_election"),
        deterministic_corroboration=action_dict.get("deterministic_corroboration") or [],
        gate_passed=bool(action_dict.get("gate_passed")),
        guidance=action_dict.get("guidance"),
    )
    try:
        final = action_layer.finalize_action(
            base, request.exemption_answers, request.publisher
        )
    except ValueError as exc:  # incomplete questionnaire
        raise HTTPException(status_code=422, detail=str(exc))

    trust_report = dict(request.trust_report)
    trust_report["action"] = {
        **action_dict,
        "exemption_answers": final.exemption_answers,
        "publisher": final.publisher,
        "packet_eligible": final.packet_eligible,
        "guidance": final.guidance,
    }
    return action_layer.assemble_evidence_packet(trust_report, final)


@app.get("/api/health")
def health():
    """Which optional capabilities are live — the UI shows this honestly rather than
    silently degrading."""
    from peachcheck.layers import provenance as prov_mod
    from peachcheck.layers.measurement import _resolve_ocr_engine

    return {
        "status": "ok",
        "c2pa": prov_mod._C2PA_AVAILABLE,
        "ocr_engine": _resolve_ocr_engine() or None,
        "samples_bundled": os.path.isdir(SAMPLES_DIR) and bool(os.listdir(SAMPLES_DIR)),
        "clip_url_support": clip_support_available(),
    }


# Serve the built frontend in production (Docker copies frontend/dist to ./static).
# Mounted last so the API routes above always win; html=True serves index.html at /
# and static assets (favicon, icons, hashed bundles) at their own paths.
STATIC_DIR = os.path.join(BASE_DIR, "static")
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
