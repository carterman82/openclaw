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

## Smoke Test

This calls Claude with the recent-title avoidance list and prints the proposed
title/category, but does not publish anything to WordPress:

```powershell
python -c "from openclaw.generator import generate_article; from openclaw.publisher import list_recent_post_titles; article = generate_article(recent_titles=list_recent_post_titles()); print(article['title']); print(article['category'])"
```

## Switching to the GPT-4o backend

The `gpt-4o` implementation is preserved as a commented block in
`openclaw/generator.py`. Uncomment it and set `OPENAI_API_KEY` in `.env` to
revert. See PLAN.md §4 for the swap history.
