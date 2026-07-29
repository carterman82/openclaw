"""Rescue a rejected-article JSON dump: fix common local-model HTML defects
(unbalanced <p> tags) and publish through the normal openclaw pipeline.

Usage:
    python scripts/publish-from-rejected.py --site catfancast --file logs/rejected-....json

Draft with --draft. Bypasses only the validation gate; still calls the same
image fetch, publish, deploy steps main.py uses.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openclaw.config import Config
from openclaw.images import track_download
from openclaw.main import (
    _activate_site,
    _enforce_external_link_attrs,
    _fetch_and_attach_image,
    _render_sources_section,
)
from openclaw.publisher import get_seo_plugin, publish_post


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# Local model frequently emits: <h2>Section</h2>\n\ntext...\n\n</p>\n\n<h2>...
# i.e. content between <h2> blocks is unwrapped but terminated with a stray </p>.
# Rewrap each section into proper <p>...</p> blocks and drop the stray closer.
_H2_BLOCK_RE = re.compile(r"(</h2>)(.*?)(?=<h2|$)", re.DOTALL)


_BLOCK_LEVEL_START_RE = re.compile(
    r"^<(ul|ol|blockquote|pre|figure|div|table|hr|h[1-6])[\s>/]", re.IGNORECASE
)


def _rewrite_section_body(inner: str) -> str:
    """Aggressive rewrap: strip existing (unbalanced) <p>/</p> tags in this
    section and re-wrap every text block in fresh <p>...</p>. Preserves
    non-<p> block-level elements (ul/ol/blockquote/etc.) untouched."""
    # First: convert paragraph boundaries into blank-line boundaries so the
    # blank-line split below actually sees them. `</p>[whitespace]<p...>` and
    # bare `</p>` in the middle both mark the end of a paragraph.
    normalized = re.sub(r"</p>\s*<p[^>]*>", "\n\n", inner, flags=re.IGNORECASE)
    normalized = re.sub(r"</p>", "\n\n", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"<p[^>]*>", "\n\n", normalized, flags=re.IGNORECASE)
    stripped = normalized.strip("\n").strip()
    if not stripped:
        return ""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", stripped) if b.strip()]
    wrapped: list[str] = []
    for b in blocks:
        if _BLOCK_LEVEL_START_RE.match(b):
            wrapped.append(b)
        else:
            wrapped.append(f"<p>{b}</p>")
    return "\n\n".join(wrapped)


def _rewrap_h2_sections(body: str) -> str:
    def repl(m: re.Match[str]) -> str:
        close_h2 = m.group(1)
        inner = m.group(2)
        rewritten = _rewrite_section_body(inner)
        return close_h2 + "\n\n" + rewritten + "\n\n" if rewritten else close_h2 + "\n\n"

    return _H2_BLOCK_RE.sub(repl, body)


def _balance_p_tags(body: str) -> str:
    body = _rewrap_h2_sections(body)
    # Sanity check.
    opens = len(re.findall(r"<p[ >]", body))
    closes = len(re.findall(r"</p>", body))
    logger.info("After rewrap: <p> opens=%d closes=%d", opens, closes)
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    parser.add_argument("--file", required=True, help="Path to rejected-*.json")
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Fix HTML but don't publish")
    parser.add_argument(
        "--inject-link",
        action="append",
        default=[],
        help="URL|anchor_text|context_sentence  (repeatable). Appends a 'Related reading' block before the sources section.",
    )
    args = parser.parse_args()

    _activate_site(args.site)
    cfg = Config.load()
    site_host = urlparse(cfg.WP_BASE_URL).hostname

    data = json.loads(Path(args.file).read_text(encoding="utf-8"))
    article = data["article"]
    logger.info("Loaded rejected article: %r (reason=%r)", article["title"], data.get("reason"))

    article["body_html"] = _balance_p_tags(article["body_html"])

    if args.inject_link:
        items = []
        for spec in args.inject_link:
            parts = spec.split("|", 2)
            if len(parts) != 3:
                raise SystemExit(
                    f"--inject-link must be URL|anchor|context, got: {spec!r}"
                )
            url, anchor, context = parts[0].strip(), parts[1].strip(), parts[2].strip()
            items.append(
                f'<li>{context} '
                f'<a href="{url}" rel="noopener" target="_blank">{anchor}</a>.</li>'
            )
        block = (
            "\n\n<h2>Related reading on the Info Verse network</h2>\n\n"
            "<p>These companion pieces on the Info Verse network cover adjacent "
            "angles worth reading alongside this one:</p>\n\n"
            "<ul>\n" + "\n".join(items) + "\n</ul>"
        )
        article["body_html"] = article["body_html"].rstrip() + block
        logger.info("Injected %d Related-reading link(s).", len(items))

    # Re-enforce external link attrs after our rewrap (in case any changed).
    article["body_html"], fixes = _enforce_external_link_attrs(article["body_html"], site_host)
    if fixes:
        logger.info("Re-applied external link attrs (%d fixes).", fixes)

    if args.dry_run:
        print("--- FIXED BODY ---")
        print(article["body_html"])
        return 0

    article["body_html"] = _render_sources_section(article, site_host)
    image, featured_media_id, final_body = _fetch_and_attach_image(article)

    seo_plugin = get_seo_plugin()
    status = "draft" if args.draft else "publish"

    post = publish_post(
        title=article["title"],
        body_html=final_body,
        category=article["category"],
        tags=article["tags"],
        status=status,
        excerpt=article.get("excerpt"),
        slug=article.get("slug"),
        focus_keyphrase=article.get("focus_keyphrase"),
        meta_description=article.get("meta_description"),
        seo_title=article.get("seo_title"),
        seo_plugin=seo_plugin,
        featured_media=featured_media_id,
        series=article.get("series") or None,
    )
    if image and featured_media_id and image.get("attribution"):
        track_download(image["attribution"])
    url = post.get("link") or post.get("guid", {}).get("rendered", "unknown")
    logger.info("Published: %s", url)
    print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
