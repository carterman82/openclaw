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

The signal is consumed by `generator.generate_article(trending_signals=...)`
and rendered into a `<reference_data type="trending_signals">` block in the
user message. TOPIC.md's evergreen/trending ratio remains authoritative;
this module supplies inputs, not directives.
"""

from __future__ import annotations

import logging
import random
import time
import xml.etree.ElementTree as ET
from typing import Final

import requests

logger = logging.getLogger(__name__)

# Reddit aggressively 403s anonymous JSON requests as of 2024+. The Atom RSS
# feed at /r/{sub}/top/.rss?t=week is the only no-auth path that still works
# reliably. RSS strips upvote counts, so per-post `score` becomes None and
# items are surfaced in Reddit's own top-sort order.
REDDIT_USER_AGENT: Final[str] = "openclaw/0.1 topic discovery"
REDDIT_PER_SUB: Final[int] = 10
_ATOM_NS: Final[str] = "{http://www.w3.org/2005/Atom}"

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
            time.sleep(random.uniform(2.0, 3.0))  # be polite to Reddit's anonymous RSS rate limit
        try:
            resp = requests.get(
                f"https://www.reddit.com/r/{sub}/top/.rss",
                params={"t": "week", "limit": REDDIT_PER_SUB},
                headers=headers,
                timeout=15,
            )
        except requests.RequestException as exc:
            logger.warning("Reddit RSS fetch failed for r/%s: %s", sub, exc)
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
) -> dict:
    """Collect both signal sources for `generator.generate_article`.

    `subreddits` and `seeds` come from `website_memory/{host}.trends.json`.
    When both are empty/None, returns empty lists rather than using any
    hardcoded defaults — no signals from one site bleed into another.

    Always returns a dict with both keys, possibly empty. Logs counts.
    """
    reddit = fetch_reddit_trends(subreddits or [], limit=reddit_limit)
    suggest = fetch_google_suggest(seeds=seeds or [], limit_per_seed=suggest_limit_per_seed)
    logger.info(
        "Trending signals: %d Reddit posts, %d Suggest completions.",
        len(reddit), len(suggest),
    )
    return {"reddit": reddit, "suggest": suggest}
