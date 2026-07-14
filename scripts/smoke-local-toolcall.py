"""Phase 3.8 smoke test for the local LM Studio model's tool-use round trip.

Usage:
    python scripts/smoke-local-toolcall.py                  # trivial 2-field schema only
    python scripts/smoke-local-toolcall.py --stages all      # + subreddit_select/generate/revise
    python scripts/smoke-local-toolcall.py --stages generate,revise

Reads LOCAL_MODEL_BASE_URL and LOCAL_MODEL_NAME from .env, plus the Step
3.8.7 tuning knobs (LOCAL_MODEL_TEMPERATURE, LOCAL_MODEL_TOP_P,
LOCAL_MODEL_MAX_TOKENS, LOCAL_MODEL_DISABLE_THINKING) via Config.load().

`--stages` reproduces the real production schemas + system prompts for
`subreddit_select`, `generate`, and `revise` against a standalone OpenAI SDK
client (this script never touches `_generate_with_local` /
`_select_subreddits_local` — see PLAN.md Step 3.8.5). Each stage call is
logged to stdout and dumped to `logs/qwen-smoke-<stage>.json` with HTTP
status, latency, token usage, finish_reason, tool_calls presence, full
content, and reasoning_content (if the server exposes one) — the exact
diagnostics needed to confirm or rule out the thinking-mode hypothesis in
PLAN.md's Step 3.8.5 working hypothesis.

Exits 0 if every requested stage passed, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Allow importing openclaw when running from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import openai  # noqa: E402

from openclaw._local_diagnostics import LOGS_DIR, response_diagnostics  # noqa: E402
from openclaw.config import Config  # noqa: E402
from openclaw.constants import ALLOWED_CATEGORIES  # noqa: E402

ALL_STAGES = ("trivial", "subreddit_select", "generate", "revise")
SITE_HOST = "localhost"
SITE_NAME = "Test Site"


def _client(cfg: Config, timeout: float = 600.0) -> "openai.OpenAI":
    return openai.OpenAI(
        base_url=cfg.LOCAL_MODEL_BASE_URL, api_key="lm-studio", timeout=timeout, max_retries=0,
    )


def _create_kwargs(cfg: Config) -> dict:
    kwargs: dict = {
        "temperature": cfg.LOCAL_MODEL_TEMPERATURE,
        "top_p": cfg.LOCAL_MODEL_TOP_P,
    }
    if cfg.LOCAL_MODEL_DISABLE_THINKING:
        kwargs["extra_body"] = {"reasoning_effort": "none"}
    return kwargs


def _run_stage(cfg: Config, stage: str, messages: list[dict], tool_schema: dict) -> bool:
    """Call the local model for one stage, dump diagnostics, return pass/fail."""
    client = _client(cfg)
    t0 = time.perf_counter()
    error: str | None = None
    response = None
    try:
        response = client.chat.completions.create(
            model=cfg.LOCAL_MODEL_NAME,
            messages=messages,
            tools=[tool_schema],
            tool_choice="required",
            max_tokens=cfg.LOCAL_MODEL_MAX_TOKENS,
            **_create_kwargs(cfg),
        )
    except Exception as exc:  # noqa: BLE001 - smoke test wants to see any failure, not crash
        error = f"{type(exc).__name__}: {exc}"
    latency = time.perf_counter() - t0

    diagnostics = response_diagnostics(response)
    tool_calls = diagnostics["message"]["tool_calls"]
    passed = error is None and bool(tool_calls)

    payload = {
        "stage": stage,
        "model": cfg.LOCAL_MODEL_NAME,
        "latency_seconds": round(latency, 2),
        "request_error": error,
        "disable_thinking": cfg.LOCAL_MODEL_DISABLE_THINKING,
        "temperature": cfg.LOCAL_MODEL_TEMPERATURE,
        "top_p": cfg.LOCAL_MODEL_TOP_P,
        "max_tokens": cfg.LOCAL_MODEL_MAX_TOKENS,
        "tool_calls_present": bool(tool_calls),
        **diagnostics,
    }
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    dump_path = LOGS_DIR / f"qwen-smoke-{stage}.json"
    dump_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    content_preview = (diagnostics["message"]["content"] or "")[:120]
    status = "PASS" if passed else "FAIL"
    print(
        f"[{status}] stage={stage} latency={latency:.2f}s "
        f"finish_reason={diagnostics['finish_reason']!r} "
        f"prompt_tokens={diagnostics['usage']['prompt_tokens'] if diagnostics['usage'] else None} "
        f"completion_tokens={diagnostics['usage']['completion_tokens'] if diagnostics['usage'] else None} "
        f"tool_calls={len(tool_calls)} content_preview={content_preview!r}"
    )
    if error:
        print(f"       error: {error}")
    print(f"       dumped to {dump_path}")
    return passed


def _trivial_tool_schema() -> dict:
    return {
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


def _run_trivial(cfg: Config) -> bool:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a test agent. Call the submit_article tool once "
                "with any short valid title and one-paragraph body_html."
            ),
        },
        {"role": "user", "content": "Submit a short article about houseplants."},
    ]
    return _run_stage(cfg, "trivial", messages, _trivial_tool_schema())


def _run_subreddit_select(cfg: Config) -> bool:
    from openclaw.trends import _SUBREDDIT_TOOL_SCHEMA, _build_subreddit_select_message

    candidates = [
        "SaaS", "Entrepreneur", "smallbusiness", "productivity", "startups",
        "indiehackers", "freelance", "digitalnomad", "marketing", "growthhacking",
    ]
    user_message = _build_subreddit_select_message(
        candidates, category="Concepts", site_name=SITE_NAME, limit=3,
    )
    tool_schema = {
        "type": "function",
        "function": {
            "name": _SUBREDDIT_TOOL_SCHEMA["name"],
            "description": _SUBREDDIT_TOOL_SCHEMA["description"],
            "parameters": _SUBREDDIT_TOOL_SCHEMA["input_schema"],
        },
    }
    messages = [{"role": "user", "content": user_message}]
    return _run_stage(cfg, "subreddit_select", messages, tool_schema)


def _run_generate(cfg: Config) -> bool:
    from openclaw.generator import (
        _anthropic_to_openai_tool_schema,
        _build_avoidance_message,
        _build_system_prompt,
        _build_tool_schema,
        _build_user_message,
    )

    system_prompt = _build_system_prompt(ALLOWED_CATEGORIES, SITE_HOST)
    user_message = _build_user_message(None, None, SITE_NAME) + _build_avoidance_message(
        ["A prior test article title to avoid duplicating"]
    )
    tool_schema = _anthropic_to_openai_tool_schema(_build_tool_schema(ALLOWED_CATEGORIES))
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    return _run_stage(cfg, "generate", messages, tool_schema)


def _stub_draft_article() -> dict:
    return {
        "title": "How Compound Interest Actually Works",
        "body_html": (
            "<p>Compound interest is the process by which interest earns "
            "interest over time, compounding growth exponentially rather "
            "than linearly.</p><h2>Why it matters</h2><p>Small differences "
            "in rate or time horizon produce large differences in outcome.</p>"
        ),
        "category": "Concepts",
        "tags": ["finance", "math", "interest"],
        "excerpt": "Compound interest explained: how interest earning interest "
                    "compounds growth exponentially over time for savers.",
        "slug": "how-compound-interest-works",
        "focus_keyphrase": "compound interest",
        "seo_title": "Compound Interest: How It Actually Works",
        "meta_description": "Compound interest explained simply: how interest "
                             "earning interest compounds growth exponentially "
                             "and why time horizon matters most.",
        "image_alt_text": "Coins stacked in ascending rows illustrating compound interest growth",
        "image_prompt": "Create a cinematic 16:9 cover photograph of ascending "
                         "stacks of coins in golden light, photorealistic, shallow "
                         "depth of field.",
        "unsplash_query": "coins growth stacks",
        "unique_angle_justification": "Contested-explanation angle grounded in "
                                       "standard compounding math.",
        "internal_links_used": [],
        "external_links_used": [],
    }


def _run_revise(cfg: Config) -> bool:
    from openclaw.generator import (
        _anthropic_to_openai_tool_schema,
        _build_editor_system_prompt,
        _build_tool_schema,
        _wrap_data,
    )

    system_prompt = _build_editor_system_prompt(ALLOWED_CATEGORIES, SITE_HOST)
    draft_json = json.dumps(_stub_draft_article(), ensure_ascii=False, indent=2)
    user_message = (
        "Review and revise the draft article below, then submit the complete "
        "revised article.\n\n" + _wrap_data(draft_json, "draft_article")
    )
    tool_schema = _anthropic_to_openai_tool_schema(_build_tool_schema(ALLOWED_CATEGORIES))
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    return _run_stage(cfg, "revise", messages, tool_schema)


_STAGE_RUNNERS = {
    "trivial": _run_trivial,
    "subreddit_select": _run_subreddit_select,
    "generate": _run_generate,
    "revise": _run_revise,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stages",
        default="trivial",
        help="Comma-separated stages to run (trivial,subreddit_select,generate,revise) "
             "or 'all'.",
    )
    args = parser.parse_args()

    load_dotenv()
    from openclaw.main import _activate_site

    _activate_site(SITE_HOST)  # copies LOCALHOST_WP_* into bare WP_* for Config.load()
    cfg = Config.load()
    if not cfg.LOCAL_MODEL_BASE_URL or not cfg.LOCAL_MODEL_NAME:
        print("ERROR: LOCAL_MODEL_BASE_URL and LOCAL_MODEL_NAME must be set in .env")
        return 1

    stages = ALL_STAGES if args.stages == "all" else tuple(
        s.strip() for s in args.stages.split(",") if s.strip()
    )
    unknown = [s for s in stages if s not in _STAGE_RUNNERS]
    if unknown:
        print(f"ERROR: unknown stage(s): {unknown}. Valid: {list(_STAGE_RUNNERS)}")
        return 1

    print(f"base_url          = {cfg.LOCAL_MODEL_BASE_URL}")
    print(f"model             = {cfg.LOCAL_MODEL_NAME}")
    print(f"disable_thinking  = {cfg.LOCAL_MODEL_DISABLE_THINKING}")
    print(f"temperature/top_p = {cfg.LOCAL_MODEL_TEMPERATURE}/{cfg.LOCAL_MODEL_TOP_P}")
    print(f"max_tokens        = {cfg.LOCAL_MODEL_MAX_TOKENS}")
    print(f"stages            = {stages}")
    print()

    results = {stage: _STAGE_RUNNERS[stage](cfg) for stage in stages}

    print()
    print("Summary:")
    for stage, passed in results.items():
        print(f"  {'PASS' if passed else 'FAIL'}  {stage}")

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
