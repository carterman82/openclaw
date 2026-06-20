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
    if host not in _LOCAL_HOSTS:
        raise RuntimeError(
            f"Refusing plain HTTP for non-local WP host {host!r}. "
            f"Application Passwords sent over HTTP are exposed in transit. "
            f"Use https:// for production targets, or one of {sorted(_LOCAL_HOSTS)} for dev."
        )


@dataclass(frozen=True)
class Config:
    ANTHROPIC_API_KEY: str
    WP_BASE_URL: str
    WP_USERNAME: str
    WP_APP_PASSWORD: str
    UNSPLASH_ACCESS_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

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
        unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY") or None
        if unsplash_key == "REPLACE_ME":
            unsplash_key = None
        return cls(
            ANTHROPIC_API_KEY=os.environ["ANTHROPIC_API_KEY"],
            WP_BASE_URL=base_url,
            WP_USERNAME=os.environ["WP_USERNAME"],
            WP_APP_PASSWORD=os.environ["WP_APP_PASSWORD"],
            UNSPLASH_ACCESS_KEY=unsplash_key,
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
        )
