"""WordPress REST API publisher for the openclaw agent."""

from __future__ import annotations

import html
import logging
import re

import requests

from .config import Config

logger = logging.getLogger(__name__)

_category_cache: dict[str, int] | None = None
_tag_cache: dict[str, int] = {}


def _plain_text(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", value)).strip()


def _raise_for_status(resp: requests.Response) -> None:
    if not resp.ok:
        raise RuntimeError(
            f"WP REST API error {resp.status_code} {resp.request.method} "
            f"{resp.request.url}: {resp.text[:500]}"
        )


def _load_categories(base_url: str, auth: tuple[str, str]) -> dict[str, int]:
    global _category_cache
    if _category_cache is not None:
        return _category_cache
    resp = requests.get(
        f"{base_url}/wp-json/wp/v2/categories",
        params={"per_page": 100},
        auth=auth,
        timeout=30,
    )
    _raise_for_status(resp)
    _category_cache = {cat["name"]: cat["id"] for cat in resp.json()}
    logger.debug("Loaded %d categories from WP.", len(_category_cache))
    return _category_cache


def _get_or_create_tag(base_url: str, auth: tuple[str, str], name: str) -> int | None:
    if name in _tag_cache:
        return _tag_cache[name]
    resp = requests.get(
        f"{base_url}/wp-json/wp/v2/tags",
        params={"search": name, "per_page": 100},
        auth=auth,
        timeout=30,
    )
    _raise_for_status(resp)
    for tag in resp.json():
        if tag["name"].lower() == name.lower():
            _tag_cache[name] = tag["id"]
            return tag["id"]
    resp = requests.post(
        f"{base_url}/wp-json/wp/v2/tags",
        json={"name": name},
        auth=auth,
        timeout=30,
    )
    if resp.status_code in (401, 403):
        logger.warning(
            "Cannot create tag %r (HTTP %d — user lacks manage_categories). Skipping.",
            name,
            resp.status_code,
        )
        return None
    _raise_for_status(resp)
    tag_id = resp.json()["id"]
    _tag_cache[name] = tag_id
    logger.debug("Created tag %r (id=%d).", name, tag_id)
    return tag_id


def get_category_names() -> tuple[str, ...]:
    """Return all non-Uncategorized category names from the configured WP site."""
    cfg = Config.load()
    auth = (cfg.WP_USERNAME, cfg.WP_APP_PASSWORD)
    category_map = _load_categories(cfg.WP_BASE_URL, auth)
    return tuple(name for name in category_map if name.lower() != "uncategorized")


def publish_post(
    title: str,
    body_html: str,
    category: str,
    tags: list[str],
    status: str = "publish",
    excerpt: str | None = None,
    slug: str | None = None,
    focus_keyphrase: str | None = None,
    seo_plugin: str | None = None,
) -> dict:
    """POST an article to WordPress and return the created post JSON."""
    cfg = Config.load()
    auth = (cfg.WP_USERNAME, cfg.WP_APP_PASSWORD)
    base_url = cfg.WP_BASE_URL

    category_map = _load_categories(base_url, auth)
    if category not in category_map:
        raise RuntimeError(
            f"Category {category!r} not found in WordPress. "
            f"Found: {list(category_map)}"
        )
    tag_ids = [tid for t in tags if (tid := _get_or_create_tag(base_url, auth, t)) is not None]

    payload: dict = {
        "title": title,
        "content": body_html,
        "status": status,
        "categories": [category_map[category]],
        "tags": tag_ids,
    }
    if excerpt:
        payload["excerpt"] = excerpt
    if slug:
        payload["slug"] = slug
    if focus_keyphrase and seo_plugin in _SEO_META_KEY:
        payload["meta"] = {_SEO_META_KEY[seo_plugin]: focus_keyphrase}

    resp = requests.post(
        f"{base_url}/wp-json/wp/v2/posts",
        json=payload,
        auth=auth,
        timeout=60,
    )
    _raise_for_status(resp)
    return resp.json()


_SEO_META_KEY: dict[str, str] = {
    "yoast": "_yoast_wpseo_focuskw",
    "rankmath": "rank_math_focus_keyword",
}


def get_seo_plugin() -> str | None:
    """Return 'yoast', 'rankmath', or None based on /wp-json/ namespaces."""
    cfg = Config.load()
    resp = requests.get(f"{cfg.WP_BASE_URL}/wp-json/", timeout=15)
    if not resp.ok:
        return None
    namespaces = resp.json().get("namespaces", [])
    if "yoast/v1" in namespaces:
        return "yoast"
    if "rankmath/v1" in namespaces:
        return "rankmath"
    return None


def get_site_name() -> str:
    """Return the WP site name from the REST API root (no auth required)."""
    cfg = Config.load()
    resp = requests.get(f"{cfg.WP_BASE_URL}/wp-json/", timeout=15)
    _raise_for_status(resp)
    return resp.json().get("name", "").strip()


def list_recent_post_titles(limit: int = 50) -> list[str]:
    """Return recent post titles (published + drafts) for topic de-duplication.

    Tries an authenticated request first so drafts are included — a draft
    created seconds ago can still trigger the avoidance check. Falls back to
    the public endpoint (published posts only) if auth fails.
    """
    cfg = Config.load()
    auth = (cfg.WP_USERNAME, cfg.WP_APP_PASSWORD)
    per_page = max(1, min(limit, 100))

    seen: dict[int, str] = {}

    for status in ("any", "publish"):
        params: dict = {"per_page": per_page, "orderby": "date", "order": "desc"}
        use_auth = auth if status == "any" else None
        if status == "any":
            params["status"] = "any"
        resp = requests.get(
            f"{cfg.WP_BASE_URL}/wp-json/wp/v2/posts",
            params=params,
            auth=use_auth,
            timeout=30,
        )
        if not resp.ok:
            if status == "any":
                continue  # auth failed — fall through to public fetch
            resp.raise_for_status()
        for post in resp.json():
            pid = post.get("id")
            rendered = post.get("title", {}).get("rendered", "")
            title = _plain_text(rendered)
            if pid and title and pid not in seen:
                seen[pid] = title
        break  # authenticated fetch succeeded; no need for the public fallback

    return list(seen.values())[:limit]
