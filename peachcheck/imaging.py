"""Shared image-evidence encoding: one place decides how report evidence images are
embedded, so the forensics and measurement layers can't drift apart on format or
size caps.
"""

from __future__ import annotations

import base64
import io


def to_data_uri(image, max_dim: int = 480) -> str:
    """Encode a PIL image as a small base64 PNG data-URI for inline report evidence.

    Always downscales to `max_dim` — evidence images ride inside the trust-report
    JSON, so an uncapped frame would bloat every response that carries one.
    """
    img = image.copy()
    img.thumbnail((max_dim, max_dim))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
