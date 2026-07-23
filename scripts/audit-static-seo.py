"""
audit-static-seo.py — Phase 7 Step 7.4 deployed-static-tree SEO/OG/sitemap audit.

Unlike `scripts/audit-content.py` (which reads the WP REST payload on the
dynamic site), this script fetches the actual deployed HTML from each
subsite's live GitHub Pages destination URL — the belt-and-braces gate that
nothing about SEO, sitemaps, or metadata quietly broke in the Staatic export
or the DNS/CNAME hop, ahead of AdSense review (Step 7.5).

Usage:
    python scripts/audit-static-seo.py                  # all 5 deployable pilots
    python scripts/audit-static-seo.py --site gardening --site dogs

For each subsite, checks:
  - Home page: <title>, meta description, canonical host, og:image (200),
    og:type=website, JSON-LD @type present, GA4 snippet.
  - One sampled post page (picked from post-sitemap.xml): same checks plus
    og:type=article.
  - robots.txt: allows "/" for Googlebot, has a Sitemap: directive pointing
    at the destination host.
  - sitemap_index.xml + every child sitemap: 200, parses as XML, every <loc>
    under the destination host (no localhost leakage).

Prints a per-site PASS/FAIL table. Exits 1 if any FAIL fires across any
site, 0 otherwise. GA4 checks will legitimately FAIL until Phase 7 Step 7.3's
measurement IDs are populated in each child theme — that is not a bug in
this script.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openclaw.deploy import DEPLOYABLE_SLUGS, _SLUG_TO_DOMAIN  # noqa: E402

_TIMEOUT = 20
_XML_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

_META_TAG_RE = re.compile(r"<meta\b([^>]*)>", re.IGNORECASE)
_ATTR_RE = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*"([^"]*)"|([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*\'([^\']*)\'')
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_CANONICAL_RE = re.compile(r'<link\b[^>]*rel\s*=\s*["\']canonical["\'][^>]*>', re.IGNORECASE)
_LDJSON_RE = re.compile(
    r'<script[^>]*type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
_GA4_RE = re.compile(r"gtag\(\s*['\"]config['\"]\s*,\s*['\"]G-", re.IGNORECASE)


class Result:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []  # (label, status, detail)

    def add(self, label: str, ok: bool, detail: str = "", warn: bool = False) -> None:
        status = "PASS" if ok else ("WARN" if warn else "FAIL")
        self.rows.append((label, status, detail))

    @property
    def fail_count(self) -> int:
        return sum(1 for _, s, _ in self.rows if s == "FAIL")


def _parse_attrs(attr_str: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for m in _ATTR_RE.finditer(attr_str):
        if m.group(1) is not None:
            attrs[m.group(1).lower()] = m.group(2)
        else:
            attrs[m.group(3).lower()] = m.group(4)
    return attrs


def _meta_tags(body: str) -> list[dict[str, str]]:
    return [_parse_attrs(m.group(1)) for m in _META_TAG_RE.finditer(body)]


def _get_meta(tags: list[dict[str, str]], key: str, attr: str = "name") -> str | None:
    for t in tags:
        if t.get(attr, "").lower() == key.lower():
            return t.get("content")
    return None


def _fetch(url: str) -> requests.Response | None:
    try:
        return requests.get(url, timeout=_TIMEOUT)
    except requests.RequestException:
        return None


def _check_page(result: Result, url: str, expected_og_type: str, dest_host: str) -> None:
    resp = _fetch(url)
    if resp is None or resp.status_code != 200:
        code = resp.status_code if resp is not None else "no response"
        result.add(f"{url} fetch", False, f"status={code}")
        return
    body = resp.text
    tags = _meta_tags(body)

    title_m = _TITLE_RE.search(body)
    title = html.unescape(title_m.group(1)).strip() if title_m else ""
    result.add(f"{url} <title>", bool(title), title[:70])

    desc = _get_meta(tags, "description")
    result.add(
        f"{url} meta description",
        bool(desc) and len(desc) >= 120,
        f"len={len(desc) if desc else 0}",
    )

    canon_m = _CANONICAL_RE.search(body)
    canon_href = _parse_attrs(canon_m.group(0)).get("href", "") if canon_m else ""
    canon_host = urlparse(canon_href).hostname or ""
    result.add(f"{url} canonical host", canon_host == dest_host, canon_href or "<absent>")

    og_image = _get_meta(tags, "og:image", attr="property")
    if not og_image:
        result.add(f"{url} og:image", False, "<absent>")
    else:
        img_resp = _fetch(og_image)
        ok = img_resp is not None and img_resp.status_code == 200
        result.add(f"{url} og:image", ok, og_image)

    og_type = _get_meta(tags, "og:type", attr="property")
    result.add(f"{url} og:type", og_type == expected_og_type, f"got={og_type!r} want={expected_og_type!r}")

    ld_hits = _LDJSON_RE.findall(body)
    has_type = False
    for block in ld_hits:
        if re.search(r'"@type"\s*:', block):
            has_type = True
            break
    result.add(f"{url} JSON-LD @type", has_type, f"{len(ld_hits)} ld+json block(s)")

    result.add(f"{url} GA4 snippet", bool(_GA4_RE.search(body)), "gtag('config','G-...') present" if _GA4_RE.search(body) else "<absent — blocked on Step 7.3>")


def _check_robots(result: Result, base: str, dest_host: str) -> None:
    resp = _fetch(f"{base}/robots.txt")
    if resp is None or resp.status_code != 200:
        result.add("robots.txt fetch", False, f"status={resp.status_code if resp else 'no response'}")
        return
    text = resp.text
    ua_block = re.search(r"User-agent:\s*\*\s*\n(.*?)(?:\n\s*\n|\Z)", text, re.IGNORECASE | re.DOTALL)
    disallow_all = bool(ua_block and re.search(r"^\s*Disallow:\s*/\s*$", ua_block.group(1), re.IGNORECASE | re.MULTILINE))
    result.add("robots.txt allows / for *", not disallow_all, "no blanket Disallow found" if not disallow_all else "Disallow: / found")

    sitemap_m = re.search(r"^Sitemap:\s*(\S+)", text, re.IGNORECASE | re.MULTILINE)
    sitemap_url = sitemap_m.group(1).strip() if sitemap_m else ""
    result.add(
        "robots.txt Sitemap: directive",
        bool(sitemap_url) and urlparse(sitemap_url).hostname == dest_host,
        sitemap_url or "<absent>",
    )


def _check_sitemaps(result: Result, base: str, dest_host: str) -> str | None:
    """Returns one sampled post URL from post-sitemap.xml, or None."""
    resp = _fetch(f"{base}/sitemap_index.xml")
    if resp is None or resp.status_code != 200:
        result.add("sitemap_index.xml fetch", False, f"status={resp.status_code if resp else 'no response'}")
        return None
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        result.add("sitemap_index.xml parse", False, str(exc))
        return None
    result.add("sitemap_index.xml parse", True, "")

    child_locs = [el.text.strip() for el in root.findall(".//sm:sitemap/sm:loc", _XML_NS) if el.text]
    if not child_locs:
        result.add("sitemap_index.xml children", False, "no <sitemap><loc> entries found")
        return None

    all_ok = True
    sample_post_url: str | None = None
    for loc in child_locs:
        if urlparse(loc).hostname != dest_host:
            all_ok = False
            continue
        child_resp = _fetch(loc)
        if child_resp is None or child_resp.status_code != 200:
            all_ok = False
            continue
        try:
            child_root = ET.fromstring(child_resp.content)
        except ET.ParseError:
            all_ok = False
            continue
        urls = [el.text.strip() for el in child_root.findall(".//sm:url/sm:loc", _XML_NS) if el.text]
        for u in urls:
            if urlparse(u).hostname != dest_host:
                all_ok = False
        if "post-sitemap" in loc and urls and sample_post_url is None:
            non_home = [u for u in urls if urlparse(u).path not in ("", "/")]
            sample_post_url = non_home[0] if non_home else None

    result.add(f"sitemap children ({len(child_locs)} file(s)) — all <loc> under {dest_host}", all_ok, "")
    return sample_post_url


def _audit_site(slug: str) -> Result:
    domain = _SLUG_TO_DOMAIN.get(slug)
    result = Result()
    if not domain:
        result.add(f"{slug}: destination domain", False, "not found in deploy._SLUG_TO_DOMAIN")
        return result
    base = f"https://{domain}"

    _check_page(result, f"{base}/", "website", domain)
    sample_post_url = _check_sitemaps(result, base, domain)
    _check_robots(result, base, domain)

    if sample_post_url:
        _check_page(result, sample_post_url, "article", domain)
    else:
        result.add("sampled post page checks", False, "no post URL found in post-sitemap.xml to sample")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 Step 7.4 deployed-static-tree SEO audit.")
    parser.add_argument(
        "--site", action="append", dest="sites", metavar="SLUG",
        help="Limit to this site slug (repeatable). Default: all deployable pilot subsites.",
    )
    args = parser.parse_args()
    sites = args.sites or sorted(DEPLOYABLE_SLUGS)

    total_fail = 0
    for slug in sites:
        print(f"\n{'=' * 78}")
        print(f"Site: {slug}")
        print("=" * 78)
        result = _audit_site(slug)
        for label, status, detail in result.rows:
            print(f"  [{status:<4}] {label}" + (f" — {detail}" if detail else ""))
        total_fail += result.fail_count

    print(f"\n{'=' * 78}")
    if total_fail:
        print(f"FAIL: {total_fail} check(s) failed across {len(sites)} site(s).")
        return 1
    print(f"PASS: zero failures across {len(sites)} site(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
