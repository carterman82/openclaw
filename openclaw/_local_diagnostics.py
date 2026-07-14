"""Shared forensics helpers for local-model (LM Studio) tool-call failures.

Used by generator.py, trends.py, and scripts/smoke-local-toolcall.py so the
JSON shape dumped to `logs/` is consistent across all three call sites.
Nothing in this module raises — a forensics dump must never take down the
fallback-to-Claude control flow it's trying to document.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"


def response_diagnostics(response: Any) -> dict:
    """Extract the fields useful for diagnosing a no-tool-call failure from
    an OpenAI-SDK ChatCompletion object. `response` may be None (e.g. "no
    choices" case) — every field degrades to None rather than raising.
    """
    if response is None:
        return {
            "finish_reason": None,
            "usage": None,
            "message": {"content": None, "reasoning_content": None, "tool_calls": []},
        }
    choice = response.choices[0] if getattr(response, "choices", None) else None
    message = getattr(choice, "message", None)
    usage = getattr(response, "usage", None)
    tool_calls = getattr(message, "tool_calls", None) or []
    return {
        "finish_reason": getattr(choice, "finish_reason", None),
        "usage": {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        } if usage else None,
        "message": {
            "content": getattr(message, "content", None),
            "reasoning_content": getattr(message, "reasoning_content", None),
            "tool_calls": [
                {
                    "name": getattr(getattr(tc, "function", None), "name", None),
                    "arguments": getattr(getattr(tc, "function", None), "arguments", None),
                }
                for tc in tool_calls
            ],
        },
    }


def dump_fallback_response(stage: str, model: str, response: Any, reason: str) -> None:
    """Persist a full raw local-model response before a production fallback.

    Fire-and-forget: any error while writing the dump is logged and
    swallowed so it can never affect the fallback-to-Claude control flow.
    """
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
        path = LOGS_DIR / f"qwen-fallback-{timestamp}-{stage}.json"
        payload = {
            "stage": stage,
            "model": model,
            "reason": reason,
            **response_diagnostics(response),
        }
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 - forensics must never break the fallback path
        logger.warning("Failed to write qwen-fallback diagnostics dump: %s", exc)
