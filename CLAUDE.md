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
- **Target WP site is portable:** point the agent at any WP site by editing `.env` only — `WP_BASE_URL` + a valid Application Password for an Author-or-higher user. Categories and SEO plugin are discovered at runtime; no code changes needed. See PLAN.md §7b.

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
├── config.py      # Config.load() → frozen dataclass from .env; called by generator, publisher, images
├── constants.py   # shared category constants (offline fallback only)
├── generator.py   # generate_article(...) — Claude tool-use; loads Instructions/*.md at runtime
├── publisher.py   # publish_post + upload_media + list_recent_post_titles + list_recent_posts_for_linking
├── images.py      # find_unsplash_image / generate_openai_image / attribution_html / track_download
├── main.py        # `python -m openclaw post` CLI entry; wires generation → links → image → publish
└── __main__.py    # module runner for `python -m openclaw`
```

Data flow: `main.py` parses args → fetches `get_site_name()`, `get_seo_plugin()`, `get_category_names()`, `list_recent_post_titles()` (for de-dup, when no `--topic`), and `list_recent_posts_for_linking()` (internal-link candidates) from WP → `generate_article()` (Claude API with the live category list, site name, avoidance titles, and link candidates threaded in) → main validates internal links against candidates (strips invented URLs) and enforces external-link safety attrs (`rel="noopener" target="_blank"`) → `_fetch_and_attach_image()` (Unsplash search + `upload_media` + `attribution_html` append to body) → `publish_post()` with `featured_media` → optional `track_download()` → prints post URL.

**Structured output:** `generator.py` uses Claude tool-use with `tool_choice={"type":"tool","name":"submit_article"}`. The tool's `input_schema` requires: `title`, `body_html`, `category` (runtime enum), `tags`, SEO fields (`excerpt`, `slug`, `focus_keyphrase`, `seo_title`, `meta_description`, `image_alt_text`, `image_prompt`, `unsplash_query`), and link reports (`internal_links_used`, `external_links_used`).

**Categories are dynamic:** `main.py` calls `publisher.get_category_names()` at startup and passes the result into `generate_article()`, so the tool schema and system prompt reflect whatever categories actually exist on the configured site. `openclaw/constants.py` `ALLOWED_CATEGORIES` is just an offline fallback — it does NOT need to track every external WP site.

**SEO routing:** `publisher.get_seo_plugin()` inspects `/wp-json/` namespaces to detect Yoast (`yoast/v1`) or RankMath (`rankmath/v1`). Three SEO fields are written via the post `meta` field: `focus_keyphrase` → `_yoast_wpseo_focuskw` / `rank_math_focus_keyword`; `meta_description` → `_yoast_wpseo_metadesc` / `rank_math_description`; `seo_title` → `_yoast_wpseo_title` / `rank_math_title`. After each POST, `publisher._verify_seo_meta_roundtrip()` GETs the post back and logs a WARNING for any key that didn't persist. On sites without the `openclaw-seo-meta` plugin (e.g. catfancast.com before the plugin is installed), the meta keys are not registered with `show_in_rest=true` and the values are silently discarded — the round-trip WARNs confirm this. `excerpt` and `slug` are standard WP fields and always posted when present. Run `python scripts/verify-seo.py <post_id>` (or `--latest`) to check all 12 Yoast SEO + Readability conditions against a published post.

**Featured images (Phase 3):** Unsplash is the active source. `images.find_unsplash_image(query)` searches `/search/photos`, downloads `urls.regular`, returns `{image_bytes, mime_type, alt_text, attribution}`. `main._fetch_and_attach_image` tries `focus_keyphrase` then `category` as queries; on success uploads via `publisher.upload_media` (raw POST then JSON metadata) and sets the photographer credit on both the media caption and as a `<p class="image-credit">` at the end of `body_html`. `track_download()` fires the Unsplash attribution endpoint after publish. Failure modes (missing key, network, empty results) skip the image with a WARNING; the article still publishes. `generate_openai_image` is a wired alternative for the AI-image swap path.

**Linking policy (Phase 3):** Internal links — `list_recent_posts_for_linking()` returns up to 30 published posts as `{title, link, excerpt}`; Claude is told to use 1–3 EXACT URLs when relevant; `main._strip_invented_internal_links` removes any `<a>` not in the candidate set. External links — Claude must include 1–2 authoritative outbound links with `rel="noopener" target="_blank"`; `main._enforce_external_link_attrs` injects missing safety attrs by comparing href host to `Config.WP_BASE_URL`.

**Instructions folder:** three editable markdown files in `Instructions/` are loaded by `generator.py` and injected into the Claude system prompt (in this order: description → style → image guide). Path constants are defined together in `generator.py` via `_INSTRUCTIONS_DIR`. Editing any file takes effect on the next run.

- `Instructions/DESCRIPTION.md` — loaded by `generator._load_description()`. Defines what the site is, target audience, tone, what to write, what to avoid, entity checklist. Edit to redirect the agent toward the site's content needs.
- `Instructions/STYLE.md` — loaded by `generator._load_style_guide()`. Voice/tone and copy-level conventions. Structural rules (length, evergreen, HTML, linking, schema) stay in `generator.py`.
- `Instructions/IMAGE_GENERATOR.md` — loaded by `generator._load_image_guide()`. Rules + formula the agent follows when writing the per-article `image_prompt` (composition, mood, lighting, palette, scale, environmental storytelling, the "movie poster test"). Hard constraints (landscape, no in-image text/logos/copyrighted characters) are duplicated in `generator.py` so they survive even if the file is missing.
- `Instructions/TOPIC.md` — loaded by `generator._load_topic_guide()`. Topic selection rules for Cat Fancast: domain-anchored model (breed, behavior, biology question, medical condition, care concern, or named real cat) with five parallel anchor inventories in §3, a heavy ~92/8 Evergreen/Trending bias, proven angle templates per anchor type, and a hard ban on copyrighted fictional cat characters as topics. Only consulted when Claude is picking the topic itself (no `--topic` flag).

**mu-plugin caveat:** WP core disables Application Passwords on plain HTTP. The tracked file `wp-content/mu-plugins/allow-app-passwords-on-localhost.php` is bind-mounted into the WordPress container and forces it on for this loopback-only dev site.

## Conventions

- Never commit `.env` or any file containing the application password / API key.
- Don't touch the WordPress core files unless explicitly asked.
- When proposing changes to the plan itself, edit PLAN.md — don't duplicate plan content here.
