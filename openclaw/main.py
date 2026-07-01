"""CLI logic for the openclaw agent."""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from html import escape as html_escape
from html.parser import HTMLParser
from urllib.parse import urlparse

from .config import Config
from .generator import generate_article
from .images import attribution_html, find_unsplash_image, generate_openai_image, track_download
from .publisher import (
    get_category_names,
    get_seo_plugin,
    get_site_name,
    list_recent_post_titles,
    list_recent_posts_for_linking,
    publish_post,
    upload_media,
)
from .trends import gather_trending_signals

logger = logging.getLogger(__name__)


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


_A_TAG_RE = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.IGNORECASE | re.DOTALL)
_HREF_RE = re.compile(r'href="([^"]+)"', re.IGNORECASE)


def _host_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except ValueError:
        return ""


# --- HTML sanitization ----------------------------------------------------
# Defense-in-depth: model output passes through a strict allowlist before
# publish. WP also sanitizes for non-admin users, but the agent could be
# upgraded to an Editor/Admin role with unfiltered_html, so we never trust
# either the model or WP to be the only line of defense.

_ALLOWED_TAGS = frozenset({
    "p", "h2", "h3", "h4", "ul", "ol", "li",
    "strong", "em", "b", "i", "a", "br",
    "blockquote", "code", "pre",
})
_ALLOWED_ATTRS_BY_TAG: dict[str, frozenset[str]] = {
    "a": frozenset({"href", "rel", "target", "title"}),
    "p": frozenset({"class"}),
}
_VOID_TAGS = frozenset({"br"})
_DROP_WITH_CONTENTS = frozenset({
    "script", "style", "iframe", "object", "embed",
    "form", "input", "button", "svg", "math",
    "frame", "frameset", "noscript", "template",
})
_SAFE_URL_SCHEMES = frozenset({"http", "https"})


def _safe_url_scheme(url: str) -> bool:
    """Allow only http(s) with a host. Rejects relative, javascript:, data:, etc."""
    if not url:
        return False
    parsed = urlparse(url.strip())
    return parsed.scheme.lower() in _SAFE_URL_SCHEMES and bool(parsed.hostname)


class _HtmlSanitizer(HTMLParser):
    """Strict allowlist sanitizer for tags, attrs, and href schemes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self._skip_tag: str | None = None
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self._skip_tag is not None:
            if tag == self._skip_tag:
                self._skip_depth += 1
            return
        if tag in _DROP_WITH_CONTENTS:
            self._skip_tag = tag
            self._skip_depth = 1
            return
        if tag not in _ALLOWED_TAGS:
            return
        allowed = _ALLOWED_ATTRS_BY_TAG.get(tag, frozenset())
        safe_attrs: list[tuple[str, str]] = []
        for k, v in attrs:
            k = k.lower()
            if k.startswith("on") or k not in allowed or v is None:
                continue
            if k == "href" and not _safe_url_scheme(v):
                continue
            safe_attrs.append((k, v))
        attr_str = "".join(f' {k}="{html_escape(v, quote=True)}"' for k, v in safe_attrs)
        self.out.append(f"<{tag}{attr_str}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # <br/>, <hr/>, etc.
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._skip_tag is not None:
            if tag == self._skip_tag:
                self._skip_depth -= 1
                if self._skip_depth <= 0:
                    self._skip_tag = None
                    self._skip_depth = 0
            return
        if tag not in _ALLOWED_TAGS or tag in _VOID_TAGS:
            return
        self.out.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._skip_tag is not None:
            return
        self.out.append(html_escape(data, quote=False))

    def handle_comment(self, data: str) -> None:
        return  # comments stripped

    def handle_decl(self, decl: str) -> None:
        return

    def handle_pi(self, data: str) -> None:
        return


def _sanitize_html(body_html: str) -> str:
    parser = _HtmlSanitizer()
    parser.feed(body_html)
    parser.close()
    return "".join(parser.out)


def _validate_anchors(
    body_html: str, candidate_urls: set[str], wp_host: str,
) -> tuple[str, int]:
    """Walk every <a> in the final HTML, drop unauthorized/unsafe ones.

    Replaces `_strip_invented_internal_links` — that one only stripped
    URLs the model self-reported. This walks actual HTML, so the model
    cannot smuggle internal URLs by omitting them from `internal_links_used`.

    A tag is dropped (replaced by its bare text) when:
      - href is missing
      - href scheme is anything other than http/https
      - href points to the WP host but is not in the candidate set
    """
    stripped = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal stripped
        attrs, text = match.group(1), match.group(2)
        href_m = _HREF_RE.search(attrs)
        if not href_m:
            stripped += 1
            return text
        href = href_m.group(1)
        if not _safe_url_scheme(href):
            stripped += 1
            return text
        href_host = _host_of(href)
        if href_host == wp_host and href not in candidate_urls:
            stripped += 1
            return text
        return match.group(0)

    return _A_TAG_RE.sub(repl, body_html), stripped


def _enforce_external_link_attrs(body_html: str, wp_host: str) -> tuple[str, int]:
    """Ensure every external <a> has rel='noopener' and target='_blank'. Return (html, fixes)."""
    fixes = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal fixes
        attrs, text = match.group(1), match.group(2)
        href_m = _HREF_RE.search(attrs)
        if not href_m:
            return match.group(0)
        href_host = _host_of(href_m.group(1))
        if not href_host or href_host == wp_host:
            return match.group(0)
        new_attrs = attrs
        changed = False
        rel_m = re.search(r'rel="([^"]*)"', new_attrs, re.IGNORECASE)
        if not rel_m:
            new_attrs = new_attrs.rstrip() + ' rel="noopener"'
            changed = True
        elif "noopener" not in rel_m.group(1).lower():
            new_attrs = re.sub(
                r'rel="([^"]*)"',
                lambda mm: f'rel="{mm.group(1).strip()} noopener"',
                new_attrs, count=1, flags=re.IGNORECASE,
            )
            changed = True
        if not re.search(r'\btarget\s*=', new_attrs, re.IGNORECASE):
            new_attrs = new_attrs.rstrip() + ' target="_blank"'
            changed = True
        if changed:
            fixes += 1
        return f"<a {new_attrs}>{text}</a>"

    return _A_TAG_RE.sub(repl, body_html), fixes


_MIME_TO_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}


def _fetch_and_attach_image(article: dict) -> tuple[dict | None, int | None, str]:
    """Generate via OpenAI, fall back to Unsplash, then publish without image.

    Returns (image, attachment_id, body_html_with_credit). The credit suffix
    is appended only for Unsplash (its attribution dict is truthy); OpenAI
    images return attribution=None and the body is unchanged. On full failure
    returns (None, None, original_body_html) so publishing never blocks.
    """
    body = article["body_html"]
    image = None

    prompt = article.get("image_prompt")
    # Prefer the generator's keyphrase-inclusive alt text; fall back gracefully.
    alt_hint = article.get("image_alt_text") or article.get("focus_keyphrase") or article["title"]
    if prompt:
        logger.info("Generating OpenAI image (prompt=%r).", prompt[:120])
        image = generate_openai_image(prompt, alt_hint)
        if not image:
            logger.warning("OpenAI image generation failed; falling back to Unsplash.")
    else:
        logger.warning("Article has no image_prompt; falling back to Unsplash.")

    if not image:
        unsplash_q = article.get("unsplash_query") or article.get("focus_keyphrase")
        if unsplash_q:
            logger.info("Searching Unsplash (query=%r).", unsplash_q)
            image = find_unsplash_image(unsplash_q)

    if not image:
        logger.warning("No image from OpenAI or Unsplash; publishing without featured image.")
        return None, None, body

    attribution = image.get("attribution")
    caption = attribution_html(attribution) if attribution else None
    ext = _MIME_TO_EXT.get(image["mime_type"], "jpg")
    slug = article.get("slug") or "featured"
    filename = f"{slug}-featured.{ext}"
    alt = article.get("image_alt_text") or image["alt_text"] or article["title"]
    try:
        attachment_id = upload_media(
            image["image_bytes"], filename, image["mime_type"], alt, caption=caption,
        )
    except Exception:
        logger.warning("upload_media failed; publishing without featured image.", exc_info=True)
        return None, None, body

    source = "OpenAI" if attribution is None else f"Unsplash ({attribution['photographer_name']})"
    logger.info("Uploaded featured image (id=%d, source=%s, alt=%r).", attachment_id, source, alt)

    final_body = body + "\n" + caption if caption else body
    return image, attachment_id, final_body


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
        metavar="CATEGORY",
        help="Force a specific category (Claude picks if omitted). Valid values are fetched from the configured WP site at runtime.",
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
            site_name = get_site_name()
            logger.info("Site name: %r", site_name)
            seo_plugin = get_seo_plugin()
            logger.info("SEO plugin: %r", seo_plugin)
            wp_categories = get_category_names()
            logger.info("WP categories: %s", list(wp_categories))
            if args.category and args.category not in wp_categories:
                logger.error(
                    "--category %r not found on site. Available: %s",
                    args.category,
                    list(wp_categories),
                )
                return 1
            recent_titles = [] if args.topic else list_recent_post_titles()
            if recent_titles:
                logger.info(
                    "Loaded %d recent post titles for topic de-duplication.",
                    len(recent_titles),
                )
            link_candidates = list_recent_posts_for_linking()
            if link_candidates:
                logger.info("Loaded %d internal-link candidates.", len(link_candidates))
            trending_signals = None if args.topic else gather_trending_signals()
            logger.info(
                "Calling Claude (topic=%r, category=%r).",
                args.topic,
                args.category,
            )
            article = generate_article(
                topic=args.topic,
                category=args.category,
                recent_titles=recent_titles,
                categories=wp_categories,
                site_name=site_name or None,
                internal_link_candidates=link_candidates,
                trending_signals=trending_signals,
            )
            word_count = len(_strip_html(article["body_html"]).split())
            logger.info(
                "Claude returned (title=%r, category=%r, words=~%d, slug=%r, keyphrase=%r).",
                article["title"],
                article["category"],
                word_count,
                article.get("slug"),
                article.get("focus_keyphrase"),
            )
            logger.info(
                "Angle justification: %s",
                article.get("unique_angle_justification") or "<missing>",
            )

            keyphrase = article.get("focus_keyphrase") or ""
            if keyphrase:
                first_p_m = re.search(r"<p[^>]*>(.*?)</p>", article["body_html"], re.IGNORECASE | re.DOTALL)
                if first_p_m:
                    first_p_text = re.sub(r"<[^>]+>", " ", first_p_m.group(1))
                    first_sentence = re.split(r"[.!?]", first_p_text)[0]
                    if keyphrase.lower() not in first_sentence.lower():
                        logger.warning(
                            "Y2: focus_keyphrase %r not found in first sentence of first <p>. "
                            "Publishing anyway.",
                            keyphrase,
                        )

            image_alt = article.get("image_alt_text") or ""
            if keyphrase and image_alt and keyphrase.lower() not in image_alt.lower():
                logger.warning(
                    "Y6: focus_keyphrase %r not found in image_alt_text %r. "
                    "Publishing anyway.",
                    keyphrase,
                    image_alt,
                )

            internal_used = article.get("internal_links_used") or []
            external_used = article.get("external_links_used") or []
            logger.info("Internal links used (self-reported): %s", internal_used)
            logger.info("External links used (self-reported): %s", external_used)
            if not external_used:
                logger.warning(
                    "Article reported zero external links; minimum is 1. Publishing anyway."
                )

            article["body_html"] = _sanitize_html(article["body_html"])

            wp_host = _host_of(Config.load().WP_BASE_URL)
            candidate_urls = {c["link"] for c in link_candidates}
            article["body_html"], stripped = _validate_anchors(
                article["body_html"], candidate_urls, wp_host,
            )
            if stripped:
                logger.warning(
                    "Stripped %d unauthorized/unsafe <a> tag(s) from body.", stripped,
                )

            article["body_html"], rel_fixes = _enforce_external_link_attrs(
                article["body_html"], wp_host,
            )
            if rel_fixes:
                logger.warning(
                    "Injected rel/target safety attrs on %d external <a> tag(s).",
                    rel_fixes,
                )

            image, featured_media_id, final_body = _fetch_and_attach_image(article)

            status = "draft" if args.draft else "publish"
            logger.info(
                "POST to WP (status=%s, excerpt=%s, slug=%s, seo_plugin=%r, featured_media=%r).",
                status,
                bool(article.get("excerpt")),
                bool(article.get("slug")),
                seo_plugin,
                featured_media_id,
            )
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
            )
            if image and featured_media_id and image.get("attribution"):
                track_download(image["attribution"])
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
