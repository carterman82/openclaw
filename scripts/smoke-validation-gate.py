"""Smoke test for openclaw.validation.validate_article (Phase 6 Step 6.1).

Feeds the validator real defective bodies pulled from the 2026-07-19
five-subsite content audit (saved under scripts/fixtures/phase6-audit/) plus
synthetic edge cases, and asserts each one is rejected for the expected
reason. Also confirms known-good bodies pass. Does not touch any WordPress
site or LLM provider — pure function tests against validate_article.

Usage: python scripts/smoke-validation-gate.py
Exit 0 on all assertions passing, 1 otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openclaw.validation import validate_article  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "phase6-audit"

_FAILURES: list[str] = []


def _check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        _FAILURES.append(name)


def _article(title: str, body_html: str, **overrides: str) -> dict:
    base = {
        "title": title,
        "body_html": body_html,
        "excerpt": "",
        "meta_description": "",
        "seo_title": "",
    }
    base.update(overrides)
    return base


def main() -> int:
    # --- Real defect fixtures from the 2026-07-19 audit --------------------
    leak_body = (FIXTURES_DIR / "reasoning-leak-boardgames-18.html").read_text(encoding="utf-8")
    result = validate_article(
        _article("Why Your Family Plays Carcassonne Wrong", leak_body),
        word_count=6210, length_band=(1600, 2000), existing_titles=[],
    )
    _check(
        "boardgames #18 (reasoning leak) rejected",
        not result.ok and result.reason and "leak" in result.reason,
        result.reason or "<no reason>",
    )

    truncated_body = (FIXTURES_DIR / "truncated-markdown-coffee-29.html").read_text(encoding="utf-8")
    result = validate_article(
        _article("Surface Tension Is the Real Reason", truncated_body),
        word_count=416, length_band=(900, 1300), existing_titles=[],
    )
    _check(
        "coffee #29 (truncated + markdown) rejected",
        not result.ok,
        result.reason or "<no reason>",
    )

    missing_tag_body = (FIXTURES_DIR / "missing-closing-tag-gardening-51.html").read_text(encoding="utf-8")
    result = validate_article(
        _article("Fungus Gnats Are Not the Problem", missing_tag_body),
        word_count=1853, length_band=(1600, 2000), existing_titles=[],
    )
    _check(
        "gardening #51 (missing closing </p>) rejected",
        not result.ok and result.reason and "closing block tag" in result.reason,
        result.reason or "<no reason>",
    )

    good_body = (FIXTURES_DIR / "known-good-dogs-21.html").read_text(encoding="utf-8")
    result = validate_article(
        _article("Why Dog Licks Face: The Puppyhood Signal Your Dog Never Outgrew", good_body),
        word_count=1579, length_band=(1300, 1700), existing_titles=["Some Other Post"],
    )
    _check("dogs #21 (known-good) passes", result.ok, result.reason or "")

    good_boardgames = (FIXTURES_DIR / "known-good-boardgames-24.html").read_text(encoding="utf-8")
    result = validate_article(
        _article("King of Tokyo: Why Your Family Plays It Wrong (And What the Dice Actually Mean)", good_boardgames),
        word_count=717, length_band=(700, 900), existing_titles=["Some Other Post"],
    )
    _check("boardgames #24 (known-good) passes", result.ok, result.reason or "")

    good_gardening = (FIXTURES_DIR / "known-good-gardening-41.html").read_text(encoding="utf-8")
    result = validate_article(
        _article("The Mulch Myth: Why Fresh Wood Chips Kill Your Roses (And What to Use Instead)", good_gardening),
        word_count=2165, length_band=(1900, 2300), existing_titles=["Some Other Post"],
    )
    _check("gardening #41 (known-good) passes", result.ok, result.reason or "")

    # These two really-published articles are about AI/prompting and use the
    # phrase "the prompt" in ordinary sentences — the original marker list
    # (which included a bare "the prompt" check) false-positived on both.
    # They must NOT be rejected now that marker is removed.
    # length_band=None here: these are real historical posts and we don't know
    # which of the three per-run bands was rolled when they were generated,
    # so we only check the absolute floor/ceiling (both word counts clear it).
    for fixture_name, title, wc in (
        ("false-positive-check-techtools-1470.html",
         "AI Temperature Settings Decide Output Quality More Than Your Prompt Does", 1297),
        ("false-positive-check-techtools-1402.html",
         "AI Writing Tools Sound Like AI Because You're Using Them Backward", 2314),
    ):
        body = (FIXTURES_DIR / fixture_name).read_text(encoding="utf-8")
        result = validate_article(
            _article(title, body),
            word_count=wc, length_band=None, existing_titles=["Some Other Post"],
        )
        _check(f"{fixture_name} (legit AI-topic article) passes", result.ok, result.reason or "")

    # --- Synthetic edge cases -----------------------------------------------
    unbalanced = "<p>Opening paragraph with no matching close.<p>Second paragraph, also unclosed.</p>"
    result = validate_article(
        _article("Unbalanced Tags Test", unbalanced),
        word_count=1000, length_band=None, existing_titles=[],
    )
    _check(
        "synthetic unbalanced <p> tags rejected",
        not result.ok and result.reason and "unbalanced" in result.reason,
        result.reason or "<no reason>",
    )

    dup_body = "<p>" + ("word " * 900) + "</p>"
    result = validate_article(
        _article("Why Your Container Potting Mix Is Killing Strawberries", dup_body),
        word_count=900, length_band=None,
        existing_titles=["Why Your Container Potting Mix Is Killing Strawberries (And What to Use Instead)"],
    )
    _check(
        "synthetic duplicate title rejected",
        not result.ok and result.reason and "collides" in result.reason,
        result.reason or "<no reason>",
    )

    short_body = "<p>" + ("word " * 100) + "</p>"
    result = validate_article(
        _article("Too Short Test", short_body),
        word_count=100, length_band=(900, 1300), existing_titles=[],
    )
    _check(
        "synthetic out-of-band-short length rejected",
        not result.ok and result.reason and "below the floor" in result.reason,
        result.reason or "<no reason>",
    )

    long_body = "<p>" + ("word " * 3500) + "</p>"
    result = validate_article(
        _article("Too Long Test", long_body),
        word_count=3500, length_band=None, existing_titles=[],
    )
    _check(
        "synthetic out-of-band-long length rejected",
        not result.ok and result.reason and "above the ceiling" in result.reason,
        result.reason or "<no reason>",
    )

    print()
    if _FAILURES:
        print(f"{len(_FAILURES)} check(s) FAILED: {_FAILURES}")
        return 1
    print("All validation-gate checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
