# CLAUDE.md

Project preamble for Claude Code sessions. Keep this file short — details
belong in [PLAN.md](./PLAN.md).

## What this project is

A WordPress prototype article site plus an **openclaw agent** — a GPT-4o-powered
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

- **Working dir:** `D:\Claude\Wordpress` — holds the docker-compose.yml, agent code, plans, and notes.
- **WordPress stack:** Docker. `docker-compose.yml` at the project root brings up `wordpress` (port 8088), `mariadb`, and a `wpcli` sidecar. Site is at `http://localhost:8088`. WP files and DB live in named Docker volumes (`openclaw_wp_data`, `openclaw_db_data`), not on the host filesystem.
- **wp-cli usage:** `docker compose run --rm wpcli <command>` — entrypoint is already `wp`, so e.g. `docker compose run --rm wpcli option get blogname`.
- **Local admin credentials:** in `CREDENTIALS.local.txt` (uncommitted, `.local` suffix).
- **OS / shell:** Windows 11, PowerShell.
- **Agent runtime:** Python 3.11+ in a `.venv` at the project root.
- **WP auth:** Application Password for the `openclaw-agent` user, stored in `.env` (never committed).
- **OpenAI SDK:** use `gpt-4o` via the `openai` Python package; structured replies use `response_format` with a JSON schema.

## Conventions

- Never commit `.env` or any file containing the application password / API key.
- Don't touch the WordPress core files in Local's site folder unless explicitly asked.
- When proposing changes to the plan itself, edit PLAN.md — don't duplicate plan content here.
