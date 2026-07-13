"""API surface: upload validation, sample safety, and the packet flow's contract."""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)

ALL_NO = {"satire": False, "parody": False, "artistic_expression": False, "journalism": False}


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (48, 48), (200, 180, 160)).save(buf, "PNG")
    return buf.getvalue()


def test_health_reports_capabilities():
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert "c2pa" in body and "ocr_engine" in body


def test_analyze_returns_full_trust_report():
    response = client.post(
        "/analyze", files={"file": ("test.png", _png_bytes(), "image/png")}
    )
    assert response.status_code == 200
    report = response.json()["trust_report"]
    assert report["provenance"]["state"] == "untrusted"
    assert report["identity"]["sha256"]
    assert report["identity"]["perceptual_hash"]
    assert report["headline"]
    assert len(report["route"]) == 5


def test_non_image_upload_rejected():
    response = client.post(
        "/analyze", files={"file": ("evil.pdf", b"%PDF-1.4", "application/pdf")}
    )
    assert response.status_code == 415


def test_unknown_sample_404s_and_traversal_is_blocked():
    assert client.post("/analyze-sample", json={"filename": "nope.jpg"}).status_code == 404
    assert (
        client.post("/analyze-sample", json={"filename": "../../etc/passwd"}).status_code
        == 404
    )


def test_packet_incomplete_questionnaire_is_422():
    response = client.post(
        "/packet",
        json={"trust_report": {"action": {}}, "exemption_answers": {"satire": False}},
    )
    assert response.status_code == 422


def test_packet_flow_from_analysis():
    analysis = client.post(
        "/analyze", files={"file": ("test.png", _png_bytes(), "image/png")}
    ).json()
    packet = client.post(
        "/packet",
        json={
            "trust_report": analysis["trust_report"],
            "exemption_answers": ALL_NO,
            "publisher": "Test Publisher",
        },
    ).json()
    assert packet["packet_version"]
    assert packet["file_sha256"] == analysis["trust_report"]["identity"]["sha256"]
    # Plain image, no deterministic corroboration -> never eligible.
    assert packet["packet_eligible"] is False
    assert "not filed automatically" in packet["submission_instructions"]
