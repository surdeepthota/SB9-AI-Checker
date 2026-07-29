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
    assert "clip_url_support" in body


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


def test_sample_preview_serves_only_bundled_images():
    response = client.get("/sample-file/peachcheck-ad-no-disclosure.png")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")
    assert client.get("/sample-file/nope.png").status_code == 404


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


def test_analyze_clip_url_rejects_invalid_scheme():
    response = client.post(
        "/analyze-clip-url",
        json={"url": "not-a-url", "is_campaign_ad": False},
    )
    assert response.status_code == 422
    assert "http://" in response.json()["detail"]


def test_analyze_clip_url_rejects_duplicated_scheme():
    # Regression: "https://www.youtube.comhttps://www.youtube.com/watch?v=..." used to pass
    # _require_http_url's check (urlparse still finds a scheme + non-empty netloc) and only
    # fail deep inside yt-dlp with a cryptic DNS-resolution error naming a garbage host.
    response = client.post(
        "/analyze-clip-url",
        json={
            "url": "https://www.youtube.comhttps://www.youtube.com/watch?v=ed9obBPmg5o",
            "is_campaign_ad": False,
        },
    )
    assert response.status_code == 422
    assert "extra" in response.json()["detail"]


def test_clip_source_ai_disclosure_is_direct_evidence():
    from peachcheck.clip_analysis import find_ai_disclosure

    disclosure = find_ai_disclosure(
        "This contains AI generated media. we know tiktok",
        None,
    )
    assert disclosure == "This contains AI generated media. we know tiktok"
    assert find_ai_disclosure("A discussion about AI policy", None) is None


def test_clip_summary_preserves_explicit_ai_disclosure():
    reports = [
        {
            "analysis": {
                "trust_report": {
                    "judgment": {"calibrated_score": 0.2, "band": "leans_authentic"}
                }
            }
        }
    ]
    summary = __import__("app")._summarize_clip_reports(
        reports,
        source_ai_disclosure="This contains AI generated media.",
    )
    assert summary["clip_decision_score"] == 0.95
    assert summary["judgment"]["band"] == "strong_signal"
    assert summary["source_ai_disclosure"] == "This contains AI generated media."


def test_analyze_clip_url_returns_frame_reports(monkeypatch, tmp_path):
    frame_path = tmp_path / "frame-1.png"
    Image.new("RGB", (48, 48), (120, 130, 140)).save(frame_path, "PNG")

    from peachcheck.clip_analysis import SampledClip, SampledFrame

    def fake_resolve_and_sample_clip(
        url: str,
        temp_dir: str,
        frame_count: int = 3,
    ):
        assert url == "https://www.youtube.com/watch?v=test"
        assert frame_count == 5
        return SampledClip(
            source_url=url,
            duration_seconds=12.0,
            frames=[
                SampledFrame(
                    frame_number=1,
                    seconds=3.0,
                    label="00:03",
                    image_path=str(frame_path),
                    preview_data_url="data:image/png;base64,abc",
                )
            ],
        )

    monkeypatch.setattr("app.resolve_and_sample_clip", fake_resolve_and_sample_clip)

    response = client.post(
        "/analyze-clip-url",
        json={"url": "https://www.youtube.com/watch?v=test", "is_campaign_ad": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["clip_url"] == "https://www.youtube.com/watch?v=test"
    assert body["duration_seconds"] == 12.0
    assert body["clip_summary"]["sampled_frames"] == 1
    assert body["clip_summary"]["clip_decision_score"] >= body["clip_summary"]["average_frame_score"]
    assert body["clip_summary"]["judgment"]["band"]
    assert len(body["reports"]) == 1
    report = body["reports"][0]
    assert report["frame_number"] == 1
    assert report["label"] == "00:03"
    assert report["preview_data_url"].startswith("data:image/png;base64,")
    assert report["analysis"]["trust_report"]["identity"]["sha256"]


def test_analyze_clip_url_strict_mode_increases_frame_request(monkeypatch, tmp_path):
    frame_path = tmp_path / "frame-1.png"
    Image.new("RGB", (48, 48), (120, 130, 140)).save(frame_path, "PNG")

    from peachcheck.clip_analysis import SampledClip, SampledFrame

    def fake_resolve_and_sample_clip(
        url: str,
        temp_dir: str,
        frame_count: int = 3,
    ):
        assert frame_count == 7
        return SampledClip(
            source_url=url,
            duration_seconds=12.0,
            frames=[
                SampledFrame(
                    frame_number=1,
                    seconds=3.0,
                    label="00:03",
                    image_path=str(frame_path),
                    preview_data_url="data:image/png;base64,abc",
                )
            ],
        )

    monkeypatch.setattr("app.resolve_and_sample_clip", fake_resolve_and_sample_clip)

    response = client.post(
        "/analyze-clip-url",
        json={
            "url": "https://www.youtube.com/watch?v=test",
            "is_campaign_ad": False,
            "strict_mode": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["clip_summary"]["strict_mode"] is True
    assert body["clip_summary"]["clip_decision_score"] >= body["clip_summary"]["average_frame_score"]
