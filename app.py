"""PeachCheck API — FastAPI wrapper around the five-layer trust pipeline.

Endpoints:
    POST /analyze          multipart upload -> full trust report JSON
    POST /analyze-sample   run the pipeline on a bundled demo-corpus file by name
    GET  /samples          list the bundled demo corpus (for the UI's demo picker)
    POST /packet           exemption questionnaire + publisher -> evidence packet JSON
    GET  /api/health       which optional capabilities are live in this environment

Endpoints are plain `def` (not `async def`) on purpose: the pipeline is CPU-bound
(hashing, FFT, model inference), so FastAPI's threadpool execution keeps the event
loop free instead of blocking it.
"""

import csv
import os
import shutil
import tempfile
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from peachcheck.layers import action as action_layer
from peachcheck.layers.forensics import extract_metadata_text
from peachcheck.pipeline import run_pipeline
from peachcheck.schema import ActionBlock, report_to_dict

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
