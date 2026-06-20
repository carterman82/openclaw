# Openclaw

A Claude-powered Python agent that writes and publishes evergreen articles to a
WordPress site. See [PLAN.md](./PLAN.md) for the full project roadmap.

## Prerequisites

- Python 3.11+
- Docker (for the WordPress stack)

## Setup

**1. Start the WordPress stack**

```powershell
docker compose up -d
```

The site is available at `http://localhost:8088`.

**2. Create a virtual environment and install dependencies**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**3. Configure secrets**

```powershell
Copy-Item .env.example .env
```

Edit `.env` and fill in:

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key (starts with `sk-ant-`) |
| `WP_BASE_URL` | WordPress URL, e.g. `http://localhost:8088` |
| `WP_USERNAME` | WordPress username for the agent (`openclaw-agent`) |
| `WP_APP_PASSWORD` | Application Password for that user (24 chars) |
| `UNSPLASH_ACCESS_KEY` | Free at [unsplash.com/developers](https://unsplash.com/developers); register an app named `openclaw`. If unset, articles publish without featured images. |
| `OPENAI_API_KEY` | Optional. Reserved for the AI-image swap path in `openclaw/images.py` (`generate_openai_image`) and the commented-out GPT-4o text path. |

> **Never commit `.env`** — it is gitignored.

## Usage

```powershell
# Generate and publish one article (Claude picks topic and category)
python -m openclaw post

# Override topic and/or category
python -m openclaw post --topic "the history of the paperclip" --category History

# Publish as a draft for review before going live
python -m openclaw post --draft

# Show verbose logging
python -m openclaw post --verbose

# Or set log level through the environment
$env:LOG_LEVEL = "DEBUG"

# Show all options
python -m openclaw post --help
```

Allowed categories: **Science**, **History**, **How Things Work**, **Concepts**

The final line of output is the URL of the published post.

When no `--topic` is provided, the agent reads recent WordPress post titles and
asks Claude to avoid repeating the same subject or angle. Each Claude request is
still stateless; no conversation/session context is reused between runs.

## Featured images

Featured images are sourced from **Unsplash** (free, attribution required). The
agent searches by `focus_keyphrase`, falls back to the article `category`, and
publishes without an image if both queries return zero results. Every image is
attached as `featured_media` on the WP post; the photographer credit is set as
the media `caption` and also appended to the post body as a small
`<p class="image-credit">` line so it renders regardless of theme. Required
UTM params (`utm_source=openclaw&utm_medium=referral`) are added to both
attribution links. An AI-generation alternative (`generate_openai_image` using
`gpt-image-1-mini`) is wired in `openclaw/images.py` for one-line swap-in —
see PLAN.md §8 Step 3.3.

## Linking policy

- **Internal links:** the agent fetches up to 30 recent published posts via
  `publisher.list_recent_posts_for_linking()` and offers them to Claude as
  link candidates. Claude is told to link to 1–3 of them WHEN GENUINELY
  RELEVANT, using the exact URLs only. After generation, any `<a>` whose href
  is not in the candidate list is stripped to bare text (with a warning).
- **External links:** Claude is required to include 1–2 outbound links to
  authoritative sources (primary sources, .edu/.gov, official docs, scholarly
  publications, or Wikipedia). SEO spam, social media, and paywalled news are
  forbidden. After generation, every external `<a>` is checked for
  `rel="noopener"` and `target="_blank"`; missing attributes are injected.

## Smoke Test

This calls Claude with the recent-title avoidance list and prints the proposed
title/category, but does not publish anything to WordPress:

```powershell
python -c "from openclaw.generator import generate_article; from openclaw.publisher import list_recent_post_titles; article = generate_article(recent_titles=list_recent_post_titles()); print(article['title']); print(article['category'])"
```

## Style guide

`STYLE.md` at the project root is loaded by `openclaw/generator.py` at runtime
and appended to the Claude system prompt. Edit it freely to tune voice,
structure, and what-to-avoid lists; changes take effect on the next run, no
code changes needed. Hard structural rules (length, evergreen, HTML format,
linking policy, schema) stay in `generator.py` and are not overridable from
STYLE.md.

## Switching to the GPT-4o backend

The `gpt-4o` implementation is preserved as a commented block in
`openclaw/generator.py`. Uncomment it and set `OPENAI_API_KEY` in `.env` to
revert. See PLAN.md §4 for the swap history.
