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
    # Step 3.8.9 (2026-07-15): bumped 0.2 -> 0.4. At 0.2 Qwen 3 falls into
    # structural repetition loops mid-body_html even with penalties active
    # (see logs/qwen-fallback-2026-07-15-185033-generate.json where it looped
    # "The time tells you about your next X" varying X). Higher temperature
    # naturally breaks out of those local minima.
    LOCAL_MODEL_TEMPERATURE: float = 0.4
    LOCAL_MODEL_TOP_P: float = 0.9
    LOCAL_MODEL_MAX_TOKENS: int = 12000
    # Step 3.8.8 (2026-07-15): Qwen 3 in JSON-schema mode falls into token-
    # repeat loops mid-body_html and burns the full max_tokens budget
    # emitting "..., the consensus, the consensus, the consensus, ..." (see
    # logs/qwen-fallback-2026-07-15-173147-generate.json). Frequency and
    # presence penalties are the standard remedy; only applied to the local
    # provider, not to Claude.
    # Step 3.8.10 (2026-07-18): bumped 0.3 -> 0.5. animefancast.com tuning run
    # (4 articles) still showed verbatim/near-verbatim sentence and paragraph
    # repetition scaling with article length, worst in the top length band
    # combined with an FAQ section (repeated content re-pasted a third time
    # in the FAQ answer). Raising frequency_penalty further discourages the
    # model from reusing the same tokens/phrases within a single completion.
    LOCAL_MODEL_FREQUENCY_PENALTY: float = 0.5
    LOCAL_MODEL_PRESENCE_PENALTY: float = 0.2
    # Step 3.8.9 (2026-07-15): frequency/presence penalties helped but weren't
    # enough - noon run had 2/3 sites still loop mid-body_html at the 12000
    # token cap (see logs/qwen-fallback-2026-07-15-180435/181229-generate.json).
    # llama.cpp's native repetition_penalty is a multiplicative penalty on the
    # raw token distribution (different mechanism than OpenAI-standard
    # frequency/presence), passed via extra_body since it's not a standard
    # OpenAI field. Default 1.15 is a common llama.cpp anti-loop value; 1.0
    # disables it entirely, values > 1.2 start hurting prose quality.
    # Step 3.8.10 (2026-07-18): bumped 1.15 -> 1.22 for the same repetition-
    # degeneration finding as the frequency_penalty change above. Kept below
    # the last-resort _retry_local_hotter() value of 1.25 so that path still
    # represents a genuine escalation over the default.
    LOCAL_MODEL_REPETITION_PENALTY: float = 1.22
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
            LOCAL_MODEL_TEMPERATURE=_parse_float(os.getenv("LOCAL_MODEL_TEMPERATURE"), 0.4),
            LOCAL_MODEL_TOP_P=_parse_float(os.getenv("LOCAL_MODEL_TOP_P"), 0.9),
            LOCAL_MODEL_MAX_TOKENS=_parse_int(os.getenv("LOCAL_MODEL_MAX_TOKENS"), 12000),
            LOCAL_MODEL_FREQUENCY_PENALTY=_parse_float(
                os.getenv("LOCAL_MODEL_FREQUENCY_PENALTY"), 0.5
            ),
            LOCAL_MODEL_PRESENCE_PENALTY=_parse_float(
                os.getenv("LOCAL_MODEL_PRESENCE_PENALTY"), 0.2
            ),
            LOCAL_MODEL_REPETITION_PENALTY=_parse_float(
                os.getenv("LOCAL_MODEL_REPETITION_PENALTY"), 1.22
            ),
            LOCAL_MODEL_DISABLE_THINKING=_parse_bool(
                os.getenv("LOCAL_MODEL_DISABLE_THINKING"), False
            ),
            LOCAL_IMAGE_BASE_URL=_normalize_optional(os.getenv("LOCAL_IMAGE_BASE_URL")),
            LOCAL_IMAGE_ENABLED=local_image_enabled_raw in _TRUE_STRINGS,
        )
