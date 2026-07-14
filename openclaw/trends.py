"""Topic-discovery signals for the openclaw agent.

Two free, no-auth sources feed Claude a snapshot of what content people are
currently asking about:

- `fetch_reddit_trends`: top posts of the last week from a given set of
  subreddits, via Reddit's public Atom RSS endpoints.
- `fetch_google_suggest`: real autocomplete completions for seed phrases,
  via Google's `suggestqueries` endpoint.

Both follow the `images.py` pattern: never raise into `main.py`. On any
network/parse failure, log a WARNING and return an empty list so the publish
path is unaffected.

Per-site subreddits and suggest seeds live in `website_memory/{host}.trends.json`.
When no trends file exists for the active site, `gather_trending_signals` returns
empty lists — no signals leak from one site to another.

Scanning every subreddit in that file serially (Reddit's anonymous RSS rate
limit forces a multi-second gap plus backoff between requests) took 15-20
minutes for a ~18-subreddit list. `select_relevant_subreddits` asks a fast
model to narrow that list down to the handful actually worth scanning this
run before `fetch_reddit_trends` touches the network at all.

The signal is consumed by `generator.generate_article(trending_signals=...)`
and rendered into a `<reference_data type="trending_signals">` block in the
user message. TOPIC.md's evergreen/trending ratio remains authoritative;
this module supplies inputs, not directives.
"""

from __future__ import annotations

import json
import logging
import random
import time
import xml.etree.ElementTree as ET
from typing import Final

import anthropic
import httpx
import openai
import requests

from ._local_diagnostics import dump_fallback_response
from .config import Config

logger = logging.getLogger(__name__)

# Reddit aggressively 403s anonymous JSON requests as of 2024+. The Atom RSS
# feed at /r/{sub}/top/.rss?t=week is the only no-auth path that still works
# reliably. RSS strips upvote counts, so per-post `score` becomes None and
# items are surfaced in Reddit's own top-sort order.
#
# Anonymous RSS is rate-limited tightly enough that 3 requests a few seconds
# apart routinely 429 on all of them. A 2-3s gap wasn't enough breathing room;
# widen the inter-request delay and retry 429s with backoff (honoring
# Retry-After when Reddit sends one) instead of giving up on the first hit.
REDDIT_USER_AGENT: Final[str] = "openclaw/0.1 topic discovery"
REDDIT_PER_SUB: Final[int] = 10
REDDIT_INTER_REQUEST_DELAY: Final[tuple[float, float]] = (6.0, 9.0)
REDDIT_429_MAX_RETRIES: Final[int] = 3
REDDIT_429_BACKOFF_BASE: Final[float] = 10.0
_ATOM_NS: Final[str] = "{http://www.w3.org/2005/Atom}"


def _get_reddit_rss(sub: str, headers: dict[str, str]) -> "requests.Response | None":
    """GET one subreddit's RSS feed, retrying on 429 with backoff.

    Returns the response (which may still be a non-429 error) or None if
    every attempt raised a network exception.
    """
    for attempt in range(REDDIT_429_MAX_RETRIES + 1):
        try:
            resp = requests.get(
                f"https://www.reddit.com/r/{sub}/top/.rss",
                params={"t": "week", "limit": REDDIT_PER_SUB},
                headers=headers,
                timeout=15,
            )
        except requests.RequestException as exc:
            logger.warning("Reddit RSS fetch failed for r/%s: %s", sub, exc)
            return None
        if resp.status_code != 429 or attempt == REDDIT_429_MAX_RETRIES:
            return resp
        retry_after = resp.headers.get("Retry-After")
        if retry_after and retry_after.strip().isdigit():
            wait = float(retry_after)
        else:
            wait = REDDIT_429_BACKOFF_BASE * (attempt + 1) + random.uniform(0.0, 3.0)
        logger.warning(
            "Reddit RSS 429 for r/%s (attempt %d/%d), backing off %.1fs",
            sub, attempt + 1, REDDIT_429_MAX_RETRIES, wait,
        )
        time.sleep(wait)
    return None  # unreachable, but keeps type-checkers happy


SUBREDDIT_SELECT_FALLBACK_MODEL: Final[str] = "claude-haiku-4-5-20251001"
TOP_N_SUBREDDITS: Final[int] = 3
# Thinking-mode local models (e.g. Qwen3.6) spend a chunk of the completion
# budget on a <think> trace before emitting the actual tool call. Step 3.8.5
# (2026-07-14) measured reasoning traces for this exact stage/schema running
# anywhere from ~300 to 11999+ tokens (observed finish_reason=length with
# zero tool call at the old 2048 cap, and even at 12000 in one trial) - the
# length is genuinely non-deterministic per call, not proportional to task
# complexity. `_select_subreddits_local` now uses `cfg.LOCAL_MODEL_MAX_TOKENS`
# (default 12000) when a Config is supplied; this constant is only the
# fallback for direct/unit-test calls that don't pass `cfg`.
_SUBREDDIT_SELECT_MAX_TOKENS: Final[int] = 12000
_SUBREDDIT_SELECT_TIMEOUT_SECONDS: Final[float] = 180.0

_SUBREDDIT_TOOL_SCHEMA: Final[dict] = {
    "name": "select_subreddits",
    "description": "Return the subreddit names most likely to have current, relevant discussion for this article run.",
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "subreddits": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Subreddit names without the r/ prefix, most relevant first.",
            },
        },
        "required": ["subreddits"],
    },
}


class _SubredditSelectionError(Exception):
    """Raised when the local provider produces an unusable subreddit selection.

    Caught by `select_relevant_subreddits`, which falls back to Claude Haiku.
    Never propagates out of this module.
    """


def _build_subreddit_select_message(
    candidates: list[str],
    category: str | None,
    site_name: str | None,
    limit: int,
) -> str:
    focus = f" This run's article category is {category!r}." if category else ""
    site = f" The site is {site_name!r}." if site_name else ""
    return (
        f"Candidate subreddits from this site's trends config: "
        f"{', '.join(candidates)}.{site}{focus} "
        f"Pick the {limit} subreddits most likely to have current, relevant "
        f"discussion for this run. Prefer names from the candidate list, but "
        f"you may name a different real subreddit instead if you're confident "
        f"it fits better. Return subreddit names only, no r/ prefix."
    )


def _clean_subreddit_names(raw: list, limit: int) -> list[str]:
    picked = [str(s).removeprefix("r/").strip() for s in raw]
    return [s for s in picked if s][:limit]


_SUBREDDIT_SELECT_STAGE: Final[str] = "subreddit_select"


def _select_subreddits_local(
    user_message: str,
    base_url: str,
    model_name: str,
    limit: int,
    cfg: Config | None = None,
) -> list[str]:
    """Call the local OpenAI-compatible server (LM Studio, e.g. Qwen 3.6) with tool-use.

    Raises `_SubredditSelectionError` on any provider-side failure so the
    caller can fall back to Claude Haiku. Before any raise past a successful
    HTTP response, the full raw response is dumped to
    `logs/qwen-fallback-<timestamp>-subreddit_select.json` for forensics
    (Step 3.8.6).
    """
    client = openai.OpenAI(
        base_url=base_url,
        api_key="lm-studio",  # LM Studio ignores it; SDK requires non-empty
        timeout=_SUBREDDIT_SELECT_TIMEOUT_SECONDS,
        max_retries=0,
    )
    tool_schema = {
        "type": "function",
        "function": {
            "name": _SUBREDDIT_TOOL_SCHEMA["name"],
            "description": _SUBREDDIT_TOOL_SCHEMA["description"],
            "parameters": _SUBREDDIT_TOOL_SCHEMA["input_schema"],
        },
    }
    create_kwargs: dict = {}
    max_tokens = _SUBREDDIT_SELECT_MAX_TOKENS
    if cfg is not None:
        create_kwargs["temperature"] = cfg.LOCAL_MODEL_TEMPERATURE
        create_kwargs["top_p"] = cfg.LOCAL_MODEL_TOP_P
        max_tokens = cfg.LOCAL_MODEL_MAX_TOKENS
        if cfg.LOCAL_MODEL_DISABLE_THINKING:
            # See generator.py::_generate_with_local for why this key was
            # chosen over chat_template_kwargs.enable_thinking.
            create_kwargs["extra_body"] = {"reasoning_effort": "none"}
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": user_message}],
            tools=[tool_schema],
            tool_choice="required",
            max_tokens=max_tokens,
            **create_kwargs,
        )
    except (openai.APIError, openai.APIConnectionError, openai.APITimeoutError,
            httpx.HTTPError) as exc:
        raise _SubredditSelectionError(f"HTTP/API error: {type(exc).__name__}: {exc}") from exc

    if not response.choices:
        dump_fallback_response(
            _SUBREDDIT_SELECT_STAGE, model_name, None, reason="no choices in response"
        )
        raise _SubredditSelectionError("no choices in response")
    message = response.choices[0].message
    tool_calls = getattr(message, "tool_calls", None) or []
    if not tool_calls:
        dump_fallback_response(
            _SUBREDDIT_SELECT_STAGE, model_name, response, reason="no tool call"
        )
        raise _SubredditSelectionError(
            f"model returned no tool call (content preview: "
            f"{(message.content or '')[:200]!r})"
        )
    call = tool_calls[0]
    call_name = getattr(getattr(call, "function", None), "name", None)
    if call_name != _SUBREDDIT_TOOL_SCHEMA["name"]:
        dump_fallback_response(
            _SUBREDDIT_SELECT_STAGE, model_name, response, reason="wrong tool name"
        )
        raise _SubredditSelectionError(
            f"expected tool call {_SUBREDDIT_TOOL_SCHEMA['name']!r}, got {call_name!r}"
        )
    raw_args = getattr(call.function, "arguments", "") or ""
    try:
        args = json.loads(raw_args)
    except json.JSONDecodeError as exc:
        dump_fallback_response(
            _SUBREDDIT_SELECT_STAGE, model_name, response, reason="invalid JSON arguments"
        )
        raise _SubredditSelectionError(
            f"tool arguments were not valid JSON: {exc}. Preview: {raw_args[:200]!r}"
        ) from exc
    picked = _clean_subreddit_names(args.get("subreddits", []), limit)
    if not picked:
        dump_fallback_response(
            _SUBREDDIT_SELECT_STAGE, model_name, response,
            reason="no usable subreddit names in tool arguments",
        )
        raise _SubredditSelectionError("no usable subreddit names in tool arguments")
    return picked


def _select_subreddits_claude(user_message: str, limit: int) -> list[str]:
    """Call Claude Haiku with tool-use. Raises `_SubredditSelectionError` on failure."""
    cfg = Config.load()
    client = anthropic.Anthropic(api_key=cfg.ANTHROPIC_API_KEY)
    try:
        response = client.messages.create(
            model=SUBREDDIT_SELECT_FALLBACK_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": user_message}],
            tools=[_SUBREDDIT_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": "select_subreddits"},
        )
    except anthropic.APIError as exc:
        raise _SubredditSelectionError(f"Claude API error: {exc}") from exc
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "select_subreddits":
            picked = _clean_subreddit_names(block.input.get("subreddits", []), limit)
            if picked:
                return picked
    raise _SubredditSelectionError("Claude returned no usable select_subreddits tool call")


def select_relevant_subreddits(
    candidates: list[str],
    category: str | None = None,
    site_name: str | None = None,
    limit: int = TOP_N_SUBREDDITS,
) -> list[str]:
    """Ask a fast model to pick the `limit` subreddits worth scanning this run.

    Replaces an O(len(candidates)) serial RSS scan with a single cheap model
    call plus an O(limit) scan. The model may return names straight from
    `candidates` or name a different real subreddit it knows fits better
    ("off the top of its head") — `fetch_reddit_trends` fails soft on any
    invalid name, so an unlisted guess is safe to try.

    Routes like `generator.py`: tries the local model (e.g. Qwen 3.6 via LM
    Studio) first when `LOCAL_MODEL_ENABLED=true`, falls back to Claude Haiku
    on any local failure, and falls back to the first `limit` candidates if
    both providers fail — never raises.
    """
    if not candidates:
        return []
    cfg = Config.load()
    user_message = _build_subreddit_select_message(candidates, category, site_name, limit)

    if cfg.LOCAL_MODEL_ENABLED and cfg.LOCAL_MODEL_BASE_URL and cfg.LOCAL_MODEL_NAME:
        try:
            picked = _select_subreddits_local(
                user_message, cfg.LOCAL_MODEL_BASE_URL, cfg.LOCAL_MODEL_NAME, limit,
                cfg=cfg,
            )
            logger.info(
                "provider=local status=success stage=subreddit_select model=%s picks=%s",
                cfg.LOCAL_MODEL_NAME, picked,
            )
            return picked
        except _SubredditSelectionError as exc:
            logger.warning(
                "provider=local status=fallback stage=subreddit_select reason=%s: %s",
                type(exc).__name__, exc,
            )

    try:
        picked = _select_subreddits_claude(user_message, limit)
        logger.info(
            "provider=claude status=success stage=subreddit_select model=%s picks=%s",
            SUBREDDIT_SELECT_FALLBACK_MODEL, picked,
        )
        return picked
    except _SubredditSelectionError as exc:
        logger.warning(
            "provider=claude status=fallback stage=subreddit_select reason=%s: %s "
            "using first %d candidates.",
            type(exc).__name__, exc, limit,
        )
    return candidates[:limit]


GOOGLE_SUGGEST_URL: Final[str] = "http://suggestqueries.google.com/complete/search"


def fetch_reddit_trends(subreddits: list[str], limit: int = 15) -> list[dict]:
    """Return up to `limit` currently-popular posts across the given subreddits.

    Fetches the Atom RSS feed `/r/{sub}/top/.rss?t=week` for each sub. Reddit
    has top-sorted them already, so we round-robin across subs to keep all
    communities represented in the final list rather than letting one sub
    dominate. Dedupes by normalized title.

    Returns [] on any failure — never raises.
    """
    if not subreddits:
        return []
    headers = {"User-Agent": REDDIT_USER_AGENT}
    per_sub: dict[str, list[dict]] = {}
    for i, sub in enumerate(subreddits):
        if i:
            time.sleep(random.uniform(*REDDIT_INTER_REQUEST_DELAY))
        resp = _get_reddit_rss(sub, headers)
        if resp is None:
            continue
        if not resp.ok:
            logger.warning(
                "Reddit RSS returned %d for r/%s: %s",
                resp.status_code, sub, resp.text[:200],
            )
            continue
        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError as exc:
            logger.warning("Reddit RSS parse failed for r/%s: %s", sub, exc)
            continue
        items: list[dict] = []
        for entry in root.findall(f"{_ATOM_NS}entry"):
            title_el = entry.find(f"{_ATOM_NS}title")
            link_el = entry.find(f"{_ATOM_NS}link")
            if title_el is None or not (title_el.text or "").strip():
                continue
            title = title_el.text.strip()
            url = link_el.get("href") if link_el is not None else ""
            items.append({
                "title": title,
                "subreddit": sub,
                "score": None,
                "url": url or "",
            })
        per_sub[sub] = items

    seen: set[str] = set()
    deduped: list[dict] = []
    sub_order = [s for s in subreddits if per_sub.get(s)]
    if not sub_order:
        return []
    max_per = max(len(items) for items in per_sub.values())
    for i in range(max_per):
        for sub in sub_order:
            items = per_sub[sub]
            if i >= len(items):
                continue
            item = items[i]
            key = item["title"].lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
            if len(deduped) >= limit:
                return deduped
    return deduped


def fetch_google_suggest(
    seeds: list[str] | None = None,
    limit_per_seed: int = 8,
) -> list[dict]:
    """Return autocomplete completions for each seed phrase.

    GETs `suggestqueries.google.com/complete/search?client=firefox&q=...` for
    each seed and parses the JSON `[query, [completions], ...]` response.

    Returns [] on any failure — never raises.
    """
    seed_list = list(seeds) if seeds else []
    if not seed_list:
        return []
    out: list[dict] = []
    seen: set[str] = set()
    for seed in seed_list:
        try:
            resp = requests.get(
                GOOGLE_SUGGEST_URL,
                params={"client": "firefox", "q": seed},
                timeout=15,
            )
        except requests.RequestException as exc:
            logger.warning("Google Suggest fetch failed for %r: %s", seed, exc)
            continue
        if not resp.ok:
            logger.warning(
                "Google Suggest returned %d for %r: %s",
                resp.status_code, seed, resp.text[:200],
            )
            continue
        try:
            payload = resp.json()
            completions = payload[1] if isinstance(payload, list) and len(payload) >= 2 else []
        except (ValueError, IndexError, TypeError) as exc:
            logger.warning("Google Suggest parse failed for %r: %s", seed, exc)
            continue
        for completion in completions[:limit_per_seed]:
            if not isinstance(completion, str):
                continue
            text = completion.strip()
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append({"completion": text, "seed": seed})
    return out


def gather_trending_signals(
    subreddits: list[str] | None = None,
    seeds: list[str] | None = None,
    reddit_limit: int = 15,
    suggest_limit_per_seed: int = 5,
    category: str | None = None,
    site_name: str | None = None,
    reddit_enabled: bool = True,
) -> dict:
    """Collect both signal sources for `generator.generate_article`.

    `subreddits` and `seeds` come from `website_memory/{host}.trends.json`.
    When both are empty/None, returns empty lists rather than using any
    hardcoded defaults — no signals from one site bleed into another.

    When `reddit_enabled` is False, the Reddit RSS scan is skipped entirely
    (Google Suggest still runs) — set this from `--skip-reddit` to speed up
    testing. Otherwise, `subreddits` is first narrowed to
    `TOP_N_SUBREDDITS` via `select_relevant_subreddits` so only a handful of
    RSS requests are made instead of scanning the whole candidate list.

    Always returns a dict with both keys, possibly empty. Logs counts.
    """
    if not reddit_enabled:
        logger.info("Reddit trend scraping disabled (--skip-reddit); skipping.")
        reddit: list[dict] = []
    elif subreddits:
        chosen = select_relevant_subreddits(subreddits, category=category, site_name=site_name)
        reddit = fetch_reddit_trends(chosen, limit=reddit_limit)
    else:
        reddit = []
    suggest = fetch_google_suggest(seeds=seeds or [], limit_per_seed=suggest_limit_per_seed)
    logger.info(
        "Trending signals: %d Reddit posts, %d Suggest completions.",
        len(reddit), len(suggest),
    )
    return {"reddit": reddit, "suggest": suggest}
