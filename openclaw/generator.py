"""Article generator powered by Claude (claude-sonnet-4-6) via tool-use."""

from __future__ import annotations

from typing import Final

import anthropic

from .config import Config
from .constants import ALLOWED_CATEGORIES

MODEL: Final[str] = "claude-sonnet-4-6"
MAX_TOKENS: Final[int] = 4096


def _build_tool_schema(categories: tuple[str, ...]) -> dict:
    return {
        "name": "submit_article",
        "description": "Submit the generated article to be published.",
        "input_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "title": {"type": "string"},
                "body_html": {"type": "string"},
                "category": {"type": "string", "enum": list(categories)},
                "tags": {"type": "array", "items": {"type": "string"}},
                "excerpt": {"type": "string"},
                "slug": {"type": "string"},
                "focus_keyphrase": {"type": "string"},
            },
            "required": ["title", "body_html", "category", "tags", "excerpt", "slug", "focus_keyphrase"],
        },
    }


def _build_system_prompt(categories: tuple[str, ...]) -> str:
    return (
        "You are a careful nonfiction explainer writing for a small evergreen blog. "
        "Every article you produce MUST:\n"
        "- be 700-1200 words of body content (not counting the title)\n"
        "- be EVERGREEN: never use phrases like 'this week', 'yesterday', "
        "'currently', 'recently', 'now', or 'today'; never reference current events, "
        "specific years close to the present, or anything that will age out. The post "
        "must read just as well a year or five years from now.\n"
        "- return the body as HTML in `body_html`: use <p>, <h2>, <h3>, <ul>, <ol>, "
        "<li>, <strong>, <em>. Do not use Markdown.\n"
        f"- assign exactly one category from this closed list: "
        f"{', '.join(categories)}. Never invent new categories.\n"
        "- supply 3 to 5 short tags: lowercase, single-word or hyphenated.\n"
        "- write an `excerpt`: 150-160 characters, includes the focus keyphrase, "
        "gives a clear reason to click. No 'In this article…' opener.\n"
        "- choose a `focus_keyphrase`: 2-4 words a reader would type into Google "
        "to find this article. Must appear naturally in the title and body.\n"
        "- write a `slug`: the URL path — 3-6 lowercase words joined by hyphens, "
        "no stop words (a, the, of, in, and…), contains the focus keyphrase.\n\n"
        "Submit the article by calling the submit_article tool."
    )


def _build_user_message(
    topic: str | None,
    category: str | None,
    site_name: str | None = None,
) -> str:
    if site_name:
        parts = [f"Write one evergreen article suited to the audience of '{site_name}'."]
    else:
        parts = ["Write one evergreen article."]
    if topic:
        parts.append(f"Topic: {topic}.")
    else:
        if site_name:
            parts.append(
                f"Pick the topic yourself. Choose something concrete, surprising, "
                f"and not time-sensitive that a fan of '{site_name}' would find valuable."
            )
        else:
            parts.append(
                "Pick the topic yourself. Choose something concrete, surprising, "
                "and not time-sensitive."
            )
    if category:
        parts.append(f"Assign category exactly: {category}.")
    else:
        parts.append("Choose the best-fitting category from the allowed list.")
    return " ".join(parts)


def _build_avoidance_message(recent_titles: list[str] | None) -> str:
    if not recent_titles:
        return ""
    title_lines = "\n".join(f"- {title}" for title in recent_titles)
    return (
        "\n\nDo not write about the same subject, object, example, or angle as "
        "any of these recent posts. Pick a clearly different topic:\n"
        f"{title_lines}"
    )


def generate_article(
    topic: str | None = None,
    category: str | None = None,
    recent_titles: list[str] | None = None,
    categories: tuple[str, ...] | None = None,
    site_name: str | None = None,
) -> dict:
    """Generate one evergreen article via Claude (sonnet 4.6).

    Returns a dict with keys: title, body_html, category, tags.
    `categories` overrides ALLOWED_CATEGORIES if provided.
    `site_name` steers topic selection toward the site's theme.
    """
    effective_categories = categories or ALLOWED_CATEGORIES
    if category and category not in effective_categories:
        raise ValueError(
            f"category must be one of {effective_categories}, got {category!r}"
        )
    cfg = Config.load()
    client = anthropic.Anthropic(api_key=cfg.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=_build_system_prompt(effective_categories),
        messages=[
            {
                "role": "user",
                "content": (
                    _build_user_message(topic, category, site_name)
                    + _build_avoidance_message(recent_titles)
                ),
            }
        ],
        tools=[_build_tool_schema(effective_categories)],
        tool_choice={"type": "tool", "name": "submit_article"},
    )

    article = None
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "submit_article":
            article = dict(block.input)
            break
    if article is None:
        raise RuntimeError(
            f"Claude did not return a submit_article tool call. "
            f"stop_reason={response.stop_reason!r}"
        )
    if article["category"] not in effective_categories:
        raise ValueError(
            f"Model returned disallowed category {article['category']!r}; "
            f"allowed: {effective_categories}"
        )
    return article


# ---------------------------------------------------------------------------
# OpenAI gpt-4o implementation — commented out on 2026-06-09 per user request
# after the OpenAI project hit `insufficient_quota`. Preserved here so the
# revert is a re-uncomment, not a rewrite. See PLAN.md §4 for swap history.
# ---------------------------------------------------------------------------
# import json
# from openai import OpenAI
#
# _OPENAI_MODEL: Final[str] = "gpt-4o"
# _OPENAI_RESPONSE_SCHEMA: Final[dict] = {
#     "type": "object",
#     "additionalProperties": False,
#     "properties": {
#         "title": {"type": "string"},
#         "body_html": {"type": "string"},
#         "category": {"type": "string", "enum": list(ALLOWED_CATEGORIES)},
#         "tags": {"type": "array", "items": {"type": "string"}},
#     },
#     "required": ["title", "body_html", "category", "tags"],
# }
#
# def generate_article_openai(topic=None, category=None):
#     cfg = Config.load()
#     if not cfg.OPENAI_API_KEY:
#         raise RuntimeError("OPENAI_API_KEY not set in .env")
#     client = OpenAI(api_key=cfg.OPENAI_API_KEY)
#     response = client.chat.completions.create(
#         model=_OPENAI_MODEL,
#         messages=[
#             {"role": "system", "content": _SYSTEM_PROMPT},
#             {"role": "user", "content": _build_user_message(topic, category)},
#         ],
#         response_format={
#             "type": "json_schema",
#             "json_schema": {
#                 "name": "Article",
#                 "strict": True,
#                 "schema": _OPENAI_RESPONSE_SCHEMA,
#             },
#         },
#     )
#     article = json.loads(response.choices[0].message.content)
#     if article["category"] not in ALLOWED_CATEGORIES:
#         raise ValueError(
#             f"Model returned disallowed category {article['category']!r}"
#         )
#     return article
