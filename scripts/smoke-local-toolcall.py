"""Phase 3.8 Step 3.8.1 smoke test: prove the local LM Studio model can do a
tool-use round trip with the OpenAI-compatible API.

Usage:
    python scripts/smoke-local-toolcall.py

Reads LOCAL_MODEL_BASE_URL and LOCAL_MODEL_NAME from .env. Sends a minimal
2-field tool schema and prints the parsed arguments dict on success or the
raw response on failure. Exits 0 on success, 1 on failure.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Allow importing openclaw when running from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import openai  # noqa: E402


def main() -> int:
    load_dotenv()
    base_url = os.getenv("LOCAL_MODEL_BASE_URL")
    model_name = os.getenv("LOCAL_MODEL_NAME")
    if not base_url or not model_name:
        print("ERROR: LOCAL_MODEL_BASE_URL and LOCAL_MODEL_NAME must be set in .env")
        return 1

    print(f"base_url = {base_url}")
    print(f"model    = {model_name}")

    client = openai.OpenAI(base_url=base_url, api_key="lm-studio", timeout=600.0)

    tool_schema = {
        "type": "function",
        "function": {
            "name": "submit_article",
            "description": "Submit a minimal article for smoke-testing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "body_html": {"type": "string"},
                },
                "required": ["title", "body_html"],
                "additionalProperties": False,
            },
        },
    }

    t0 = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a test agent. Call the submit_article tool once "
                        "with any short valid title and one-paragraph body_html."
                    ),
                },
                {
                    "role": "user",
                    "content": "Submit a short article about houseplants.",
                },
            ],
            tools=[tool_schema],
            tool_choice={"type": "function", "function": {"name": "submit_article"}},
            max_tokens=1024,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: request raised {type(exc).__name__}: {exc}")
        return 1
    latency = time.perf_counter() - t0
    print(f"latency  = {latency:.2f}s")

    if not response.choices:
        print(f"FAIL: no choices in response. Raw: {response!r}")
        return 1

    message = response.choices[0].message
    tool_calls = getattr(message, "tool_calls", None) or []
    if not tool_calls:
        print("FAIL: no tool_calls in message.")
        print(f"  content = {(message.content or '')[:400]!r}")
        return 1

    call = tool_calls[0]
    fn = call.function
    print(f"tool     = {fn.name}")
    try:
        args = json.loads(fn.arguments or "")
    except json.JSONDecodeError as exc:
        print(f"FAIL: arguments not valid JSON: {exc}")
        print(f"  raw = {(fn.arguments or '')[:400]!r}")
        return 1

    print(f"parsed args:\n{json.dumps(args, indent=2)[:800]}")
    missing = [k for k in ("title", "body_html") if k not in args or not args[k]]
    if missing:
        print(f"FAIL: missing/empty required fields: {missing}")
        return 1

    print("PASS: tool-use round-trip succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
