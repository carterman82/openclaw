"""
create-legal-pages.py — Phase 7 Step 7.5 About / Privacy / Contact pages.

AdSense review requires these three pages to exist and be linked (the
footer's new "Legal" column, added alongside this script, links to
/about/, /privacy/, /contact/ on every subsite). Creates or updates
(idempotent on slug) one page of each type per pilot subsite via the REST
API, using each site's website_memory persona for on-brand About copy and a
single shared contact address for Contact/Privacy.

Usage:
    python scripts/create-legal-pages.py               # all 5 deployable pilots
    python scripts/create-legal-pages.py --site coffee
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import openclaw  # noqa: F401  (installs the *.localhost DNS shim)
from openclaw.main import _activate_site
from openclaw.config import Config
from openclaw.deploy import DEPLOYABLE_SLUGS

CONTACT_EMAIL = "info.verse.real@gmail.com"

# brand, domain, one-line site description (drawn from each site's
# website_memory/*.localhost.md "What this site is" section).
SITE_INFO: dict[str, dict[str, str]] = {
    "gardening": {
        "brand": "Rootstock",
        "domain": "gardening.info-verse.org",
        "blurb": (
            "Rootstock is a home-gardening editorial site for curious hobbyists who "
            "grow things — houseplants on a windowsill, tomatoes in a raised bed, "
            "herbs on a balcony, a small backyard border. It covers plants, soil, "
            "pests, and design with the voice of an experienced gardener talking "
            "across a fence, not a university extension bulletin or a big-box "
            "store's \"10 easy houseplants\" listicle."
        ),
    },
    "dogs": {
        "brand": "Kennelside",
        "domain": "dogs.info-verse.org",
        "blurb": (
            "Kennelside is a dog enthusiast site and editorial blog for real dogs. "
            "It covers the world of domestic dogs — breed history, behavior, health, "
            "and training — with the voice of an experienced, knowledgeable "
            "enthusiast, not a detached vet-school textbook or a surface-level "
            "pet-care aggregator."
        ),
    },
    "boardgames": {
        "brand": "Meeple",
        "domain": "boardgames.info-verse.org",
        "blurb": (
            "Meeple is a tabletop-gaming editorial site for players who already own "
            "a shelf of games and want to think about them more carefully. It "
            "covers modern hobby board games, classic gateway titles, mechanics, "
            "strategy, and the history of the medium, written by someone who reads "
            "the rulebook before the first play."
        ),
    },
    "coffee": {
        "brand": "Crema",
        "domain": "coffee.info-verse.org",
        "blurb": (
            "Crema is a home-brewing editorial site for people who care about the "
            "coffee they make at home — pour-over converts, espresso hobbyists, "
            "French press loyalists who want to level up. It covers beans, brewing "
            "methods, equipment, and technique with the voice of a serious home "
            "barista, not a specialty-coffee marketing site."
        ),
    },
    "techtools": {
        "brand": "Tech Tool Guide",
        "domain": "techtools.info-verse.org",
        "blurb": (
            "Tech Tool Guide is a practical editorial site for founders, "
            "freelancers, marketers, and small business operators who live in "
            "software every day. It covers SaaS products, AI tools, productivity "
            "systems, and business strategy with the voice of a well-informed "
            "practitioner, not a vendor press release."
        ),
    },
}


def _about_html(info: dict[str, str]) -> str:
    return (
        f"<p>{info['blurb']}</p>"
        f"<p>{info['brand']} is part of the Info Verse network of independently "
        "written, single-topic editorial sites. Each site in the network covers "
        "one subject in depth rather than many subjects shallowly — articles are "
        "researched and written to be genuinely useful to someone dealing with "
        "the specific problem in front of them, not to hit a keyword quota.</p>"
        f"<p>Have a correction, a topic suggestion, or feedback on an article? "
        f'See the <a href="/contact/">Contact</a> page.</p>'
    )


def _privacy_html(info: dict[str, str]) -> str:
    return f"""
<p>This Privacy Policy explains what data {info['brand']} ({info['domain']}) collects
from visitors and how it is used. It applies to this site as part of the Info
Verse network.</p>

<h2>Analytics</h2>
<p>We use Google Analytics (GA4) to understand how visitors use this site —
which pages are read, how people arrive, and general audience trends. Google
Analytics uses cookies and similar technologies to collect this information.
No personally identifying information is collected by us through this
process. See
<a href="https://policies.google.com/privacy" rel="noopener" target="_blank">Google's Privacy Policy</a>
for details on how Google handles this data.</p>

<h2>Advertising</h2>
<p>This site may display ads served by Google AdSense. Google and its
partners may use cookies to serve ads based on a visitor's prior visits to
this and other websites. Visitors can opt out of personalized advertising by
visiting
<a href="https://adssettings.google.com" rel="noopener" target="_blank">Google Ads Settings</a>.
Third-party vendors, including Google, use cookies to serve ads based on a
visitor's past visits; see
<a href="https://policies.google.com/technologies/partner-sites" rel="noopener" target="_blank">how Google uses data</a>
when partner sites use its services.</p>

<h2>Cookies</h2>
<p>Cookies set by the analytics and advertising services described above are
used to distinguish visitors and, where applicable, personalize ads. You can
disable cookies through your browser settings; doing so may affect some site
functionality but will not prevent you from reading articles.</p>

<h2>Third-Party Links</h2>
<p>Articles on this site link to external sources for reference and
attribution. We are not responsible for the content or privacy practices of
external sites linked from our articles.</p>

<h2>Data We Don't Collect</h2>
<p>We do not require account registration to read this site, and we do not
sell visitor data to third parties.</p>

<h2>Contact</h2>
<p>Questions about this policy can be sent to
<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>

<p><em>This policy may be updated from time to time; the version on this page
is always current.</em></p>
""".strip()


def _contact_html(info: dict[str, str]) -> str:
    return (
        f"<p>Have a correction, a topic suggestion, or feedback about an article "
        f"on {info['brand']}? Send it to "
        f'<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>'
        "<p>We read every message, though we can't guarantee a reply to every one.</p>"
    )


PAGES = [
    ("about", "About", _about_html),
    ("privacy", "Privacy Policy", _privacy_html),
    ("contact", "Contact", _contact_html),
]


def _upsert_page(base_url: str, auth: tuple[str, str], slug: str, title: str, content: str) -> None:
    existing = requests.get(
        f"{base_url}/wp-json/wp/v2/pages",
        params={"slug": slug, "status": "any"},
        auth=auth,
        timeout=15,
    )
    existing.raise_for_status()
    matches = existing.json()

    payload = {
        "title": title,
        "content": content,
        "slug": slug,
        "status": "publish",
    }
    if matches:
        page_id = matches[0]["id"]
        resp = requests.post(
            f"{base_url}/wp-json/wp/v2/pages/{page_id}", json=payload, auth=auth, timeout=15
        )
        action = "updated"
    else:
        resp = requests.post(
            f"{base_url}/wp-json/wp/v2/pages", json=payload, auth=auth, timeout=15
        )
        action = "created"
    resp.raise_for_status()
    print(f"  [{action}] /{slug}/ -> {resp.json()['link']}")


def create_pages_for_site(slug: str) -> None:
    info = SITE_INFO.get(slug)
    if not info:
        print(f"[{slug}] no SITE_INFO entry — skipping.")
        return
    print(f"\n{slug} ({info['brand']}):")
    _activate_site(slug)
    cfg = Config.load()
    auth = (cfg.WP_USERNAME, cfg.WP_APP_PASSWORD)
    base_url = cfg.WP_BASE_URL

    for page_slug, title, content_fn in PAGES:
        _upsert_page(base_url, auth, page_slug, title, content_fn(info))


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 Step 7.5 legal pages.")
    parser.add_argument(
        "--site", action="append", dest="sites", metavar="SLUG",
        help="Limit to this site slug (repeatable). Default: all deployable pilot subsites.",
    )
    args = parser.parse_args()
    sites = args.sites or sorted(DEPLOYABLE_SLUGS)

    for slug in sites:
        create_pages_for_site(slug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
