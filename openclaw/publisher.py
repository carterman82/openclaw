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

    resp = requests.post(
        f"{base_url}/wp-json/wp/v2/posts",
        json={
            "title": title,
            "content": body_html,
            "status": status,
            "categories": [category_map[category]],
            "tags": tag_ids,
        },
        auth=auth,
        timeout=60,
    )
    _raise_for_status(resp)
    return resp.json()


def list_recent_post_titles(limit: int = 20) -> list[str]:
    """Return recent public post titles for topic de-duplication."""
    cfg = Config.load()
    resp = requests.get(
        f"{cfg.WP_BASE_URL}/wp-json/wp/v2/posts",
        params={
            "per_page": max(1, min(limit, 100)),
            "orderby": "date",
            "order": "desc",
        },
        timeout=30,
    )
    _raise_for_status(resp)
    titles = []
    for post in resp.json():
        rendered = post.get("title", {}).get("rendered", "")
        title = _plain_text(rendered)
        if title:
            titles.append(title)
    return titles
