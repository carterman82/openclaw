"""CLI logic for the openclaw agent."""

from __future__ import annotations

import argparse
import difflib
import json
import logging
import os
import random
import re
import sys
from html import escape as html_escape
from html import unescape as html_unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from .config import Config
from .deploy import deploy_after_publish, is_deployable
from .generator import generate_article, revise_article
from .images import (
    attribution_html,
    find_unsplash_image,
    generate_local_image,
    generate_openai_image,
    track_download,
)
from .publisher import (
    get_category_names,
    get_seo_plugin,
    get_site_name,
    list_recent_post_titles,
    list_recent_posts_for_linking,
    publish_post,
    reset_site_caches,
    upload_media,
)
from .trends import gather_trending_signals
from .validation import dump_rejected_article, find_title_collision, validate_article

logger = logging.getLogger(__name__)


_SITE_PREFIXED_KEYS: tuple[str, ...] = (
    "WP_BASE_URL",
    "WP_USERNAME",
    "WP_APP_PASSWORD",
)


def _activate_site(slug: str | None) -> None:
    """Copy prefixed env vars (e.g. CATFANCAST_WP_BASE_URL) into their bare positions.

    Called before Config.load() so downstream code reads bare WP_* env vars
    without knowing about per-site prefixes. Cross-site keys (ANTHROPIC_API_KEY,
    OPENAI_API_KEY, UNSPLASH_ACCESS_KEY) are never prefixed and never touched.
    """
    from dotenv import load_dotenv
    load_dotenv()  # ensure .env is read before we inspect os.environ

    reset_site_caches()

    if not slug:
        return

    prefix = slug.upper() + "_"
    missing: list[str] = []
    for key in _SITE_PREFIXED_KEYS:
        prefixed = prefix + key
        value = os.environ.get(prefixed)
        if value is None or value == "":
            missing.append(prefixed)
            continue
        os.environ[key] = value
    if missing:
        raise RuntimeError(
            f"--site {slug!r}: missing env vars {missing}. "
            f"Add them to .env with the {prefix} prefix."
        )
    logger.info("Activated site %r → %s", slug, os.environ["WP_BASE_URL"])


_WEBSITE_MEMORY_DIR: Path = Path(__file__).resolve().parent.parent / "website_memory"


def _load_trends_config(site_host: str) -> tuple[list[str], list[str]]:
    """Return (subreddits, seeds) from website_memory/{site_host}.trends.json.

    Returns ([], []) when the file is absent — no hardcoded fallback so no
    signals from one site bleed into another. Logs a warning when the file
    is missing so operators know to create it.
    """
    path = _WEBSITE_MEMORY_DIR / f"{site_host}.trends.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        subreddits = [str(s) for s in data.get("reddit_subreddits", [])]
        seeds = [str(s) for s in data.get("google_suggest_seeds", [])]
        logger.debug(
            "Loaded trends config for %r: %d subreddits, %d seeds.",
            site_host, len(subreddits), len(seeds),
        )
        return subreddits, seeds
    except FileNotFoundError:
        logger.warning(
            "No trends config at %s — skipping Reddit/Suggest signals. "
            "Create it to enable trending topic discovery.",
            path,
        )
        return [], []
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Trends config at %s is invalid JSON: %s — skipping.", path, exc)
        return [], []


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


# The model keeps emitting em dashes despite hard prompt constraints (verified
# across 4 consecutive generations), so we strip them mechanically before
# publish. An em-dash aside reads naturally as a comma in nearly all cases.
_EM_DASH_RE = re.compile(r"\s*—+\s*")


def _strip_em_dashes(text: str) -> tuple[str, int]:
    count = len(_EM_DASH_RE.findall(text))
    if not count:
        return text, 0
    replaced = _EM_DASH_RE.sub(", ", text)
    # An em dash right after punctuation ("said —" or ",—") would leave ", ,".
    replaced = re.sub(r"([,:;])\s*,\s*", r"\1 ", replaced)
    return replaced, count


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


# Match runs of anything that isn't a letter, number, or whitespace so we can
# collapse things like "Soil & Composting" -> "soil composting" before feeding
# to Unsplash's search endpoint (which returns 0 results on the raw string).
_UNSPLASH_QUERY_STRIP_RE = re.compile(r"[^\w\s]+", re.UNICODE)


def _clean_unsplash_query(q: str) -> str:
    collapsed = _UNSPLASH_QUERY_STRIP_RE.sub(" ", q)
    return " ".join(collapsed.split()).lower()


def _build_unsplash_query_ladder(article: dict) -> list[str]:
    """Return an ordered, de-duplicated list of Unsplash queries to try.

    Progressively broader — the specific `unsplash_query` from the model
    (which is often too niche for stock photography, e.g. "soil test report
    lime bag" -> 0 results) first, then focus_keyphrase, then just the head
    of it, then category, then category head, then first tag. Each subsequent
    query drops specificity so we eventually hit something the Unsplash
    library actually contains.
    """
    raw_candidates: list[str] = []
    for key in ("unsplash_query", "focus_keyphrase"):
        value = article.get(key)
        if isinstance(value, str) and value.strip():
            raw_candidates.append(value)

    keyphrase = article.get("focus_keyphrase") or ""
    if isinstance(keyphrase, str):
        kp_words = keyphrase.strip().split()
        if len(kp_words) >= 2:
            raw_candidates.append(" ".join(kp_words[:2]))
        if len(kp_words) >= 1:
            raw_candidates.append(kp_words[0])

    category = article.get("category") or ""
    if isinstance(category, str) and category.strip():
        raw_candidates.append(category)
        cat_words = _clean_unsplash_query(category).split()
        if cat_words:
            raw_candidates.append(cat_words[0])

    tags = article.get("tags") or []
    if isinstance(tags, list) and tags:
        for tag in tags[:2]:
            if isinstance(tag, str) and tag.strip():
                raw_candidates.append(tag)

    seen: set[str] = set()
    ladder: list[str] = []
    for raw in raw_candidates:
        cleaned = _clean_unsplash_query(raw)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        ladder.append(cleaned)
    return ladder


def _fetch_and_attach_image(article: dict) -> tuple[dict | None, int | None, str]:
    """Generate via local Flux, fall back to OpenAI, then Unsplash, then no image.

    Returns (image, attachment_id, body_html_with_credit). The credit suffix
    is appended only for Unsplash (its attribution dict is truthy); local and
    OpenAI images return attribution=None and the body is unchanged. On full
    failure returns (None, None, original_body_html) so publishing never blocks.
    """
    body = article["body_html"]
    image = None
    source = ""

    prompt = article.get("image_prompt")
    # Prefer the generator's keyphrase-inclusive alt text; fall back gracefully.
    alt_hint = article.get("image_alt_text") or article.get("focus_keyphrase") or article["title"]
    if prompt:
        if Config.load().LOCAL_IMAGE_ENABLED:
            logger.info("Generating local image via Draw Things (prompt=%r).", prompt[:120])
            image = generate_local_image(prompt, alt_hint)
            if image:
                source = "Local (Draw Things)"
            else:
                logger.warning("Local image generation failed; falling back to OpenAI.")
        if not image:
            logger.info("Generating OpenAI image (prompt=%r).", prompt[:120])
            image = generate_openai_image(prompt, alt_hint)
            if image:
                source = "OpenAI"
            else:
                logger.warning("OpenAI image generation failed; falling back to Unsplash.")
    else:
        logger.warning("Article has no image_prompt; falling back to Unsplash.")

    if not image:
        ladder = _build_unsplash_query_ladder(article)
        if not ladder:
            logger.warning("No Unsplash query candidates on article; skipping Unsplash.")
        else:
            logger.info("Unsplash query ladder: %s", ladder)
            for idx, query in enumerate(ladder, start=1):
                logger.info(
                    "Searching Unsplash (%d/%d, query=%r).", idx, len(ladder), query,
                )
                image = find_unsplash_image(query)
                if image:
                    source = (
                        f"Unsplash ({image['attribution']['photographer_name']}, "
                        f"query={query!r})"
                    )
                    break

    if not image:
        logger.warning(
            "No image from local, OpenAI, or Unsplash; publishing without featured image."
        )
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

    logger.info("Uploaded featured image (id=%d, source=%s, alt=%r).", attachment_id, source, alt)

    final_body = body + "\n" + caption if caption else body
    return image, attachment_id, final_body


# --- Per-run variation ------------------------------------------------------
# LLMs can't self-randomize: given the same prompt they gravitate to the same
# high-probability picks (same category, same length, FAQ on every article).
# Real randomness has to come from code, so we roll structural directives here
# and inject them into the prompt.

# Step 3.8.10 (2026-07-18): top band trimmed 1800-2400 -> 1600-2000. The
# animefancast.com tuning run's worst content-repetition case (verbatim
# paragraph duplication, FAQ answer re-pasting body content a third time)
# came from the top band combined with an FAQ section — longer targets give
# the local model more room to loop before it burns through max_tokens.
_LENGTH_BANDS: tuple[tuple[int, int], ...] = ((900, 1300), (1300, 1700), (1600, 2000))

_HOOK_TYPES: tuple[str, ...] = (
    "the surprising fact",
    "the intriguing anecdote",
    "the bold stance",
    'the "yeah, but..."',
    "in medias res",
    "the reader's own moment",
)

_FAQ_PROBABILITY: float = 1 / 3

# Step 6.5 (2026-07-19): the site's title corpus skewed heavily toward one
# contrarian shape ("X Is Not the Problem", "Your X Isn't Y. It's Z." —
# STYLE.md Formula E) because the model reaches for it by default whenever
# it's available, not just when the material earns it. Capping it via a
# prompt directive alone didn't work for the same reason FAQ inclusion
# needed a code-level coin flip instead of a soft "use sometimes" note — the
# model can't self-randomize. So the constraint is rolled in code, same
# pattern as _FAQ_PROBABILITY.
_CONTRARIAN_HEADLINE_PROBABILITY: float = 1 / 3


def _roll_variation_directives() -> tuple[str, tuple[int, int]]:
    """Roll random structural directives so articles vary in shape and length.

    Returns (directive_text, (low, high)) — the band is threaded through to
    the Step 6.1 validation gate so it can check the final word count
    against the same band the model was told to target.
    """
    low, high = random.choice(_LENGTH_BANDS)
    hook = random.choice(_HOOK_TYPES)
    if random.random() < _FAQ_PROBABILITY:
        faq_line = "Include a short FAQ section near the end."
    else:
        faq_line = "Do NOT include an FAQ section in this article."
    if random.random() < _CONTRARIAN_HEADLINE_PROBABILITY:
        headline_line = (
            "This run's title MAY use the contrarian-reframe formula "
            "(STYLE.md Formula E: \"Your X Isn't Y. It's Z.\" / \"X Is Not "
            "the Problem\" / \"You're Doing X Wrong\") if the material "
            "genuinely earns it."
        )
    else:
        headline_line = (
            "Do NOT use the contrarian-reframe formula (STYLE.md Formula E: "
            "\"Your X Isn't Y. It's Z.\" / \"X Is Not the Problem\" / "
            "\"You're Doing X Wrong\") for this article's title. Pick a "
            "different formula (A, B, C, D, F, G, H, I, or J)."
        )
    directive = (
        "Variation directives for this article (assigned at random for this run; "
        f"follow them): target {low}-{high} words of body content. {faq_line} "
        f"Open with a hook of the {hook!r} type (see the style guide's Hook Craft "
        f"section). {headline_line}"
    )
    return directive, (low, high)


def _pick_random_category(wp_categories: tuple[str, ...]) -> str:
    selectable = [c for c in wp_categories if c.lower() != "uncategorized"]
    return random.choice(selectable or list(wp_categories))


def _find_duplicate_title(title: str, recent_titles: list[str]) -> str | None:
    """Return the colliding recent title if `title` is an exact or near-exact repeat.

    The LLM is instructed not to repeat a recent topic, but local models are
    unreliable at honoring that soft instruction (observed: the same title
    reproduced verbatim across two separate runs). This is the hard backstop.
    Delegates to validation.find_title_collision so this pre-generation check
    (against the recent-N titles used for prompt steering) and the Step 6.1
    post-generation gate (against the full site catalog) share one
    definition of "duplicate."
    """
    return find_title_collision(title, recent_titles)


# Step 3.8.10 (2026-07-18): animefancast.com tuning found the local model
# collapsing into sentence/paragraph repeat loops in the back half of long
# articles (e.g. "keeping the pilots small, keeping them weak, keeping them
# dependent" repeated 7x verbatim in one draft) — sampling-parameter tuning
# alone (repetition_penalty, frequency_penalty) did not stop it. This is a
# hard backstop analogous to _find_duplicate_title.
#
# Step 6.5 (2026-07-20): the original 25-char sentence-length floor was
# too high to catch a different flavor of the same degeneration — dogs #4
# in a verification batch ended with a ~12-sentence echo-fragment block
# ("The dog will come. The dog will stay. The dog will be home. ... The
# dog will be loved. The dog will be yours.") repeated twice verbatim,
# entirely built from sub-25-char sentences that were filtered out before
# the repeat check ever saw them. Lowered the floor to catch short
# sentences too, but short sentences also legitimately recur two other
# ways: (a) deliberate near-rhyme contrast (e.g. "The crown stays wet." /
# "The crown stays dry." in a real "cause vs. fix" explainer — 0.85
# similar, not degeneration) and (b) a short verdict/imperative reused as
# a structural refrain across many different conditions in a decision
# framework (e.g. "Cancel it." answering six different trigger conditions
# in a SaaS-audit checklist). Fix for (a): below _REPEAT_EXACT_ONLY_MAX_LEN,
# only a literal exact match counts as a repeat — fuzzy-paraphrase
# matching stays reserved for longer sentences, where the original
# animefancast.com failure mode lives. Fix for (b): raised the floor to
# 15 chars, just enough to exclude 2-3 word imperatives like "Cancel it."
# while still admitting the "[Subject] will/is [predicate]." shape that
# made up the actual dogs #4 degenerate block. Verified against 48 clean
# articles from three verification batches: this combination catches both
# known true positives (dogs #4, boardgames #5's "The first movers win."
# repeated 3x) with zero false positives.
_REPEAT_MIN_SENTENCE_LEN = 15
_REPEAT_EXACT_ONLY_MAX_LEN = 40
_REPEAT_SIMILARITY_THRESHOLD = 0.85
_REPEAT_MAX_OCCURRENCES = 2


def _find_repeated_content(body_html: str) -> str | None:
    """Return an offending sentence if body_html shows repeat-loop degeneration.

    Flags any sentence that occurs more than `_REPEAT_MAX_OCCURRENCES` times
    verbatim, or (for sentences longer than `_REPEAT_EXACT_ONLY_MAX_LEN`) as a
    close paraphrase.
    """
    text = html_unescape(_strip_html(body_html))
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", text)
        if len(s.strip()) >= _REPEAT_MIN_SENTENCE_LEN
    ]
    if len(sentences) < 10:
        return None
    normalized = [re.sub(r"\s+", " ", s.lower()) for s in sentences]
    for i, a in enumerate(normalized):
        occurrences = 1
        for j in range(i + 1, len(normalized)):
            b = normalized[j]
            if a == b:
                occurrences += 1
            elif (
                len(a) > _REPEAT_EXACT_ONLY_MAX_LEN
                and len(b) > _REPEAT_EXACT_ONLY_MAX_LEN
                and difflib.SequenceMatcher(None, a, b).ratio() >= _REPEAT_SIMILARITY_THRESHOLD
            ):
                occurrences += 1
        if occurrences > _REPEAT_MAX_OCCURRENCES:
            return sentences[i]
    return None


# Step 6.5 (2026-07-19): STYLE.md's prompt-only ban on the echo-fragment
# closer tic ("It is not X. It is Y. It is Z.", "The choice is yours.") did
# not hold up — a 25-generation verification batch across all 5 pilot sites
# still produced it in 7/25 articles even after the editor pass. Same lesson
# as _find_duplicate_title and _find_repeated_content: a soft instruction
# isn't enough for a pattern this specific and memorized. Regex matches
# scripts/audit-content.py's _CLOSER_TIC_RE so detection stays consistent
# between the generation-time gate and the standalone audit scanner.
_CLOSER_TIC_RE = re.compile(
    r"(?:\bthe choice is yours\b"
    r"|\bit is not [^.!?]{2,40}\. it is [^.!?]{2,40}\.)",
    re.IGNORECASE,
)


def _find_closer_tic(body_html: str) -> str | None:
    """Return a snippet if body_html contains the banned echo-fragment closer tic."""
    text = html_unescape(_strip_html(body_html))
    m = _CLOSER_TIC_RE.search(text)
    if not m:
        return None
    start = max(0, m.start() - 40)
    end = min(len(text), m.end() + 40)
    return text[start:end].strip()


# Step 6.5 (2026-07-20): STYLE.md's Anti-Fabrication section and EDITOR.md's
# Hallucination Checklist (both prompt-only) did not hold up either — a
# 25-generation verification batch still produced fabricated-sounding named
# citations in 2/16 would-publish articles even after the editor pass:
# dogs #3 invented "Dr. S. Jane Sykes and Dr. Madhuri Koutmos at UC Davis"
# and a company "ABCDNA"; techtools #2 invented "A 2014 study at the
# University of Illinois" tracking "102 knowledge workers" for the
# Pomodoro/52-17 rule. This can't verify truth, only flag suspicious
# over-specific attribution shape (named person + institution, or a
# study/company claim with fabricated-plausible specificity) — same
# lesson as _find_closer_tic: a soft instruction isn't enough, so push
# the model toward STYLE.md's own stated fallback ("a correct vague
# sentence beats a precise invented one") by regenerating once on a hit.
# A round-2 verification batch (after the checks below were first added)
# still slipped one through in a different shape: gardening #3 cited
# "(Cornell University Extension, 2018)" with specific rot-rate/temperature
# stats attached to a claim about "land-grant universities in the Pacific
# Northwest" — Cornell is in New York, so the citation is not just
# unverifiable but geographically incoherent. Parenthetical "(Institution,
# YYYY)" academic-style citations are a distinct fabrication shape from
# prose "a study at X" phrasing, so they need their own pattern.
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


def _find_suspicious_citation(body_html: str) -> str | None:
    """Return a snippet if body_html contains a suspiciously over-specific,
    unverifiable-looking named citation (person, institution, or study claim).
    """
    text = html_unescape(_strip_html(body_html))
    m = _SUSPICIOUS_CITATION_RE.search(text)
    if not m:
        return None
    start = max(0, m.start() - 60)
    end = min(len(text), m.end() + 60)
    return text[start:end].strip()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m openclaw",
        description="Generate and publish an evergreen article to WordPress.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    post = sub.add_parser("post", help="Generate and publish one article.")
    post.add_argument(
        "--site",
        metavar="SLUG",
        help=(
            "Select which site's prefixed env vars (SLUG_WP_BASE_URL etc.) and "
            "website_memory/{host}.md file to use. Omit to use bare WP_* env vars."
        ),
    )
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
        "--skip-review",
        action="store_true",
        help="Skip the second-pass editor agent (publish the raw first draft).",
    )
    post.add_argument(
        "--skip-deploy",
        action="store_true",
        help=(
            "Skip the Phase 5 static export + GitHub Pages push after publish. "
            "Only affects local multisite pilot subsites; other sites never deploy."
        ),
    )
    post.add_argument(
        "--skip-reddit",
        action="store_true",
        help=(
            "Skip the Reddit trend scrape entirely (Google Suggest signals still "
            "gathered). Speeds up testing runs."
        ),
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
            _activate_site(args.site)
            cfg = Config.load()
            logger.info("Config loaded.")
            site_host = urlparse(cfg.WP_BASE_URL).hostname or ""
            if not site_host:
                raise RuntimeError(
                    f"Could not parse hostname from WP_BASE_URL {cfg.WP_BASE_URL!r}."
                )
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
            category = args.category
            if not args.topic and not category:
                category = _pick_random_category(wp_categories)
                logger.info(
                    "Randomly selected category: %r (from %s)",
                    category,
                    list(wp_categories),
                )
            if args.topic:
                variation_directives, length_band = None, None
            else:
                variation_directives, length_band = _roll_variation_directives()
            if variation_directives:
                logger.info("Variation directives: %s", variation_directives)
            recent_titles = [] if args.topic else list_recent_post_titles()
            if recent_titles:
                logger.info(
                    "Loaded %d post title(s) (full catalog) for topic de-duplication.",
                    len(recent_titles),
                )
            link_candidates = list_recent_posts_for_linking()
            if link_candidates:
                logger.info("Loaded %d internal-link candidates.", len(link_candidates))
            if args.topic:
                trending_signals = None
            else:
                site_subreddits, site_seeds = _load_trends_config(site_host)
                trending_signals = gather_trending_signals(
                    subreddits=site_subreddits,
                    seeds=site_seeds,
                    category=category,
                    site_name=site_name or None,
                    reddit_enabled=not args.skip_reddit,
                )
            logger.info(
                "Calling Claude (topic=%r, category=%r).",
                args.topic,
                category,
            )
            article = generate_article(
                topic=args.topic,
                category=category,
                recent_titles=recent_titles,
                categories=wp_categories,
                site_name=site_name or None,
                site_host=site_host,
                internal_link_candidates=link_candidates,
                trending_signals=trending_signals,
                variation_directives=variation_directives,
            )

            def _generation_problem(article: dict) -> str | None:
                if recent_titles and not args.topic:
                    collision = _find_duplicate_title(article["title"], recent_titles)
                    if collision:
                        return f"title is a near-duplicate of existing post {collision!r}"
                repeat = _find_repeated_content(article["body_html"])
                if repeat:
                    return f"body_html has repeat-loop degeneration (e.g. {repeat!r} repeated)"
                closer_tic = _find_closer_tic(article["body_html"])
                if closer_tic:
                    return f"body_html has the banned echo-fragment closer tic (e.g. {closer_tic!r})"
                suspicious_citation = _find_suspicious_citation(article["body_html"])
                if suspicious_citation:
                    return f"body_html has a suspicious unverifiable-looking citation (e.g. {suspicious_citation!r})"
                return None

            problem = _generation_problem(article)
            if problem:
                logger.warning(
                    "Generated article has a problem (%s); regenerating once.", problem
                )
                article = generate_article(
                    topic=args.topic,
                    category=category,
                    recent_titles=recent_titles,
                    categories=wp_categories,
                    site_name=site_name or None,
                    site_host=site_host,
                    internal_link_candidates=link_candidates,
                    trending_signals=trending_signals,
                    variation_directives=variation_directives,
                )
                problem = _generation_problem(article)
                if problem:
                    logger.error(
                        "Regenerated article still has a problem (%s); aborting without "
                        "publishing.",
                        problem,
                    )
                    return 1

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

            if args.skip_review:
                logger.info("Editor pass skipped (--skip-review).")
            else:
                logger.info("Running second-pass editor review.")
                article = revise_article(
                    article,
                    categories=wp_categories,
                    site_host=site_host,
                    variation_directives=variation_directives,
                )
                revised_word_count = len(_strip_html(article["body_html"]).split())
                logger.info(
                    "Editor pass complete (title=%r, words ~%d -> ~%d, delta %+d).",
                    article["title"],
                    word_count,
                    revised_word_count,
                    revised_word_count - word_count,
                )
                word_count = revised_word_count

                post_revise_problem = _generation_problem(article)
                if post_revise_problem:
                    logger.error(
                        "Editor pass left/introduced a problem (%s); aborting without "
                        "publishing.",
                        post_revise_problem,
                    )
                    return 1

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

            dash_total = 0
            for field in ("body_html", "title", "excerpt", "meta_description", "seo_title", "image_alt_text"):
                value = article.get(field)
                if value:
                    article[field], n = _strip_em_dashes(value)
                    dash_total += n
            if dash_total:
                logger.warning(
                    "Replaced %d em dash(es) with commas across article fields "
                    "(model ignored the no-em-dash constraint).",
                    dash_total,
                )

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

            word_count = len(_strip_html(article["body_html"]).split())
            existing_titles = list_recent_post_titles(limit=1000)
            validation = validate_article(
                article,
                word_count=word_count,
                length_band=length_band,
                existing_titles=existing_titles,
            )
            if not validation.ok:
                dump_rejected_article(article, site_host, validation.reason or "unknown")
                logger.error(
                    "Validation gate rejected article %r: %s",
                    article["title"],
                    validation.reason,
                )
                return 1
            logger.info("Validation gate: pass (words=%d).", word_count)

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

            if args.skip_deploy:
                logger.info("Deploy step skipped (--skip-deploy).")
            elif is_deployable(args.site):
                logger.info("Starting Phase 5 deploy for %r.", args.site)
                if deploy_after_publish(args.site, article["title"]):
                    logger.info(
                        "Deployed to https://carterman82.github.io/openclaw-%s/",
                        args.site,
                    )
                else:
                    logger.warning(
                        "Deploy failed for %r (post is published; deploy owed).",
                        args.site,
                    )
            return 0
        except Exception as exc:
            logger.exception("Run failed: %s", exc)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
