# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A WordPress prototype article site plus an **openclaw agent** — a Claude-powered
Python script that writes and publishes one article on demand (Phase 2),
later automated to run daily at 07:00 (Phase 3), and eventually analytics-aware
(Phase 4). "Openclaw" = our name for the agent, not an external tool.

## Read this first

**Always start a session by reading [PLAN.md](./PLAN.md).** It contains:
- Current phase and what's done
- Step-by-step plan with verification checklists
- Architecture decisions log (§4)
- Open questions (§8)

If you're about to do real work, update PLAN.md as steps complete (check the
boxes) and append any new decisions to §4.

## Key facts

- **Working dir:** `D:\Claude\Wordpress` — holds docker-compose.yml, agent code, plans, and notes.
- **WordPress stack:** Docker. `docker-compose.yml` at the project root brings up `wordpress` (port 8088), `mariadb`, and a `wpcli` sidecar. Site is at `http://localhost:8088`. WP files and DB live in named Docker volumes (`openclaw_wp_data`, `openclaw_db_data`), not on the host filesystem.
- **wp-cli usage:** `docker compose run --rm wpcli <command>` — entrypoint is already `wp`, so e.g. `docker compose run --rm wpcli option get blogname`.
- **Local admin credentials:** in `CREDENTIALS.local.txt` (uncommitted, `.local` suffix).
- **OS / shell:** Windows 11, PowerShell.
- **Agent runtime:** Python 3.11+ in a `.venv` at the project root.
- **WP auth:** Application Password for the `openclaw-agent` user, stored in `.env` (never committed).
- **Anthropic SDK:** use `claude-sonnet-4-6` via the `anthropic` Python package; structured replies use tool-use (`tools=[...]` + `tool_choice={"type":"tool", "name":"submit_article"}`). The GPT-4o code path is preserved as a commented block in `openclaw/generator.py` for easy revert.

## Common commands

```powershell
# Activate the virtual environment (PowerShell)
.venv\Scripts\Activate.ps1

# Install / sync dependencies
pip install -r requirements.txt

# WordPress stack
docker compose up -d       # start
docker compose down        # stop (keeps volumes)
docker compose down -v     # stop + DELETE volumes (destructive; tracked mu-plugin is remounted on next up)

# wp-cli (entrypoint is already `wp`)
docker compose run --rm wpcli option get blogname
docker compose run --rm wpcli post list

# Run the agent
python -m openclaw post                                                 # generate + publish
python -m openclaw post --topic "history of jazz" --category History   # override topic/category
python -m openclaw post --draft                                         # publish as draft
python -m openclaw post --help

# Generation-only smoke test: calls Claude, uses recent-title de-duplication, does NOT publish
python -c "from openclaw.generator import generate_article; from openclaw.publisher import list_recent_post_titles; article = generate_article(recent_titles=list_recent_post_titles()); print(article['title']); print(article['category'])"
```

There are no automated tests. Verification steps are manual (see PLAN.md §7).

## Architecture

```
openclaw/
├── config.py      # Config.load() → frozen dataclass from .env; called by generator & publisher
├── constants.py   # shared category constants
├── generator.py   # generate_article(topic?, category?) → {title, body_html, category, tags}
├── publisher.py   # publish_post(title, body_html, category, tags, status) → post JSON
├── main.py        # `python -m openclaw post` CLI entry (argparse)
└── __main__.py    # module runner for `python -m openclaw`
```

Data flow: `main.py` parses args → `generate_article()` (Claude API) → `publish_post()` (WP REST API) → prints post URL.

**Structured output:** `generator.py` uses Claude tool-use with `tool_choice={"type":"tool","name":"submit_article"}`. The tool's `input_schema` enforces the four-category enum and required fields — Anthropic's equivalent of OpenAI Structured Outputs.

**Category IDs (WP):** Science=2, History=3, How Things Work=4, Concepts=5. `publisher.py` resolves these at runtime via a single GET to `/wp-json/wp/v2/categories`. The `ALLOWED_CATEGORIES` tuple in `openclaw/constants.py` is the authoritative code list and must stay in sync with WP.

**mu-plugin caveat:** WP core disables Application Passwords on plain HTTP. The tracked file `wp-content/mu-plugins/allow-app-passwords-on-localhost.php` is bind-mounted into the WordPress container and forces it on for this loopback-only dev site.

## Conventions

- Never commit `.env` or any file containing the application password / API key.
- Don't touch the WordPress core files unless explicitly asked.
- When proposing changes to the plan itself, edit PLAN.md — don't duplicate plan content here.
