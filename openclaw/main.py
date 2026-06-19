"""CLI logic for the openclaw agent."""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys

from .config import Config
from .constants import ALLOWED_CATEGORIES
from .generator import generate_article
from .publisher import list_recent_post_titles, publish_post

logger = logging.getLogger(__name__)


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m openclaw",
        description="Generate and publish an evergreen article to WordPress.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    post = sub.add_parser("post", help="Generate and publish one article.")
    post.add_argument("--topic", help="Article topic (Claude picks if omitted).")
    post.add_argument(
        "--category",
        choices=ALLOWED_CATEGORIES,
        metavar="{" + ",".join(ALLOWED_CATEGORIES) + "}",
        help="Force a specific category (Claude picks if omitted).",
    )
    post.add_argument(
        "--draft",
        action="store_true",
        help="Publish as draft instead of a live post.",
    )
    post.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    log_level_name = os.getenv("LOG_LEVEL", "DEBUG" if args.verbose else "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level_name.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if args.command == "post":
        try:
            Config.load()
            logger.info("Config loaded.")
            recent_titles = [] if args.topic else list_recent_post_titles()
            if recent_titles:
                logger.info(
                    "Loaded %d recent post titles for topic de-duplication.",
                    len(recent_titles),
                )
            logger.info(
                "Calling Claude (topic=%r, category=%r).",
                args.topic,
                args.category,
            )
            article = generate_article(
                topic=args.topic,
                category=args.category,
                recent_titles=recent_titles,
            )
            word_count = len(_strip_html(article["body_html"]).split())
            logger.info(
                "Claude returned (title=%r, category=%r, words=~%d).",
                article["title"],
                article["category"],
                word_count,
            )
            status = "draft" if args.draft else "publish"
            logger.info("POST to WP (status=%s).", status)
            post = publish_post(
                title=article["title"],
                body_html=article["body_html"],
                category=article["category"],
                tags=article["tags"],
                status=status,
            )
            url = post.get("link") or post.get("guid", {}).get("rendered", "unknown")
            logger.info("Published: %s", url)
            print(url)
            return 0
        except Exception as exc:
            logger.exception("Run failed: %s", exc)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
