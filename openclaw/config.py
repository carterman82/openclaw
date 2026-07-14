"""Centralized env loading for the openclaw agent."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from dotenv import load_dotenv

_LOCAL_HOSTS = frozenset({
    "localhost", "127.0.0.1", "::1",
    "wordpress", "host.docker.internal",
})


def _validate_base_url(url: str) -> None:
    """Reject http:// for non-local targets — Application Password must not travel cleartext."""
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme == "https":
        return
    if scheme != "http":
        raise RuntimeError(
            f"WP_BASE_URL must use http or https; got scheme {scheme!r} in {url!r}."
        )
    host = (parsed.hostname or "").lower()
    # *.localhost is reserved per RFC 6761 — subdomains resolve to the loopback
    # interface, so they're safe for HTTP just like bare `localhost` (used by the
    # Phase 5 multisite pilot: gardening.localhost, dogs.localhost, ...).
    if host in _LOCAL_HOSTS or host.endswith(".localhost"):
        return
    raise RuntimeError(
        f"Refusing plain HTTP for non-local WP host {host!r}. "
        f"Application Passwords sent over HTTP are exposed in transit. "
        f"Use https:// for production targets, or one of {sorted(_LOCAL_HOSTS)} "
        f"(or a *.localhost subdomain) for dev."
    )


_TRUE_STRINGS = frozenset({"true", "1", "yes", "on"})


def _normalize_optional(value: str | None) -> str | None:
    if not value:
        return None
    if value == "REPLACE_ME":
        return None
    return value


def _parse_float(value: str | None, default: float) -> float:
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _parse_int(value: str | None, default: int) -> int:
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_bool(value: str | None, default: bool) -> bool:
    if not value:
        return default
    return value.strip().lower() in _TRUE_STRINGS


@dataclass(frozen=True)
class Config:
    ANTHROPIC_API_KEY: str
    WP_BASE_URL: str
    WP_USERNAME: str
    WP_APP_PASSWORD: str
    UNSPLASH_ACCESS_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    LOCAL_MODEL_BASE_URL: str | None = None
    LOCAL_MODEL_NAME: str | None = None
    LOCAL_MODEL_ENABLED: bool = False
    LOCAL_MODEL_TEMPERATURE: float = 0.2
    LOCAL_MODEL_TOP_P: float = 0.9
    LOCAL_MODEL_MAX_TOKENS: int = 12000
    # Default False: Step 3.8.5/3.8.7 (2026-07-14) found that the only
    # mechanism that actually suppresses thinking on this LM Studio build
    # (extra_body={"reasoning_effort":"none"}) also reliably breaks
    # tool_choice="required" grammar enforcement, so the model answers in
    # plain prose instead of calling the tool. See PLAN.md §12 for the full
    # writeup. Kept as an opt-in knob in case a future server/model build
    # handles it correctly.
    LOCAL_MODEL_DISABLE_THINKING: bool = False
    LOCAL_IMAGE_BASE_URL: str | None = None
    LOCAL_IMAGE_ENABLED: bool = False

    @classmethod
    def load(cls) -> "Config":
        load_dotenv()
        required = (
            "ANTHROPIC_API_KEY",
            "WP_BASE_URL",
            "WP_USERNAME",
            "WP_APP_PASSWORD",
        )
        missing = [k for k in required if not os.getenv(k)]
        if missing:
            raise RuntimeError(
                f"missing required env vars: {', '.join(missing)}. "
                f"Copy .env.example to .env and fill them in."
            )
        base_url = os.environ["WP_BASE_URL"].rstrip("/")
        _validate_base_url(base_url)
        local_enabled_raw = (os.getenv("LOCAL_MODEL_ENABLED") or "").strip().lower()
        local_image_enabled_raw = (os.getenv("LOCAL_IMAGE_ENABLED") or "").strip().lower()
        return cls(
            ANTHROPIC_API_KEY=os.environ["ANTHROPIC_API_KEY"],
            WP_BASE_URL=base_url,
            WP_USERNAME=os.environ["WP_USERNAME"],
            WP_APP_PASSWORD=os.environ["WP_APP_PASSWORD"],
            UNSPLASH_ACCESS_KEY=_normalize_optional(os.getenv("UNSPLASH_ACCESS_KEY")),
            OPENAI_API_KEY=_normalize_optional(os.getenv("OPENAI_API_KEY")),
            LOCAL_MODEL_BASE_URL=_normalize_optional(os.getenv("LOCAL_MODEL_BASE_URL")),
            LOCAL_MODEL_NAME=_normalize_optional(os.getenv("LOCAL_MODEL_NAME")),
            LOCAL_MODEL_ENABLED=local_enabled_raw in _TRUE_STRINGS,
            LOCAL_MODEL_TEMPERATURE=_parse_float(os.getenv("LOCAL_MODEL_TEMPERATURE"), 0.2),
            LOCAL_MODEL_TOP_P=_parse_float(os.getenv("LOCAL_MODEL_TOP_P"), 0.9),
            LOCAL_MODEL_MAX_TOKENS=_parse_int(os.getenv("LOCAL_MODEL_MAX_TOKENS"), 12000),
            LOCAL_MODEL_DISABLE_THINKING=_parse_bool(
                os.getenv("LOCAL_MODEL_DISABLE_THINKING"), False
            ),
            LOCAL_IMAGE_BASE_URL=_normalize_optional(os.getenv("LOCAL_IMAGE_BASE_URL")),
            LOCAL_IMAGE_ENABLED=local_image_enabled_raw in _TRUE_STRINGS,
        )
