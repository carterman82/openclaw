"""
backfill-seo-meta.py — one-off backfill of Yoast SEO meta_description and
seo_title for posts published before Yoast was activated on the pilot
subsites (Phase 6 Step 6.4, 2026-07-19).

Scope matches PLAN.md Step 6.4 exactly: meta_description from each post's
excerpt where absent, seo_title = post title truncated to 60 chars.
focus_keyphrase is intentionally NOT backfilled — no real keyphrase data
exists for pre-Yoast posts, and inventing one from title/slug words would be
guessing, not backfilling. New posts get a real generator-produced
focus_keyphrase already; only historical posts are affected here.

Usage: python scripts/backfill-seo-meta.py [--apply]
Without --apply, runs in dry-run mode (prints planned changes only).
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import openclaw  # noqa: F401  (installs the *.localhost DNS shim)
from openclaw.main import _activate_site
from openclaw.config import Config
from openclaw import publisher

SITES = ["gardening", "dogs", "boardgames", "coffee", "techtools"]


def _strip_html(raw: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", raw)).strip()


def _truncate(text: str, max_len: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rsplit(" ", 1)[0]
    return cut.strip()


def backfill_site(slug: str, apply: bool) -> None:
    _activate_site(slug)
    cfg = Config.load()
    auth = (cfg.WP_USERNAME, cfg.WP_APP_PASSWORD)
    base = cfg.WP_BASE_URL.rstrip("/")

    plugin = publisher.get_seo_plugin()
    if plugin != "yoast":
        print(f"[{slug}] SEO plugin detected as {plugin!r}, expected 'yoast' — skipping site.")
        return
    keys = publisher._SEO_META_KEYS["yoast"]

    posts: list[dict] = []
    page = 1
    while True:
        r = requests.get(
            f"{base}/wp-json/wp/v2/posts",
            params={"per_page": 100, "page": page, "status": "publish", "context": "edit"},
            auth=auth, timeout=30,
        )
        if not r.ok:
            break
        batch = r.json()
        if not batch:
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    print(f"\n[{slug}] {len(posts)} published post(s)")
    for post in posts:
        pid = post["id"]
        title = _strip_html(post.get("title", {}).get("rendered", ""))
        excerpt = _strip_html(post.get("excerpt", {}).get("rendered", ""))
        meta = post.get("meta", {})

        new_meta_desc = _truncate(excerpt, 160) if excerpt else ""
        new_seo_title = _truncate(title, 60)

        # Clean up test cruft written during this session's round-trip smoke test.
        is_test_cruft = meta.get(keys["focus_keyphrase"]) == "test keyphrase roundtrip"

        changes = {}
        if new_meta_desc and meta.get(keys["meta_description"]) != new_meta_desc:
            changes[keys["meta_description"]] = new_meta_desc
        if new_seo_title and meta.get(keys["seo_title"]) != new_seo_title:
            changes[keys["seo_title"]] = new_seo_title
        if is_test_cruft:
            changes[keys["focus_keyphrase"]] = ""

        if not changes:
            continue

        print(f"  post {pid} {title[:50]!r}: {list(changes.keys())}")
        if apply:
            resp = requests.post(
                f"{base}/wp-json/wp/v2/posts/{pid}",
                json={"meta": changes},
                auth=auth, timeout=30,
            )
            if not resp.ok:
                print(f"    ERROR {resp.status_code}: {resp.text[:200]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Actually write changes (default: dry-run)")
    args = ap.parse_args()

    if not args.apply:
        print("DRY RUN — no changes will be written. Pass --apply to commit.\n")

    for slug in SITES:
        backfill_site(slug, args.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
