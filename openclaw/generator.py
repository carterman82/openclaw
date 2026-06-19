"""Article generator powered by Claude (claude-sonnet-4-6) via tool-use."""

from __future__ import annotations

from typing import Final

import anthropic

from .config import Config
from .constants import ALLOWED_CATEGORIES

MODEL: Final[str] = "claude-sonnet-4-6"
MAX_TOKENS: Final[int] = 4096

_TOOL_SCHEMA: Final[dict] = {
    "name": "submit_article",
    "description": "Submit the generated article to be published.",
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": "string"},
            "body_html": {"type": "string"},
            "category": {"type": "string", "enum": list(ALLOWED_CATEGORIES)},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["title", "body_html", "category", "tags"],
    },
}

_SYSTEM_PROMPT: Final[str] = (
    "You are a careful nonfiction explainer writing for a small evergreen blog. "
    "Every article you produce MUST:\n"
    "- be 700-1200 words of body content (not counting the title)\n"
    "- be EVERGREEN: never use phrases like 'this week', 'yesterday', "
    "'currently', 'recently', 'now', or 'today'; never reference current events, "
    "specific years close to the present, or anything that will age out. The post "
    "must read just as well a year or five years from now.\n"
    "- return the body as HTML in `body_html`: use <p>, <h2>, <h3>, <ul>, <ol>, "
    "<li>, <strong>, <em>. Do not use Markdown.\n"
    "- assign exactly one category from this closed list: "
    "Science, History, How Things Work, Concepts. Never invent new categories.\n"
    "- supply 3 to 5 short tags: lowercase, single-word or hyphenated.\n\n"
    "Submit the article by calling the submit_article tool."
)


def _build_user_message(topic: str | None, category: str | None) -> str:
    parts = ["Write one evergreen article."]
    if topic:
        parts.append(f"Topic: {topic}.")
    else:
        parts.append(
            "Pick the topic yourself. Choose something concrete, surprising, "
            "and not time-sensitive."
        )
    if category:
        if category not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"category must be one of {ALLOWED_CATEGORIES}, got {category!r}"
            )
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
) -> dict:
    """Generate one evergreen article via Claude (sonnet 4.6).

    Returns a dict with keys: title, body_html, category, tags.
    """
    cfg = Config.load()
    client = anthropic.Anthropic(api_key=cfg.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    _build_user_message(topic, category)
                    + _build_avoidance_message(recent_titles)
                ),
            }
        ],
        tools=[_TOOL_SCHEMA],
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
    if article["category"] not in ALLOWED_CATEGORIES:
        raise ValueError(
            f"Model returned disallowed category {article['category']!r}; "
            f"allowed: {ALLOWED_CATEGORIES}"
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
