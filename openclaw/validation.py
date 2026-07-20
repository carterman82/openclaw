"""Deterministic pre-publish validation gate for generated articles.

See PLAN.md Phase 6 Step 6.1. `validate_article` runs after revision and
HTML sanitization but before `publish_post()`. Unlike main.py's other
post-processors (em-dash strip, anchor validation, external-link attrs)
which repair content in place, a failure here means REJECT: main.py aborts
the run with no publish, so the Phase 4 wrapper's retry logic gets a fresh
generation attempt rather than a scheduled run silently publishing broken
content.

Every check here traces back to a real defect found in the 2026-07-19
five-subsite content audit (see PLAN.md Phase 6 intro table): the local
model, when unsupervised, has published its own reasoning monologue, raw
markdown, truncated/malformed HTML, wildly out-of-band lengths, and
duplicate topics under fresh titles.
"""

from __future__ import annotations

import difflib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    reason: str | None = None


# --- Reasoning-leak / internal-file-name markers ----------------------------
# Every phrase here was observed verbatim in a real leaked article (boardgames
# #18) or names an internal artifact (a prompt file, a tool-schema field) that
# can never legitimately appear in published body copy. A single hit is
# sufficient to reject — these are not phrases that occur in normal prose.
# Deliberately excludes generic phrases that plausibly occur in legitimate
# prose on an AI/tech-tools site — confirmed false positives during Step 6.1
# fixture testing: "the prompt" (techtools #1470/#1402, ordinary sentences
# about prompt engineering), "system prompt" (#1402, "a good system prompt"
# as a real technical term), and "tool_choice"/"input_schema" (plausible in
# an article about building AI agents/tool-calling APIs). Kept markers are
# either verbatim from the real boardgames #18 leak or names of internal
# artifacts (Instructions/*.md files, the submit_article tool name) that a
# real article body has no legitimate reason to mention at all.
_LEAK_MARKERS: tuple[str, ...] = (
    "[output generation]",
    "[final check",
    "[output ",
    "self-correction",
    "self-verification",
    "i need to make sure the body",
    "i will output it now",
    "i will now generate the json",
    "the json structure is correct",
    "all constraints checked",
    "output matches schema",
    "no extra text. only json",
    "as an ai language model",
    "as an ai,",
    "as an ai assistant",
    "submit_article",
    "style.md",
    "topic.md",
    "editor.md",
    "description.md",
    "image_generator.md",
    "word count requirement",
)


def _find_leak_marker(text: str) -> str | None:
    lowered = text.lower()
    for marker in _LEAK_MARKERS:
        if marker in lowered:
            return marker
    return None


# --- Markdown leakage --------------------------------------------------------
# The article body must be pure HTML (STYLE.md / generator.py schema
# requirement). Observed real leak: coffee #29 had a `## Heading` markdown
# heading typed directly inside a `<p>` tag instead of `<h2>`.
_MD_HEADING_RE = re.compile(r"<p[^>]*>\s*#{1,6}\s", re.IGNORECASE)
_MD_HEADING_LINE_RE = re.compile(r"^#{1,6}\s", re.MULTILINE)
_MD_FENCE_RE = re.compile(r"```")
_MD_BOLD_RE = re.compile(r"\*\*[^*]+\*\*")


def _find_markdown_leak(body_html: str) -> str | None:
    if _MD_HEADING_RE.search(body_html) or _MD_HEADING_LINE_RE.search(body_html):
        return "markdown heading (# ) found in body"
    if _MD_FENCE_RE.search(body_html):
        return "markdown code fence (```) found in body"
    if _MD_BOLD_RE.search(body_html):
        return "markdown bold (**text**) found in body"
    return None


# --- Truncation / malformed HTML --------------------------------------------
_BLOCK_TAGS: tuple[str, ...] = ("p", "h2", "h3", "h4", "ul", "ol", "li", "blockquote", "pre")
_CLOSING_BLOCK_RE = re.compile(
    r"</(?:p|h2|h3|h4|ul|ol|li|blockquote|pre)>\s*$", re.IGNORECASE
)


def _find_malformed_html(body_html: str) -> str | None:
    stripped = body_html.strip()
    if not stripped:
        return "body_html is empty"
    if not _CLOSING_BLOCK_RE.search(stripped):
        return "body does not end with a closing block tag (looks truncated)"
    for tag in _BLOCK_TAGS:
        opens = len(re.findall(rf"<{tag}(?:\s[^>]*)?>", stripped, re.IGNORECASE))
        closes = len(re.findall(rf"</{tag}>", stripped, re.IGNORECASE))
        if opens != closes:
            return f"unbalanced <{tag}> tags ({opens} open, {closes} close)"
    if re.search(r"<h1[\s>]", stripped, re.IGNORECASE):
        return "body contains an <h1> (only h2/h3/h4 allowed)"
    return None


# --- Length band -------------------------------------------------------------
# Absolute bounds regardless of the per-run variation directive: catches both
# the 416-word coffee #29 truncation and the 6,210-word boardgames #18
# double-article fusion.
_ABSOLUTE_MIN_WORDS = 700
_ABSOLUTE_MAX_WORDS = 3000
_BAND_TOLERANCE = 300


def _find_length_problem(word_count: int, length_band: tuple[int, int] | None) -> str | None:
    low, high = _ABSOLUTE_MIN_WORDS, _ABSOLUTE_MAX_WORDS
    if length_band:
        band_low, band_high = length_band
        low = max(_ABSOLUTE_MIN_WORDS, band_low - _BAND_TOLERANCE)
        high = min(_ABSOLUTE_MAX_WORDS, band_high + _BAND_TOLERANCE)
    if word_count < low:
        return f"word count {word_count} is below the floor of {low}"
    if word_count > high:
        return f"word count {word_count} is above the ceiling of {high}"
    return None


# --- Duplicate title (against the FULL catalog, not just recent-N) ---------
# The dup-guard main.py already runs pre-generation only checks the last N
# titles used for prompt steering; this checks against every title on the
# site so an old post from months back still blocks a repeat.
_TITLE_COLLISION_RATIO = 0.80


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9\s]", "", title.lower()).strip()


def find_title_collision(title: str, existing_titles: list[str]) -> str | None:
    """Return the colliding existing title if `title` is an exact or near-exact repeat."""
    normalized = normalize_title(title)
    if not normalized:
        return None
    for existing in existing_titles:
        existing_normalized = normalize_title(existing)
        if not existing_normalized:
            continue
        if normalized == existing_normalized:
            return existing
        ratio = difflib.SequenceMatcher(None, normalized, existing_normalized).ratio()
        if ratio >= _TITLE_COLLISION_RATIO:
            return existing
    return None


def validate_article(
    article: dict,
    *,
    word_count: int,
    length_band: tuple[int, int] | None,
    existing_titles: list[str],
) -> ValidationResult:
    """Run every Step 6.1 check. Returns the first failure found, or ok=True."""
    body = article.get("body_html") or ""
    title = article.get("title") or ""

    checked_fields = {
        "title": title,
        "body_html": body,
        "excerpt": article.get("excerpt") or "",
        "meta_description": article.get("meta_description") or "",
        "seo_title": article.get("seo_title") or "",
    }
    for field_name, value in checked_fields.items():
        marker = _find_leak_marker(value)
        if marker:
            return ValidationResult(
                False, f"reasoning/internal-artifact leak in {field_name}: matched {marker!r}"
            )

    md_problem = _find_markdown_leak(body)
    if md_problem:
        return ValidationResult(False, md_problem)

    html_problem = _find_malformed_html(body)
    if html_problem:
        return ValidationResult(False, html_problem)

    length_problem = _find_length_problem(word_count, length_band)
    if length_problem:
        return ValidationResult(False, length_problem)

    collision = find_title_collision(title, existing_titles)
    if collision:
        return ValidationResult(False, f"title collides with existing post {collision!r}")

    return ValidationResult(True)


def dump_rejected_article(article: dict, site_host: str, reason: str) -> None:
    """Persist a rejected article's full JSON for forensic review.

    Fire-and-forget: any error while writing the dump is logged and
    swallowed so it never masks the real rejection with a write failure.
    """
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
        safe_host = re.sub(r"[^a-z0-9.-]", "_", site_host.lower()) or "unknown"
        path = LOGS_DIR / f"rejected-{timestamp}-{safe_host}.json"
        payload = {"reason": reason, "site_host": site_host, "article": article}
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        logger.info("Rejected article dumped to %s", path)
    except Exception as exc:  # noqa: BLE001 - forensics must never break error reporting
        logger.warning("Failed to write rejected-article diagnostics dump: %s", exc)
