"""
verify-seo.py — programmatic Yoast SEO + Readability checker for openclaw posts.

Usage:
    python scripts/verify-seo.py <post_id>
    python scripts/verify-seo.py --latest

Reads the post and its featured media via the WP REST API, then asserts every
Yoast SEO condition (Y1-Y10) and Readability condition (Y11-Y12) that the
openclaw agent can affect. Prints a PASS/FAIL/WARN/SKIP report and exits 1 on
any FAIL.

PASS  — condition met.
WARN  — condition partially met; Yoast would show orange, not red.
FAIL  — condition not met; Yoast would show red.
SKIP  — not programmatically checkable (requires manual WP Admin check).
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import requests

# Add the project root to sys.path so we can import openclaw.config.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openclaw.config import Config

# ---------------------------------------------------------------------------
# Yoast's published English transition-word list (subset that covers single
# words and short phrases likely to appear at the start of or within a sentence).
# Source: https://yoast.com/transition-words/ (accessed 2026-06-29).
# ---------------------------------------------------------------------------
_TRANSITION_WORDS: frozenset[str] = frozenset({
    "above all", "accordingly", "additionally", "admittedly", "after",
    "after all", "after that", "afterward", "afterwards", "albeit",
    "all in all", "all of a sudden", "all things considered", "also",
    "although", "altogether", "and", "and then", "another",
    "as a consequence", "as a result", "as a rule", "as if",
    "as long as", "as opposed to", "as soon as", "as though",
    "as well as", "at any rate", "at first", "at last", "at least",
    "at length", "at the same time", "at this point", "because",
    "because of this", "before", "beforehand", "besides", "both",
    "but", "by all means", "by comparison", "by contrast",
    "by the same token", "certainly", "clearly", "comparatively",
    "consequently", "conversely", "correspondingly", "despite",
    "due to", "during", "equally", "equally important", "especially",
    "eventually", "evidently", "explicitly", "finally", "first",
    "for", "for example", "for instance", "for one thing",
    "for that reason", "for this purpose", "for this reason",
    "from this point on", "furthermore", "generally", "given that",
    "hence", "here", "hereafter", "however", "if", "if only",
    "importantly", "in addition", "in any case", "in any event",
    "in brief", "in comparison", "in conclusion", "in contrast",
    "in detail", "in effect", "in fact", "in general", "in other words",
    "in particular", "in short", "in spite of", "in sum",
    "in summary", "in the end", "in the meantime", "in the same way",
    "in turn", "indeed", "instead", "likewise", "meanwhile",
    "moreover", "most importantly", "nevertheless", "next",
    "nonetheless", "nor", "not only", "not to mention",
    "notwithstanding", "now that", "obviously", "of course",
    "on account of", "on balance", "on the contrary", "on the other hand",
    "on the whole", "once", "only", "otherwise", "overall",
    "particularly", "perhaps", "plus", "previously", "provided that",
    "rather", "regardless", "second", "similarly", "since",
    "so", "so that", "specifically", "still", "subsequently",
    "such as", "than", "that is", "that is to say", "then",
    "therefore", "thereafter", "thereby", "third", "though",
    "thus", "to begin with", "to clarify", "to conclude",
    "to illustrate", "to put it another way", "to start with",
    "to sum up", "to summarize", "to that end", "together with",
    "too", "ultimately", "undoubtedly", "unless", "until",
    "when", "whenever", "whereas", "whether", "while",
    "with this in mind", "yet",
})

# ---------------------------------------------------------------------------
# HTML utilities (mirrors publisher._plain_text logic)
# ---------------------------------------------------------------------------

def _strip_html(raw: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", raw)).strip()


class _FirstParagraphExtractor(HTMLParser):
    """Extract text content of the first <p> element."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_p = False
        self._depth = 0
        self.text: str = ""
        self.done: bool = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if self.done:
            return
        if tag == "p":
            if not self._in_p:
                self._in_p = True
                self._depth = 1
            else:
                self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self.done or not self._in_p:
            return
        if tag == "p":
            self._depth -= 1
            if self._depth <= 0:
                self._in_p = False
                self.done = True

    def handle_data(self, data: str) -> None:
        if self._in_p and not self.done:
            self.text += data


def _first_paragraph_text(body_html: str) -> str:
    p = _FirstParagraphExtractor()
    p.feed(body_html)
    return p.text.strip()


def _sentences(plain_text: str) -> list[str]:
    """Tokenize text into sentences, ignoring very short fragments."""
    parts = re.split(r"[.!?]+\s+", plain_text.strip())
    return [s.strip() for s in parts if len(s.split()) >= 3]


def _first_word(sentence: str) -> str:
    words = sentence.split()
    return words[0].lower() if words else ""


# ---------------------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------------------

_RESULTS: list[tuple[str, str, str]] = []  # (status, label, detail)


def _record(status: str, label: str, detail: str = "") -> None:
    _RESULTS.append((status, label, detail))


def _check(condition: bool, label: str, fail_detail: str = "", warn: bool = False) -> bool:
    if condition:
        _record("PASS", label)
        return True
    _record("WARN" if warn else "FAIL", label, fail_detail)
    return False


# ---------------------------------------------------------------------------
# Main checks
# ---------------------------------------------------------------------------

def run_checks(post_id: int) -> int:
    """Run all checks against post_id. Returns exit code (0=ok, 1=fail)."""
    cfg = Config.load()
    auth = (cfg.WP_USERNAME, cfg.WP_APP_PASSWORD)
    base = cfg.WP_BASE_URL.rstrip("/")

    # Fetch the post.
    r = requests.get(f"{base}/wp-json/wp/v2/posts/{post_id}?context=edit", auth=auth, timeout=30)
    if not r.ok:
        print(f"ERROR: GET post/{post_id} returned {r.status_code}: {r.text[:200]}")
        return 1
    post = r.json()

    title = _strip_html(post.get("title", {}).get("rendered", ""))
    slug = post.get("slug", "")
    body_html = post.get("content", {}).get("rendered", "")
    body_text = _strip_html(body_html)
    meta = post.get("meta", {})
    featured_media_id = post.get("featured_media") or 0

    # Fetch featured media alt text (if any).
    alt_text = ""
    if featured_media_id:
        rm = requests.get(f"{base}/wp-json/wp/v2/media/{featured_media_id}", auth=auth, timeout=15)
        if rm.ok:
            alt_text = rm.json().get("alt_text", "")

    # --- Routing: did Yoast meta persist? ---
    focuskw    = meta.get("_yoast_wpseo_focuskw")
    metadesc   = meta.get("_yoast_wpseo_metadesc")
    seo_title  = meta.get("_yoast_wpseo_title")

    print(f"\nSEO Verification: post {post_id} — \"{title}\"")
    print("=" * 70)
    print("\nRouting (REST meta round-trip)")
    for label, val, key in [
        ("_yoast_wpseo_focuskw ", focuskw,   "_yoast_wpseo_focuskw"),
        ("_yoast_wpseo_metadesc", metadesc,  "_yoast_wpseo_metadesc"),
        ("_yoast_wpseo_title   ", seo_title, "_yoast_wpseo_title"),
    ]:
        if val is None:
            print(f"  [WARN] {label} = <absent> (plugin not installed — install openclaw-seo-meta to enable REST writes)")
            _record("WARN", f"Routing: {key}", "absent — install openclaw-seo-meta plugin (see demo/)")
        elif val == "":
            print(f"  [WARN] {label} = '' (registered but empty — plugin installed, value not written)")
            _record("WARN", f"Routing: {key}", "registered but empty")
        else:
            print(f"  [PASS] {label} = {val!r}")
            _record("PASS", f"Routing: {key}")

    # The keyphrase to use for content checks: prefer the stored Yoast value,
    # fall back to inferring from the slug (best available without the plugin).
    keyphrase = (focuskw or "").strip()
    if not keyphrase:
        # Infer from slug. Slugs start with the keyphrase but may have extra words
        # ("maine-coon-size-genetics-explained" → keyphrase is "maine coon size").
        # Try longest prefix of 2-4 slug words that appears verbatim in the body.
        slug_words = slug.split("-")
        keyphrase = slug.replace("-", " ").strip()  # full slug as fallback
        body_lower = body_text.lower()
        for n in range(min(4, len(slug_words)), 1, -1):
            candidate = " ".join(slug_words[:n])
            if candidate.lower() in body_lower:
                keyphrase = candidate
                break

    print(f"\n  (using keyphrase for content checks: {keyphrase!r})\n")

    # --- Yoast SEO conditions (Y1–Y10) ---
    print("Yoast SEO (10 conditions)")

    plugin_absent = focuskw is None  # True = no plugin, REST keys not registered

    # Y1 — focus keyphrase set
    if plugin_absent:
        _record("SKIP", "Y1  Focus keyphrase set and non-empty", "plugin not installed — keyphrase unreadable via REST")
    else:
        _check(bool(focuskw), "Y1  Focus keyphrase set and non-empty", "empty")

    # Y2 — keyphrase in introduction (first sentence of first <p>)
    first_p = _first_paragraph_text(body_html)
    first_sentence = re.split(r"[.!?]", first_p)[0] if first_p else ""
    y2 = keyphrase and keyphrase.lower() in first_sentence.lower()
    _check(y2, "Y2  Keyphrase in introduction (first sentence of first <p>)",
           f"first sentence: {first_sentence[:120]!r}")

    # Y3 — keyphrase at start of SEO title
    # Without the plugin we can only see the post title, not the Yoast seo_title field.
    # The generator requires seo_title to start with keyphrase, but we can't verify
    # it here without the plugin → SKIP to avoid false FAILs.
    if plugin_absent:
        _record("SKIP", "Y3  Keyphrase at start of SEO title",
                "plugin not installed — seo_title field unreadable via REST")
    else:
        y3 = keyphrase and (seo_title or "").lower().startswith(keyphrase.lower())
        _check(y3, "Y3  Keyphrase at start of SEO title",
               f"seo_title: {seo_title!r}, keyphrase: {keyphrase!r}")

    # Y4 — SEO title <= 60 chars.
    # With plugin: check actual seo_title. Without: proxy with post title (seo_title is
    # a separate shorter field, so a long post title is a WARN, not a FAIL).
    effective_seo_title = seo_title or title
    title_len = len(effective_seo_title)
    if title_len <= 60:
        _record("PASS", f"Y4  SEO title <=60 chars ({title_len})")
    elif seo_title is not None:
        _record("FAIL", f"Y4  SEO title <=60 chars ({title_len})",
                f"length {title_len} > 60: {seo_title!r}")
    else:
        _record("WARN", f"Y4  Post title {title_len} chars (seo_title <=60 unverifiable without plugin)",
                f"post title: {title!r}")

    # Y5 — keyphrase in slug
    y5 = keyphrase and keyphrase.lower().replace(" ", "-") in slug.lower()
    if not y5:
        # Also check if all keyphrase words appear somewhere in the slug
        y5 = keyphrase and all(w in slug.lower() for w in keyphrase.lower().split())
    _check(y5, "Y5  Keyphrase in slug",
           f"slug: {slug!r}, keyphrase: {keyphrase!r}")

    # Y6 — keyphrase in featured image alt text
    if not featured_media_id:
        _record("WARN", "Y6  Keyphrase in image alt_text", "no featured image attached")
    else:
        y6 = keyphrase and keyphrase.lower() in alt_text.lower()
        _check(y6, "Y6  Keyphrase in image alt_text",
               f"alt: {alt_text!r}")

    # Y7 — meta description set
    if plugin_absent:
        _record("SKIP", "Y7  Meta description set and non-empty", "plugin not installed — meta unreadable via REST")
    else:
        _check(bool(metadesc), "Y7  Meta description set and non-empty", "empty")

    # Y8 — keyphrase in meta description
    if plugin_absent:
        _record("SKIP", "Y8  Keyphrase in meta description", "plugin not installed — meta unreadable via REST")
    else:
        y8 = keyphrase and keyphrase.lower() in (metadesc or "").lower()
        _check(y8, "Y8  Keyphrase in meta description",
               f"meta desc: {(metadesc or '')[:100]!r}")

    # Y9 — previously used keyphrase (requires manual check)
    _record("SKIP", "Y9  Previously-used keyphrase check", "requires manual WP Admin check")

    # Y10 — keyphrase length (2–4 words is green; 1 or 5–6 is orange; 0/7+ is red)
    kw_words = len(keyphrase.split()) if keyphrase else 0
    if kw_words == 0:
        _record("FAIL", f"Y10 Keyphrase length ({kw_words} words)", "no keyphrase")
    elif 2 <= kw_words <= 4:
        _record("PASS", f"Y10 Keyphrase length ({kw_words} words)")
    else:
        _record("WARN", f"Y10 Keyphrase length ({kw_words} words)", "Yoast prefers 2–4 words")

    # --- Readability (Y11–Y12) ---
    print("\nYoast Readability (2 conditions)")
    sentences = _sentences(body_text)

    # Y11 — no 3+ consecutive same-start sentences
    max_run = 1
    run = 1
    worst_word = ""
    for i in range(1, len(sentences)):
        if _first_word(sentences[i]) == _first_word(sentences[i - 1]) and _first_word(sentences[i]):
            run += 1
            if run > max_run:
                max_run = run
                worst_word = _first_word(sentences[i])
        else:
            run = 1
    _check(max_run < 3, f"Y11 No 3+ consecutive same-start sentences (max run: {max_run})",
           f"word {worst_word!r} started {max_run} sentences in a row")

    # Y12 — >=30% of sentences contain a transition word
    if not sentences:
        _record("SKIP", "Y12 Transition words", "no sentences found")
    else:
        def _has_transition(s: str) -> bool:
            sl = s.lower()
            return any(tw in sl for tw in _TRANSITION_WORDS)

        with_tw = sum(1 for s in sentences if _has_transition(s))
        pct = with_tw / len(sentences) * 100
        if pct >= 30:
            _record("PASS", f"Y12 Transition words: {pct:.1f}% (>=30%)")
        elif pct >= 20:
            _record("WARN", f"Y12 Transition words: {pct:.1f}% (target >=30%)")
        else:
            _record("FAIL", f"Y12 Transition words: {pct:.1f}% (target >=30%)")

    # --- Print per-check results ---
    print()
    for status, label, detail in _RESULTS:
        line = f"  [{status:<4}] {label}"
        if detail:
            line += f"\n              {detail}"
        print(line)

    # --- Summary ---
    counts = {s: sum(1 for r in _RESULTS if r[0] == s) for s in ("PASS", "FAIL", "WARN", "SKIP")}
    print(f"\nSummary: {counts['PASS']} PASS / {counts['FAIL']} FAIL / "
          f"{counts['WARN']} WARN / {counts['SKIP']} SKIP")

    if counts["FAIL"]:
        print("Exit: 1 (FAIL)")
        return 1
    print("Exit: 0 (OK)")
    return 0


def _latest_post_id(cfg: Config) -> int:
    auth = (cfg.WP_USERNAME, cfg.WP_APP_PASSWORD)
    r = requests.get(
        f"{cfg.WP_BASE_URL.rstrip('/')}/wp-json/wp/v2/posts",
        params={"per_page": 1, "orderby": "date", "order": "desc",
                "status": "any", "author_name": cfg.WP_USERNAME},
        auth=auth,
        timeout=15,
    )
    posts = r.json() if r.ok else []
    if not posts:
        # Fall back without author filter
        r2 = requests.get(
            f"{cfg.WP_BASE_URL.rstrip('/')}/wp-json/wp/v2/posts",
            params={"per_page": 1, "orderby": "date", "order": "desc", "status": "any"},
            auth=auth, timeout=15,
        )
        posts = r2.json() if r2.ok else []
    if not posts:
        print("ERROR: could not find any posts.")
        sys.exit(1)
    return posts[0]["id"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Yoast SEO conditions for an openclaw post.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("post_id", nargs="?", type=int, help="WordPress post ID")
    group.add_argument("--latest", action="store_true", help="Use the most recent post")
    args = parser.parse_args()

    cfg = Config.load()
    post_id = args.post_id if args.post_id else _latest_post_id(cfg)
    return run_checks(post_id)


if __name__ == "__main__":
    sys.exit(main())
