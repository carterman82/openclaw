"""
create-legal-pages.py — trust + legal pages per subsite.

Phase 7 Step 7.5 added About / Privacy / Contact for AdSense review.
Phase 8 Step 8.7 extends this same script with Editorial Policy +
Fact-Checking pages for E-E-A-T authority, and upgrades the About copy to
disclose AI-assisted authorship + name Carter Bolz as the human editor.
All five pages are upserted idempotently by slug via REST.

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
HUMAN_EDITOR = "Carter Bolz"

# brand, domain, one-line site description (drawn from each site's
# website_memory/*.localhost.md "What this site is" section), plus the
# authoritative bodies used to fact-check content in that niche (drawn from
# each persona's Entity checklist section).
SITE_INFO: dict[str, dict[str, object]] = {
    "gardening": {
        "brand": "Rootstock",
        "domain": "gardening.info-verse.org",
        "byline": "Rootstock Editors",
        "topic_shortname": "home gardening",
        "blurb": (
            "Rootstock is a home-gardening editorial site for curious hobbyists who "
            "grow things — houseplants on a windowsill, tomatoes in a raised bed, "
            "herbs on a balcony, a small backyard border. It covers plants, soil, "
            "pests, and design with the voice of an experienced gardener talking "
            "across a fence, not a university extension bulletin or a big-box "
            "store's \"10 easy houseplants\" listicle."
        ),
        "authorities": [
            ("Royal Horticultural Society (RHS)", "https://www.rhs.org.uk/",
             "plant profiles, cultivar naming, pest and disease reference"),
            ("USDA Plant Hardiness Zone Map + USDA agricultural research",
             "https://planthardiness.ars.usda.gov/",
             "hardiness zones, native range, invasive-species status"),
            ("Cornell Cooperative Extension, UC Davis Master Gardener program, "
             "Texas A&M AgriLife Extension, and other land-grant university extension services",
             "https://extension.org/",
             "region-specific growing advice, IPM (integrated pest management) guidance, soil science"),
            ("Peer-reviewed horticultural and plant-science research", "",
             "when a claim contradicts common gardening wisdom or asserts a specific mechanism"),
        ],
    },
    "dogs": {
        "brand": "Kennelside",
        "domain": "dogs.info-verse.org",
        "byline": "Kennelside Editors",
        "topic_shortname": "domestic dogs",
        "blurb": (
            "Kennelside is a dog enthusiast site and editorial blog for real dogs. "
            "It covers the world of domestic dogs — breed history, behavior, health, "
            "and training — with the voice of an experienced, knowledgeable "
            "enthusiast, not a detached vet-school textbook or a surface-level "
            "pet-care aggregator."
        ),
        "authorities": [
            ("American Kennel Club (AKC) and United Kennel Club (UKC)",
             "https://www.akc.org/",
             "breed standards, breed history, recognition dates"),
            ("American Veterinary Medical Association (AVMA)",
             "https://www.avma.org/",
             "clinical guidance, canine health policy, vaccination protocols"),
            ("American College of Veterinary Internal Medicine (ACVIM) and "
             "American College of Veterinary Behaviorists (ACVB)", "",
             "board-certified specialist consensus on internal medicine and behavior"),
            ("World Small Animal Veterinary Association (WSAVA) and AAFCO",
             "https://wsava.org/",
             "international small-animal standards; AAFCO for pet-food labeling and nutritional adequacy"),
            ("Peer-reviewed veterinary behavior and canine-cognition research", "",
             "when a claim about training, behavior, or cognition warrants a citation"),
        ],
    },
    "boardgames": {
        "brand": "Meeple",
        "domain": "boardgames.info-verse.org",
        "byline": "Meeple Editors",
        "topic_shortname": "modern hobby board games",
        "blurb": (
            "Meeple is a tabletop-gaming editorial site for players who already own "
            "a shelf of games and want to think about them more carefully. It "
            "covers modern hobby board games, classic gateway titles, mechanics, "
            "strategy, and the history of the medium, written by someone who reads "
            "the rulebook before the first play."
        ),
        "authorities": [
            ("BoardGameGeek (BGG)", "https://boardgamegeek.com/",
             "publication dates, designer/publisher credits, weight ratings, rulebook archives"),
            ("Published rulebooks and official designer errata", "",
             "the primary source for any rules interpretation or edge-case ruling"),
            ("Designer statements — interviews, published essays, official blog posts", "",
             "attributed directly rather than paraphrased"),
            ("Established tabletop review outlets (Shut Up & Sit Down, "
             "The Dice Tower, Space-Biff, Meeple Mountain)", "",
             "when representing critical consensus on a title"),
        ],
    },
    "coffee": {
        "brand": "Crema",
        "domain": "coffee.info-verse.org",
        "byline": "Crema Editors",
        "topic_shortname": "home coffee brewing",
        "blurb": (
            "Crema is a home-brewing editorial site for people who care about the "
            "coffee they make at home — pour-over converts, espresso hobbyists, "
            "French press loyalists who want to level up. It covers beans, brewing "
            "methods, equipment, and technique with the voice of a serious home "
            "barista, not a specialty-coffee marketing site."
        ),
        "authorities": [
            ("Specialty Coffee Association (SCA)", "https://sca.coffee/",
             "cupping protocol, brewing standards, the flavor wheel, water chemistry guidance"),
            ("World Coffee Research", "https://worldcoffeeresearch.org/",
             "varietal reference, cultivar characteristics, agronomic research"),
            ("James Hoffmann (World Barista Champion 2007) and Scott Rao "
             "(author of Everything but Espresso and The Coffee Roaster's Companion)", "",
             "authoritative practitioner sources on brewing technique and roasting"),
            ("Peer-reviewed coffee chemistry and sensory research", "",
             "when a claim about extraction, chemistry, or physiology warrants a citation"),
        ],
    },
    "techtools": {
        "brand": "Tech Tool Guide",
        "domain": "techtools.info-verse.org",
        "byline": "Tech Tool Guide Editors",
        "topic_shortname": "software tools for operators",
        "blurb": (
            "Tech Tool Guide is a practical editorial site for founders, "
            "freelancers, marketers, and small business operators who live in "
            "software every day. It covers SaaS products, AI tools, productivity "
            "systems, and business strategy with the voice of a well-informed "
            "practitioner, not a vendor press release."
        ),
        "authorities": [
            ("Official vendor documentation and product changelogs", "",
             "the primary source for feature capabilities, API behavior, and pricing"),
            ("Vendor pricing pages captured at the time of writing", "",
             "prices change without notice; every quoted price includes the observation date"),
            ("Public SEC filings, S-1s, and investor letters", "",
             "for revenue, funding, and business-model claims about public companies"),
            ("Established trade publications (TechCrunch, The Information, "
             "Stratechery, a16z research)", "",
             "when representing industry analysis or reporting on private-company news"),
        ],
    },
    # Phase 8 Step 8.13: hub parity. info-verse.org is aggregation-only —
    # no article content of its own — so About/EditorialPolicy/FactChecking
    # get hub-specific rendering (the pilot renderers assume each site
    # publishes its own articles). Privacy + Contact reuse the shared
    # renderers unchanged.
    "hub": {
        "brand": "Info Verse",
        "domain": "info-verse.org",
        "byline": "Info Verse Editors",
        "topic_shortname": "single-topic editorial writing across a network of niche sites",
        "is_hub": True,
        "blurb": (
            "Info Verse is a network of independently written, single-topic "
            "editorial sites. info-verse.org is the hub — the front door that "
            "aggregates the latest articles from each site in the network. Every "
            "article link on this page leads to the site that published it."
        ),
        "subsites": [
            ("Rootstock", "https://gardening.info-verse.org", "home gardening"),
            ("Kennelside", "https://dogs.info-verse.org", "domestic dogs"),
            ("Meeple", "https://boardgames.info-verse.org", "modern hobby board games"),
            ("Crema", "https://coffee.info-verse.org", "home coffee brewing"),
            ("Tech Tool Guide", "https://techtools.info-verse.org", "software tools for operators"),
        ],
        # Authorities on the hub are the union of every subsite's own
        # authoritative sources, deduped conceptually — reviewers who land
        # on the hub's fact-checking page see one consolidated view of the
        # standards the network holds itself to.
        "authorities": [
            ("Per-subsite Fact-Checking pages", "",
             "each subsite lists the authoritative bodies specific to its niche — "
             "RHS + USDA + land-grant extension services for gardening; AKC + AVMA + "
             "ACVIM + WSAVA + AAFCO for dogs; BoardGameGeek + rulebooks + designer "
             "statements for boardgames; SCA + World Coffee Research + Hoffmann + Rao "
             "for coffee; vendor docs + SEC filings + trade press for techtools"),
            ("Peer-reviewed research", "",
             "when a claim in any niche warrants primary-source scientific citation"),
            ("Government agencies and standards bodies", "",
             "regulatory filings, EPA registrations, official standards documents"),
            ("Established trade publications", "",
             "when representing critical consensus or reporting on the field"),
        ],
    },
}


def _about_html(info: dict[str, object]) -> str:
    if info.get("is_hub"):
        return _about_html_hub(info)
    return (
        f"<p>{info['blurb']}</p>"
        f"<p>{info['brand']} is part of the Info Verse network of independently "
        "written, single-topic editorial sites. Each site in the network covers "
        "one subject in depth rather than many subjects shallowly — articles are "
        "researched and written to be genuinely useful to someone dealing with "
        "the specific problem in front of them, not to hit a keyword quota.</p>"

        "<h2>Editorial team</h2>"
        f"<p>Articles on {info['brand']} are drafted with the assistance of AI "
        f"language models, then reviewed and edited by <strong>{HUMAN_EDITOR}</strong>, "
        f"who oversees editorial across the Info Verse network. The published byline "
        f"on individual articles reads &ldquo;{info['byline']}&rdquo; because "
        "editorial responsibility is shared between the drafting and editing steps, "
        "not attributed to a single author.</p>"

        f'<p>Every article is checked against the authoritative sources listed on our '
        f'<a href="/fact-checking/">Fact-Checking Standards</a> page before it '
        f'publishes. Our topic selection, sourcing standards, and correction policy '
        f'are documented in the <a href="/editorial-policy/">Editorial Policy</a>.</p>'

        f"<p>Have a correction, a topic suggestion, or feedback on an article? "
        f'See the <a href="/contact/">Contact</a> page.</p>'
    )


def _subsite_list_html(info: dict[str, object]) -> str:
    items = []
    for brand, url, topic in info["subsites"]:  # type: ignore[assignment]
        items.append(
            f'<li><p><strong><a href="{url}" rel="noopener">{brand}</a></strong> — {topic}.</p></li>'
        )
    return "<ul>\n" + "\n".join(items) + "\n</ul>"


def _about_html_hub(info: dict[str, object]) -> str:
    return (
        f"<p>{info['blurb']}</p>"

        "<h2>Sites in the network</h2>"
        + _subsite_list_html(info) +

        "<h2>Editorial team</h2>"
        f"<p>Articles across the Info Verse network are drafted with the assistance "
        f"of AI language models, then reviewed and edited by <strong>{HUMAN_EDITOR}</strong>, "
        f"who oversees editorial across all five sites. Each site's byline reads as "
        f"the site's own editor team (&ldquo;Rootstock Editors&rdquo;, "
        f"&ldquo;Kennelside Editors&rdquo;, etc.) because editorial responsibility "
        f"is shared between the drafting and editing steps, not attributed to a "
        f"single author.</p>"

        f'<p>The standards every site in the network holds itself to — topic selection, '
        f'sourcing, corrections — are documented in the '
        f'<a href="/editorial-policy/">Editorial Policy</a>. Authoritative sources '
        f'consulted across the network are listed on the '
        f'<a href="/fact-checking/">Fact-Checking Standards</a> page; each subsite '
        f'also maintains its own niche-specific fact-checking page.</p>'

        f"<p>Have a correction, a topic suggestion, or feedback on any site in the "
        f'network? See the <a href="/contact/">Contact</a> page.</p>'
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


def _contact_html(info: dict[str, object]) -> str:
    return (
        f"<p>Have a correction, a topic suggestion, or feedback about an article "
        f"on {info['brand']}? Send it to "
        f'<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>'
        "<p>We read every message, though we can't guarantee a reply to every one.</p>"
    )


def _editorial_policy_html(info: dict[str, object]) -> str:
    if info.get("is_hub"):
        return _editorial_policy_html_hub(info)
    return f"""
<p>This page documents how {info['brand']} chooses topics, sources claims, and
handles corrections. It applies to every article published on this site.</p>

<h2>What we cover</h2>
<p>{info['brand']} is a single-topic editorial site focused on {info['topic_shortname']}.
We only publish articles that fall inside that focus. We do not chase adjacent
trending topics for traffic if they fall outside the site's subject.</p>

<h2>How we pick topics</h2>
<p>Topics come from three places: reader questions and repeated patterns we
notice in the niche, gaps in existing coverage where the top search results
answer the question shallowly or incorrectly, and material we want to
understand better ourselves. We aim to publish articles that are genuinely
useful to someone dealing with a specific problem, not to hit a keyword quota
or rewrite what other sites already cover well.</p>

<h2>How we source claims</h2>
<p>Every non-obvious claim in an article — a statistic, a strong recommendation,
a claim that contradicts common wisdom — is grounded in an authoritative source
listed on our <a href="/fact-checking/">Fact-Checking Standards</a> page. Sources
are cited inline or in a &ldquo;Sources &amp; Further Reading&rdquo; section at
the end of the article, with direct links wherever a link exists. We do not
cite ourselves as a source for our own claims.</p>

<p>Contested or surprising claims are structured to make our reasoning visible:
we state the claim plainly, cite the specific evidence backing it, and explain
the reasoning connecting the evidence to the claim. If we cannot find a real
source, we do not make the claim.</p>

<h2>Editorial process</h2>
<p>Articles are drafted with the assistance of AI language models and then
reviewed and edited by {HUMAN_EDITOR}, who oversees editorial across the
Info Verse network. The editing pass audits sourcing, checks the article
against the fact-checking standards, and revises for accuracy and clarity
before the article publishes. See the <a href="/about/">About</a> page for
more on the editorial team.</p>

<h2>Corrections and updates</h2>
<p>If we get something wrong, we fix it. Email
<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> with the article URL and
the specific correction. Substantive corrections are noted at the bottom of
the affected article with the date of the fix. Minor typo fixes are made
silently.</p>

<p>Articles are reviewed for accuracy over time. Each article displays a
&ldquo;Reviewed&rdquo; date next to its byline; when we re-verify an article
against current sources, we update that date. Older articles may still be
accurate but reflect the state of the field at the time of writing.</p>

<h2>Independence</h2>
<p>{info['brand']} is independently written. We do not accept paid placements,
sponsored posts, or free products in exchange for coverage. Any affiliate
relationships — where a link to a product pays a small commission at no cost
to the reader — are disclosed within the article. Display advertising served
via Google AdSense is standard programmatic advertising and does not influence
editorial coverage.</p>

<h2>Contact</h2>
<p>Editorial questions, corrections, and feedback:
<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>
""".strip()


def _editorial_policy_html_hub(info: dict[str, object]) -> str:
    return f"""
<p>This page documents the editorial standards every site in the Info Verse
network holds itself to. Each site — Rootstock (gardening), Kennelside (dogs),
Meeple (board games), Crema (coffee), and Tech Tool Guide (software) — applies
these standards to its own subject; this page describes the shared policy.</p>

<h2>What we cover</h2>
<p>Each site in the network is a single-topic editorial site focused on one
subject. We only publish articles on a given site that fall inside that site's
focus. We do not chase adjacent trending topics for traffic if they fall
outside a site's subject.</p>

<h2>How we pick topics</h2>
<p>Topics come from three places: reader questions and repeated patterns we
notice in each niche, gaps in existing coverage where the top search results
answer a question shallowly or incorrectly, and material we want to understand
better ourselves. We aim to publish articles that are genuinely useful to
someone dealing with a specific problem, not to hit a keyword quota or rewrite
what other sites already cover well.</p>

<h2>How we source claims</h2>
<p>Every non-obvious claim in an article — a statistic, a strong recommendation,
a claim that contradicts common wisdom — is grounded in an authoritative source.
Each subsite maintains its own <a href="/fact-checking/">Fact-Checking Standards</a>
page listing the authoritative bodies specific to its niche. Sources are cited
inline or in a &ldquo;Sources &amp; Further Reading&rdquo; section at the end
of each article, with direct links wherever a link exists. We do not cite
ourselves as a source for our own claims.</p>

<p>Contested or surprising claims are structured to make our reasoning visible:
we state the claim plainly, cite the specific evidence backing it, and explain
the reasoning connecting the evidence to the claim. If we cannot find a real
source, we do not make the claim.</p>

<h2>Editorial process</h2>
<p>Articles are drafted with the assistance of AI language models and then
reviewed and edited by {HUMAN_EDITOR}, who oversees editorial across the
Info Verse network. The editing pass audits sourcing, checks the article
against the fact-checking standards, and revises for accuracy and clarity
before the article publishes. See the <a href="/about/">About</a> page for
more on the editorial team.</p>

<h2>Corrections and updates</h2>
<p>If we get something wrong, we fix it. Email
<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> with the article URL and
the specific correction. Substantive corrections are noted at the bottom of
the affected article with the date of the fix. Minor typo fixes are made
silently.</p>

<p>Articles are reviewed for accuracy over time. Each article displays a
&ldquo;Reviewed&rdquo; date next to its byline; when we re-verify an article
against current sources, we update that date. Older articles may still be
accurate but reflect the state of the field at the time of writing.</p>

<h2>Independence</h2>
<p>Every site in the Info Verse network is independently written. We do not
accept paid placements, sponsored posts, or free products in exchange for
coverage. Any affiliate relationships — where a link to a product pays a small
commission at no cost to the reader — are disclosed within the article.
Display advertising served via Google AdSense is standard programmatic
advertising and does not influence editorial coverage.</p>

<h2>Contact</h2>
<p>Editorial questions, corrections, and feedback:
<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>
""".strip()


def _fact_checking_html(info: dict[str, object]) -> str:
    if info.get("is_hub"):
        return _fact_checking_html_hub(info)
    authorities_html_parts = []
    for name, url, purpose in info["authorities"]:  # type: ignore[assignment]
        if url:
            heading = f'<a href="{url}" rel="noopener" target="_blank">{name}</a>'
        else:
            heading = name
        authorities_html_parts.append(
            f"<li><p><strong>{heading}</strong> — {purpose}.</p></li>"
        )
    authorities_html = "\n".join(authorities_html_parts)

    return f"""
<p>This page lists the authoritative sources {info['brand']} relies on to
fact-check the claims in its articles. It applies to every article on this
site, in combination with the <a href="/editorial-policy/">Editorial
Policy</a>.</p>

<h2>Standards we hold sources to</h2>
<p>A source counts as authoritative when it meets one or more of these criteria:</p>
<ul>
    <li><p>It is a standards body, professional association, or government agency
        with recognized authority in the subject.</p></li>
    <li><p>It is peer-reviewed research published in a reputable venue.</p></li>
    <li><p>It is a primary source — a rulebook, a piece of official documentation,
        a designer or maker's own published statement, a regulatory filing.</p></li>
    <li><p>It is an established, editorially-independent trade publication with a
        track record of accurate reporting in the field.</p></li>
</ul>

<p>Individual bloggers, forum posts, and unverified social-media claims are not
treated as authoritative on their own. They may be cited when attributed
transparently (&ldquo;a user on the r/coffee subreddit reports…&rdquo;) but do
not carry the weight of the sources listed below.</p>

<h2>Authoritative sources for {info['topic_shortname']}</h2>
<ol>
{authorities_html}
</ol>

<h2>What we do when sources disagree</h2>
<p>If two authoritative sources disagree on a factual point, the article says
so explicitly, names both positions, and explains which one we're following
and why. We do not launder disagreements into a single-voice answer that
pretends the disagreement doesn't exist.</p>

<h2>What we do when we cannot find a source</h2>
<p>If we cannot find an authoritative source for a claim, we either drop the
claim, mark it clearly as speculation or personal observation, or replace it
with a weaker claim that we can source. Our editorial process treats
&ldquo;we're not sure&rdquo; as an acceptable answer; &ldquo;we sound sure but
made it up&rdquo; is not.</p>

<h2>Reporting a factual error</h2>
<p>Found something we got wrong? Email
<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> with the article URL, the
specific claim, and the source that shows the correct answer. Corrections are
handled per the <a href="/editorial-policy/">Editorial Policy</a>.</p>
""".strip()


def _fact_checking_html_hub(info: dict[str, object]) -> str:
    authorities_html_parts = []
    for name, url, purpose in info["authorities"]:  # type: ignore[assignment]
        if url:
            heading = f'<a href="{url}" rel="noopener" target="_blank">{name}</a>'
        else:
            heading = name
        authorities_html_parts.append(
            f"<li><p><strong>{heading}</strong> — {purpose}.</p></li>"
        )
    authorities_html = "\n".join(authorities_html_parts)

    return f"""
<p>This page describes the standards the Info Verse network holds its sources
to. Each site in the network — Rootstock, Kennelside, Meeple, Crema, and
Tech Tool Guide — maintains its own niche-specific Fact-Checking Standards
page; this page summarizes the shared standard and points to each subsite's
authoritative sources.</p>

<h2>Standards we hold sources to</h2>
<p>A source counts as authoritative when it meets one or more of these criteria:</p>
<ul>
    <li><p>It is a standards body, professional association, or government agency
        with recognized authority in the subject.</p></li>
    <li><p>It is peer-reviewed research published in a reputable venue.</p></li>
    <li><p>It is a primary source — a rulebook, a piece of official documentation,
        a designer or maker's own published statement, a regulatory filing.</p></li>
    <li><p>It is an established, editorially-independent trade publication with a
        track record of accurate reporting in the field.</p></li>
</ul>

<p>Individual bloggers, forum posts, and unverified social-media claims are not
treated as authoritative on their own. They may be cited when attributed
transparently (&ldquo;a user on the r/coffee subreddit reports…&rdquo;) but do
not carry the weight of the sources listed below.</p>

<h2>Per-site fact-checking authorities</h2>
{_subsite_list_html(info)}
<p>Each subsite's Fact-Checking Standards page lists the specific authoritative
bodies for its niche.</p>

<h2>Cross-network source categories</h2>
<ol>
{authorities_html}
</ol>

<h2>What we do when sources disagree</h2>
<p>If two authoritative sources disagree on a factual point, the article says
so explicitly, names both positions, and explains which one we're following
and why. We do not launder disagreements into a single-voice answer that
pretends the disagreement doesn't exist.</p>

<h2>What we do when we cannot find a source</h2>
<p>If we cannot find an authoritative source for a claim, we either drop the
claim, mark it clearly as speculation or personal observation, or replace it
with a weaker claim that we can source. Our editorial process treats
&ldquo;we're not sure&rdquo; as an acceptable answer; &ldquo;we sound sure but
made it up&rdquo; is not.</p>

<h2>Reporting a factual error</h2>
<p>Found something we got wrong? Email
<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> with the article URL, the
specific claim, and the source that shows the correct answer. Corrections are
handled per the <a href="/editorial-policy/">Editorial Policy</a>.</p>
""".strip()


PAGES = [
    ("about", "About", _about_html),
    ("privacy", "Privacy Policy", _privacy_html),
    ("contact", "Contact", _contact_html),
    ("editorial-policy", "Editorial Policy", _editorial_policy_html),
    ("fact-checking", "Fact-Checking Standards", _fact_checking_html),
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


def _upsert_brand_option(base_url: str, auth: tuple[str, str], brand: str) -> None:
    """Set the openclaw_brand site option so the byline shortcode and any other
    theme code can render the brand name (Rootstock) rather than the network
    blogname (Gardening Info Verse). Idempotent — WP settings endpoint accepts
    a re-write of the same value with no side effects."""
    resp = requests.post(
        f"{base_url}/wp-json/wp/v2/settings",
        json={"openclaw_brand": brand},
        auth=auth,
        timeout=15,
    )
    if resp.status_code == 400 and "rest_invalid_param" in resp.text:
        # Option not registered on this site — swallow so publish continues.
        print(f"  [warn] openclaw_brand option not registered on this site; skipping brand set")
        return
    resp.raise_for_status()
    print(f"  [option] openclaw_brand = {brand!r}")


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

    _upsert_brand_option(base_url, auth, str(info["brand"]))

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
