# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A WordPress prototype article site plus an **openclaw agent** — a Claude-powered
Python script that writes and publishes one article on demand (Phase 2),
augments with images and SEO fields (Phase 3), scheduled unattended daily at
07:00 via Windows Task Scheduler (Phase 4), fanned out into a local WordPress
multisite with per-subsite static export to GitHub Pages (Phase 5), and
eventually analytics-aware (Phase 6). "Openclaw" = our name for the agent, not
an external tool.

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
- **Multi-site (Phase 3.6):** `.env` supports per-site prefixes (`CATFANCAST_WP_BASE_URL`, `CATFANCAST_WP_USERNAME`, `CATFANCAST_WP_APP_PASSWORD`). Select the active site with `--site catfancast` on `python -m openclaw post`; `main._activate_site()` copies the prefixed vars into their bare positions before anything else loads. Bare `WP_*` vars are still honored when `--site` is omitted. Each site's persona lives in `website_memory/{hostname}.md` (hostname is parsed from `WP_BASE_URL`); missing file is a hard error.
- **Local model + fallback (Phase 3.8):** `openclaw/generator.py`'s `generate_article()` is a router. When `LOCAL_MODEL_ENABLED=true` in `.env`, it tries `_generate_with_local` (LM Studio OpenAI-compatible endpoint at `LOCAL_MODEL_BASE_URL`, model id in `LOCAL_MODEL_NAME`) and falls back to `_generate_with_claude` on any `LocalProviderError` (connection failure, timeout, empty/wrong tool call, non-JSON args, missing/empty required field). When unset or false, routes directly to Claude — pre-3.8 behavior. Structured log lines: `provider=<local|claude> status=<success|fallback> [reason=...]`.
- **Local image + fallback (Phase 3.9):** `openclaw/images.py`'s `generate_local_image(prompt, alt_text)` calls a local Draw Things app's Automatic1111-compatible HTTP API (`POST {LOCAL_IMAGE_BASE_URL}/sdapi/v1/txt2img`, gated by `LOCAL_IMAGE_ENABLED`) to run Flux, returning the same `{image_bytes, mime_type, alt_text, attribution=None}` shape as `generate_openai_image`. `main._fetch_and_attach_image` tries it first, then `generate_openai_image`, then `find_unsplash_image` — every source function returns `None` and logs a WARNING on failure instead of raising, so the chain always degrades gracefully to "publish with no image" in the worst case. When `LOCAL_IMAGE_ENABLED` is unset/false, behavior is unchanged from pre-3.9 (OpenAI then Unsplash).
- **Per-run randomness + second-pass editor (2026-07-11):** when neither `--topic` nor `--category` is given, `main.py` rolls a random category (`_pick_random_category`) and per-run variation directives (`_roll_variation_directives`: length band, FAQ ~1-in-3, hook type) — LLMs can't self-randomize, so structural variety comes from code. After generation, `generator.revise_article()` runs an editor pass over the draft through the same provider router (`stage=revise`): helpfulness/redundancy/style/SEO audit, category code-guarded, no new links, hrefs must stay byte-identical. Bypass with `--skip-review`.
- **Scheduling (Phase 4):** `scripts/run-openclaw.ps1` is the wrapper invoked by Windows Task Scheduler at 07:00 daily. Reads `scheduled-sites.json` at the project root (array of `{slug, enabled, notes}`), runs `python -m openclaw post --site <slug> --verbose` per enabled entry, retries N=2 (60s→300s), writes per-attempt logs to `logs/openclaw-YYYY-MM-DD-<slug>.log`, and drops `logs/last-run-failed.flag` on any final failure (removes it on all-pass). Log-flag-only notification — no email/toast/push. Uses `Start-Process` with `-RedirectStandardOutput/-RedirectStandardError` to sidestep PS 5.1's native-command stderr wrapping (which otherwise turns Python `logging` output into `NativeCommandError` records that trip `$ErrorActionPreference=Stop`).
- **Multisite + static export (Phase 5):** the local Docker WordPress is a subdomain multisite. Primary site (`blog_id=1`) is at `http://localhost:8088/` (now admin/hub only, `enabled=false` in `scheduled-sites.json` since Step 5.10). Subsites live at `<slug>.localhost:8088/`: four first-round pilots (`gardening`/`dogs`/`boardgames`/`coffee`, blog_ids 2–5, all `enabled=false` awaiting Step 5.9 rebuild) plus `techtools` (blog_id 6, Tech Tool Guide, Step 5.10). `.localhost` is RFC 6761 loopback — browsers/curl resolve it for free; `openclaw/_localhost_dns.py` (auto-loaded from `openclaw/__init__.py`) monkey-patches `socket.getaddrinfo` so Python does the same. Each subsite has a bind-mounted child theme at `wp-content/themes/openclaw-<slug>/` (individual mounts survive volume resets), a persona at `website_memory/<slug>.localhost.md`, and its own scheduled-sites.json entry. **Themes (Step 5.11):** parent theme `wp-content/themes/openclaw-base/` provides the shared editorial layout (topbar with wordmark + category nav, featured lead + 6-tile category-explorer + 3-col card grid on home, 720px reading column with auto-injected TOC + related-posts on single, 3-column footer). Six semantic color slots (`--wp--preset--color--openclaw-{background,surface,text,muted,primary,accent}`) and two font families (`--wp--preset--font-family--openclaw-{body,display}`) are exposed via `theme.json`; child themes override just those. `functions.php` registers image sizes (all 16:9: `openclaw-hero` 1600×900, `openclaw-card` 480×270, `openclaw-thumb` 240×135), enqueues Inter Tight + Space Grotesk from Google Fonts, defines `[openclaw_related_posts]` (same-category → same-tag → most-recent priority) and `[openclaw_explore_categories]` (top N by post count, meta cats excluded), and hooks `the_content` to auto-inject a table of contents on any singular post with ≥3 H2s (assigns stable `id="openclaw-h2-<slug>"` anchors, skippable via post_meta `_openclaw_disable_toc=1`). Active child theme on techtools is `openclaw-techtools` (indigo #4F46E5 + cyan #06B6D4 on white/slate, Inter Tight + Space Grotesk). The four retired first-round child themes (`openclaw-{gardening,dogs,boardgames,coffee}`) remain bind-mounted; they'll be replaced by four fandom child themes when Step 5.9 rebuilds those subsites. `openclaw-agent` is a network super-admin, but `wp site create` does NOT grant per-blog roles — run `wp user add-role openclaw-agent administrator --url=<subsite>` on each new subsite before REST auth returns roles. One app password works for the whole network. **Staatic 1.12.5** is network-active; per-subsite options (`staatic_deployment_method=filesystem`, `staatic_filesystem_target_directory=/var/www/html/wp-content/staatic-exports/<slug>`, `staatic_destination_url=https://carterman82.github.io/openclaw-<slug>/`) point the export at the bind-mounted `staatic-exports/<slug>/` on the host with URLs pre-rewritten for GH Pages. `openclaw/deploy.py::deploy_after_publish` runs after `publish_post()` for the five deployable slugs (`DEPLOYABLE_SLUGS = {gardening, dogs, boardgames, coffee, techtools}` allowlist — non-pilot sites skip the whole chain, so a scheduled catfancast run never accidentally tries to git-push somewhere): fires `wp staatic publish`, then commits + pushes the export into `.gh-worktree/openclaw-<slug>/` on the `main` branch of `github.com/carterman82/openclaw-<slug>`. Bypass with `--skip-deploy` on `python -m openclaw post`. Docker plumbing worth remembering: (a) `apache/openclaw-multisite.conf` bind-mount adds `Listen 8088` + `ServerAlias *.localhost` so both host and container reach the site at `<slug>.localhost:8088`; (b) `extra_hosts` on the `wordpress` service maps subsite domains → 127.0.0.1 (must add each new subsite hostname here + restart the wordpress container); (c) `network_mode: "service:wordpress"` on `wpcli` shares that hosts file so `wp staatic publish` from wpcli can crawl the subsites; (d) `staatic-exports/` bind-mount is on BOTH wordpress and wpcli services (wpcli-side is the one Staatic actually writes from). Content migration between blogs (e.g. localhost → techtools per Step 5.10) uses `scripts/migrate-techtools-featured-images.sh` after a `wp export` + `wp import` pass — the WordPress Importer's HTTP fetch of `localhost:8088` deadlocks synchronously from inside the same PHP process, so attachments must be re-imported via `wp media import <local path> --post_id=<pid> --featured_image` (no HTTP), which also copies files into `wp-content/uploads/sites/<blog_id>/`. Multisite default 1500 KB `fileupload_maxk` also has to be raised (10240 KB) or attachment imports silently drop.

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

# Multi-site: select a per-site prefix block from .env
python -m openclaw post --site catfancast --draft

# Phase 5 pilot subsites (local WP multisite → Staatic → GitHub Pages)
python -m openclaw post --site gardening --draft            # publish + export + push
python -m openclaw post --site dogs --draft --skip-deploy   # publish only, skip static export/git push

# Generation-only smoke test: calls Claude, uses recent-title de-duplication, does NOT publish
python scripts/smoke-trends.py

# Phase 4 wrapper: reads scheduled-sites.json and publishes one post per enabled site
.\scripts\run-openclaw.ps1                          # scheduled path
.\scripts\run-openclaw.ps1 -Sites localhost -Draft  # one-shot smoke
```

There are no automated tests. Verification steps are manual (see PLAN.md §7).

## Architecture

```
openclaw/
├── __init__.py    # auto-installs the _localhost_dns shim on any openclaw import
├── _localhost_dns.py # monkey-patches socket.getaddrinfo so *.localhost resolves to 127.0.0.1 in this process
├── config.py      # Config.load() → frozen dataclass from .env; called by generator, publisher, images
├── constants.py   # shared category constants (offline fallback only)
├── generator.py   # generate_article(...) — Claude tool-use; loads Instructions/*.md + website_memory/{host}.md at runtime
├── publisher.py   # publish_post + upload_media + list_recent_post_titles + list_recent_posts_for_linking
├── images.py      # generate_local_image / generate_openai_image / find_unsplash_image / attribution_html / track_download
├── deploy.py      # Phase 5: trigger_staatic_export + commit_and_push for the four pilot subsites
├── main.py        # `python -m openclaw post` CLI entry; wires generation → links → image → publish → deploy
└── __main__.py    # module runner for `python -m openclaw`
```

Data flow: `main.py` parses args → `_activate_site(args.site)` copies prefixed env vars into bare positions (no-op when `--site` omitted) → `Config.load()` and hostname derived from `WP_BASE_URL` for the per-site persona lookup → fetches `get_site_name()`, `get_seo_plugin()`, `get_category_names()`, `list_recent_post_titles()` (for de-dup, when no `--topic`), and `list_recent_posts_for_linking()` (internal-link candidates) from WP → `generate_article()` (Claude API with the live category list, site name, `site_host` for `website_memory/{host}.md` lookup, avoidance titles, and link candidates threaded in) → `revise_article()` second-pass editor (same local-with-Claude-fallback router, `stage=revise` in provider log lines; audits helpfulness, redundancy, style compliance, and SEO fields; category is code-guarded and no new links are allowed; skip with `--skip-review`) → main validates internal links against candidates (strips invented URLs) and enforces external-link safety attrs (`rel="noopener" target="_blank"`) → `_fetch_and_attach_image()` (Unsplash search + `upload_media` + `attribution_html` append to body) → `publish_post()` with `featured_media` → optional `track_download()` → prints post URL → for Phase 5 pilot slugs (`gardening`, `dogs`, `boardgames`, `coffee`), `deploy.deploy_after_publish()` runs `wp staatic publish` and commits + pushes `staatic-exports/<slug>/` to `github.com/carterman82/openclaw-<slug>` (unless `--skip-deploy`).

**Structured output:** `generator.py` uses Claude tool-use with `tool_choice={"type":"tool","name":"submit_article"}`. The tool's `input_schema` requires: `title`, `body_html`, `category` (runtime enum), `tags`, SEO fields (`excerpt`, `slug`, `focus_keyphrase`, `seo_title`, `meta_description`, `image_alt_text`, `image_prompt`, `unsplash_query`), and link reports (`internal_links_used`, `external_links_used`).

**Categories are dynamic:** `main.py` calls `publisher.get_category_names()` at startup and passes the result into `generate_article()`, so the tool schema and system prompt reflect whatever categories actually exist on the configured site. `openclaw/constants.py` `ALLOWED_CATEGORIES` is just an offline fallback — it does NOT need to track every external WP site.

**SEO routing:** `publisher.get_seo_plugin()` inspects `/wp-json/` namespaces to detect Yoast (`yoast/v1`) or RankMath (`rankmath/v1`). Three SEO fields are written via the post `meta` field: `focus_keyphrase` → `_yoast_wpseo_focuskw` / `rank_math_focus_keyword`; `meta_description` → `_yoast_wpseo_metadesc` / `rank_math_description`; `seo_title` → `_yoast_wpseo_title` / `rank_math_title`. After each POST, `publisher._verify_seo_meta_roundtrip()` GETs the post back and logs a WARNING for any key that didn't persist. On sites without the `openclaw-seo-meta` plugin (e.g. catfancast.com before the plugin is installed), the meta keys are not registered with `show_in_rest=true` and the values are silently discarded — the round-trip WARNs confirm this. `excerpt` and `slug` are standard WP fields and always posted when present. Run `python scripts/verify-seo.py <post_id>` (or `--latest`) to check all 12 Yoast SEO + Readability conditions against a published post.

**Featured images (Phase 3 / 3.9):** three-tier fallback chain — local Flux via Draw Things (`generate_local_image`, Phase 3.9) → OpenAI `gpt-image-2` (`generate_openai_image`) → Unsplash search (`find_unsplash_image`). `images.find_unsplash_image(query)` searches `/search/photos`, downloads `urls.regular`, returns `{image_bytes, mime_type, alt_text, attribution}`; the two AI sources return `attribution=None`. `main._fetch_and_attach_image` tries local (if `LOCAL_IMAGE_ENABLED`), then OpenAI, using `image_prompt` from the generated article; if neither produces an image it falls back to Unsplash keyed on `focus_keyphrase` then `category`. On success it uploads via `publisher.upload_media` (raw POST then JSON metadata); for Unsplash hits it sets the photographer credit on both the media caption and as a `<p class="image-credit">` at the end of `body_html` (AI-generated images need no credit). `track_download()` fires the Unsplash attribution endpoint after publish, only when an Unsplash image was used. Every source function fails soft (returns `None` + WARNING) so a bad local host or dead OpenAI key just falls through to the next source; the article still publishes even if all three fail.

**Linking policy (Phase 3):** Internal links — `list_recent_posts_for_linking()` returns up to 30 published posts as `{title, link, excerpt}`; Claude is told to use 1–3 EXACT URLs when relevant; `main._strip_invented_internal_links` removes any `<a>` not in the candidate set. External links — Claude must include 1–2 authoritative outbound links with `rel="noopener" target="_blank"`; `main._enforce_external_link_attrs` injects missing safety attrs by comparing href host to `Config.WP_BASE_URL`.

**Instructions folder + website_memory:** three cross-site editable markdown files in `Instructions/` plus one per-site persona file in `website_memory/` are loaded by `generator.py` and injected into the Claude system prompt (in this order: description → style → topic guide → image guide). Path constants live together in `generator.py` under `_INSTRUCTIONS_DIR` and `_WEBSITE_MEMORY_DIR`. Editing any file takes effect on the next run.

- `website_memory/{hostname}.md` — loaded by `generator._load_description(site_host)` where `site_host` is `urlparse(WP_BASE_URL).hostname`. Defines what the site is, target audience, tone, what to write, what to avoid, entity checklist. One file per site. Missing file is a **hard error** (fail-fast, since publishing without a persona would produce off-brand content silently). See `website_memory/README.md`.
- `Instructions/STYLE.md` — loaded by `generator._load_style_guide()`. Voice/tone and copy-level conventions. Cross-site. Structural rules (length, evergreen, HTML, linking, schema) stay in `generator.py`.
- `Instructions/IMAGE_GENERATOR.md` — loaded by `generator._load_image_guide()`. Rules + formula the agent follows when writing the per-article `image_prompt` (composition, mood, lighting, palette, scale, environmental storytelling, the "movie poster test"). Cross-site. Hard constraints (landscape, no in-image text/logos/copyrighted characters) are duplicated in `generator.py` so they survive even if the file is missing.
- `Instructions/TOPIC.md` — loaded by `generator._load_topic_guide()`. Topic selection rules for Cat Fancast: domain-anchored model (breed, behavior, biology question, medical condition, care concern, or named real cat) with five parallel anchor inventories in §3, a heavy ~92/8 Evergreen/Trending bias, proven angle templates per anchor type, and a hard ban on copyrighted fictional cat characters as topics. Currently cat-domain-specific; treat as cross-site until a second site needs a different framework. Only consulted when Claude is picking the topic itself (no `--topic` flag).

**mu-plugin caveat:** WP core disables Application Passwords on plain HTTP. The tracked file `wp-content/mu-plugins/allow-app-passwords-on-localhost.php` is bind-mounted into the WordPress container and forces it on for this loopback-only dev site.

## Conventions

- Never commit `.env` or any file containing the application password / API key.
- Don't touch the WordPress core files unless explicitly asked.
- When proposing changes to the plan itself, edit PLAN.md — don't duplicate plan content here.
