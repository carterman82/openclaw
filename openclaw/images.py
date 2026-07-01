"""Featured-image sources for openclaw articles.

Active path: OpenAI gpt-image-2 (see `generate_openai_image`). The Unsplash
search/download/attribution helpers below are kept as a flippable fallback.
"""

from __future__ import annotations

import base64
import html
import logging
from typing import Final
from urllib.parse import urlparse

import requests

from .config import Config

logger = logging.getLogger(__name__)

UNSPLASH_API: Final[str] = "https://api.unsplash.com"
UTM_PARAMS: Final[str] = "utm_source=openclaw&utm_medium=referral"
OPENAI_IMAGE_MODEL: Final[str] = "gpt-image-2"
OPENAI_IMAGE_SIZE: Final[str] = "1536x1024"
OPENAI_IMAGE_QUALITY: Final[str] = "medium"

ALLOWED_IMAGE_MIME: Final[frozenset[str]] = frozenset({
    "image/jpeg", "image/png", "image/webp", "image/gif",
})
MAX_IMAGE_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB


def _validate_image(image_bytes: bytes, mime_type: str) -> bool:
    if not image_bytes:
        logger.warning("Image bytes empty; rejecting.")
        return False
    if mime_type not in ALLOWED_IMAGE_MIME:
        logger.warning(
            "Image MIME %r not in allowlist %s; rejecting.",
            mime_type, sorted(ALLOWED_IMAGE_MIME),
        )
        return False
    if len(image_bytes) > MAX_IMAGE_BYTES:
        logger.warning(
            "Image size %d exceeds cap %d; rejecting.",
            len(image_bytes), MAX_IMAGE_BYTES,
        )
        return False
    return True


def _safe_http_url(url: str, default: str) -> str:
    """Return `url` if it is an http(s) URL with a host, else `default`."""
    if not url:
        return default
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https") and parsed.hostname:
        return url
    return default


def generate_openai_image(prompt: str, alt_text: str) -> dict | None:
    """Generate one image via OpenAI gpt-image-2.

    Returns the same dict shape as `find_unsplash_image` so main.py is source-
    agnostic. `attribution` is None for AI-generated images (no credit needed).
    Returns None on missing key, network error, or content-policy refusal —
    never raises.
    """
    cfg = Config.load()
    if not cfg.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set; skipping featured image.")
        return None
    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai SDK not installed; skipping featured image.")
        return None
    client = OpenAI(api_key=cfg.OPENAI_API_KEY)
    try:
        result = client.images.generate(
            model=OPENAI_IMAGE_MODEL,
            prompt=prompt,
            size=OPENAI_IMAGE_SIZE,
            quality=OPENAI_IMAGE_QUALITY,
            n=1,
        )
    except Exception as exc:
        logger.warning("OpenAI image generation failed: %s", exc)
        return None
    try:
        b64 = result.data[0].b64_json
        image_bytes = base64.b64decode(b64)
    except (AttributeError, IndexError, ValueError) as exc:
        logger.warning("OpenAI image response malformed: %s", exc)
        return None
    if not _validate_image(image_bytes, "image/png"):
        return None
    return {
        "image_bytes": image_bytes,
        "mime_type": "image/png",
        "alt_text": alt_text,
        "attribution": None,
    }


def _auth_header(access_key: str) -> dict[str, str]:
    return {"Authorization": f"Client-ID {access_key}"}


def _with_utm(url: str) -> str:
    if not url:
        return f"https://unsplash.com?{UTM_PARAMS}"
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{UTM_PARAMS}"


def find_unsplash_image(query: str) -> dict | None:
    """Search Unsplash for `query` and return the top hit as a dict.

    Returns None on missing API key, network error, empty results, or any
    Unsplash error. Callers should treat None as "publish without an image".

    The returned dict has keys:
        image_bytes: bytes
        mime_type: str
        alt_text: str
        attribution: {photographer_name, photographer_url, unsplash_url, download_location}
    """
    cfg = Config.load()
    if not cfg.UNSPLASH_ACCESS_KEY:
        logger.warning("UNSPLASH_ACCESS_KEY not set; skipping featured image.")
        return None
    auth = _auth_header(cfg.UNSPLASH_ACCESS_KEY)
    try:
        resp = requests.get(
            f"{UNSPLASH_API}/search/photos",
            params={"query": query, "orientation": "landscape", "per_page": 10},
            headers=auth,
            timeout=30,
        )
    except requests.RequestException as exc:
        logger.warning("Unsplash search failed for %r: %s", query, exc)
        return None
    if not resp.ok:
        logger.warning(
            "Unsplash search returned %d for %r: %s",
            resp.status_code, query, resp.text[:200],
        )
        return None
    results = resp.json().get("results", [])
    if not results:
        logger.info("Unsplash returned 0 results for %r.", query)
        return None

    photo = results[0]
    image_url = photo.get("urls", {}).get("regular")
    if not image_url:
        logger.warning("Unsplash top hit had no urls.regular for %r.", query)
        return None
    try:
        image_resp = requests.get(image_url, timeout=60)
        image_resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Unsplash image download failed: %s", exc)
        return None

    mime_type = image_resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip().lower()
    if not _validate_image(image_resp.content, mime_type):
        return None
    alt_text = (photo.get("alt_description") or photo.get("description") or "").strip()
    user = photo.get("user") or {}
    return {
        "image_bytes": image_resp.content,
        "mime_type": mime_type,
        "alt_text": alt_text,
        "attribution": {
            "photographer_name": user.get("name") or "Unsplash photographer",
            "photographer_url": user.get("links", {}).get("html") or "https://unsplash.com",
            "unsplash_url": "https://unsplash.com",
            "download_location": photo.get("links", {}).get("download_location") or "",
        },
    }


def attribution_html(attribution: dict) -> str:
    """Render the photographer credit as a single <p class="image-credit"> line.

    All Unsplash-provided values are HTML-escaped and URLs are scheme-validated
    before interpolation. Photographer names can contain `<`, `&`, `"`, etc.
    """
    raw_name = (attribution.get("photographer_name") or "Unsplash photographer").strip()
    name = html.escape(raw_name) or "Unsplash photographer"
    p_url_raw = _safe_http_url(attribution.get("photographer_url", ""), "https://unsplash.com")
    u_url_raw = _safe_http_url(attribution.get("unsplash_url", ""), "https://unsplash.com")
    p_url = html.escape(_with_utm(p_url_raw), quote=True)
    u_url = html.escape(_with_utm(u_url_raw), quote=True)
    return (
        '<p class="image-credit">'
        f'Photo by <a href="{p_url}" rel="noopener" target="_blank">{name}</a> '
        f'on <a href="{u_url}" rel="noopener" target="_blank">Unsplash</a>.'
        "</p>"
    )


def track_download(attribution: dict) -> None:
    """Fire the Unsplash download-tracking endpoint. Fire-and-forget; never raises."""
    location = attribution.get("download_location")
    if not location:
        return
    cfg = Config.load()
    if not cfg.UNSPLASH_ACCESS_KEY:
        return
    try:
        requests.get(location, headers=_auth_header(cfg.UNSPLASH_ACCESS_KEY), timeout=15)
    except requests.RequestException as exc:
        logger.warning("Unsplash download tracking failed: %s", exc)
