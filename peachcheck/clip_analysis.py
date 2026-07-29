"""Server-side clip URL resolution and frame sampling.

This module exists because asking users for a raw .mp4 URL is not a realistic UX.
Given a normal video page URL (TikTok, YouTube, Instagram, or a direct file), it
uses yt-dlp to fetch a locally readable copy of the clip, then samples a few still
frames server-side so the existing image pipeline can analyze them unchanged.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from peachcheck.imaging import to_data_uri as _thumbnail_data_uri


@dataclass
class SampledFrame:
    frame_number: int
    seconds: float
    label: str
    image_path: str
    preview_data_url: str


@dataclass
class SampledClip:
    source_url: str
    duration_seconds: float
    frames: list[SampledFrame]
    source_title: str | None = None
    source_description: str | None = None
    ai_disclosure: str | None = None


_AI_DISCLOSURE_PATTERNS = (
    re.compile(r"\bai[\s-]+generated\b", re.IGNORECASE),
    re.compile(r"\bgenerated\s+(?:with|by|using)\s+(?:an?\s+)?ai\b", re.IGNORECASE),
    re.compile(r"\bartificial[\s-]+intelligence[\s-]+generated\b", re.IGNORECASE),
    re.compile(r"\bsynthetic[\s-]+media\b", re.IGNORECASE),
)


def find_ai_disclosure(title: str | None, description: str | None) -> str | None:
    """Return the uploader/platform text that explicitly declares AI generation.

    This is direct source evidence, not a visual-model inference. Deliberately narrow
    phrases avoid treating a casual mention of "AI" as a generation disclosure.
    """
    for text in (title, description):
        cleaned = " ".join((text or "").split())
        if cleaned and any(pattern.search(cleaned) for pattern in _AI_DISCLOSURE_PATTERNS):
            return cleaned[:500]
    return None


def _require_http_url(url: str) -> None:
    # A duplicated scheme (e.g. "https://www.youtube.comhttps://www.youtube.com/...",
    # which happens when a URL gets pasted onto un-cleared field text) parses "successfully"
    # under urlparse — it reports a non-empty scheme and netloc — but the netloc is garbage
    # and the failure only surfaces later as a cryptic DNS error deep inside yt-dlp. Catch it
    # here with an actionable message instead.
    if url.count("://") > 1:
        raise ValueError(
            "That URL has an extra 'https://' in it — paste just the clip link on its own, "
            "e.g. https://www.youtube.com/watch?v=..."
        )
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Enter a valid http:// or https:// clip URL.")


def _format_time(seconds: float) -> str:
    whole = max(0, round(seconds))
    mins = whole // 60
    secs = whole % 60
    return f"{mins:02d}:{secs:02d}"


def _download_clip(url: str, temp_dir: str) -> tuple[str, dict]:
    try:
        import yt_dlp
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Clip-link support requires yt-dlp on the server. Install requirements and try again."
        ) from exc

    outtmpl = os.path.join(temp_dir, "clip.%(ext)s")
    options = {
        "outtmpl": outtmpl,
        "format": "mp4/best[ext=mp4]/best",
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "restrictfilenames": True,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
        if not os.path.exists(path):
            requested = info.get("requested_downloads") or []
            filepath = requested[0].get("filepath") if requested else None
            if filepath and os.path.exists(filepath):
                path = filepath
            else:
                mp4_path = os.path.splitext(path)[0] + ".mp4"
                if os.path.exists(mp4_path):
                    path = mp4_path
        if not os.path.exists(path):
            raise RuntimeError("Could not resolve a downloadable clip from that URL.")
        return path, info


def _sample_frames_from_local_clip(
    clip_path: str,
    temp_dir: str,
    frame_count: int,
    max_duration_seconds: int,
) -> tuple[float, list[SampledFrame]]:
    try:
        import imageio_ffmpeg
        import numpy as np
        from PIL import Image
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Clip-link support requires imageio-ffmpeg, Pillow, and numpy on the server."
        ) from exc

    reader = imageio_ffmpeg.read_frames(clip_path, pix_fmt="rgb24")
    meta = next(reader)
    fps = float(meta.get("fps") or 0.0)
    size = tuple(meta.get("size") or (0, 0))
    duration = float(meta.get("duration") or 0.0)
    if not fps or not size[0] or not size[1] or not duration:
        raise RuntimeError("Could not read duration and frame metadata from that clip.")
    if duration > max_duration_seconds:
        raise RuntimeError(
            f"Only short clips up to {max_duration_seconds} seconds are supported right now."
        )

    usable_frame_count = max(1, frame_count)
    target_times = [((i + 1) / (usable_frame_count + 1)) * duration for i in range(usable_frame_count)]
    target_indices = [min(round(t * fps), max(0, round(duration * fps) - 1)) for t in target_times]

    frames: list[SampledFrame] = []
    target_map = {index: position for position, index in enumerate(target_indices)}
    width, height = size
    try:
        for frame_index, frame_bytes in enumerate(reader):
            if frame_index not in target_map:
                continue
            position = target_map[frame_index]
            seconds = target_times[position]
            array = np.frombuffer(frame_bytes, dtype=np.uint8).reshape((height, width, 3))
            image = Image.fromarray(array, mode="RGB")
            output_path = os.path.join(temp_dir, f"frame-{position + 1}.png")
            image.save(output_path, "PNG")
            # The full-resolution frame stays on disk at `output_path` for the forensics
            # pipeline (which needs real pixel detail). The *preview* only needs to be
            # recognizable in a UI thumbnail, so it goes through the same downscaling
            # every other evidence image uses — an uncapped full-res preview per frame
            # (easily 1MB+ for a vertical video) is what was blowing past the browser's
            # sessionStorage quota and history.pushState size limit, silently dropping
            # the clip report on any re-render that couldn't read location.state.
            frames.append(
                SampledFrame(
                    frame_number=position + 1,
                    seconds=seconds,
                    label=_format_time(seconds),
                    image_path=output_path,
                    preview_data_url=_thumbnail_data_uri(image),
                )
            )
            if len(frames) == usable_frame_count:
                break
    finally:
        reader.close()

    if len(frames) != usable_frame_count:
        raise RuntimeError("Could not extract the expected number of frames from that clip.")

    frames.sort(key=lambda frame: frame.frame_number)
    return duration, frames


def resolve_and_sample_clip(
    url: str,
    temp_dir: str,
    frame_count: int = 3,
    max_duration_seconds: int = 90,
) -> SampledClip:
    _require_http_url(url)
    clip_path, source_info = _download_clip(url, temp_dir)
    duration, frames = _sample_frames_from_local_clip(
        clip_path,
        temp_dir=temp_dir,
        frame_count=frame_count,
        max_duration_seconds=max_duration_seconds,
    )
    title = source_info.get("title")
    description = source_info.get("description")
    return SampledClip(
        source_url=url,
        duration_seconds=duration,
        frames=frames,
        source_title=title,
        source_description=description,
        ai_disclosure=find_ai_disclosure(title, description),
    )


def clip_support_available() -> bool:
    try:
        import yt_dlp  # noqa: F401
        import imageio_ffmpeg  # noqa: F401
    except Exception:
        return False
    return True
