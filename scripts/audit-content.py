"""audit-content.py — Phase 6 Step 6.6 persistent content-quality audit scanner.

Repeatable, deterministic re-run of the 2026-07-19 five-subsite content audit
(see PLAN.md Phase 6 intro table + `project-content-audit-2026-07-19` memory).
Reuses the exact same defect checks as `openclaw.validation` (Step 6.1's
publish-time gate) so "what would be rejected today" and "what's already
live" never drift apart, then adds catalog-wide checks that only make sense
against the full post list: duplicate titles, <2 H2 sections, missing SEO
meta, and the staccato closer-tic voice pattern (flagged for Step 6.5, not
fixed here).

Usage:
    python scripts/audit-content.py                  # all five pilot subsites
    python scripts/audit-content.py --site gardening --site dogs

Each row also reports word count, featured-image presence, and category —
plain inventory, not a defect signal on their own.

Prints a per-site post table plus a flag-count summary. Exit 0 if zero
REASONING-LEAK / MD-LEAK / TRUNCATED / DUP-TITLE / OOB-LENGTH flags fired
across every checked site (the Step 6.1-equivalent hard-defect set); exit 1
otherwise. NO-SEO-META, CLOSER-TIC, SUSPICIOUS-CITATION, and DUP-KEYPHRASE
are informational only and never affect the exit code — CLOSER-TIC and
SUSPICIOUS-CITATION are heuristic pattern matches (see openclaw.main's
_find_closer_tic / _find_suspicious_citation) with a real false-positive
rate, appropriate to gate a fresh generation into a regenerate-once retry
but not to fail an audit of already-published content outright, and
DUP-KEYPHRASE is an SEO-cannibalization signal (two posts targeting the
same focus keyphrase), not a content defect.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openclaw.deploy import DEPLOYABLE_SLUGS  # noqa: E402
from openclaw.main import _activate_site  # noqa: E402
from openclaw.config import Config  # noqa: E402
from openclaw.publisher import _load_categories  # noqa: E402
from openclaw.validation import (  # noqa: E402
    _find_leak_marker,
    _find_length_problem,
    _find_malformed_html,
    _find_markdown_leak,
    normalize_title,
)

_DIFFLIB_RATIO = 0.80

_CLOSER_TIC_RE = re.compile(
    r"(?:\bthe choice is yours\b"
    r"|\bit is not [^.!?]{2,40}\. it is [^.!?]{2,40}\.)",
    re.IGNORECASE,
)

# Mirrors openclaw.main._SUSPICIOUS_CITATION_RE (Step 6.5) so pre-publish
# generation-time flagging and this catalog-wide audit never drift apart.
_SUSPICIOUS_CITATION_RE = re.compile(
    r"\bDr\.\s?[A-Z][a-z]+"
    r"|\bresearchers?\s+[A-Z][a-z]+\s+[A-Z][a-z]+"
    r"|\b(?:a|the)\s+\d{4}\s+study\b"
    r"|\bstudy\s+(?:by|from|published|conducted)\b"
    r"|\b(?:a|the)\s+study\s+at\s+(?:the\s+)?[A-Z][A-Za-z.&' ]{2,50}\b"
    r"|\baccording to\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b"
    r"|\([A-Z][A-Za-z.&' ]{2,60}(?:University|Extension|Institute|College|Association|Society|Foundation|Journal)[A-Za-z.&' ]{0,20},\s*(?:19|20)\d{2}\)",
    re.IGNORECASE,
)


def _strip_html(raw: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", raw)).strip()


def _fetch_all_posts(cfg: Config) -> list[dict]:
    auth = (cfg.WP_USERNAME, cfg.WP_APP_PASSWORD)
    base = cfg.WP_BASE_URL.rstrip("/")
    posts: list[dict] = []
    page = 1
    while True:
        resp = requests.get(
            f"{base}/wp-json/wp/v2/posts",
            params={
                "per_page": 100, "page": page, "status": "any",
                "orderby": "date", "order": "desc", "context": "edit",
            },
            auth=auth, timeout=30,
        )
        if not resp.ok:
            if resp.status_code == 400 and page > 1:
                break  # WP returns 400 "invalid page number" past the last page
            raise RuntimeError(f"GET posts page {page} returned {resp.status_code}: {resp.text[:200]}")
        batch = resp.json()
        if not batch:
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return posts


def _audit_site(slug: str) -> tuple[int, dict[str, int]]:
    """Returns (post_count, flag_counts) and prints the per-post table."""
    _activate_site(slug)
    cfg = Config.load()
    auth = (cfg.WP_USERNAME, cfg.WP_APP_PASSWORD)
    posts = _fetch_all_posts(cfg)
    category_map = _load_categories(cfg.WP_BASE_URL, auth)
    id_to_category = {cat_id: name for name, cat_id in category_map.items()}

    print(f"\n{'=' * 78}")
    print(f"Site: {slug}  ({cfg.WP_BASE_URL})  —  {len(posts)} post(s)")
    print("=" * 78)

    flag_counts: dict[str, int] = {}
    normalized_titles: list[tuple[str, int, str]] = []  # (normalized, id, raw title)
    keyphrases: list[tuple[str, int]] = []  # (normalized keyphrase, id) — non-empty only

    rows: list[tuple[int, str, int, bool, str, list[str]]] = []
    for post in posts:
        post_id = post["id"]
        title = html.unescape(post.get("title", {}).get("rendered", ""))
        body = post.get("content", {}).get("rendered", "") or ""
        excerpt = html.unescape(post.get("excerpt", {}).get("rendered", "")) or ""
        meta = post.get("meta", {}) or {}
        body_text = _strip_html(body)
        word_count = len(body_text.split())
        has_image = bool(post.get("featured_media"))
        cat_names = ", ".join(
            id_to_category.get(cid, f"#{cid}") for cid in post.get("categories", []) or []
        ) or "-"

        flags: list[str] = []

        leak_hit = _find_leak_marker(title) or _find_leak_marker(body) or _find_leak_marker(excerpt)
        if leak_hit:
            flags.append("REASONING-LEAK")

        if _find_markdown_leak(body):
            flags.append("MD-LEAK")

        if _find_malformed_html(body):
            flags.append("TRUNCATED")

        h2_count = len(re.findall(r"<h2[\s>]", body, re.IGNORECASE))
        if h2_count < 2:
            flags.append("FEW-H2")

        if _find_length_problem(word_count, None):
            flags.append("OOB-LENGTH")

        if _CLOSER_TIC_RE.search(body_text):
            flags.append("CLOSER-TIC")

        if _SUSPICIOUS_CITATION_RE.search(body_text):
            flags.append("SUSPICIOUS-CITATION")

        seo_desc = meta.get("_yoast_wpseo_metadesc") or meta.get("rank_math_description")
        seo_kw = meta.get("_yoast_wpseo_focuskw") or meta.get("rank_math_focus_keyword")
        if not seo_desc or not seo_kw:
            flags.append("NO-SEO-META")
        if seo_kw:
            keyphrases.append((seo_kw.strip().lower(), post_id))

        normalized = normalize_title(title)
        normalized_titles.append((normalized, post_id, title))

        for f in flags:
            flag_counts[f] = flag_counts.get(f, 0) + 1
        rows.append((post_id, title, word_count, has_image, cat_names, flags))

    # Duplicate-title pass: exact or near-exact (ratio >= 0.80) normalized-title
    # collisions between distinct posts on the same site.
    dup_ids: set[int] = set()
    for i in range(len(normalized_titles)):
        norm_i, id_i, _ = normalized_titles[i]
        if not norm_i:
            continue
        for j in range(i + 1, len(normalized_titles)):
            norm_j, id_j, _ = normalized_titles[j]
            if not norm_j:
                continue
            if norm_i == norm_j:
                dup_ids.add(id_i)
                dup_ids.add(id_j)
                continue
            ratio = __import__("difflib").SequenceMatcher(None, norm_i, norm_j).ratio()
            if ratio >= _DIFFLIB_RATIO:
                dup_ids.add(id_i)
                dup_ids.add(id_j)

    # Duplicate-keyphrase pass: exact (case-insensitive) focus-keyphrase reuse
    # across distinct posts — SEO cannibalization, not a hard content defect.
    keyphrase_counts: dict[str, int] = {}
    for kw, _post_id in keyphrases:
        keyphrase_counts[kw] = keyphrase_counts.get(kw, 0) + 1
    dup_keyphrase_ids: set[int] = {
        post_id for kw, post_id in keyphrases if keyphrase_counts[kw] > 1
    }

    for post_id, title, word_count, has_image, cat_names, flags in rows:
        if post_id in dup_ids:
            flags.append("DUP-TITLE")
            flag_counts["DUP-TITLE"] = flag_counts.get("DUP-TITLE", 0) + 1
        if post_id in dup_keyphrase_ids:
            flags.append("DUP-KEYPHRASE")
            flag_counts["DUP-KEYPHRASE"] = flag_counts.get("DUP-KEYPHRASE", 0) + 1

    print(f"  {'ID':<7} {'Title':<50} {'Words':>6} {'Img':>4} {'Category':<14} Flags")
    for post_id, title, word_count, has_image, cat_names, flags in rows:
        flag_str = ", ".join(flags) if flags else "-"
        img_str = "Y" if has_image else "N"
        print(
            f"  #{post_id:<6} {title[:50]:<50} {word_count:>6} {img_str:>4} "
            f"{cat_names[:14]:<14} {flag_str}"
        )

    return len(posts), flag_counts


_HARD_FLAGS = {"REASONING-LEAK", "MD-LEAK", "TRUNCATED", "DUP-TITLE", "OOB-LENGTH"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 6 Step 6.6 content audit scanner.")
    parser.add_argument(
        "--site", action="append", dest="sites", metavar="SLUG",
        help="Limit to this site slug (repeatable). Default: all deployable pilot subsites.",
    )
    args = parser.parse_args()
    sites = args.sites or sorted(DEPLOYABLE_SLUGS)

    grand_totals: dict[str, int] = {}
    total_posts = 0
    for slug in sites:
        count, flags = _audit_site(slug)
        total_posts += count
        for k, v in flags.items():
            grand_totals[k] = grand_totals.get(k, 0) + v

    print(f"\n{'=' * 78}")
    print(f"Summary across {len(sites)} site(s), {total_posts} post(s):")
    if not grand_totals:
        print("  No flags of any kind.")
    else:
        for flag in sorted(grand_totals):
            marker = "hard" if flag in _HARD_FLAGS else "info"
            print(f"  {flag:<14} {grand_totals[flag]:>3}  ({marker})")

    hard_hits = sum(v for k, v in grand_totals.items() if k in _HARD_FLAGS)
    if hard_hits:
        print(f"\nFAIL: {hard_hits} hard-defect flag(s) across {len(sites)} site(s).")
        return 1
    print("\nPASS: zero hard-defect flags.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
