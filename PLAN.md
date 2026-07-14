# PLAN - WordPress Sandbox + Openclaw Agent

> Living handoff for future LLM sessions.
> Last updated: 2026-07-13.

## 1. Current State

Openclaw is a WordPress prototype article site plus a Python agent that uses
Claude to generate evergreen articles and publish them through the WordPress
REST API.

Completed:
- Phase 1: local Docker WordPress site is running and REST publishing works.
- Phase 2: `python -m openclaw post` generates and publishes articles end to end.

Current active work:
- Phase 4: scheduling `python -m openclaw post` for unattended daily runs.
  Code complete (wrapper + sites config + retry + failure flag + docs)
  and end-to-end verified against localhost on 2026-07-10 (draft
  post id 1424). Owed to user: (a) Task Scheduler registration
  (`Register-ScheduledTask` block in README.md / PLAN.md §10 Step 4.3),
  and (b) Step 4.5 multi-day E2E gate.
- Phase 5: multisite + static export + GitHub Pages. First-round pilot
  (Steps 5.1–5.8) shipped 2026-07-13 with four subsites
  (`gardening`/`dogs`/`boardgames`/`coffee`) — full pipeline verified
  end-to-end. User rejected the niche picks and the default-WP look;
  Steps 5.9–5.11 replan the rework: (5.9) rebuild the four pilots with
  narrow-fandom niches and original brand names (proposed: Redstone
  Register / Sprue & Codex / Slipstream Journal / Clack Report); (5.10)
  add Tech Tool Guide as a dedicated `techtools.localhost` subsite;
  (5.11) build an `openclaw-base` parent theme in the catfancast /
  animefancast editorial-magazine style + five new child themes.
  Awaiting user review of Steps 5.9–5.11 before executing.

Deferred (ready to resume):
- Phase 3.8: local model primary (Qwen3.6 on LM Studio) with Claude fallback.
  All code is landed (Steps 3.8.2–3.8.4) and behaves as pre-3.8 while
  `LOCAL_MODEL_ENABLED` is unset/false — so Phase 4 automation is safe to
  build on top of it. To resume: load the Qwen model into LM Studio's
  memory, set the three `LOCAL_MODEL_*` env vars in `.env`, run
  `scripts\smoke-local-toolcall.py` to close Step 3.8.1, then continue
  with Steps 3.8.5–3.8.7 (quality gate, regression sweep, docs).

Future:
- Phase 3.8: switch primary LLM to a locally hosted Qwen3.6 (LM Studio on the LAN); keep Claude Sonnet 4.6 as automatic fallback.
- Phase 4: schedule daily publishing at 07:00 America/Denver.
- Phase 5: multisite + static export + GitHub Pages auto-commit after every publish.
- Phase 6: make the agent analytics-aware.

Recently completed:
- Phase 3: featured images and contextual links (2026-06-19).
- Phase 3.5: SEO hardening (2026-06-29).
- Phase 3.6: multi-site modularity (2026-07-01) — per-site persona files under
  `website_memory/{hostname}.md` + prefixed `.env` credentials + `--site` flag.

Content rules:
- Evergreen informational articles.
- Target length: 700-1200 words.
- No reader comments.
- No featured images yet; planned for Phase 3.
- Categories are discovered from the configured WordPress site at runtime.

## ⚠ Plugin Required for Full Yoast SEO Integration

> **READ THIS BEFORE RUNNING PHASE 3.5 ON ANY NEW SITE.**

Yoast SEO and RankMath do not register their per-post meta fields
(`_yoast_wpseo_focuskw`, `_yoast_wpseo_metadesc`, `_yoast_wpseo_title`, etc.)
for the WordPress REST API by default. Any values the openclaw agent writes to
the `meta:` payload are **silently discarded** by WordPress.

This blocks 5–6 of the 10 Yoast SEO problems from being fixed programmatically:

| Problem                        | Fixable without plugin? |
|-------------------------------|------------------------|
| Focus keyphrase not set (Y1)   | ❌ Needs plugin        |
| Keyphrase not in SEO title (Y3)| ❌ Needs plugin        |
| SEO title too wide (Y4)        | ⚠ Partial (keep title short) |
| No meta description (Y7)       | ❌ Needs plugin        |
| Keyphrase not in meta desc (Y8)| ❌ Needs plugin        |
| Previously-used keyphrase (Y9) | ❌ Downstream of Y1    |
| Keyphrase length (Y10)         | ❌ Downstream of Y1    |
| Keyphrase in introduction (Y2) | ✅ Content only        |
| Keyphrase in slug (Y5)         | ✅ Content only        |
| Keyphrase in image alt (Y6)    | ✅ Content only        |
| Consecutive sentences (Y11)    | ✅ Readability only    |
| Transition words (Y12)         | ✅ Readability only    |

### The plugin: `demo/openclaw-seo-meta/`

A prototype installable WordPress plugin lives at
`demo/openclaw-seo-meta/openclaw-seo-meta.php`. It does one thing: calls
`register_post_meta()` with `show_in_rest = true` for all six SEO meta keys
(Yoast + RankMath). No admin UI, no database, no options — safe to install
and deactivate at any time.

**When you own a site (or buy animefancast.com):**

Option A — WP Admin upload (no FTP needed):
1. ZIP the folder: `Compress-Archive demo\openclaw-seo-meta openclaw-seo-meta.zip`
2. WP Admin → Plugins → Add New → Upload Plugin → select the ZIP → Activate.
3. Verify: `python scripts/verify-seo.py <post_id>` → Routing section all PASS.

Option B — mu-plugin (local Docker, auto-active):
The file is already at `wp-content/mu-plugins/openclaw-register-seo-meta.php`
and is bind-mounted into the local Docker WordPress container.

**Current status (animefancast.com, 2026-06-29):**
The agent does not own animefancast.com and cannot install plugins. Phase 3.5
proceeds with content-shape and readability fixes only (Y2, Y5, Y6, Y11, Y12).
The plugin prototype is ready for deployment on any owned site.

---

## 2. Environment

- Working directory: `D:\Claude\Wordpress`
- OS/shell: Windows 11, PowerShell
- Local site: `http://localhost:8088`
- Docker stack: `wordpress:6.7-php8.3-apache`, `mariadb:11`,
  `wordpress:cli-php8.3`
- WordPress port binding: `127.0.0.1:8088:80`
- WordPress data: Docker named volumes `openclaw_wp_data`,
  `openclaw_db_data`
- Local mu-plugin: `wp-content/mu-plugins/allow-app-passwords-on-localhost.php`
  is bind-mounted into WordPress to allow Application Passwords on local HTTP.
- Python runtime: Python 3.11+ in `.venv`
- Secrets: `.env` and `CREDENTIALS.local.txt` are local only; never commit or
  paste secrets into tracked docs.
- Version control: local `.git` exists; no remote chosen yet.

## 3. Project Layout

```text
D:\Claude\Wordpress\
|-- PLAN.md
|-- CLAUDE.md
|-- README.md
|-- docker-compose.yml
|-- requirements.txt
|-- .env.example
|-- wp-content/
|   `-- mu-plugins/
|       `-- allow-app-passwords-on-localhost.php
`-- openclaw/
    |-- __init__.py
    |-- __main__.py
    |-- config.py
    |-- constants.py
    |-- generator.py
    |-- main.py
    `-- publisher.py
```

Known cleanup note: if `openclaw/*.tmp.*` files exist, they are scratch output
and should not be treated as source.

## 4. Common Commands

```powershell
# Start local WordPress
docker compose up -d

# Stop local WordPress but keep volumes
docker compose down

# wp-cli sidecar; entrypoint is already "wp"
docker compose run --rm wpcli option get blogname
docker compose run --rm wpcli post list

# Activate Python env
.venv\Scripts\Activate.ps1

# Install deps
pip install -r requirements.txt

# Generate and publish
python -m openclaw post

# Draft instead of publish
python -m openclaw post --draft

# Force a topic/category
python -m openclaw post --topic "history of jazz" --category History

# Help
python -m openclaw post --help

# Generation-only smoke test; calls Claude but does not publish
python -c "from openclaw.generator import generate_article; from openclaw.publisher import list_recent_post_titles; article = generate_article(recent_titles=list_recent_post_titles()); print(article['title']); print(article['category'])"
```

## 5. Implemented Architecture

Runtime flow:
1. `main.py` parses CLI args.
2. `Config.load()` reads `.env`.
3. `publisher.get_site_name()` reads `/wp-json/` for site-aware topic choice.
4. `publisher.get_seo_plugin()` detects Yoast or RankMath namespaces.
5. `publisher.get_category_names()` fetches live WordPress categories.
6. If no `--topic` is provided, `publisher.list_recent_post_titles()` fetches
   recent published/draft titles for de-duplication.
7. `generator.generate_article()` calls Claude using tool-use structured output.
8. `publisher.publish_post()` creates the WordPress post.
9. The CLI prints the final post URL.

Claude generation:
- Model: `claude-sonnet-4-6`
- API style: Anthropic Messages API, one fresh request per run.
- There is no continuing Claude session or conversation state to clear.
- Topic repetition is controlled by passing recent WordPress titles into the
  prompt and instructing Claude to avoid the same subject/angle.
- Tool schema returns:
  - `title`
  - `body_html`
  - `category`
  - `tags`
  - `excerpt`
  - `slug`
  - `focus_keyphrase`

WordPress publishing:
- Auth: WordPress Application Password for `WP_USERNAME`.
- Categories: loaded from WordPress at runtime; `constants.py` is only an
  offline fallback.
- Tags: looked up by exact-name search and created on miss. If a target site
  user cannot create tags, the tag is skipped with a warning.
- SEO fields:
  - `excerpt` and `slug` are standard WordPress post fields.
  - `focus_keyphrase` is routed to Yoast (`_yoast_wpseo_focuskw`) or RankMath
    (`rank_math_focus_keyword`) when the plugin namespace is detected.

## 6. Completed Phase Summaries

### Phase 1 - Website

Status: complete.

What exists:
- Docker WordPress site at `http://localhost:8088`.
- WordPress bound to loopback only.
- Site title/tagline/timezone configured.
- Permalinks configured.
- Comments disabled.
- Categories created on the local site.
- Manual test post exists.
- Dedicated `openclaw-agent` WordPress user exists with Author role.
- Application Password auth verified through REST.
- Local HTTP Application Password caveat handled by tracked mu-plugin mount.

Important caveat:
- `docker compose down -v` deletes WordPress/database volumes. The tracked
  mu-plugin will remount on next `docker compose up -d`, but WordPress content,
  users, passwords, categories, and posts must be recreated/restored if volumes
  are removed.

### Phase 2 - Manual Agent

Status: complete.

What exists:
- CLI entrypoint: `python -m openclaw post`
- Flags: `--topic`, `--category`, `--draft`, `--verbose`
- Structured Claude output via tool-use.
- Runtime category discovery from WordPress.
- Site-aware topic prompt from WordPress site name.
- Recent-title de-duplication when topic is omitted.
- WordPress publisher with category lookup, tag lookup/creation, post creation.
- SEO field generation and publishing (`excerpt`, `slug`, `focus_keyphrase`).
- Yoast/RankMath focus-keyphrase routing when detected.
- Logging via Python `logging`; `--verbose` or `LOG_LEVEL=DEBUG` for debug.
- README documents setup, usage, and generation-only smoke test.

Verification already performed:
- CLI help works.
- Invalid category fails clearly.
- `compileall openclaw` passed.
- End-to-end runs produced published WordPress posts.
- Generation-only smoke test avoided repeated honey topics after de-duplication.

## 7. External WordPress Site Checklist

Goal: point the agent at a different WordPress site by changing `.env` only.

Required:
- Target site must support HTTPS for Application Passwords.
- User must have Author, Editor, or Administrator role.
- `.env` must contain:
  - `ANTHROPIC_API_KEY`
  - `WP_BASE_URL` with no trailing slash
  - `WP_USERNAME` as the WordPress login name, not display name/email
  - `WP_APP_PASSWORD`

Smoke checks:
```powershell
# Auth: should print status 200, username slug, and roles.
.venv\Scripts\python.exe -c "import os, requests; from dotenv import load_dotenv; load_dotenv(); base=os.environ['WP_BASE_URL'].rstrip('/'); r=requests.get(base + '/wp-json/wp/v2/users/me', auth=(os.environ['WP_USERNAME'], os.environ['WP_APP_PASSWORD'])); print(r.status_code, r.json().get('slug',''), r.json().get('roles',''), r.json().get('code',''))"

# Categories: should print target-site categories.
.venv\Scripts\python.exe -c "from openclaw.publisher import get_category_names; print(get_category_names())"

# Draft creation.
python -m openclaw post --draft
```

Expected:
- Auth check returns 200.
- Categories come from the target site.
- Draft appears in target WP Admin under the configured author.
- If tag creation is forbidden, warnings are acceptable and publishing should
  still succeed.

## 8. Phase 3 Plan - Featured Images And Links

Status: complete. All steps 3.1-3.7 verified. Phase 3 exit criteria met
on 2026-06-19 with end-to-end run https://animefancast.com/?p=10910.

Goal: every new article includes:
- Featured image from Unsplash.
- Descriptive image alt text.
- Photographer attribution with required Unsplash UTM links.
- 1-3 contextual internal links to prior posts when relevant.
- 1-2 authoritative outbound links with `rel="noopener"` and `target="_blank"`.

### Step 3.1 - Unsplash Access

Status: code done; user action required.

Done (code):
- `.env.example` now lists `UNSPLASH_ACCESS_KEY=REPLACE_ME` with a comment
  pointing to `unsplash.com/developers`.
- `Config` exposes `UNSPLASH_ACCESS_KEY` as `Optional[str]`; `REPLACE_ME` is
  normalized to `None` so the placeholder never reaches the network.

User action required:
- Create an Unsplash developer app named `openclaw`.
- Put the Access Key into local `.env` as `UNSPLASH_ACCESS_KEY`.
- Confirm with the smoke test below.

Smoke test (after setting the key):
```powershell
.venv\Scripts\python.exe -c "import os, requests; from dotenv import load_dotenv; load_dotenv(); r = requests.get('https://api.unsplash.com/search/photos', params={'query':'honey','per_page':1}, headers={'Authorization': f'Client-ID {os.environ[\"UNSPLASH_ACCESS_KEY\"]}'}); print(r.status_code, r.json()['results'][0]['urls']['regular'][:60])"
```
Expected: `200 https://images.unsplash.com/...`.

Key details:
- Endpoint: `GET https://api.unsplash.com/search/photos`
- Auth header: `Authorization: Client-ID {access_key}`
- Use `orientation=landscape&per_page=10`.
- Use `results[i].urls.regular` for the image download.
- After using an image, call `results[i].links.download_location`.
- Attribution links must include `utm_source=openclaw&utm_medium=referral`.

### Step 3.2 - WordPress Media Upload

Status: complete.

Implemented `publisher.upload_media(image_bytes, filename, mime_type, alt_text, caption=None) -> int`:
- POSTs raw bytes to `/wp/v2/media` with `Content-Disposition: attachment; filename="..."` and the appropriate `Content-Type`.
- Follow-up POST to `/wp/v2/media/{id}` sets `alt_text` and `caption` as JSON.
- Returns the attachment ID.
- Uses the shared `_raise_for_status` for clear REST errors.

### Step 3.3 - Image Generation And Attribution

Status: complete. Default source: OpenAI `gpt-image-1-mini` (medium, 1536x1024, ~$0.011-$0.015 per image). Unsplash is the automatic fallback when OpenAI returns nothing. Wired into `main.py` 2026-06-20 — prior versions of this section claimed OpenAI was active but the runtime path was still Unsplash-only.

`openclaw/images.py`:
- `generate_openai_image(prompt, alt_text)` - calls OpenAI `images.generate`, decodes the base64 PNG, returns `{image_bytes, mime_type, alt_text, attribution: None}`. Returns `None` on missing key, content-policy refusal, or any error.
- `find_unsplash_image(query)` - now the fallback, called when OpenAI returns None.
- `attribution_html(attribution)` / `track_download(attribution)` - only used when the active source has an `attribution` dict (Unsplash). No-ops for AI generation; the existing `track_download` gate in `main.main()` already keys on `image.get("attribution")`.

`publisher.publish_post()` accepts `featured_media: int | None = None`.

Per-article prompt: `generate_article()` now requires an `image_prompt` field in the Claude tool schema. The system prompt instructs Claude to tailor the visual style to the article's subject and the site's audience (editorial illustration / cinematic key art / diagrammatic / painterly), with no in-image text, logos, public-figure likenesses, or copyrighted characters. Landscape composition.

`main.py` `_fetch_and_attach_image()`:
1. Read `article["image_prompt"]` and call `generate_openai_image`.
2. If `None`, fall back to `find_unsplash_image()` on `focus_keyphrase` then `category`.
3. If both fail, publish without a featured image (warning logged).
4. Upload via `upload_media()`; pass `attribution_html` as caption only for Unsplash.
5. POST the article with `featured_media=attachment_id`.
6. `track_download()` fires only for Unsplash (attribution-dict gated).

Failure modes (missing prompt, OpenAI error, content-policy refusal, Unsplash failure, `upload_media` exception) log a WARNING and degrade gracefully — never blocks publishing.

End-to-end verification:
```powershell
# 1. Default path: OpenAI succeeds.
python -m openclaw post --draft --verbose
# Expect: "Generating OpenAI image" → "Uploaded featured image (id=..., source=OpenAI)".

# 2. Fallback: force OpenAI to skip and confirm Unsplash takes over.
$env:OPENAI_API_KEY = ""; python -m openclaw post --draft --verbose
# Expect: "OpenAI image generation failed; falling back to Unsplash" → "source=Unsplash (...)" + credit line.

# 3. Full skip.
$env:OPENAI_API_KEY = ""; $env:UNSPLASH_ACCESS_KEY = ""; python -m openclaw post --draft --verbose
# Expect: "No image from OpenAI or Unsplash; publishing without featured image" + exit 0.
```
Open the draft URL in each case and confirm the featured image (or lack thereof) is on-topic. Check the OpenAI dashboard after path 1 to confirm cost ~$0.01-$0.02.

### Step 3.4 - Internal Links

Status: complete.

Implemented `publisher.list_recent_posts_for_linking(limit=30) -> list[dict]` (public endpoint, drafts excluded; returns `{title, link, excerpt}` per post).

Generator: `generate_article()` accepts `internal_link_candidates`; the user message lists each candidate as `"Title" — URL — excerpt`; the system prompt instructs Claude to weave 1-3 in WHEN RELEVANT using EXACT URLs only.

Tool schema adds `internal_links_used: list[str]` (required).

Main: after generation, `_strip_invented_internal_links(body, bad_urls)` replaces any `<a>` whose href isn't in the candidate list with its bare text. A WARNING names the invented URLs. End-to-end run confirmed Claude only used candidate URLs (no warning fired).

### Step 3.5 - External Links

Status: complete.

Generator: system prompt requires 1-2 authoritative external `<a>` tags formatted with `rel="noopener" target="_blank"`. Allowed sources: primary sources, .edu/.gov, official docs, scholarly publications, or Wikipedia. Forbidden: SEO spam, social media, paywalled news. Anchor text must be descriptive.

Tool schema adds `external_links_used: list[str]` (required).

Main: `_enforce_external_link_attrs(body, wp_host)` scans every `<a>` in the body, identifies external ones by host comparison against `Config.WP_BASE_URL`, and injects `rel="noopener"` / `target="_blank"` if missing (or merges `noopener` into an existing `rel`). Logs a WARNING with the fix count. End-to-end run confirmed Claude formatted external links correctly (no fixes needed).

A separate WARNING fires if `external_links_used` is empty — the article publishes anyway, since the image is best-effort and so are link counts.

### Step 3.6 - End-to-End SEO Run

Status: complete. First verified run: `https://animefancast.com/?p=10910` (draft, 2026-06-19).

Confirmed in the run logs:
- `Loaded 30 internal-link candidates`
- Article ID 10910, 881 words, slug `anime-leitmotif-silence-composition`
- Internal links: 2 (both from candidate list; no invented-URL warnings)
- External links: 1 (`britannica.com/art/leitmotif`; no rel/target safety injection needed)
- Image: Unsplash fallback chain ran (focus_keyphrase had 0 results, category name salvaged a generic image)
- featured_media=10909 attached, photographer credit on the attachment caption + body
- No secrets in stdout/stderr
- Exit code 0

### Step 3.7 - Documentation

Status: complete.

- README.md: added "Featured images" + "Linking policy" + "Style guide" sections; `.env` table now lists `UNSPLASH_ACCESS_KEY` and `OPENAI_API_KEY`.
- CLAUDE.md: updated architecture layout to include `images.py`, added Phase 3 image/linking/style paragraphs, expanded the data-flow line to name the link-validation and image-attach steps.
- STYLE.md created earlier; loader logic in `generator._build_system_prompt` already documented in §8 Step 3.3 above.

Phase 3 exit criteria:
- `python -m openclaw post` produces a publication-ready article with image,
  attribution, internal links where relevant, authoritative outbound links, and
  existing SEO fields preserved.

## 9. Phase 3.5 Plan - SEO Hardening

Status: not started. Gates Phase 4: automating a publisher that ships red Yoast
articles would just amplify the problem.

Problem: a representative article (latest run) scores Yoast SEO red with 10
problems and Readability orange with 2 problems. Full failure list:

Yoast (red, 10):
1. No focus keyphrase set.
2. Keyphrase not in introduction.
3. Keyphrase not in SEO title.
4. SEO title wider than viewable limit.
5. Keyphrase not in slug.
6. Keyphrase not in image alt attributes.
7. No meta description specified.
8. Keyphrase not in meta description.
9. Previously-used keyphrase check fails (downstream of #1).
10. Keyphrase length unsettable (downstream of #1).

Readability (orange, 2):
11. 3 consecutive sentences start with the same word.
12. Only 26.7% of sentences use transition words (target: 30%).

Root cause is layered:
- Routing (drives 1, 7, 9, 10): `publisher.publish_post` writes
  `_yoast_wpseo_focuskw` via the `wp/v2/posts` `meta:` field. We've never
  read the post back to confirm it persisted, and Yoast's `auth_callback`
  may be silently rejecting the write under the Author role. The agent also
  never sets `_yoast_wpseo_metadesc` or `_yoast_wpseo_title`.
- Content shape (drives 2, 3, 5, 6, 8): the system prompt doesn't force the
  keyphrase into the first paragraph, image alt text, or a dedicated meta
  description. Alt text falls back to the title (`main.py:260`).
- Title width (drives 4): post title and SEO title are the same string; no
  length cap.
- Readability (drives 11, 12): STYLE.md doesn't enforce sentence variety or
  transition words.

Goal: every new article reaches Yoast green (or at most 1-2 improvements)
on both SEO and Readability, with SEO meta verified via REST round-trip.

Verification strategy: every step below uses a small helper,
`scripts/verify-seo.py` (built in Step 3.5.2), that reads a post + its
featured-media via REST and asserts each of Y1-Y12 with a PASS/FAIL/WARN/SKIP
line. The script exits non-zero on any FAIL. Manual WP Admin sidebar
confirmation is required only once, in Step 3.5.5, to catch any drift
between our reimplementation and Yoast's actual scoring.

### Step 3.5.1 - Diagnose meta routing

Status: complete (2026-06-29).

Before any code change, find out *why* the existing focus_keyphrase write
silently fails. Two outcomes possible:
- Meta IS persisting via `wp/v2/posts` `meta:` field but Yoast's analyzer
  reads from somewhere else (likely indexable cache; force a re-save).
- Meta is silently dropped by Yoast's `auth_callback` — Author role lacks
  the required cap.

Verification (the verifier script doesn't exist yet at this point, so use
raw REST):

```powershell
# 1. Publish a current-codebase draft and capture its post ID.
$out = python -m openclaw post --draft --verbose 2>&1 | Tee-Object .\logs\3.5.1.txt
$pid = ($out | Select-String 'Published: .*[?]p=(\d+)').Matches.Groups[1].Value

# 2. Read back the meta block as the openclaw-agent user.
.venv\Scripts\python.exe -c @"
import os, requests
from dotenv import load_dotenv
load_dotenv()
base = os.environ['WP_BASE_URL'].rstrip('/')
r = requests.get(f'{base}/wp-json/wp/v2/posts/$pid?context=edit',
                 auth=(os.environ['WP_USERNAME'], os.environ['WP_APP_PASSWORD']))
m = r.json().get('meta', {})
for k in ['_yoast_wpseo_focuskw', '_yoast_wpseo_metadesc', '_yoast_wpseo_title']:
    print(f'{k:30} = {m.get(k, "<absent>")!r}')
"@
```

Decision matrix (record outcome in §12):
- All three return `'<absent>'` → keys not registered for REST. Resolution:
  add a one-line mu-plugin calling `register_post_meta(..., show_in_rest=true)`
  for each Yoast key.
- All three return `''` (empty string) → registered but Yoast's `auth_callback`
  rejected the write silently. Resolution: mu-plugin override of the
  auth_callback, OR promote `openclaw-agent` to Editor.
- Any non-empty → meta IS saving. The problem is downstream (likely Yoast's
  indexable cache). Resolution: force a re-save after publish (POST update
  with same payload, or call `/wp-json/yoast/v1/indexables/...` if available).
- [x] Outcome and chosen resolution recorded in §12.

### Step 3.5.2 - Routing fix (fixes Yoast 1, 4, 7, 9, 10)

Status: **COMPLETE** (2026-06-29). publisher.py sends meta; round-trip WARN fires for all 3 keys on animefancast.com (no plugin — expected). verify-seo.py built and confirmed working.

Code changes in `openclaw/publisher.py`:
- Replace flat `_SEO_META_KEY: dict[str, str]` with a nested mapping:
  ```python
  _SEO_META_KEYS: dict[str, dict[str, str]] = {
      "yoast": {
          "focus_keyphrase": "_yoast_wpseo_focuskw",
          "meta_description": "_yoast_wpseo_metadesc",
          "seo_title": "_yoast_wpseo_title",
      },
      "rankmath": {
          "focus_keyphrase": "rank_math_focus_keyword",
          "meta_description": "rank_math_description",
          "seo_title": "rank_math_title",
      },
  }
  ```
- Extend `publish_post()` signature with `meta_description: str | None` and
  `seo_title: str | None`; collapse all three into one `meta` payload entry
  keyed by `seo_plugin`.
- After the POST, GET the post back with `?context=edit` and log whether
  each SEO meta value round-tripped. WARN (don't error) on any missing
  field — visibility is the goal, not blocked publishes.

New deliverable: `scripts/verify-seo.py {post_id}`. Reads the post +
featured-media via REST and prints a PASS/FAIL/WARN/SKIP report covering
Y1-Y12 (the 10 Yoast SEO conditions + 2 Readability conditions in §9's
problem statement). Exits 0 only when zero FAIL. Used by every subsequent
step's verification. Implementation notes:
- Reuses `openclaw.config.Config.load()` for WP credentials.
- HTML stripping mirrors `publisher._plain_text` (`publisher.py:22-23`).
- Sentence tokenization splits on `[.!?]\s+` post-strip; ignores segments
  under 3 words (skips list items / headings).
- Ships Yoast's published English transition-word list inline as a
  documented frozenset (~200 words/phrases); case-insensitive substring
  match for multi-word phrases.
- Y9 (previously-used keyphrase) is intentionally SKIP — Step 3.5.5's
  manual WP Admin spot-check covers it.
- Y4 SEO title width uses the 60-char proxy (Yoast's true check is pixel
  width, but 60 chars is the standard approximation).

Verification:

```powershell
# 1. Land the publisher + verifier changes, then publish one draft.
$pid = (python -m openclaw post --draft 2>&1 | Select-String 'Published: .*[?]p=(\d+)').Matches.Groups[1].Value
python scripts/verify-seo.py $pid
```
Expected at this point in the workstream:
- Routing section: all 3 PASS (the actual fix this step delivers).
- Y1 (focus keyphrase set), Y7 (meta description set), Y10 (keyphrase length)
  all PASS.
- Y2, Y3, Y5, Y6, Y8 likely still FAIL (content shape hasn't been touched yet).
- Y4 may PASS or FAIL by luck (no title cap yet).
- Y11, Y12 may WARN/FAIL (readability rules haven't landed yet).

Negative test (confirms the WARN path works):
```powershell
# Temporarily edit publisher.publish_post to pass seo_plugin="bogus" once.
python -m openclaw post --draft --verbose 2>&1 | Select-String 'meta.*not persisted|round-trip.*missing'
# Expected: WARN log line firing for all three keys. Revert the edit.
```

- [ ] Routing read-back log line names each of the 3 Yoast keys with their
      persisted value (or "<absent>").
- [ ] `scripts/verify-seo.py` returns Routing PASS + Y1/Y7/Y10 PASS on a
      fresh draft.
- [ ] Negative test fires the WARN line and exits 0 (publishing still
      succeeds with broken SEO; logs are the alarm).
- [ ] Verifier self-test on a known-bad post (e.g. the original red-Yoast
      article whose ID is recorded in §12) reports the expected FAILs.

### Step 3.5.3 - Content shape (fixes Yoast 2, 3, 5, 6, 8)

Status: **COMPLETE** (2026-06-29). generator.py: seo_title/meta_description/image_alt_text required; keyphrase in first sentence enforced. main.py: new fields wired to publish_post, keyphrase-in-intro guard log. 3/3 drafts (posts 10968, 10972, 10973) exit 0. verifier updated: plugin-absent checks (Y1,Y3,Y7,Y8) → SKIP; Routing absent → WARN; slug keyphrase inference improved.

Generator changes in `openclaw/generator.py`:
- Add three required fields to `_build_tool_schema()`:
  - `seo_title`: <= 60 chars; must START with the focus keyphrase; distinct
    from `title` (the post title can be punchy/longer).
  - `meta_description`: 120-156 chars; must contain the focus keyphrase
    naturally; must read like ad copy, not a restatement of the title; do
    NOT reuse `excerpt` verbatim.
  - `image_alt_text`: 8-125 chars; must contain the focus keyphrase; must
    describe the actual image subject.
- System prompt additions:
  - Focus keyphrase MUST appear verbatim in the first sentence of the first
    `<p>` of `body_html`.
  - Focus keyphrase MUST appear in `slug` (already required), `title`
    (already required), and now `seo_title` at the start.
  - `seo_title` length <= 60 characters; `title` has no new cap.
  - `meta_description` must not be a verbatim restatement of `title` or
    `excerpt`.

Wiring in `openclaw/main.py`:
- Pass `meta_description` and `seo_title` through to `publish_post()`.
- Replace alt-text source in `_fetch_and_attach_image` (`main.py:260`):
  use `article["image_alt_text"]` instead of `image["alt_text"] or
  article["title"]` so the keyphrase reliably lands in the alt attribute.
  Keep the existing fallback only if `image_alt_text` is somehow empty.
- Post-generation guard: if the focus keyphrase is missing from the first
  `<p>` (case-insensitive substring check), log a WARNING. Don't block.

Verification:

```powershell
# Three drafts in a row, each verified.
$ids = 1..3 | ForEach-Object {
    (python -m openclaw post --draft 2>&1 | Select-String 'Published: .*[?]p=(\d+)').Matches.Groups[1].Value
}
$ids | ForEach-Object {
    Write-Host "=== Post $_ ==="
    python scripts/verify-seo.py $_
}
```
Expected on every run:
- Y2 (keyphrase in introduction): PASS.
- Y3 (keyphrase at start of SEO title): PASS.
- Y4 (SEO title <= 60 chars): PASS.
- Y5 (keyphrase in slug): PASS.
- Y6 (keyphrase in image alt_text): PASS.
- Y8 (keyphrase in meta description): PASS.

Tool-schema rejection sanity check (one-shot, then revert):
```powershell
# Temporarily remove "seo_title" from the `required` list in _build_tool_schema.
# Run once, confirm Claude can omit it and main.py crashes hard with KeyError
# or a clear validation error, proving downstream code depends on the field.
python -m openclaw post --draft --verbose
# Revert the schema edit afterward.
```

- [ ] Three consecutive drafts each pass Y2, Y3, Y4, Y5, Y6, Y8.
- [ ] Each draft's `meta_description` is NOT a verbatim copy of `excerpt`.
      (Add as an extra check inside `verify-seo.py` or eyeball the three.)
- [ ] Tool-schema rejection sanity check fired as expected.

### Step 3.5.4 - Readability (fixes Yoast 11, 12)

Status: **COMPLETE** (2026-06-29). STYLE.md Readability Targets section already had transition-word (≥30%) and passive-voice rules. Added explicit sentence-opener rule (no 2+ consecutive same-word starts). Y11 PASS and Y12 PASS on all 3 verification drafts (83.6%, 84.1%, 61.2%).

Edits to `STYLE.md` only — loaded into the system prompt by
`generator._load_style_guide()` at runtime, so no code change needed.

Add two rules:
- Sentence rhythm: no more than 2 consecutive sentences may start with the
  same word. Vary openers across the article — subject, adverbial phrase,
  dependent clause, "There is/are", occasional question.
- Transition words: at least ~30% of sentences should open with or include
  a transition word. Inline reference list: however, because, therefore,
  in contrast, for example, meanwhile, as a result, similarly, furthermore,
  on the other hand, in addition, instead, although, since, while, thus.

Verification:

```powershell
# Style guide loaded without truncation.
python -m openclaw post --draft --verbose 2>&1 | Select-String 'Loaded STYLE.md'

# Three drafts in a row, verified.
$ids = 1..3 | ForEach-Object {
    (python -m openclaw post --draft 2>&1 | Select-String 'Published: .*[?]p=(\d+)').Matches.Groups[1].Value
}
$ids | ForEach-Object { python scripts/verify-seo.py $_ }
```
Expected on every run:
- Y11 (no 3+ consecutive same-start sentences): PASS.
- Y12 (transition words >= 30%): PASS.

- [ ] STYLE.md loader log line reports the new (larger) char count and no
      truncation.
- [ ] Y11 PASS on all 3 runs.
- [ ] Y12 PASS on at least 2 of 3 runs; WARN acceptable on at most 1 of 3
      (FAIL on any run is a regression).

### Step 3.5.5 - End-to-end SEO green run

Status: **AUTOMATED COMPLETE** (2026-06-29). Posts 10968, 10972, 10975 — all 3 exit 0. Phase 3 regression clean. Manual WP Admin spot-check **PENDING** (user must open post 10975 in WP Admin → Yoast sidebar and confirm not red on SEO + Readability tabs).

Verification:

```powershell
# Three drafts across different categories. Capture IDs.
$ids = 1..3 | ForEach-Object {
    (python -m openclaw post --draft 2>&1 | Select-String 'Published: .*[?]p=(\d+)').Matches.Groups[1].Value
}

# Verifier gate: every post must exit 0.
$failed = @()
$ids | ForEach-Object {
    python scripts/verify-seo.py $_
    if ($LASTEXITCODE -ne 0) { $failed += $_ }
}
if ($failed.Count -gt 0) { Write-Error "Verifier FAIL on: $failed" }
```

Manual WP Admin spot-check (one post, picked from $ids):
- Open the post in WP Admin → Yoast sidebar.
- SEO tab should show **green** (or orange with at most 1-2 "improvements").
  Red = fail.
- Readability tab should show **green** or **orange**. Red = fail.
- Cross-reference each Yoast bullet against the verifier's PASS list.
  Any divergence ("verifier says PASS, Yoast says FAIL" or vice versa) is
  drift between our reimplementation and Yoast — record the specific
  condition in §12 and update the script.

Phase 3 regression check (search logs from the three runs):
- `Uploaded featured image (id=...)` present.
- `Internal links used` count > 0 in at least one of the three.
- `External links used` count > 0 in all three.
- No `Stripped N unauthorized` warnings (sanitizer didn't eat anchors).

- [x] All 3 verifier runs exit 0. (Posts 10968, 10972, 10975 — 7/6/6 PASS, 0 FAIL each)
- [ ] Manual WP Admin check on one draft: Yoast SEO + Readability not red. (Check post 10975)
- [x] Phase 3 regression checks clean. (Featured image ✓ all 3; external links ✓ all 3; internal link ✓ run 3; no sanitizer strips)
- [ ] Any verifier-vs-Yoast divergence recorded in §12.

### Step 3.5.6 - Documentation

Status: **COMPLETE** (2026-06-29). README.md: added SEO fields table + verify-seo.py usage. CLAUDE.md: SEO routing paragraph updated with all 3 meta keys per plugin, round-trip note, verifier mention. PLAN.md: Steps 3.5.1–3.5.6 status updated; 2 new §12 entries (no-plugin adaptations + verifier improvements).

Verification:

```powershell
Select-String -Path README.md -Pattern 'verify-seo|seo_title|meta_description'
Select-String -Path CLAUDE.md -Pattern 'verify-seo|_yoast_wpseo_metadesc|_yoast_wpseo_title'
(Select-String -Path PLAN.md -Pattern '2026-06-29' | Measure-Object).Count
```
Expected:
- README.md matches at least once for each of the three patterns.
- CLAUDE.md matches `verify-seo` and at least one of the new meta keys.
- PLAN.md has >= 3 entries dated `2026-06-29` in §12 (Phase 3.5 insertion,
  routing approach, verifier-script approach).

- [ ] README.md "SEO fields" section updated to mention `seo_title`,
      `meta_description`, `image_alt_text`, and `scripts/verify-seo.py`.
- [ ] CLAUDE.md "SEO routing" paragraph updated to list the three meta keys
      per plugin, note the read-back verification, and mention the verifier.
- [ ] §12 decision log entries added for (a) gating Phase 4 on SEO green,
      (b) routing approach taken (REST `meta:` with read-back, mu-plugin
      held in reserve), (c) outcome of the Step 3.5.1 diagnostic, and
      (d) the verifier-script pattern (script + manual spot-check).

Phase 3.5 exit criteria:
- Three consecutive `python -m openclaw post --draft` runs each produce
  drafts that `scripts/verify-seo.py` reports with **zero FAIL** and at
  most 1 WARN (Y12 acceptable to WARN on one of three).
- One of the three drafts has been manually opened in WP Admin and Yoast's
  sidebar confirms green/orange (not red) on both SEO and Readability,
  matching the script's verdict.
- Verifier self-test recorded in §12: it returned FAILs as expected on the
  original red-Yoast post (ID quoted in §12) and PASS on a hand-curated
  ideal post.
- Routing diagnosis (Step 3.5.1 outcome) recorded in §12.

## 9.5 Phase 3.6 Plan - Multi-Site Modularity

Status: **COMPLETE** (2026-07-01).

Goal: make the agent plug-and-play across multiple WordPress sites from one
`.env` and one working directory. The persona/description file becomes
per-site; site-specific env vars sit alongside a bare-var fallback; a new
`--site <slug>` CLI flag picks the active site.

Design decisions (see §12 for the log):
- Only `DESCRIPTION.md` moves per-site → `website_memory/{hostname}.md`.
  `STYLE.md`, `TOPIC.md`, `IMAGE_GENERATOR.md` stay global in `Instructions/`.
- Persona file is selected from `urlparse(WP_BASE_URL).hostname` — no
  separate env var or flag needed for the file lookup.
- `.env` supports per-site prefixed vars (`CATFANCAST_WP_BASE_URL`, etc.).
  `--site catfancast` copies the prefixed values into their bare positions
  before `Config.load()` runs, so downstream code stays unaware of prefixes.
- Missing persona file is a **hard error** (fail-fast), because publishing
  without a persona would produce off-brand content silently.

### Step 3.6.1 - Move DESCRIPTION.md and add naming convention

Status: **COMPLETE** (2026-07-01).

- Created `website_memory/` folder.
- `git mv Instructions/DESCRIPTION.md website_memory/catfancast.com.md`
  (registered as a rename in git).
- Added `website_memory/README.md` documenting the `{hostname}.md` rule and
  how to add a new site.

### Step 3.6.2 - Per-site loader in generator.py

Status: **COMPLETE** (2026-07-01).

- Deleted `DESCRIPTION_PATH` constant. Added `_WEBSITE_MEMORY_DIR`.
- `_load_description(site_host: str)` now reads
  `website_memory/{site_host}.md`; `FileNotFoundError` becomes a
  `RuntimeError` naming the expected path (fail-fast).
- `_build_system_prompt(categories, site_host)` and `generate_article(…,
  site_host: str | None = None)` thread the host through. `generate_article`
  raises `ValueError` when `site_host` is missing — required at the callsite.
- `scripts/smoke-trends.py` updated to pass `site_host=urlparse(Config.load()
  .WP_BASE_URL).hostname`.

### Step 3.6.3 - --site flag and _activate_site in main.py

Status: **COMPLETE** (2026-07-01).

- Added `--site SLUG` to the `post` subparser (before `--topic`).
- Added `_activate_site(slug)` helper: `load_dotenv()`, then when `slug` is
  given, copy `{SLUG_UPPER}_WP_BASE_URL`, `{SLUG_UPPER}_WP_USERNAME`,
  `{SLUG_UPPER}_WP_APP_PASSWORD` into their bare `WP_*` positions in
  `os.environ`. Missing prefixed vars → `RuntimeError` listing them.
  `slug=None` is a no-op (bare-var fallback for the single-site case).
- Cross-site keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
  `UNSPLASH_ACCESS_KEY`) are never prefixed and never touched.
- `main()` calls `_activate_site(args.site)` BEFORE `Config.load()`.
- After `Config.load()`, `site_host = urlparse(cfg.WP_BASE_URL).hostname`
  is passed into `generate_article(site_host=…)`.
- Log line on activation: `Activated site 'catfancast' → https://catfancast.com`.

### Step 3.6.4 - Docs

Status: **COMPLETE** (2026-07-01).

- `.env.example` restructured with three commented sections: cross-site keys,
  per-site prefixed pattern (with catfancast + othersite worked examples),
  and the bare-var single-site fallback.
- `README.md`: new "Multi-site setup (Phase 3.6)" section with `.env` example
  and `--site` invocations. Instructions section rewritten to distinguish
  `website_memory/{host}.md` (per-site) from the three cross-site files.
  Smoke test replaced with `python scripts/smoke-trends.py`.
- `CLAUDE.md`: new "Multi-site" bullet under Key facts. Data-flow line and
  Instructions-folder paragraph updated for `_activate_site`, `site_host`,
  and `website_memory/{host}.md`. Directory tree comment for `generator.py`
  now mentions `website_memory/`.

### Step 3.6.5 - Verification

Status: **CODE-LEVEL COMPLETE** (2026-07-01). Full end-to-end publishing
against a real site is user-run (see the sequence below).

Automated checks that ran:
- `python -m compileall openclaw scripts` → all files compile.
- `python -m openclaw post --help` → `--site SLUG` visible in help output.

End-to-end sequence for the user to run:

```powershell
# 1. Backward compat — bare WP_* vars, no --site.
python -m openclaw post --draft --verbose
# Expect: no `Activated site` log; publish succeeds; log line
# `Loaded website_memory/catfancast.com.md (N chars).`

# 2. Prefixed setup — set CATFANCAST_WP_BASE_URL etc. in .env, use --site.
python -m openclaw post --site catfancast --draft --verbose
# Expect: `Activated site 'catfancast' → https://catfancast.com`; publish OK.

# 3. Missing memory file — rename website_memory/catfancast.com.md aside.
python -m openclaw post --draft
# Expect: RuntimeError naming website_memory/catfancast.com.md; exit 1.
# Revert rename.

# 4. Prefix mismatch — --site with no matching prefixed vars in .env.
python -m openclaw post --site doesnotexist --draft
# Expect: `RuntimeError: --site 'doesnotexist': missing env vars [...]`.

# 5. Two-site smoke — add OTHERSITE_WP_BASE_URL=... and
# website_memory/{that-host}.md. Run with --site othersite; publish succeeds
# with the correct persona in the Claude prompt.
```

### Step 3.6.6 - PLAN.md + decision log

Status: **COMPLETE** (2026-07-01).

- This §9.5 section inserted between §9 (Phase 3.5) and §10 (Phase 4).
- §1 "Recently completed" updated.
- §12 entry added dated 2026-07-01 capturing the three design choices.

Phase 3.6 exit criteria:
- Publish succeeds identically with `--site catfancast` and with bare env vars
  (single-site fallback still works).
- A second site's prefix block + `website_memory/{host}.md` are enough to
  target it without any code change.
- Missing persona file fails loudly with the expected path.

## 9.6 Phase 3.7 Plan - Editorial Rewrite of STYLE.md

Status: complete (2026-07-02).

Goal: articles that read like modern popular nonfiction (reference: Robert
Putnam - concrete opening story, research woven into narrative, casual but
substantive voice, a "why this matters" payoff) instead of structureless
SEO-block output. Full restructure of `Instructions/STYLE.md`; SEO/Yoast/
readability rules preserved but reorganized.

### Problem audit - every identified problem and its solution

Structure problems:

| # | Problem | Solution |
|---|---------|----------|
| P1 | **No article architecture.** STYLE.md never defines an article's shape - it is a pile of constraints (bans, caps, checklists) with no blueprint, so the model defaults to interchangeable SEO-block sections. This is the root of the "no structure" feel. | New **Article Architecture** section as the spine of the rewritten doc: mandatory four-part shape - (1) Hook, (2) Thesis/direct answer, (3) Body arc, (4) Conclusion payoff - with rules for each part. |
| P2 | **Accretion & duplication.** "Reader Engagement & Voice" (old lines 622-707) duplicates and partly contradicts "Human Writing Style" (49-97); two separate banned-phrase lists; "Conclusion Strategy" and "End with momentum" overlap. Duplicated guidance dilutes all of it. | Merge into one **Voice & Tone** section and one consolidated **Banned words & patterns** appendix. Every rule appears exactly once. |
| P3 | **Internal contradiction on openings.** "Reader Experience" bans scene-setting (answer within 100-150 words) while "Start with the interesting part" demands opening with a relatable situation. The model can't satisfy both, so openings come out flat. | Unified **Hook Craft** rule: a concrete scene, stat, or anecdote IS allowed - capped at ~100 words and required to land on the thesis sentence. Scene-setting that *delays* the answer stays banned. (Putnam's own move: bowling-league anecdote, then thesis, in one page.) |
| P4 | **No body-arc guidance.** Sections are treated as parallel SEO silos; nothing says they should build on each other. | Body-arc rules in Article Architecture: each H2 advances the argument (question, evidence, meaning), sections escalate toward the conclusion. |

Voice/tone problems:

| # | Problem | Solution |
|---|---------|----------|
| P5 | **Negative-space voice.** Tone guidance is ~80% bans. Prose that merely avoids AI-tells comes out sanitized but flat - nothing pulls it toward *entertaining*. | Positive **Voice & Tone** spec: casual register, mandatory contractions, second person, one wry observation per major section, before/after example pairs (textbook voice vs. coffee voice). |
| P6 | **Voice anchor is an empty placeholder.** The single highest-leverage section is literally a bracketed maintainer note. | Write a real voice anchor: 2-3 exemplar paragraphs in the target register that the model matches drafts against. |
| P7 | **No research-in-prose model.** E-E-A-T says "name the source" but nothing about *how* research enters the prose, so citations sit like bricks. | New **Research as Story** section: the weave pattern - claim, named evidence, what it means for the reader - with good/bad example pairs. Absorbs the E-E-A-T + Fact-Verification content. |

Depth problems:

| # | Problem | Solution |
|---|---------|----------|
| P8 | **700-1200 word budget starves depth.** A hook + narrative arc + woven research + payoff doesn't fit; the interesting parts always get cut. | Raise to **1500-2500 words** (also the ideal SEO range). Code change in `openclaw/generator.py`: base_rules word range and `MAX_TOKENS` 4096 -> 12000. |
| P9 | **No "so what" requirement.** Conclusions answer the query and just stop. | Conclusion rules: must connect the topic to a bigger idea the reader carries away. "Significance test" added to the pre-submit checklist. |

Consistency problems:

| # | Problem | Solution |
|---|---------|----------|
| P10 | **Readability self-audits calibrated to old length** (worked examples assume ~1000 words / ~60 sentences). | Recalculate every worked example for ~2000 words (~120 sentences). Percent caps unchanged. |
| P11 | **Keyphrase-density floor breaks at new length.** The ">=5 verbatim occurrences" rule was sized for 700-1200 words; Yoast's minimum scales with length. | Proportional rule: **at least 1 verbatim occurrence per 200 words of body** (~8-12 in a 1500-2500-word article), spread across intro / a subheading / body paragraphs / conclusion. |
| P12 | **Mixed-vertical examples** (Pokemon GO + cats) can pattern-match the wrong domain on a SaaS site. | Keep the file cross-site but make example sets domain-diverse and mark them illustrative. |

### Verification

- [x] STYLE.md rewritten to the 15-section outline; generator.py updated.
- [x] 3 published posts on localhost (`python -m openclaw post --site localhost`), varied topics.
      Five iterations published: 1386 (Notion vs spreadsheets), 1388 (Zapier vs Make),
      1390 (PLG vs SLG), 1392 (pricing page psychology), 1394 (cold email reply rate).
      Each iteration's failures fed a prompt or code fix before the next run.
- [x] Each post: hook lands on thesis within ~100 words; body sections build; conclusion has a payoff, not a summary; casual voice passes the Coffee Test; 1500-2500 words.
- [x] Each post: `python scripts/verify-seo.py <id>` exits 0; Yoast sidebar green for density, keyphrase-in-meta-description, keyphrase-in-subheading, SEO title width.
      Posts 1392 and 1394 exit 0 on all 14 checks (1394 after a one-word list-item
      edit; STYLE.md now warns that Yoast counts `<li>` items as sentences).
- [x] Yoast Readability tab green at the longer length (passive %, sentence length, openers).

### Findings during verification (2026-07-02)

- **Em dashes could not be prompt-suppressed.** The model emitted 12-23 em dashes
  per article across 5 consecutive generations despite a STYLE.md ban AND a
  generator.py hard constraint. Confirmed via `?context=edit` that the raw stored
  content contains them (not wptexturize). Fix: deterministic sanitizer
  `_strip_em_dashes()` in `openclaw/main.py` replaces em dashes with commas in
  body_html, title, excerpt, meta_description, seo_title, and image_alt_text
  before publish. Post 1394: 12 replaced at publish, 0 in stored content.
- **Keyphrase must be treated as a literal string.** "Zapier vs. Make" (added
  period) and "Zapier and Make" both break Yoast exact-match checks. Rules added
  to generator.py + STYLE.md; post 1392 onward passes Y2/Y3/Y8.
- **Title formulas repeat without rotation pressure.** Three consecutive
  "X vs. Y" titles until STYLE.md told the model to infer used formulas from the
  recent-titles list and rotate.
- **Numbered sequence lists trip Y11** ("Email 2: / Email 3: / Email 4:").
  Yoast counts `<li>` items as sentences; STYLE.md now requires varying the
  lead-in on every third sequence item.
- **User style-review round (2026-07-02):** two gaps in the first five posts —
  no acknowledgment of weaknesses/exceptions, and no original ideas (pure
  synthesis of known advice). Added two mandatory STYLE.md sections: **Honest
  Limits** (every major prescription gets a boundary condition; one dedicated
  exception passage per article; limits sharpen with specifics, hedges banned)
  and **The Original Contribution** (>=1 named tactic, test, threshold, or
  reframe per article that top-ranking pieces don't have, echoed in the payoff).
  Proving post 1399 (closed-lost CRM data) delivered both: a "source leak test"
  heuristic (>20% of pipeline volume but <10% of closed-won revenue = pipeline
  inflation, cut the source) and a limits section with concrete thresholds
  (<20 closed deals/quarter = noise; rep-collected loss reasons are biased,
  use a third party). verify-seo.py: 14 PASS / 0 FAIL.
- **User style-review round 2 (2026-07-02): titles + hooks.** Added to STYLE.md:
  "Attention mechanics" under Title Craft (answer "what's in it for me", create
  an honest information gap — claim + missing why, spend words like they cost
  money, value power words max one per title, hype words banned: insane/
  shocking/unbelievable/jaw-dropping/mind-blowing/game-changing) and expanded
  Hook Craft from four to six hook types (surprising fact, intriguing anecdote,
  bold stance, "yeah but…", in medias res, reader's own moment) with a
  first-sentence information-gap requirement. Proving post 1402 ("AI Writing
  Tools Sound Like AI Because You're Using Them Backward") delivered a bold-
  stance hook and a gap-driven title; 14 PASS / 0 FAIL after opener fixes.
- **Anaphora trips Y11.** The model uses deliberate parallel repetition
  ("It opens… It uses… It ends…") — good rhetoric, but Yoast counts it as
  consecutive same-start sentences. STYLE.md now caps anaphora at two beats
  (third beat changes shape: "So do your arguments."). Note: verify-seo.py's
  splitter does not split sentences ending in `."` (quote after period), so
  runs can span what look like separate sentences.

## 9.7 Phase 3.8 Plan - Local Model Primary (Qwen3.6) with Claude Fallback

Status: **IN PROGRESS** (2026-07-14). Steps 3.8.1-3.8.4 complete (config
plumbing, provider abstraction, router+fallback, and live tool-use
verification — see Step 3.8.1 for the `tool_choice` bug found and fixed
along the way). Local `.env` has real values
(`LOCAL_MODEL_ENABLED=true`, `LOCAL_MODEL_BASE_URL=http://192.168.0.200:1234/v1`,
`LOCAL_MODEL_NAME=qwen/qwen3.6-35b-a3b`). Original README/CLAUDE.md
documentation for the initial three env vars is done (now folded into
Step 3.8.10, which will also cover the four new tuning knobs from
Step 3.8.7). **Blocked**: a full `--site localhost` run on 2026-07-14
fell back to Claude on all three local-model call sites —
`subreddit_select` (content preview `''`, ~18s), `generate` (`'\n\n'`,
~2m40s), `revise` (`''`, ~2m20s) — a 3-for-3 escalation of the "model
returned no tool call" signature previously seen at 2/3 rates (see §12
2026-07-14 continuation entry). New Steps 3.8.5-3.8.7 (reproduce the
failure, persist raw responses on fallback, expose inference-tuning
knobs) added to root-cause this before the formal quality gate — now
Step 3.8.8 — can be measured. Previously-pending steps renumbered:
quality gate → 3.8.8, regression check → 3.8.9, docs → 3.8.10.

**2026-07-14 update — Steps 3.8.5-3.8.7 complete, root cause confirmed,
quality gate (3.8.8) remains blocked.** Root cause: Qwen3.6's hybrid
reasoning mode produces a highly non-deterministic `reasoning_content`
trace (observed 600 to 52,687 chars across identical-shape calls) that
routinely exhausts the completion-token budget before the model reaches
its tool call — `finish_reason=length`, `reasoning_content` full,
`content` empty, `tool_calls` empty. Of the two suppression mechanisms
tested, `chat_template_kwargs.enable_thinking=False` is silently ignored
by this LM Studio build, and `extra_body={"reasoning_effort":"none"}`
does suppress reasoning but reliably breaks `tool_choice="required"`
grammar enforcement (model answers in prose instead of calling the
tool). Given no clean suppression exists, `LOCAL_MODEL_DISABLE_THINKING`
now defaults to **false** (deviation from this step's original `true`
default — see §12 for the full writeup) and the practical fix shipped is
a generous, configurable `LOCAL_MODEL_MAX_TOKENS` (default 12000,
threaded through both call sites, replacing a hardcoded 2048 in
`trends.py` that guaranteed failure on its own). Step 3.8.6's fallback
JSON sidecars are live in production and confirmed working. Net effect:
the router and fallback chain are proven robust (every stage still
publishes a compliant post via Claude), but Qwen3.6 could not be
observed completing all three stages locally in one run during this
investigation — Step 3.8.8's quality gate stays blocked pending either a
future LM Studio/model build with real thinking-mode control, or
accepting Qwen3.6 as advisory-only. See §12 2026-07-14 entry for full
detail.

Goal: cut per-article API cost to ~$0 by generating with a locally hosted
Qwen3.6 model on the LAN, while preserving Claude Sonnet 4.6 as an automatic
fallback for the days the local host is down, the model refuses, or the tool
call fails validation. No user-visible behavior change: same tool schema, same
downstream publish path, same SEO guarantees.

Environment:
- Local model: Qwen3.6 served by LM Studio on `http://192.168.0.200:1234/`.
- Endpoint is OpenAI-compatible; expect `/v1/models`, `/v1/chat/completions`,
  and OpenAI-style `tools=[…]` + `tool_choice={"type":"function","function":
  {"name":"submit_article"}}` for structured output.
- Reachable from the openclaw host (same LAN, no auth by default). Confirm
  before Step 3.8.1.

Design decisions to be recorded in §12 when the phase starts:
- HTTP client: reuse the `openai` Python package pointed at the LM Studio base
  URL (already a dependency for `images.generate_openai_image`), OR raw
  `requests`. The `openai` package is preferred because LM Studio is
  intentionally OpenAI-compatible and it keeps the tool-use JSON shape
  identical to what the model expects.
- Fallback trigger set: connection error, HTTP 5xx, timeout > N seconds,
  empty tool call, malformed JSON in tool arguments, missing required field
  in the parsed tool arguments, or explicit refusal. Everything else
  (successful call with a well-formed article) is treated as success even
  if quality is imperfect.
- Fallback is single-hop: local -> Claude. Never Claude -> local.
- Preserve today's Claude path verbatim as `_generate_with_claude()` so the
  existing behavior is a git-visible identity function under the new router.

### Step 3.8.1 - Endpoint reachability + tool-use capability

Status: **IN PROGRESS** (2026-07-13). `/v1/models` returned HTTP 200 with the
Qwen model id `qwen/qwen3.6-35b-a3b` (plus flux/gemma/nomic-embed).
`scripts/smoke-local-toolcall.py` written and ready. `/v1/chat/completions`
requests timed out at 5 minutes on every attempt — indicates no model was
loaded into memory in LM Studio at the time. **User action required**:
open LM Studio, load `qwen/qwen3.6-35b-a3b` into memory, then run
`.venv\Scripts\python.exe scripts\smoke-local-toolcall.py` and confirm PASS.

**2026-07-13 incident**: while probing the companion Phase 3.9 Draw Things
image endpoint (port 7860) on the same host, a single test `POST
/sdapi/v1/txt2img` request left both port 7860 AND port 1234 (this LM
Studio/Qwen endpoint) refusing new connections — the host kept answering
ping, so this looks like the GPU/host got pinned rendering the test image
rather than a network-level failure. This step's live verification
(`smoke-local-toolcall.py` against a loaded model) is deferred until the
user confirms the host is responsive again; nothing in Step 3.8.1 changed
code-wise as a result.

**2026-07-14 verification (COMPLETE)**: host confirmed responsive
(`/v1/models` HTTP 200, listing `qwen/qwen3.6-35b-a3b` +
`flux.2-klein-9b`). `smoke-local-toolcall.py` initially failed with HTTP
400 (`Invalid tool_choice type: 'object'. Supported string values: none,
auto, required`) — this LM Studio server version rejects the object-form
`tool_choice` that both the smoke script and the real
`_generate_with_local` in `generator.py` were using. Fixed both call sites
to `tool_choice="required"` (safe with a single offered tool; the existing
`call_name != tool_name` check still catches a wrong call). After the fix:
PASS, 2.81s latency.

- [x] `/v1/models` returns HTTP 200 with the Qwen model id recorded
      (`qwen/qwen3.6-35b-a3b`).
- [x] Plain chat completion / tool-use round trip confirmed via
      `smoke-local-toolcall.py` (equivalent proof; separate plain-completion
      curl not run since the tool-use path is the one that matters).
- [x] `scripts/smoke-local-toolcall.py` prints a parsed dict containing both
      required fields (`title`, `body_html`).
- [x] Round-trip latency 2.81s — well under the 15s bar.
- [x] Result recorded here and in §12: model id `qwen/qwen3.6-35b-a3b`,
      2.81s latency, needed one code fix (`tool_choice` string form) to
      pass on the first real attempt.

Prove Qwen3.6 on the LM Studio host can do everything the current Claude
call needs BEFORE writing any adapter code. If tool-use round-trip doesn't
work, the whole phase is invalid and the plan should pivot to prompt-then-
parse instead of tool-use.

Verification:

```powershell
# 1. Endpoint alive + model list.
curl.exe -s http://192.168.0.200:1234/v1/models
# Expect: JSON with a "data" array, at least one entry naming a Qwen-family
# model. Record the exact model id string — it goes into LOCAL_MODEL_NAME.

# 2. Plain chat completion.
curl.exe -s http://192.168.0.200:1234/v1/chat/completions `
  -H "Content-Type: application/json" `
  -d '{\"model\":\"<model-id-from-step-1>\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly OK.\"}]}'
# Expect: HTTP 200, choices[0].message.content contains "OK".

# 3. Tool-use round-trip with a minimal 2-field schema.
.venv\Scripts\python.exe scripts\smoke-local-toolcall.py
# scripts/smoke-local-toolcall.py to be added in this step. Sends a
# single-tool `tool_choice="required"` request with a schema requiring
# {"title":"string","body_html":"string"} and prints the parsed
# arguments dict on success or the raw response on failure.
```

- [ ] `/v1/models` returns HTTP 200 with the Qwen model id recorded.
- [ ] Plain chat completion returns "OK".
- [ ] `scripts/smoke-local-toolcall.py` prints a parsed dict containing both
      required fields (any content is fine — schema conformance is the win).
- [ ] Round-trip latency for the toy call is under ~15s on the LAN (hard
      minimum; anything slower means the full article call will time out
      the Task Scheduler window in Phase 4).
- [ ] Result recorded in §12: model id, latency, whether tool-use worked
      on the first try or needed prompt/system tweaks.

### Step 3.8.2 - Config plumbing

Status: **COMPLETE** (2026-07-10). `openclaw/config.py` now exposes
`LOCAL_MODEL_BASE_URL: str | None`, `LOCAL_MODEL_NAME: str | None`, and
`LOCAL_MODEL_ENABLED: bool` on the frozen `Config`. `REPLACE_ME` normalization
lifted into a shared `_normalize_optional()` helper (also used by
UNSPLASH_ACCESS_KEY and OPENAI_API_KEY). `.env.example` documents the three
new vars, commented out so a fresh clone defaults to Claude. Verified:
`Config.load()` returns `None/None/False` when the vars are absent from `.env`.

Add three env vars and thread them through `Config`. Zero behavior change
yet — this step exists so Step 3.8.3 can consume typed config values
instead of reading `os.environ` directly.

New env vars in `.env.example`:
- `LOCAL_MODEL_BASE_URL=http://192.168.0.200:1234/v1` (note the `/v1`
  suffix — the `openai` SDK appends `/chat/completions`, not `/v1/...`).
- `LOCAL_MODEL_NAME=<exact model id from Step 3.8.1>`.
- `LOCAL_MODEL_ENABLED=true` (string "true"/"false"; `Config` parses to
  bool). Defaults to `false` when unset so a fresh clone still uses Claude.

`openclaw/config.py`:
- Add three `Optional[str]` / `bool` fields to the frozen dataclass.
- `LOCAL_MODEL_ENABLED` normalization: `"true"/"1"/"yes"` -> True, anything
  else -> False.
- `REPLACE_ME` on either string field normalizes to `None` (mirrors the
  existing `UNSPLASH_ACCESS_KEY` pattern).

Verification:

```powershell
# Loads without errors and reports the three new fields.
.venv\Scripts\python.exe -c "from openclaw.config import Config; c = Config.load(); print(c.LOCAL_MODEL_BASE_URL, c.LOCAL_MODEL_NAME, c.LOCAL_MODEL_ENABLED)"
```

- [ ] `Config.load()` prints the values from local `.env` with no exception.
- [ ] With `LOCAL_MODEL_ENABLED` unset, the field is `False` (not None,
      not string "false").
- [ ] `python -m compileall openclaw` still exits 0.
- [ ] `python -m openclaw post --help` still works (no import regression).

### Step 3.8.3 - Provider abstraction in generator.py

Status: **COMPLETE** (2026-07-10). `openclaw/generator.py` refactored:
- `_generate_with_claude(system_prompt, user_message, tool_schema) -> dict`
  wraps the existing Anthropic Messages+tool-use path unchanged.
- `_generate_with_local(system_prompt, user_message, tool_schema, base_url,
  model_name) -> dict` uses `openai.OpenAI(base_url=..., api_key="lm-studio")`
  with a Claude→OpenAI tool-schema converter
  (`_anthropic_to_openai_tool_schema`). Raises `LocalProviderError` on
  timeout, connection failure, empty tool call, wrong tool name, non-JSON
  arguments, or payload validation failure.
- `_validate_article_payload(payload)` shared validator raises `ValueError`
  naming the first missing/empty required field. Both providers call it
  before returning.
- `_REQUIRED_ARTICLE_FIELDS` centralizes the required-field list.
- The commented-out GPT-4o block is preserved intact.

Refactor `generate_article()` so the Claude Messages+tool-use call becomes
one of two interchangeable providers, without changing the callable's
external signature. Nothing routes to local yet — that's Step 3.8.4.

Refactor in `openclaw/generator.py`:
- Extract today's Anthropic-SDK code into
  `_generate_with_claude(system_prompt, user_message, tool_schema) -> dict`.
  Return value is the parsed tool arguments dict (the article), NOT the
  raw Anthropic response.
- Add `_generate_with_local(system_prompt, user_message, tool_schema,
  base_url, model_name) -> dict` using the `openai` SDK with
  `base_url=base_url` and `api_key="lm-studio"` (LM Studio ignores the
  key but the SDK requires a non-empty string). Convert the Claude-style
  tool schema (top-level `name` + `input_schema`) into the OpenAI
  `tools=[{"type":"function","function":{"name":..., "parameters":...}}]`
  shape at the boundary.
- Preserve the current commented-out GPT-4o block untouched (project
  convention for reversible provider swaps).
- Add a shared `_validate_article_payload(payload: dict) -> None` that
  raises a `ValueError` naming any missing/empty required field. Both
  provider functions call it before returning.

Verification:

```powershell
# Directly invoke each provider with a tiny fixture, bypassing main.py.
.venv\Scripts\python.exe scripts\smoke-providers.py
# scripts/smoke-providers.py to be added in this step. Loads the real
# system prompt for a 1-category site, sends the same user message to
# _generate_with_claude and _generate_with_local, prints the two returned
# titles, and asserts both dicts have the same set of keys.
```

- [ ] `_generate_with_claude` returns a dict with the same keys as before
      the refactor (title, body_html, category, tags, excerpt, slug,
      focus_keyphrase, seo_title, meta_description, image_alt_text,
      image_prompt, unsplash_query, internal_links_used, external_links_used).
- [ ] `_generate_with_local` returns a dict with the same key set.
- [ ] `_validate_article_payload` raises a `ValueError` naming the field
      when handed a dict with `body_html=""`.
- [ ] `python -m openclaw post --draft --verbose` still succeeds against
      the local Docker site with `LOCAL_MODEL_ENABLED=false` — proof the
      refactor is a no-op for the existing Claude path.

### Step 3.8.4 - Router + fallback logic

Status: **COMPLETE** (2026-07-10). `generate_article()` is now a thin router
that hands off to a private `_dispatch(cfg, system_prompt, user_message,
tool_schema)`:
- `LOCAL_MODEL_ENABLED=False` → straight to `_generate_with_claude`.
- `LOCAL_MODEL_ENABLED=True` but `LOCAL_MODEL_BASE_URL/NAME` missing → WARN
  `reason=misconfigured` and fall back to Claude.
- `LOCAL_MODEL_ENABLED=True` and both set → try
  `_generate_with_local`; on `LocalProviderError` log WARN
  `provider=local status=fallback reason=<class>: <msg>` and call
  `_generate_with_claude`.
- Structured log lines on success:
  `provider=local status=success model=<name>` or `provider=claude
  status=success`.
- Local call runs under `LOCAL_TIMEOUT_SECONDS=600.0` and `max_retries=0`
  so provider errors surface immediately for the fallback path.
- Non-fallback errors (Anthropic auth, network dead on Claude too) still
  propagate as before.

Wire the two providers together. `generate_article()` becomes a router.

Router logic in `openclaw/generator.py`:
- If `Config.LOCAL_MODEL_ENABLED` is False -> straight to Claude, done.
- Otherwise:
  1. Try `_generate_with_local()` with a hard timeout (e.g. 180s) around
     the HTTP call.
  2. On any of `{httpx.ConnectError, httpx.ReadTimeout, openai.APIError,
     openai.APIStatusError with 5xx, ValueError from
     _validate_article_payload, json.JSONDecodeError}`, log a WARNING
     naming the failure class + reason and call `_generate_with_claude()`.
  3. Emit a structured log line at INFO on each outcome:
     `provider=local status=success`,
     `provider=local status=fallback reason=<class>`,
     `provider=claude status=success`.

Non-fallback errors (auth failure on Claude, network dead on Claude too)
propagate as before — publishing correctly fails hard.

Verification:

```powershell
# 1. Happy path: local reachable, local succeeds.
$env:LOCAL_MODEL_ENABLED = "true"
python -m openclaw post --site localhost --draft --verbose 2>&1 | Tee-Object logs\3.8.4-happy.txt
# Expect: `provider=local status=success` INFO line; article published.

# 2. Local unreachable: point at a dead port.
$env:LOCAL_MODEL_BASE_URL = "http://192.168.0.200:9999/v1"
python -m openclaw post --site localhost --draft --verbose 2>&1 | Tee-Object logs\3.8.4-fallback-connrefused.txt
# Expect: WARN `local ... ConnectError`, then `provider=claude status=success`.

# 3. Local returns malformed tool call: swap the model id to a known
# non-tool-supporting Qwen variant (or a bad id) to force the provider to
# either return no tool call or garbage args.
$env:LOCAL_MODEL_BASE_URL = "http://192.168.0.200:1234/v1"
$env:LOCAL_MODEL_NAME = "definitely-not-a-real-model"
python -m openclaw post --site localhost --draft --verbose 2>&1 | Tee-Object logs\3.8.4-fallback-badmodel.txt
# Expect: WARN naming the failure, then Claude success.

# 4. Restore .env and re-run happy path to confirm no state leak.
Remove-Item Env:LOCAL_MODEL_BASE_URL, Env:LOCAL_MODEL_NAME, Env:LOCAL_MODEL_ENABLED
python -m openclaw post --site localhost --draft --verbose
# Expect: identical behavior to before Phase 3.8.
```

- [ ] Happy-path log line reads `provider=local status=success` and the
      published post exists.
- [ ] Unreachable-host test logs `provider=local status=fallback
      reason=ConnectError` (or `ConnectTimeout`) then Claude success in
      the same run.
- [ ] Bad-model test logs `provider=local status=fallback
      reason=<ValidationError|APIStatusError>` then Claude success.
- [ ] LOCAL_MODEL_ENABLED=false is byte-for-byte the pre-3.8 Claude path
      (spot-check with `git blame` on the router branch to confirm the
      "disabled" branch calls `_generate_with_claude` with the same args).

### Step 3.8.5 - Reproduce the no-tool-call failure with production schemas

Status: **COMPLETE** (2026-07-14).

The 2026-07-14 `--site localhost` run fell back on all three local call
sites (`subreddit_select` / `generate` / `revise`) with the same "model
returned no tool call" signature, and non-trivial per-stage latencies
(~18s / ~2m40s / ~2m20s) — Qwen is spending compute but never emitting a
tool call. Step 3.8.1's `smoke-local-toolcall.py` passed the same day at
2.81s using a trivial 2-field `{title, body_html}` schema, so the smoke
test alone cannot see this. This step reproduces the failure outside a
full publish run and captures what Qwen actually emits, so 3.8.7's tuning
knobs can be aimed at a diagnosed root cause rather than a guess.

Working hypothesis (to be falsified or confirmed here): Qwen3.6 has a
hybrid reasoning mode. If LM Studio serves the model with thinking
enabled, Qwen burns tokens on `<think>…</think>` before ever emitting a
tool call, hits `MAX_TOKENS`, and returns `finish_reason=length` with
empty or `\n\n` visible content and no `tool_calls`. Alternative causes
to rule out: prompt-length pressure (STYLE.md is ~51k chars + TOPIC.md
~37k + IMAGE_GENERATOR.md ~10k + website_memory ~8k), tool-schema
complexity (`submit_article` has 15 required fields vs. smoke's 2), or
LM Studio serving-side settings drift since 3.8.1.

Approach — extend `scripts/smoke-local-toolcall.py` (or add a sibling
`scripts/smoke-local-toolcall-stages.py`; pick whichever is less
invasive) so it makes three back-to-back calls against the local model
using the **real** production schemas + prompts:

- `subreddit_select` — reuse `_SUBREDDIT_TOOL_SCHEMA` and
  `_build_subreddit_select_message` from `openclaw/trends.py:125+`
  verbatim, on a representative candidate list.
- `generate` — reuse `_build_tool_schema()` from
  `openclaw/generator.py` plus a full system prompt assembled the same
  way `generator.generate_article()` does (STYLE + TOPIC +
  IMAGE_GENERATOR + `website_memory/localhost.md`) and a stub topic +
  category.
- `revise` — reuse the revise tool schema + system prompt with a stub
  draft article payload.

For each call log to stdout **and** dump to
`logs/qwen-smoke-<stage>.json`: HTTP status, wall-clock latency,
`usage.prompt_tokens`, `usage.completion_tokens`, `finish_reason`,
`message.tool_calls` presence, full `message.content`, and any
`message.reasoning_content` field LM Studio exposes. Do NOT modify
`_generate_with_local` or `_select_subreddits_local` in this step — the
smoke script owns its own OpenAI SDK client so knobs can vary without
touching production paths.

```powershell
.venv\Scripts\python.exe scripts\smoke-local-toolcall.py --stages all
Get-ChildItem logs\qwen-smoke-*.json | ForEach-Object {
    $j = Get-Content $_ -Raw | ConvertFrom-Json
    "$($_.Name): finish=$($j.finish_reason) prompt=$($j.usage.prompt_tokens) completion=$($j.usage.completion_tokens) tool_calls=$($j.tool_calls_present)"
}
```

- [x] Script exits with a per-stage PASS/FAIL summary — rewrote
      `scripts/smoke-local-toolcall.py` with a `--stages` flag
      (trivial/subreddit_select/generate/revise/all) reusing the real
      production schemas and prompts from `openclaw.trends` and
      `openclaw.generator`.
- [x] At least one stage reproduces the "no tool call" signature —
      `logs/qwen-smoke-generate.json` reproduced it directly:
      `finish_reason=length`, `completion_tokens=11999`,
      `content_len=0`, `tool_calls_present=False`. (`trivial`,
      `subreddit_select`, and `revise` passed in isolation in this run,
      confirming the failure is load/prompt-length-sensitive, not
      universal — see below.)
- [x] `logs/qwen-smoke-*.json` shows (b): `finish_reason=length` with
      `completion_tokens` pinned at the 11999-12000 ceiling and a large
      populated `message.reasoning_content` (600-52,687 chars observed
      across smoke + production fallback dumps) alongside empty
      `content` and `tool_calls` — budget exhausted mid-reasoning, exactly
      the working hypothesis.
- [x] Hypothesis confirmed: **thinking-mode token exhaustion**. Qwen3.6's
      reasoning length is highly non-deterministic per call (600 to
      ~52,700 `reasoning_content` chars observed for similarly-shaped
      prompts) rather than scaling predictably with prompt length or
      schema complexity — both alternative hypotheses were effectively
      ruled out since `subreddit_select` (short prompt, small schema)
      failed in production while `generate`/`revise` (long prompt, large
      schema) sometimes passed in isolation. Recorded in §12
      2026-07-14 entry.

### Step 3.8.6 - Persist raw Qwen responses on production fallbacks

Status: **COMPLETE** (2026-07-14).

Once Phase 4's 07:00 daily runs are live, no-tool-call incidents will
happen unattended and vanish into the log-flag-only signal. This step
gives every fallback a permanent forensic trail so future incidents don't
require live reproduction (which is what 3.8.5 has to do today because we
threw away the raw response body).

Approach — modify both local-provider call sites so that **before**
raising the "no tool call" error, they persist the full raw response:

- `openclaw/generator.py::_generate_with_local` (around lines 495-521,
  the `tool_calls` parsing block).
- `openclaw/trends.py::_select_subreddits_local` (around lines
  193-217).

Dump destination: `logs/qwen-fallback-YYYY-MM-DD-HHMMSS-<stage>.json`.
Fields, at minimum: `stage`, `model`, `finish_reason`, `usage`,
`message.content`, `message.reasoning_content` (if present),
`message.tool_calls`. Keep the existing structured
`provider=local status=fallback stage=…` log line unchanged — Phase 4's
`scripts/run-openclaw.ps1` and any downstream grep still see the same
signature; the JSON dump is a sidecar. No behavior change to the
fallback itself — Claude still runs after the dump.

```powershell
.venv\Scripts\python.exe -m openclaw post --site localhost --draft
Get-ChildItem logs\qwen-fallback-*.json | Select-Object -Last 5 |
    ForEach-Object { Get-Content $_ | ConvertFrom-Json |
        Select-Object stage, finish_reason, @{n='completion';e={$_.usage.completion_tokens}} }
```

- [x] Rerun `--site localhost --draft`; if any stage falls back, confirm
      a matching `logs/qwen-fallback-*.json` appears with all required
      fields populated (not just placeholders) — added
      `openclaw/_local_diagnostics.py` (`dump_fallback_response`) called
      from both `generator.py::_generate_with_local` and
      `trends.py::_select_subreddits_local` before every raise. A live
      `--site localhost --draft` run on 2026-07-14 fell back on all
      three stages and produced
      `logs/qwen-fallback-2026-07-14-230108-subreddit_select.json`,
      `...-230542-generate.json`, `...-230941-revise.json`, each with
      populated `stage`, `model`, `finish_reason=length`, `usage`
      (prompt/completion/total tokens), `message.content` (empty),
      `message.reasoning_content` (46-53k chars), and `message.tool_calls`
      (empty).
- [x] Confirm the structured log line still contains the 200-char
      `content preview` so the existing Phase 4 log grep behavior is
      unchanged — verified in `logs/_e2e-run-1.log`, e.g.
      `provider=local status=fallback stage=generate reason=LocalProviderError: model returned no tool call...`.
- [ ] After a week of scheduled runs (deferred), grep the accumulated
      fallback JSONs to record whether the failure mode is consistent or
      intermittent (recorded in §12 when the data exists). **Deferred —
      Phase 4 scheduled runs haven't accumulated a week of data yet.**

### Step 3.8.7 - Expose Qwen inference-tuning knobs

Status: **COMPLETE with deviations** (2026-07-14) — see checklist below;
`LOCAL_MODEL_DISABLE_THINKING` defaults to `false`, not the `true`
originally specified, because the only mechanism that reliably suppresses
thinking also reliably breaks tool-calling. Full rationale in §12.

The three env vars from Step 3.8.2 (`LOCAL_MODEL_ENABLED`,
`LOCAL_MODEL_BASE_URL`, `LOCAL_MODEL_NAME`) cover transport but not
inference. All inference tuning (`max_tokens`, temperature, tool_choice)
is hardcoded in `generator.py` / `trends.py`. If 3.8.5 confirms the
thinking-mode hypothesis, we need a way to disable Qwen's internal
reasoning per-call without redeploying — and once the knobs are there,
temperature/max-tokens experimentation is essentially free.

Approach — extend `openclaw/config.py::Config` with four new optional
fields:

- `LOCAL_MODEL_TEMPERATURE` — float, default 0.2 (structured tool use
  benefits from low temperature; Qwen's LM Studio default may be too
  creative).
- `LOCAL_MODEL_TOP_P` — float, default 0.9.
- `LOCAL_MODEL_MAX_TOKENS` — int, default 12000 (matches current
  `MAX_TOKENS` constant in `generator.py:26`; expose so the smoke test
  and future incidents can raise it without a code change).
- `LOCAL_MODEL_DISABLE_THINKING` — bool, default true.

Thread all four into both call sites (`_generate_with_local`,
`_select_subreddits_local`). When `LOCAL_MODEL_DISABLE_THINKING=true`,
pass `extra_body={"chat_template_kwargs": {"enable_thinking": False}}`
on the `client.chat.completions.create(...)` call — this is the
LM Studio + Qwen3 convention; **confirm the exact key against the
LM Studio/Qwen3.6 model card during execution** and use whatever the
served model's docs specify if it differs. Add all four vars to
`.env.example` in the existing LOCAL_MODEL block, with a comment
explaining that thinking-mode is disabled by default because Qwen3 will
otherwise burn its output budget on `<think>` tokens before emitting a
tool call.

```powershell
# With defaults (thinking disabled, temp 0.2) — expect all three stages to succeed.
$env:LOCAL_MODEL_DISABLE_THINKING = "true"
.venv\Scripts\python.exe scripts\smoke-local-toolcall.py --stages all

# Toggle back to prove diagnosis, not accidental fix.
$env:LOCAL_MODEL_DISABLE_THINKING = "false"
.venv\Scripts\python.exe scripts\smoke-local-toolcall.py --stages all

# End-to-end.
.venv\Scripts\python.exe -m openclaw post --site localhost --draft --verbose
```

- [x] All four new fields present in `Config` and `.env.example`; unset
      env vars produce the documented defaults —
      `LOCAL_MODEL_TEMPERATURE=0.2`, `LOCAL_MODEL_TOP_P=0.9`,
      `LOCAL_MODEL_MAX_TOKENS=12000`, `LOCAL_MODEL_DISABLE_THINKING=false`
      (deviation, see Status line above), all wired through
      `Config.load()` via new `_parse_float`/`_parse_int`/`_parse_bool`
      helpers and threaded into both `_generate_with_local` and
      `_select_subreddits_local`.
- [x] **Deviation from plan**: the specified
      `extra_body={"chat_template_kwargs": {"enable_thinking": False}}`
      convention was tested first and found to be silently ignored by
      this LM Studio build (identical results with the flag true/false).
      The only mechanism that actually suppresses `reasoning_content`
      is `extra_body={"reasoning_effort": "none"}`, but across repeated
      trials it also reliably broke `tool_choice="required"` grammar
      enforcement (0/4 trials produced a tool call when present — the
      model answered in prose instead). A third option,
      Qwen3's native `/no_think` inline suffix, partially suppressed
      reasoning and preserved tool-calling but was unreliable (~40-60%
      success across repeated trials) and was not adopted. Net: no
      dependable suppression mechanism exists on this server/model
      build, so thinking-mode suppression stays wired as an opt-in
      escape hatch (`LOCAL_MODEL_DISABLE_THINKING=true` uses the
      `reasoning_effort` mechanism) but is **not** the default.
- [x] Practical fix shipped instead: `LOCAL_MODEL_MAX_TOKENS` (default
      12000) threaded through both call sites. This also fixed a
      pre-existing, previously-undocumented bug —
      `trends.py::_SUBREDDIT_SELECT_MAX_TOKENS` was hardcoded to 2048,
      well below the 600-52,700+ char reasoning traces observed, which
      guaranteed failure on its own regardless of the thinking-mode
      question.
- [ ] `python -m openclaw post --site localhost --draft` logs
      `provider=local status=success` on all three stages in the same
      run — **NOT achieved.** The 2026-07-14 `logs/_e2e-run-1.log` run
      fell back on all three stages (subreddit_select, generate, revise)
      even with the Step 3.8.7 knobs in place; each fallback produced a
      matching `logs/qwen-fallback-*.json` (Step 3.8.6) showing
      `finish_reason=length` with `completion_tokens` pinned near the
      12000 ceiling. Qwen3.6's reasoning-length nondeterminism was not
      resolved by these knobs alone. The post still published
      successfully via the Claude fallback chain, so the router/fallback
      contract holds even though the "local as primary" goal remains
      unmet.
- [x] Which knob mattered (with before/after fallback rates) recorded in
      §12 — see 2026-07-14 entry. Summary: `LOCAL_MODEL_MAX_TOKENS`
      raised from a broken 2048 default to 12000 is necessary but not
      sufficient; no thinking-suppression knob is both effective and
      safe on this server/model build, so fallback rate remained
      effectively 100% in the one full end-to-end run captured here (n=1
      run, not the 5-run sample Step 3.8.8 requires — see that step's
      blocked status).

### Step 3.8.8 - Structured-output parity + quality gate

Status: not started. **Blocked by Steps 3.8.5-3.8.7** — this gate cannot
be measured while all local calls fall back to Claude.

The router works, but "works" only means "the fallback saves us." This step
proves Qwen3.6 can carry the primary path unassisted often enough to be
worth being primary.

Verification — five consecutive `--site localhost --draft` runs with
`LOCAL_MODEL_ENABLED=true` and the local host up:

```powershell
$env:LOCAL_MODEL_ENABLED = "true"
$ids = 1..5 | ForEach-Object {
    (python -m openclaw post --site localhost --draft --verbose 2>&1 |
        Tee-Object -Append logs\3.8.5.txt |
        Select-String 'Published: .*[?]p=(\d+)').Matches.Groups[1].Value
}
$ids | ForEach-Object { python scripts/verify-seo.py $_ }
Select-String -Path logs\3.8.5.txt -Pattern 'provider=(local|claude) status=(success|fallback)' |
    Select-Object -ExpandProperty Line
```

- [ ] At least 4 of 5 runs log `provider=local status=success` (fallback
      rate <=20% is the primary-model bar; higher rate means either the
      prompt needs tuning or Qwen3.6 stays as a secondary).
- [ ] All 5 posts exit 0 on `verify-seo.py` (proves the local model
      produces SEO-compliant articles, not just any articles).
- [ ] Word count of each local-generated post is within 1500-2500 (STYLE.md
      target from Phase 3.7).
- [ ] Manual style-review of 2 randomly picked local-generated posts using
      the Phase 3.7 hook + thesis + payoff rubric; both pass.
- [ ] Cost check: local runs record $0 outbound; the 1 fallback run (if
      any) shows the expected Claude usage. Recorded in §12.

### Step 3.8.9 - Full end-to-end + Phase 3 regression check

Status: not started. Runs against the five posts published in Step 3.8.8.

Confirm nothing upstream in the publish path (images, links, SEO meta
routing) regressed. The generator is the only moving part in this phase,
so the regression surface is small but the failure would be silent.

Verification: reuse the Phase 3 exit-criteria checklist against the 5
posts from Step 3.8.8 logs:

- [ ] `Uploaded featured image (id=...)` present in each run.
- [ ] `Internal links used` count > 0 in at least 2 of 5 runs.
- [ ] `External links used` count > 0 in all 5.
- [ ] No `Stripped N unauthorized` warnings from the sanitizer.
- [ ] `_strip_em_dashes` (Phase 3.7 post-processor) runs cleanly on
      local-generated body_html; count logged (may be higher than for
      Claude — this is fine, it's exactly what the deterministic
      sanitizer is there to catch).
- [ ] SEO meta round-trip WARN behavior unchanged vs. pre-3.8 (this is
      site-state, not model-state; a delta here means something else
      moved).

### Step 3.8.10 - Documentation

Status: partial (original three-env-var wording landed with Step 3.8.4;
this step re-opens to cover the four new tuning knobs from Step 3.8.7
and the diagnostic tooling from Steps 3.8.5-3.8.6).

Verification:

```powershell
Select-String -Path README.md -Pattern 'LOCAL_MODEL|Qwen|LM Studio|DISABLE_THINKING'
Select-String -Path CLAUDE.md -Pattern 'LOCAL_MODEL|Qwen|_generate_with_local|chat_template_kwargs'
(Select-String -Path PLAN.md -Pattern '2026-\d\d-\d\d.*Phase 3\.8' | Measure-Object).Count
```

- [ ] README.md's "LLM providers" section covers the local/Claude split,
      the three transport env vars **plus** the four new tuning knobs
      (`LOCAL_MODEL_TEMPERATURE`, `LOCAL_MODEL_TOP_P`,
      `LOCAL_MODEL_MAX_TOKENS`, `LOCAL_MODEL_DISABLE_THINKING`), how to
      toggle back to Claude-only, and expected fallback log lines. Also
      documents the `logs/qwen-fallback-*.json` sidecars from Step 3.8.6
      and how to read them.
- [ ] CLAUDE.md "Key facts" Anthropic-SDK bullet updated to name the
      router and Qwen3.6 primary; architecture paragraph mentions
      `_generate_with_local`, `_generate_with_claude`, the fallback
      trigger set, and the `extra_body={"chat_template_kwargs":
      {"enable_thinking": …}}` convention used to disable Qwen's
      reasoning mode.
- [ ] `.env.example` shows the three original LOCAL_MODEL_* vars plus
      the four new tuning knobs with realistic sample values and the
      "defaults to Claude when unset" note.
- [ ] §12 decision-log entries added for: (a) the LM Studio + OpenAI-SDK
      transport choice, (b) the fallback trigger set, (c) the Step 3.8.8
      quality/fallback-rate outcome, (d) the recorded per-article cost
      delta, (e) the Step 3.8.5-3.8.7 root cause + fix.

Phase 3.8 exit criteria:
- Steps 3.8.5-3.8.7 complete and the "model returned no tool call"
  failure root-caused + fixed (or, if unfixable, `LOCAL_MODEL_ENABLED`
  documented as advisory-only and the primary path reverted to Claude
  with a §12 note explaining why).
- 3 consecutive `--site localhost --draft` runs with LOCAL_MODEL_ENABLED=true
  each publish successfully via the local model (`provider=local
  status=success`) and each pass `scripts/verify-seo.py` with 0 FAIL.
- One deliberate local-outage run (bad host or bad model id) fires the
  Claude fallback in-run and still publishes a compliant post.
- Toggling LOCAL_MODEL_ENABLED=false restores the pre-3.8 Claude-only
  behavior with no observable change to output shape.
- Documentation updated; decision-log entries recorded.

## 9.8 Phase 3.9 Plan - Local Image Generation (Flux / Draw Things)

Status: **IN PROGRESS** (2026-07-13). All code, config, and doc changes
below are complete. Live verification is blocked pending user confirmation
that `192.168.0.200` is responsive again (see the incident note in §9.7
Step 3.8.1 — a test request against this same Draw Things endpoint appears
to have pinned the host).

Goal: same local-first, graceful-fallback philosophy as Phase 3.8, applied
to featured-image generation. When a local Flux model (served by the
Draw Things app's HTTP API) is available, use it for $0-cost, unlimited
images; fall back to the existing OpenAI `gpt-image-2` -> Unsplash chain on
any failure. No user-visible behavior change when disabled.

Environment:
- Local image model: Flux (`flux.2-klein-9b`) served by Draw Things on
  `http://192.168.0.200:7860`.
- API is Automatic1111-compatible: `POST /sdapi/v1/txt2img` with a JSON
  body (`prompt`, `negative_prompt`, `width`, `height`, ...) and a JSON
  response `{"images": ["<base64 PNG>", ...], ...}`. `GET /` returns the
  currently-loaded model's default generation parameters, not a generation
  call — confirmed via live probing before any adapter code was written.

### Step 3.9.1 - Config plumbing

Status: **COMPLETE** (2026-07-13). `openclaw/config.py` gained
`LOCAL_IMAGE_ENABLED: bool = False` and `LOCAL_IMAGE_BASE_URL: str | None =
None` on the frozen `Config`, following the exact `LOCAL_MODEL_*` pattern
(including `_normalize_optional` for `REPLACE_ME`/empty handling and
`_TRUE_STRINGS` for the bool parse). `.env.example` documents both vars,
commented out. Verified via a one-off script that `Config.load()` returns
both `True`/`http://192.168.0.200:7860` from local `.env`.

### Step 3.9.2 - `generate_local_image()` in images.py

Status: **COMPLETE** (2026-07-13). Added to `openclaw/images.py`, mirroring
`generate_openai_image`'s signature and never-raises contract:
- New constants: `LOCAL_IMAGE_TIMEOUT_SECONDS = 300.0`,
  `LOCAL_IMAGE_WIDTH = 1024`, `LOCAL_IMAGE_HEIGHT = 576` (16:9 landscape —
  matches the hard landscape-orientation rule already in `generator.py`'s
  system prompt), and `LOCAL_IMAGE_NEGATIVE_PROMPT` reinforcing "no text,
  watermark, logo, signature" (Draw Things' API, unlike OpenAI's, actually
  supports a negative prompt).
- Returns `None` + a WARNING log on: `LOCAL_IMAGE_ENABLED` false/unset,
  request exception, non-2xx status, non-JSON response, empty `images`
  list, or a base64-decode failure.
- On success, decodes `images[0]`, validates with the existing
  `_validate_image()`, and returns the same
  `{image_bytes, mime_type, alt_text, attribution}` shape as
  `generate_openai_image` (`attribution=None` — no credit needed for
  AI-generated images).

### Step 3.9.3 - Wire into the fallback chain in main.py

Status: **COMPLETE** (2026-07-13). `main._fetch_and_attach_image()`
rewritten as a 3-tier chain: local Flux (if `LOCAL_IMAGE_ENABLED`) ->
OpenAI `gpt-image-2` -> Unsplash. Each tier's success is tracked in a local
`source` variable set at the point of success (`"Local (Draw Things)"` /
`"OpenAI"` / `f"Unsplash ({photographer})"`) rather than re-derived from
`attribution` after the fact, so the final
`Uploaded featured image (id=..., source=..., alt=...)` log line always
names the actual provider that produced the image. When
`LOCAL_IMAGE_ENABLED` is unset/false, this tier is skipped entirely — the
function falls straight to OpenAI, byte-identical to pre-3.9 behavior.

### Step 3.9.4 - Smoke test script

Status: **COMPLETE** (2026-07-13). `scripts/smoke-local-image.py` added,
mirroring `scripts/smoke-local-toolcall.py`'s shape: calls
`images.generate_local_image` directly with a fixed test prompt (a cat on a
windowsill), writes the resulting PNG to `logs/smoke-local-image.png`, and
prints PASS/FAIL + latency. Not yet run against a live host (see status
note above).

### Step 3.9.5 - Live verification

Status: **COMPLETE** (2026-07-14). Host confirmed responsive; all checks
below ran successfully. One real bug was found and fixed along the way (see
decision log): `_generate_with_local`'s `tool_choice={"type":"function",
"function":{"name":...}}` was rejected with HTTP 400 by this LM Studio
server version ("Supported string values: none, auto, required"). Changed
to `tool_choice="required"` in both `generator.py` and
`smoke-local-toolcall.py` — safe since only one tool is ever offered, and
the existing `call_name != tool_name` check still guards correctness.

Results:
- `smoke-local-toolcall.py`: PASS, 2.81s latency, well under the 15s bar.
- `smoke-local-image.py`: PASS, 109.39s latency, 909KB PNG — landscape,
  on-topic (orange tabby on a windowsill), no visible text/watermark.
- Happy-path full run (`--site localhost --draft --verbose`, both flags
  on): `generate` stage fell back to Claude (`LocalProviderError: model
  returned no tool call, content preview: ''`); `revise` stage succeeded
  locally; image succeeded locally (`source=Local (Draw Things)`,
  ~106s). Published post 1443 passed `verify-seo.py` 14/14 (0 FAIL).
  `_thumbnail_id` confirmed via wp-cli to match the uploaded local image.
- Dead-port test (`LOCAL_IMAGE_BASE_URL` pointed at :9999), attempt 1:
  `generate` succeeded locally, `revise` fell back to Claude, but the
  Claude HTTP request stalled ~9.5 hours before a `ConnectionResetError` —
  consistent with the host machine sleeping mid-request, not a code
  defect. Retried once the machine was confirmed awake: `generate` AND
  `revise` both succeeded locally this time, `generate_local_image` logged
  a clean connection-refused WARNING, and the run fell through to OpenAI
  (`source=OpenAI`) and published normally.
- Both-disabled run: `provider=claude status=success` for both stages,
  `source=OpenAI` for the image — confirms byte-identical-in-shape
  pre-3.8/3.9 behavior.
- Net across the 3 full pipeline runs in this session: local `generate`
  succeeded 2/3 times, local `revise` succeeded 2/3 times. The one
  `generate`-stage miss and one `revise`-stage miss both had the identical
  signature (`model returned no tool call`, empty or near-empty content
  preview) — consistent with Qwen3.6's reasoning/thinking tokens
  occasionally consuming the `MAX_TOKENS=12000` budget before emitting the
  tool call on the larger article-generation and revision prompts (the
  tiny 2-field smoke-test schema never hit this). Not yet root-caused or
  fixed; flagged for Step 3.8.8's formal 5-run gate rather than patched
  ad hoc here, since the fallback safety net is working exactly as
  designed in the meantime.

- [x] `smoke-local-image.py` PASSes with a landscape, on-topic, uncorrupted
      PNG.
- [x] Dead-port test logs a WARNING from `generate_local_image` and still
      publishes, sourced from OpenAI.
- [x] Full-pipeline run logs `source=Local (Draw Things)` and the WP draft
      has a visible featured image (post 1443, `_thumbnail_id=1442`).
- [x] Both-disabled run is unchanged in shape from pre-3.8/3.9 output.
- [ ] Re-run the Phase 3.8 Step 3.8.8 5-run quality gate with
      `LOCAL_IMAGE_ENABLED=true` too, to catch any cross-provider
      regression (e.g. combined local-text + local-image runtime) — still
      owed; this session's 3 runs are informative but not the formal gate.
- [x] §12 decision-log entry recorded with the incident resolution and
      observed local image latency.

Phase 3.9 exit criteria: **met**.
- A `--site localhost --draft` run with `LOCAL_IMAGE_ENABLED=true` and the
  host up publishes with a local-sourced featured image. ✓ (post 1443)
- A dead-endpoint run still publishes, falling through to OpenAI then
  Unsplash as needed. ✓
- `LOCAL_IMAGE_ENABLED=false` restores pre-3.9 behavior exactly. ✓
- Documentation updated; decision-log entry recorded. ✓

## 10. Phase 4 Plan - Scheduling

Status: in progress (2026-07-10). Wrapper + sites-config + retry landed;
Task Scheduler entry to be created by user; multi-day E2E owed.

Goal: `python -m openclaw post` runs unattended once per day at 07:00
America/Denver. Transient failures retry; hard failures leave a flag file
the user checks manually.

Multi-site: the daily run publishes ONE article per enabled site listed in
`scheduled-sites.json` (project root), iterated sequentially. Each site has
its own retry cycle; a failure on one site does not skip the others.

### Step 4.1 - Choose hosting target

Status: **COMPLETE** (2026-07-10). Decision: **Windows Task Scheduler on
the user's laptop**. Rationale: no infra cost, no cloud account, and the
laptop is already the working environment; Phase 4 exists to prove
automation, not to invest in hosting. Cost ceiling: $0/mo. Known failure
modes:
- Laptop off or asleep with Wake-to-Run misconfigured → the 07:00 trigger
  is skipped that day (Task Scheduler does NOT catch up by default; the
  "Run task as soon as possible after a scheduled start is missed" option
  handles the case where the laptop wakes after 07:00 but is on that day).
- Laptop unplugged with the default AC-power condition on the scheduled
  task → the trigger silently skips. The Register-ScheduledTask example
  in Step 4.3 disables this condition explicitly.
- Docker Desktop not started at 07:00 → the localhost site publish path
  will fail; retries will not help. Considered acceptable for the
  prototype; the wrapper's failure flag surfaces it.
- Cloud migration (VM + cron) remains the escape hatch when reliability
  matters; the wrapper is Docker-agnostic and would move over as-is.

### Step 4.2 - Wrapper script

Status: **COMPLETE** (2026-07-10). `scripts/run-openclaw.ps1` implements
the full wrapper (retry + log flag are folded in here rather than split
across 4.2/4.4, since the retry loop is trivial once the per-site
invocation exists).

Responsibilities:
- `cd` into the project root using `Split-Path -Parent $PSScriptRoot` so
  the scheduler's working directory does not matter.
- Invoke `.venv\Scripts\python.exe` directly (skips the interactive
  Activate.ps1 step Task Scheduler cannot run).
- Read `scheduled-sites.json` at the project root, iterate the entries
  with `enabled=true`, and run `python -m openclaw post --site <slug>
  --verbose` for each. `-Sites <string[]>` parameter overrides the file;
  `-Draft` appends `--draft`.
- Append stdout+stderr to `logs/openclaw-YYYY-MM-DD-<slug>.log` (one file
  per site per day).
- `logs/` is in `.gitignore` (Phase 3.5 log files remain tracked as audit
  trail; new files are ignored).

Retry policy: N=2 retries per site = 3 attempts total, waiting 60s after
attempt 1 and 300s after attempt 2. Retries fire on any non-zero exit
from `python -m openclaw post`.

Failure flag: on final failure of one or more sites, writes
`logs/last-run-failed.flag` with a summary (which sites failed, exit
codes, log paths) + the last 50 lines of the most recent failing log.
On a fully successful run, removes the flag if it exists. Exit code =
number of sites that ultimately failed (0 = all passed).

Verification (owed to user):
- [x] `scripts/run-openclaw.ps1` exists; `logs/` in `.gitignore`.
- [ ] Invoking the script from a fresh PowerShell session in an arbitrary
      cwd produces one published post per enabled site.
- [ ] The log for that run contains the full pipeline output (config
      loaded, Claude call, image upload, publish URL) per site.
- [ ] Exit code is 0 on all-pass and equals the failure count otherwise.

### Step 4.3 - Schedule configuration

Status: not started (owed to user).

Create the Task Scheduler entry once. All the settings live in a
Register-ScheduledTask incantation — safer than clicking through the GUI
because the exact config is git-visible and reproducible.

```powershell
# Run in an elevated PowerShell prompt on the user's laptop.

$Action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument '-NoProfile -ExecutionPolicy Bypass -File "D:\Claude\Wordpress\scripts\run-openclaw.ps1"' `
    -WorkingDirectory 'D:\Claude\Wordpress'

# 07:00 America/Denver. Windows Task Scheduler triggers use the machine's
# local time zone, so if the laptop is not on Mountain Time set the hour
# offset to match 07:00 Denver (e.g. 08:00 CT / 09:00 ET).
$Trigger = New-ScheduledTaskTrigger -Daily -At 07:00

$Settings = New-ScheduledTaskSettingsSet `
    -WakeToRun `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Runs whether the user is logged on or not, with the current user's SID
# and stored password. Requires the interactive password at registration.
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Password `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName 'Openclaw daily post' `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description 'Runs D:\Claude\Wordpress\scripts\run-openclaw.ps1 daily at 07:00 to generate and publish one article per enabled site in scheduled-sites.json.'
```

Verification (owed to user):
- [ ] Task 'Openclaw daily post' appears in Task Scheduler.
- [ ] Right-click → Run publishes one post per enabled site.
- [ ] Setting the trigger to "in 5 minutes" (`Set-ScheduledTask` with a
      new `New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(5))`)
      fires it automatically and publishes.
- [ ] Task Scheduler History tab shows "Task Started" → "Action Completed"
      with exit code 0.
- [ ] Sleeping the machine before a near-future test trigger fires the task
      within a few minutes (Wake-to-Run one-time check).

### Step 4.4 - Retry + failure flag

Status: **COMPLETE** (2026-07-10). Folded into `scripts/run-openclaw.ps1`
(see Step 4.2). Log-flag-only notification per §12 decision — no email,
toast, or push service. The user checks `logs/last-run-failed.flag` after
suspected misses.

Implementation (in the wrapper):
- Retries the Python command per site on non-zero exit up to **N=2** times,
  waiting 60s after attempt 1 and 300s after attempt 2.
- After all retries for a site fail, adds it to a failure summary.
- After all sites processed, if any failed, writes
  `logs/last-run-failed.flag` containing: failed site slugs + exit codes +
  log paths + the last 50 lines of the most recent failing log.
- On a fully successful run, removes `logs/last-run-failed.flag` if
  present. Wrapper exit code = number of sites that ultimately failed.

Verification (owed to user):
- [ ] Simulated transient failure (e.g. unset `ANTHROPIC_API_KEY` in `.env`
      before invoking the wrapper) → wrapper logs 2 retries and writes the
      failure flag.
- [ ] Simulated transient-then-recover (restore the env var between
      retries) → wrapper logs success and does NOT write the flag; any
      previous flag is removed.
- [ ] After a subsequent successful run, `logs/last-run-failed.flag` is
      removed.

### Step 4.5 - Multi-day end-to-end verification

Status: not started (owed to user).

Verification:
- [ ] 3 consecutive scheduled days each produce ONE published article per
      enabled site in `scheduled-sites.json`.
- [ ] `logs/openclaw-YYYY-MM-DD-<slug>.log` files exist for each day × slug
      with timestamps inside the trigger window (07:00-07:02 America/Denver).
- [ ] The 3 article topics per site are distinct (recent-title de-dup still
      works within each site).
- [ ] Task Scheduler History shows 3 successful runs, 0 failed runs.
- [ ] `logs/last-run-failed.flag` is absent.
- [ ] `logs/` disk usage after 3 days is under 10 MB per site.

### Step 4.6 - Documentation

Status: **COMPLETE** (2026-07-10).

Verification:
- [x] README.md gains a "Scheduling (Phase 4)" section: schema,
      wrapper path, `Register-ScheduledTask` command, disable/re-enable
      cmdlets, and how to check the failure flag.
- [x] CLAUDE.md gains a "Scheduling (Phase 4)" bullet under Key facts
      and adds the wrapper invocations to Common commands. The top-of-file
      project description was corrected (Phase 4 = scheduling, Phase 5 =
      multisite + static, Phase 6 = analytics; the old wording had them swapped).
- [x] §12 decision-log entry for hosting target + notification channel
      landed 2026-07-10 alongside Steps 4.1/4.2/4.4.

Phase 4 exit criteria:
- 7 consecutive scheduled days produce one distinct published article per
  enabled site with no manual intervention.
- At least one transient failure (real or simulated) has been recovered
  by the retry logic without human intervention beyond a subsequent
  scheduled run.

## 11. Phase 5 Plan - Multisite + Static Export + GitHub Pages

Status: not started.

Goal: turn the local Docker WordPress into a small multi-tenant content
network. Openclaw feeds each subsite; every `python -m openclaw post`
triggers a per-subsite static export and commits the result to a GitHub
Pages branch. Public-facing hosting is free, CDN-backed, and static; the
WP layer stays private on the laptop.

**Scale target:** 3-5 pilot subsites. Design must not preclude scaling to
20+ later.

**Cross-cutting decisions (locked 2026-07-11, see §12):**
- Multisite topology: subdomain install (`site1.openclaw.local`,
  `site2.openclaw.local`, ...) — matches production custom-domain mapping.
- Static exporter: **Staatic** (free, multisite-native, released May 2026).
- Publishing target: private GitHub repo `openclaw-sites`, one branch per
  subsite (`site/<slug>`), each branch attached to its own custom domain
  via GH Pages' branch-level custom-domain feature.
- Design system: one network-default block theme (Twenty Twenty-Five) plus
  per-subsite child themes for structural overrides. Palette / logo /
  tagline set via each child theme's `theme.json` and site options.

### Step 5.1 - Enable multisite in Docker WP

Status: **COMPLETE** (2026-07-13). Deviations from original plan:

- **Domain suffix pivoted from `.openclaw.local` to `.localhost`.** Windows
  hosts file doesn't support wildcards, and admin rights weren't
  available to add per-subsite entries. `.localhost` is RFC 6761-reserved
  for loopback; Chrome/Firefox/curl short-circuit it to `127.0.0.1`
  automatically — no hosts-file edit required.
- **Python's `socket.getaddrinfo` still refuses `*.localhost`** on Windows
  (unlike browsers/curl). Added `openclaw/_localhost_dns.py` — a
  process-local `socket.getaddrinfo` monkeypatch that redirects any
  `*.localhost` lookup to `127.0.0.1`. Auto-installed via
  `openclaw/__init__.py`; safe outside the pilot because it only rewrites
  hostnames ending in `.localhost`.
- **wp-config generated via wp-cli, not the docker-compose env var.** The
  wordpress image only writes `wp-config.php` on first-run initialization,
  so `WORDPRESS_CONFIG_EXTRA` couldn't retroactively add
  `WP_ALLOW_MULTISITE=true` to an existing install. Used
  `wp config set WP_ALLOW_MULTISITE true --raw`, then `wp core
  multisite-convert --subdomains --title="Openclaw Network"` wrote the
  remaining multisite constants directly to `wp-config.php`.
- **No new mu-plugin needed** — `multisite-convert` handled every
  constant listed in the original plan.

Additional work required to make Staatic (which runs inside the wpcli
container) crawl subsite URLs:
- Bind-mounted `apache/openclaw-multisite.conf` adds `Listen 8088` +
  `ServerAlias *.localhost` so the site is reachable via
  `<slug>.localhost:8088` from both host and container.
- `extra_hosts:` on the wordpress compose service maps each pilot subsite
  domain → `127.0.0.1` inside the container.
- `network_mode: "service:wordpress"` on the wpcli service shares the
  wordpress container's network namespace so `docker compose run --rm
  wpcli staatic publish` inherits those `extra_hosts`.

Verification (passed):
- [x] Network admin dashboard reachable at `http://localhost:8088/wp-admin/network/`.
- [x] Four subsites created via `wp site create` reachable at their
      subdomains.
- [x] Regression: `python -m openclaw post --site localhost --draft`
      still publishes to the primary site with no code changes.
      (openclaw-agent is now a network super-admin; the multisite
      conversion invalidated the prior app password so a fresh one was
      generated via `wp user application-password create`.)

### Step 5.2 - Create the pilot subsites

Status: **COMPLETE** (2026-07-13). Four pilot subsites created via
`wp site create`:

| slug         | blog_id | URL                              | niche                       |
|--------------|---------|----------------------------------|-----------------------------|
| gardening    | 2       | http://gardening.localhost:8088/ | Home & container gardening  |
| dogs         | 3       | http://dogs.localhost:8088/      | Dog care & training         |
| boardgames   | 4       | http://boardgames.localhost:8088/| Board games & tabletop      |
| coffee       | 5       | http://coffee.localhost:8088/    | Home coffee & tea brewing   |

Niche selection criteria (per user request): high organic search demand +
high AI-writability (evergreen, factual, structured, low legal/YMYL
risk).

Per-subsite work landed:
- `website_memory/{hostname}.md` written for each — persona modelled on
  `catfancast.com.md` (what to write, what NOT to write, audience, tone,
  entity checklist).
- `website_memory/{hostname}.trends.json` written with per-niche
  subreddits + Google Suggest seeds.
- `wp term create category` populated 8 evergreen categories per subsite.
- Prefixed env vars added to `.env`: `GARDENING_WP_*`, `DOGS_WP_*`,
  `BOARDGAMES_WP_*`, `COFFEE_WP_*` — all four share the same
  `openclaw-agent` super-admin app password (regenerated via wp-cli).
- `.env.example` commented block updated with the same four slugs.
- `scheduled-sites.json` gained four new entries with `enabled=false`.

`openclaw/config.py::_validate_base_url` was widened to allow `*.localhost`
subdomains under plain HTTP (the same guarantee bare `localhost` already had).

Verification (passed):
- [x] `python -m openclaw post --site <slug> --draft --skip-review`
      published one on-brand draft to each of the four subsites (see
      `logs/phase5-smoke-<slug>.log`).
- [x] `/wp-json/wp/v2/posts` per subsite returns only its own posts.

### Step 5.3 - Base block theme + per-subsite child themes

Status: **COMPLETE** (2026-07-13).

- Twenty Twenty-Five was already installed; got network-enabled as a
  side effect of the child-theme activation dance.
- Four child themes scaffolded on the host (bind-mounted individually to
  survive `docker compose down -v` per the original plan):
  - `wp-content/themes/openclaw-gardening/` — greens + earth tones (leaf
    green primary, wheat accent, Playfair Display headings).
  - `wp-content/themes/openclaw-dogs/` — warm mid-neutrals (rich brown
    primary, tan accent, Merriweather headings).
  - `wp-content/themes/openclaw-boardgames/` — bold desaturated palette
    (deep purple primary, dice red accent, Space Grotesk headings).
  - `wp-content/themes/openclaw-coffee/` — espresso/cream (dark
    espresso primary, caramel accent, Fraunces headings).
- Each child theme has `style.css` (`Template: twentytwentyfive`) plus a
  `theme.json` overriding palette and typography. No template-part
  overrides — the parent's structural HTML is fine.
- Individually bind-mounted (four separate host→container mounts) in
  `docker-compose.yml` so the WP volume's other themes stay visible.
- Network-enabled + per-site-activated via
  `wp theme enable openclaw-<slug> --network` +
  `wp theme activate openclaw-<slug> --url=http://<slug>.localhost:8088`.

Verification (passed):
- [x] `wp theme list --url=http://<slug>.localhost:8088 --status=active`
      returns `openclaw-<slug>` for each of the four pilots.
- [x] Static exports (Step 5.6) render without broken block styles.

### Step 5.4 - Install and configure Staatic

Status: **COMPLETE** (2026-07-13). Staatic 1.12.5 installed via
`wp plugin install staatic --activate-network`.

Per-subsite configuration (via `wp option update --url=...`):
- `staatic_deployment_method` = `filesystem`
- `staatic_filesystem_target_directory` =
  `/var/www/html/wp-content/staatic-exports/<slug>` (bind-mounted →
  `staatic-exports/<slug>/` on host)
- `staatic_destination_url` =
  `https://carterman82.github.io/openclaw-<slug>/`

Programmatic trigger: `wp staatic publish --url=http://<slug>.localhost:8088`.
`openclaw/deploy.py::trigger_staatic_export` shells out to it.

Gotchas learned in flight (recorded in §12):
- git-bash on Windows rewrote the `/var/www/...` path in
  `wp option update` calls; had to `export MSYS_NO_PATHCONV=1`.
- Staatic runs inside the wpcli container; needed `extra_hosts` +
  `network_mode: "service:wordpress"` to reach `<slug>.localhost:8088`
  from inside.
- The staatic-exports bind-mount had to be added to BOTH `wordpress`
  and `wpcli` services (originally only wordpress) — wpcli-side
  `wp staatic publish` writes from wpcli's filesystem view.

Verification (passed):
- [x] `wp staatic publish --url=http://gardening.localhost:8088`
      produces a self-contained static tree at `staatic-exports/gardening/`.
- [x] URL rewrites: 100% of `<a>` and asset URLs point to
      `https://carterman82.github.io/openclaw-gardening/*` (one residual
      reference to the source WP URL in a JSON API endpoint; not
      user-visible; tolerable).
- [x] Featured images render from relative paths in the export.

### Step 5.5 - GitHub repo + Pages topology

Status: **COMPLETE** (2026-07-13). Deviated from the original single-repo,
branch-per-subsite design and instead created **one public repo per
subsite**, main branch:

- `carterman82/openclaw-gardening`
- `carterman82/openclaw-dogs`
- `carterman82/openclaw-boardgames`
- `carterman82/openclaw-coffee`

Why the pivot: GitHub Pages serves only one site per repo unless each
branch has its own custom domain. The user's chosen hosting mode is
"free github.io URLs" (no custom domains yet), and free-tier accounts
can't run GH Pages on private repos anyway. Repo-per-subsite gives each
pilot a clean `carterman82.github.io/openclaw-<slug>/` URL today, and
each can be independently swapped to a custom domain later without
touching the others.

Each repo initialized with:
- `README.md` — one-liner describing the export.
- `.nojekyll` — so GH Pages doesn't feed `wp-*` directories through Jekyll.

Pages enabled via `gh api repos/carterman82/openclaw-<slug>/pages -X POST
-f 'source[branch]=main' -f 'source[path]=/'`.

**Reggae-Fancast CNAME caveat:** the user's `carterman82.github.io` repo
has an account-level custom domain (`www.reggaefancast.com`). All project
Pages URLs therefore 301-redirect from
`carterman82.github.io/openclaw-<slug>/` to
`www.reggaefancast.com/openclaw-<slug>/`. The redirect is transparent, so
this is documented as fine, not fixed.

Verification (passed):
- [x] `git push origin main` for each pilot triggers a GH Pages build
      (status building → built within ~1-2 min).
- [x] Public URL `https://carterman82.github.io/openclaw-<slug>/` returns
      200 (after the 301 to reggaefancast.com) for gardening, dogs,
      boardgames at smoke time; coffee still building.

### Step 5.6 - Post-publish deploy hook

Status: **COMPLETE** (2026-07-13). `openclaw/deploy.py` implements:

- `trigger_staatic_export(slug)` — shells out to
  `docker compose run --rm wpcli staatic publish --url=http://<slug>.localhost:8088`.
  5-min timeout. Returns False + logs WARNING on failure; never raises.
- `commit_and_push(slug, post_title)` — persistent working tree at
  `.gh-worktree/openclaw-<slug>/` (cloned once, `fetch + reset --hard
  origin/main` on subsequent runs). Mirrors `staatic-exports/<slug>/`
  into the working tree, commits `Publish: <title> [<slug>]`, pushes.
  Never raises.
- `deploy_after_publish(slug, post_title)` — composed pipeline main.py
  calls. Silently no-ops when `slug` is not one of `DEPLOYABLE_SLUGS`
  (`{gardening, dogs, boardgames, coffee}`), so `--site catfancast`
  and `--site localhost` never trigger a push.

Wiring in `main.py`:
- New CLI flag `--skip-deploy` mirroring `--skip-review`.
- After `publish_post()` succeeds and the URL is printed:
  - if `--skip-deploy` → log and skip.
  - elif `is_deployable(args.site)` → call `deploy_after_publish(...)`
    and log outcome. A failed deploy does NOT roll back the WP publish;
    log line says "post is published; deploy owed".

Non-pilot slugs skip the whole chain via the `DEPLOYABLE_SLUGS`
allowlist — no risk that a Phase 4 scheduled run against catfancast.com
suddenly tries to git-push somewhere.

Verification (passed):
- [x] `python -m openclaw post --site gardening --draft --skip-review`
      end-to-end: draft in WP → Staatic export → git clone → commit +
      push in ~45 s (subsequent runs will reuse the working tree, ~5–10 s).
- [x] All four pilot subsites got a smoke deploy: draft publish → static
      export → main-branch commit → GH Pages build kicked off.
- [x] Non-pilot regression: `python -m openclaw post --site localhost
      --draft` continues to work without triggering deploy (deploy step
      logs "Skipping deploy for non-pilot slug 'localhost'" at DEBUG).

### Step 5.7 - Multi-subsite scheduled runs

Status: **CODE-LEVEL COMPLETE** (2026-07-13). Pilot entries added to
`scheduled-sites.json` with `enabled=false`; flip to `true` once ready
for daily runs. No wrapper changes needed — `scripts/run-openclaw.ps1`
already iterates enabled entries.

Owed to user (multi-day passive verification):
- [ ] Flip the four pilot entries in `scheduled-sites.json` from
      `enabled=false` to `enabled=true`.
- [ ] 3 consecutive daily runs each produce 1 new post per enabled
      subsite AND 1 new commit per subsite AND 1 live GH Pages update.
- [ ] `logs/last-run-failed.flag` surfaces deploy failures the same way
      it surfaces publish failures.
- [ ] Total wall-clock stays under the 60-min task limit. Six sites ×
      ~2 min publish + ~1 min deploy = ~18 min; well within.

### Step 5.8 - Documentation

Status: **COMPLETE** (2026-07-13). PLAN.md §11 rewritten to match
actual shipped state; README.md gained a "Multisite + static export
(Phase 5)" section; CLAUDE.md gained a Phase 5 bullet under Key facts
and the data-flow paragraph now includes Staatic + git push.

Phase 5 (initial pilot) exit criteria:
- [x] All four pilot subsites run end-to-end: 1 published draft AND
      static export AND GitHub main-branch commit AND GH Pages build in
      a single `python -m openclaw post --site <slug>` invocation.
- [ ] Multi-day passive verification (7 consecutive scheduled days)
      **owed to user** — matches how Phase 4's exit was closed out.
- [ ] Deliberate failure recovery at each stage **not yet exercised**;
      the code is graceful-fail by design but this hasn't been chaos-tested.

### Post-pilot rework (Steps 5.9 – 5.11)

Status: **not started** — Steps 5.9 – 5.11 supersede the first-round
pilot's niche and theming decisions. User feedback (2026-07-13): the
first-round niches were too broad for the "fancast" family, `dogfancast.com`
already exists (name collision), and the subsites still look like default
WordPress. This section replans the pilot into narrow-fandom subsites with
original branding, adds Tech Tool Guide as a dedicated subsite, and lands
a proper editorial-magazine base theme.

### Step 5.9 - Rebuild pilot subsites with focused-fandom niches and original branding

Status: not started.

**Context:** the first-round pilot shipped four subsites named
`gardening`, `dogs`, `boardgames`, `coffee`. The niches were too broad
(the "fancast"-family sites work better around a single-fandom hobby than
a generic category), one name collided with an existing production site
(`dogfancast.com` is live), and none of the four had distinctive
branding. This step deletes those pilots and replaces them with four
narrow-fandom sites using original brand names — **not** the `X-fancast`
pattern.

**Proposed niches + brand names** (domain availability probed at planning
time via HTTP+DNS; final selection pending user approval during review):

| slug            | niche               | brand name          | proposed domain           | why                                                                                                        |
|-----------------|---------------------|---------------------|---------------------------|------------------------------------------------------------------------------------------------------------|
| redstone        | Minecraft           | Redstone Register   | `redstoneregister.com`    | User's own example. Massive audience; redstone/mods/versions/biomes are endlessly AI-writable and factual. |
| sprueandcodex   | Warhammer 40K       | Sprue & Codex       | `sprueandcodex.com`       | Deep hobby (painting + rules + lore + army lists). "Sprue" = plastic frame minis come on; "codex" = army rulebook. |
| slipstream      | Formula 1           | Slipstream Journal  | `slipstreamjournal.com`   | Global fandom. Tech + drama + drivers + circuits + history. Original name evokes the racing draft mechanic. |
| clack           | Mechanical keyboards| Clack Report        | `clackreport.com`         | Dedicated enthusiast community; switches/keycaps/layouts/builds = evergreen AI-writable content.           |

Domain probes (2026-07-13):
`redstoneregister.com` no HTTP response + 1 DNS record (likely available or parked),
`sprueandcodex.com` same, `slipstreamjournal.com` same, `clackreport.com`
same. Live sites already ruled out for `formationlap.com`, `paddockpost.com`,
`chequeredflag.com`, `apexline.com`, `racingline.com`. No domain has been
registered yet — GH Pages URLs use the free
`carterman82.github.io/openclaw-<slug>/` pattern per Step 5.5's decision,
so buying the branded domain and pointing it at the GH Pages repo can
happen later without redoing this step.

Work:
- `wp site delete <blog_id>` for blogs 2–5 (Hello World + smoke drafts
  only, no content loss).
- `wp site create --slug=<slug>` for the four new slugs at
  `<slug>.localhost:8088`.
- Write `website_memory/<slug>.localhost.md` for each new site — mirror
  the catfancast persona template, with fandom-specific green-light /
  red-light lists and entity checklists (redstone components, W40K
  chapters/factions, F1 drivers/circuits/teams, keyboard switch families
  / layouts).
- Write `website_memory/<slug>.localhost.trends.json` per fandom
  (subreddits + Google Suggest seeds).
- 6–10 evergreen categories per subsite via `wp term create category ...`.
- Delete the old prefixed env-var blocks from `.env` / `.env.example`;
  add new ones: `REDSTONE_WP_*`, `SPRUE_WP_*`, `SLIPSTREAM_WP_*`,
  `CLACK_WP_*`.
- `scheduled-sites.json`: delete old pilot entries; add four new ones
  with `enabled=false`.
- Update `openclaw/deploy.py::DEPLOYABLE_SLUGS` to the new slug set.
- Update `docker-compose.yml` `extra_hosts` for the new subdomains
  (remove old, add new).
- Delete/archive old GH repos (`openclaw-{gardening,dogs,boardgames,coffee}`);
  create new ones (`openclaw-redstone`, `openclaw-sprueandcodex`,
  `openclaw-slipstream`, `openclaw-clack`) via `gh repo create ... --public`.
- Configure Staatic per new subsite (`staatic_deployment_method`,
  `staatic_filesystem_target_directory`, `staatic_destination_url`).
- Purge and recreate `staatic-exports/` subdirs.

Verification:
- [ ] Four new subsites exist at their `.localhost` URLs, each with the
      Step-5.11 child theme activated, persona loaded, categories present.
- [ ] `python -m openclaw post --site <slug> --draft --skip-review`
      produces an on-brand draft per subsite whose entities land on the
      specific fandom (redstone components for Minecraft, chapters/
      factions for W40K, drivers/circuits for F1, switches/keycaps for
      keyboards).
- [ ] End-to-end deploy per subsite → GH Pages 200 OK at
      `carterman82.github.io/openclaw-<slug>/`.
- [ ] Regression: `python -m openclaw post --site catfancast --draft`
      still publishes correctly (unchanged remote site).

### Step 5.10 - Add Tech Tool Guide as a dedicated `techtools.localhost` subsite

Status: not started.

**Context:** the localhost primary site (blog_id 1) currently holds the
"Software Tool Guide" persona in `website_memory/localhost.md`. User
decision (2026-07-13): migrate the persona into a dedicated subsite so
Tech Tool Guide flows through the same Staatic → GH Pages pipeline as
the four hobby pilots, leaving the localhost primary role as the
network's admin/hub (no scheduled publishing against it directly).

Work:
- `wp site create --slug=techtools --title="Tech Tool Guide"` at
  `techtools.localhost:8088`.
- Move + rename `website_memory/localhost.md` →
  `website_memory/techtools.localhost.md`. Rebrand the persona from
  "Software Tool Guide" to "Tech Tool Guide" (user's preferred name);
  update the "What this site is" and voice-anchor sections accordingly.
- Move + rename `website_memory/localhost.trends.json` →
  `website_memory/techtools.localhost.trends.json`.
- Add `techtools.localhost` to `extra_hosts` on the wordpress compose
  service (Apache's `ServerAlias *.localhost` already covers the vhost
  side).
- Add `TECHTOOLS_WP_*` block to `.env` and `.env.example`.
- Add `techtools` to `openclaw/deploy.DEPLOYABLE_SLUGS` (five deployable
  slugs total after this step).
- Add `scheduled-sites.json` entry (`enabled=false` initially).
- `gh repo create carterman82/openclaw-techtools --public` + init
  (README + `.nojekyll`) + enable Pages.
- Configure Staatic per new subsite.
- **Content migration decision (open for user):** if there are already
  Tech-Tool-Guide-branded posts on the localhost primary site that
  should carry over, export via `wp export --url=http://localhost:8088`
  and re-import into `techtools.localhost` via `wp import`. If localhost
  primary is treated as a scratch/network hub, skip the migration.
- Decide localhost primary's new role:
  - Option A: leave in `scheduled-sites.json enabled=true` for
    regression coverage of the openclaw pipeline against the primary.
  - Option B: flip to `enabled=false` so Tech Tool Guide is the only
    "tech tool" publisher and localhost becomes admin-only.
  - Recommended: Option B — matches the "dedicated subsite" answer.

Verification:
- [ ] `http://techtools.localhost:8088/` reachable; Tech Tool Guide
      persona loaded; categories intact (migrated from primary or
      freshly created 6–10 categories mirroring the current localhost
      set: AI Tools, Automation & Workflows, Best Of / Comparisons,
      Business, Design, Marketing, Freelance, Productivity Tools, SaaS,
      Uncategorized).
- [ ] `python -m openclaw post --site techtools --draft` produces a
      Tech Tool Guide draft; deploy pushes to `openclaw-techtools`;
      GH Pages URL returns 200 OK.
- [ ] Localhost primary is either a network hub or `enabled=false`;
      no duplicate deploys.

### Step 5.11 - Build `openclaw-base` parent theme + editorial-magazine child themes

Status: not started.

**Context:** the first-round pilot used Twenty Twenty-Five as the parent
theme with per-subsite `theme.json` overrides for palette and font
stacks. This shipped, but the subsites still LOOK like default WordPress
— Twenty Twenty-Five's block templates are generic and there's no shared
editorial identity across the network. Reference sites (catfancast.com,
animefancast.com) share a magazine-editorial layout that reads as a real
publication: sticky nav + wordmark, full-width hero, card grid, optional
sidebar, footer with brand + social + copyright.

**Design brief** (from WebFetch analysis of catfancast + animefancast,
2026-07-13):

- **Layout — magazine grid.**
  - Sticky top bar: wordmark left, primary category nav center (≤ 6
    top-level categories), social + optional subscribe/login right.
  - Full-width hero at top of home: latest featured article, prominent
    image, bold headline, dek/lede, byline + date.
  - Article grid below: cards with ~240×160 thumbnails, headline + tags
    + date, 3-col desktop / 2-col tablet / 1-col mobile.
  - Optional sidebar (child-theme opt-in): about blurb, category list,
    newsletter opt-in, social follow.
  - Footer: brand + tagline + link columns + social + copyright.
  - Article page: max-width ~720px reading column; full-bleed hero
    image; optional drop-cap; author card at the bottom.
- **Typography.** Sans-serif dominant per reference sites, with an
  optional serif for wordmark and dek. Suggested pairings per child
  theme (child-overridable):
  - Editorial-warm: Inter (body) + Fraunces Wide (display).
  - Modern-tech: Inter Tight (body) + Space Grotesk (display).
  - Softer editorial: Source Sans 3 (body) + Playfair Display (display).
- **Color system.** Parent defines six semantic slots as CSS variables —
  `background`, `surface`, `text`, `muted`, `primary`, `accent`. Every
  child overrides all six in `theme.json`; parent's block CSS never
  hard-codes hex.
- **Spacing scale.** 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 px. Grid gutter 24 px.

Work:
- Scaffold `wp-content/themes/openclaw-base/` on the host, bind-mounted
  like the child themes.
  - `style.css` — Theme URI, Author, `Text Domain: openclaw-base`, version.
  - `theme.json` — six semantic color slots (CSS vars), font-family
    presets, spacing scale, font-size scale, image size registrations
    (`hero-1600`, `card-480x320`, `card-240x160`).
  - `functions.php` — enqueue Google Fonts (or self-hosted); register
    image sizes; register block patterns; expose the sidebar toggle as
    a child-theme filter.
  - Block templates: `templates/index.html` (hero + grid),
    `templates/single.html`, `templates/archive.html`, `templates/page.html`.
  - Template parts: `parts/header.html`, `parts/footer.html`,
    `parts/hero.html`, `parts/card.html`, `parts/sidebar.html`,
    `parts/newsletter.html`, `parts/author-card.html`.
  - Block patterns: hero pattern, card-grid pattern, newsletter block,
    category chip strip.
- Retire the current `openclaw-{gardening,dogs,boardgames,coffee}` child
  themes. Create five new child themes (one per new subsite from 5.9 +
  techtools from 5.10):
  - `openclaw-redstone` — Minecraft. Moody dark background with a
    restrained editorial vibe; accent redstone-red. Font pair: Inter
    Tight + Space Grotesk.
  - `openclaw-sprueandcodex` — Warhammer 40K. Grimdark: near-black
    background, oxblood primary, brass accent. Font pair: Fraunces Wide
    (display) + Inter (body) — serif-heavy to evoke a gothic manuscript.
  - `openclaw-slipstream` — Formula 1. High-contrast bright: racing red
    primary, carbon black, safety-yellow accent. Font pair: Inter Tight
    + Space Grotesk (mechanical / technical).
  - `openclaw-clack` — Mechanical keyboards. Warm neutrals: muted almond
    background, walnut primary, teal accent (keycap-color inspired).
    Font pair: Inter body + JetBrains Mono for pull-quotes / specs.
  - `openclaw-techtools` — Tech Tool Guide. Clean modern SaaS: white
    background, indigo primary, cyan accent. Font pair: Inter Tight +
    Space Grotesk.
- Update `docker-compose.yml` volumes (both `wordpress` and `wpcli`):
  bind-mount the parent theme dir + the five new child theme dirs;
  remove the four retired child-theme mounts.
- Network-enable the parent + each child theme via wp-cli. Activate the
  appropriate child theme on each subsite.

**Design-skill note:** no dedicated WordPress-design skill exists in
this Claude Code environment (verified 2026-07-11; only `review` is
registered). Theme JSON, block templates, template parts, and block
patterns will be authored via normal Edit/Write. Claude can generate
all of the above but visual QA requires the user opening the subsites
in a browser after 5.11 lands.

Verification:
- [ ] Each subsite home renders a proper hero + card grid (not the
      Twenty Twenty-Five default layout).
- [ ] Each child theme has a visibly distinct palette, font pair, and
      wordmark treatment while sharing the parent's structural layout.
- [ ] Staatic re-export of each subsite reproduces the styled layout on
      GH Pages (no missing assets, no broken block styles).
- [ ] Regression: `python -m openclaw post --site catfancast --draft`
      still works (catfancast is a remote site; the openclaw-base
      changes don't affect it).

### Phase 5 revised exit criteria (supersedes prior)

- [x] Original four-subsite pipeline landed end-to-end (Steps 5.1–5.8).
- [ ] Four rebuilt pilot subsites (Step 5.9) + Tech Tool Guide subsite
      (Step 5.10) all publish end-to-end: WP publish → Staatic export
      → GH commit + push → GH Pages 200 OK.
- [ ] Each of the five subsites renders on GH Pages with the parent
      theme's magazine-editorial layout and its own child theme's
      identity — visibly a real publication, not a stock WP install.
- [ ] Multi-day passive verification (7 consecutive scheduled days) —
      **owed to user**.
- [ ] Deliberate failure recovery testing (Staatic error / git push
      error / GH Pages misconfig) — **owed to user**.

## 11.5 Phase 6 Plan - Analytics-Aware Agent

Status: not started.

Goal: feed measurable post performance back into topic and angle choices, so
later articles lean toward what is actually working.

### Step 6.1 - Choose analytics source

Status: not started.

Decide between:
- **Jetpack Stats** - WordPress plugin; per-post pageview API; requires the
  plugin active on the target site plus a Jetpack/WordPress.com account.
- **Google Analytics 4** - free; per-page metrics via Data API; needs a GA
  property, a service-account JSON, and URL matching with WP permalinks.
- **Plausible** - paid; simple stats API; needs a Plausible account + site.
- **The site's existing analytics** - check the target WP site first; if it
  already has analytics installed, prefer that.

Verification:
- [ ] Source decision recorded in §12 with date, choice, rationale (cost,
  setup effort, data freshness).
- [ ] Account/property/key obtained.
- [ ] New env var(s) added to `.env.example` (e.g. `JETPACK_TOKEN`,
  `GA_PROPERTY_ID`, or `PLAUSIBLE_API_KEY`).
- [ ] `Config` exposes the new env var; `.env` populated.
- [ ] Smoke test: a one-liner that fetches pageviews for one known URL
  returns a non-error response with a numeric view count.

### Step 6.2 - Build the analytics fetcher

Status: not started.

Add `openclaw/analytics.py` exposing:
- `fetch_top_posts(limit=10, lookback_days=30) -> list[dict]` returning
  `[{title, link, views}]` ordered by views descending.
- `fetch_bottom_posts(limit=5, lookback_days=30) -> list[dict]` for the
  opposite end of the distribution.
- Graceful failure: return `[]` on missing key, network error, or empty
  data; never raise into `main.py`.

Verification:
- [ ] `fetch_top_posts()` returns a non-empty list against a live site with
  30+ days of analytics.
- [ ] Same call with `lookback_days=1` succeeds (boundary check).
- [ ] Returned `link` values match the WP permalinks (cross-reference one
  link against `publisher.list_recent_posts_for_linking()`).
- [ ] Forcing a failure (delete the key in env, or block network) returns
  `[]` plus a WARNING log line; no exception escapes.

### Step 6.3 - Wire the signal into the generator

Status: not started.

Extend `generate_article()`:
- New params `top_performing_posts` and `bottom_performing_posts`
  (both `list[dict] | None`).
- User-message helper renders each as `"Title" — URL — N views in the last
  30 days`. Phrase the instruction in relative terms ("highest-performing")
  to avoid the model fixating on absolute view counts.
- System prompt addition: "These are the best- and worst-performing recent
  articles on this site. Identify what worked (topic types, angles, tone)
  and lean toward similar choices. Avoid the patterns that under-performed."

Wire `main.py` to call `fetch_top_posts()` and `fetch_bottom_posts()` and
pass the result through.

Verification:
- [ ] With analytics enabled, the assembled user message (logged at DEBUG)
  includes both top and bottom blocks.
- [ ] With analytics disabled (no key) the user message omits both blocks
  cleanly and the publish path still succeeds.
- [ ] Across 5 generated articles with analytics on, at least one has a
  topic or angle that visibly echoes a top-performer (qualitative check).

### Step 6.4 - Multi-week observation

Status: not started.

Analytics drift can't be A/B tested cleanly on a single low-traffic site, so
verification here is observational rather than experimental.

Verification:
- [ ] 14+ days of analytics-aware scheduled runs complete without
  introducing scheduling regressions (Phase 4 exit criteria still pass).
- [ ] A written weekly review captures: which top-performer patterns the
  agent picked up on, which it missed, and whether the running average
  pageviews/article trended up.
- [ ] No analytics-side failure has ever blocked a publish (graceful-skip
  pattern from `images.py` is preserved here).

### Step 6.5 - Documentation

Status: not started.

Verification:
- [ ] README.md "Analytics" section: source, env var, what the agent does
  with the data.
- [ ] CLAUDE.md architecture paragraph on `analytics.py` and its place in
  the data flow.
- [ ] §12 decision log entry for the chosen source and how performance is
  surfaced to the generator.

Phase 6 exit criteria:
- The agent has run for 14+ analytics-informed days without scheduling
  regressions, and the weekly review documents whether the signal
  influenced topic choice and whether average traffic moved.

## 12. Decision Log

- 2026-07-11: Phase reorder — analytics pushed to Phase 6; new Phase 5 = multisite + static export + GitHub Pages auto-commit. Rationale: distribution/hosting durability and free CDN matter more than per-post analytics tuning until the pipeline reliably produces publishable content at N-site scale. Analytics is more useful once there is meaningful traffic to observe, which requires the static-site distribution layer first.
- 2026-07-11: Phase 5 topology decisions (locked via AskUserQuestion): (a) 3-5 pilot subsites — prove the pattern before scaling; (b) monorepo `openclaw-sites` with per-subsite branches `site/<slug>`, each attached to its own custom domain via GH Pages branch-level custom-domain feature; (c) Staatic as static exporter (free, multisite-native, active as of May 2026); (d) network-default block theme (Twenty Twenty-Five) plus per-subsite child themes for structural overrides — mirrors the existing shared-style + per-site-persona split in `Instructions/*.md` + `website_memory/*.md`. Design-skill note: no dedicated WordPress-design skill exists in this Claude Code environment (checked 2026-07-11); theme JSON and pattern HTML will be authored via normal Edit/Write with Claude generating content.
- 2026-07-11: Editor pass (`revise_article`) verified working end-to-end. Two-agent generate→revise pipeline is now the default publish path. `--skip-review` preserved for smoke tests and single-provider comparisons. Editor rules are externalized to `Instructions/EDITOR.md` (loaded by `generator._load_editor_guide`) so they can be tuned without code changes, matching the STYLE.md / TOPIC.md pattern.
- 2026-06-09: Python agent - Anthropic SDK is first-class in Python and easy to schedule on Windows.
- 2026-06-09: WordPress REST API + Application Passwords - no plugin needed for posting.
- 2026-06-09: Manual CLI trigger before automation - easier to debug.
- 2026-06-09: Evergreen informational articles, 700-1200 words - focused enough for coherent output.
- 2026-06-09: Site identity: title `Openclaw`, tagline `A Claude-powered article experiment.`
- 2026-06-09: Timezone `America/Denver` - required for future 07:00 schedule.
- 2026-06-09: Comments disabled - avoids moderation/spam.
- 2026-06-09: No featured images in Phase 2 - deferred to Phase 3.
- 2026-06-09: Pivoted from Local by WP Engine to Docker - CLI-controllable setup on Windows.
- 2026-06-09: Local HTTP Application Passwords use a dev-only mu-plugin.
- 2026-06-09: `openclaw-agent` uses a Gmail plus-alias for identity.
- 2026-06-09: Tried OpenAI `gpt-4o`, then reverted to Claude after OpenAI quota issue.
- 2026-06-09: Claude structured output uses tool-use with forced `submit_article`.
- 2026-06-18: Phase 2 complete: publisher, CLI, logging, README, end-to-end publishing.
- 2026-06-18: Categories made dynamic from the configured WP site; constants are only fallback.
- 2026-06-18: Site-aware topic selection uses the WP site name.
- 2026-06-18: SEO fields added: `excerpt`, `slug`, `focus_keyphrase`.
- 2026-06-19: WordPress port bound to `127.0.0.1`; mu-plugin became repo-owned bind mount.
- 2026-06-19: Added recent-title de-duplication; Anthropic calls are stateless but topic choice needed steering.
- 2026-06-19: Added Phase 3 before automation: featured images plus internal/external links.
- 2026-06-19: Chose Unsplash dev tier for Phase 3 images: free, real photos, attribution required.
- 2026-06-19: Condensed `PLAN.md` for future LLM handoff after Phases 1 and 2 completed.
- 2026-06-20: OpenAI `gpt-image-1-mini` wired in as the default featured-image source; Unsplash retained as an automatic fallback. Per-article `image_prompt` field added to the Claude tool schema so visual style adapts to topic and site.
- 2026-06-29: Inserted Phase 3.5 SEO Hardening between Phase 3 and Phase 4 - Yoast SEO rated a representative article red (10 problems) with orange readability (2 problems); automating in that state would amplify, not reduce, the problem. Gating Phase 4 scheduling on this.
- 2026-06-29: Phase 3.5 routing approach: continue using `wp/v2/posts` `meta:` field (Yoast's `yoast/v1` REST namespace is mostly read-only) but add explicit post-publish read-back to confirm each meta key persisted; mu-plugin override of Yoast's `auth_callback` held in reserve if the Author-role agent is being silently rejected. Diagnostic step (3.5.1) decides which path.
- 2026-06-29: Phase 3.5 verification approach: `scripts/verify-seo.py` reimplements every Yoast SEO + Readability condition the agent can affect (Y1-Y12), reads each post + featured-media via REST, prints PASS/FAIL/WARN/SKIP per check, exits non-zero on any FAIL. Used by every Step 3.5.2+ verification block. Yoast's actual sidebar verdict still requires one manual WP Admin spot-check in Step 3.5.5 to catch any drift between the script's reimplementation and Yoast's live scoring (e.g. transition-word list differences).
- 2026-06-29 Step 3.5.1 outcome: Yoast meta keys (`_yoast_wpseo_focuskw`, `_yoast_wpseo_metadesc`, `_yoast_wpseo_title`) are absent from the REST meta block — they are NOT registered with `show_in_rest=true` on animefancast.com. A test write returns HTTP 200 but the value is silently discarded. Resolution chosen: mu-plugin (`wp-content/mu-plugins/openclaw-register-seo-meta.php`) that calls `register_post_meta` with `show_in_rest=true` and `auth_callback` requiring `edit_posts`. Auto-deployed on local Docker via bind mount; deployed to animefancast.com by the user via FTP/hosting panel or as an installable plugin ZIP.
- 2026-06-29 verify-seo.py no-plugin adaptations (Steps 3.5.2-3.5.4): On sites without the openclaw-seo-meta plugin, the Yoast meta keys are absent from REST. The verifier was updated to: (1) Routing absent → WARN instead of FAIL (unavoidable limitation, not a code bug); (2) Y1/Y3/Y7/Y8 → SKIP when plugin absent (can't verify keyphrase/seo_title/meta_description without REST access); (3) Y4 → WARN when plugin absent and post title >60 chars (actual seo_title is a separate shorter field); (4) slug-to-keyphrase inference improved: instead of using full slug as keyphrase, find the longest 2-4 word prefix of the slug that appears verbatim in the body text (corrects false FAILs on Y2/Y6/Y10 when slug has extra trailing words).
- 2026-07-01: Inserted Phase 3.6 (Multi-Site Modularity) between Phase 3.5 and Phase 4. Three design choices: (a) only DESCRIPTION.md moves per-site into `website_memory/{hostname}.md`; STYLE.md, TOPIC.md, IMAGE_GENERATOR.md stay global (TOPIC/IMAGE are cat-domain-specific today but not yet worth splitting until a second site demands it); (b) the persona file is picked from `urlparse(WP_BASE_URL).hostname` — no extra selector; changing WP_BASE_URL is already the site-swap lever; (c) `.env` supports per-site prefixed vars (e.g. `CATFANCAST_WP_BASE_URL`) and a new `--site <slug>` CLI flag; `main._activate_site()` copies prefixed vars into their bare positions before `Config.load()`, so downstream code stays unaware of prefixes. Missing persona file is a hard error (fail-fast), because silent generic content would be worse than a clear stop.
- 2026-07-02: Inserted Phase 3.7 (Editorial Rewrite of STYLE.md) as §9.6. User verdict on generated output: "no structure, made by AI." Full restructure of STYLE.md around a mandatory article architecture (hook -> thesis -> body arc -> conclusion payoff), casual Putnam-style voice with a real voice anchor, research-woven-into-narrative rules, and consolidated banned-lists. Article length raised 700-1200 -> 1500-2500 words (ideal SEO range); `generator.py` MAX_TOKENS 4096 -> 12000. Keyphrase-density floor made proportional (1 per 200 words) so the Yoast v25 check still passes at the longer length. Proof: 3 published posts on localhost, each gated on style review + verify-seo.py.
- 2026-07-02: Em-dash elimination moved from prompt to code. Five consecutive generations ignored both the STYLE.md ban and a generator.py hard constraint (verified against raw stored content via `?context=edit`, ruling out wptexturize). Added `main._strip_em_dashes()`: deterministic post-processor that replaces em dashes with commas across body_html, title, excerpt, meta_description, seo_title, and image_alt_text before publish, logging a WARNING with the count. Lesson recorded: negative stylistic constraints the model reliably violates belong in deterministic post-processing, not in more prompt emphasis.
- 2026-07-02: Reddit RSS 429s hardened in `openclaw/trends.py`. Anonymous RSS
  rate limiting meant a fixed 2-3s gap between subreddit requests routinely
  429'd all 3 subs in a row. Widened the inter-request delay to 6-9s and added
  `_get_reddit_rss()`, which retries a 429 up to 3 times with backoff (honors
  `Retry-After` when present, else 10s/21s/31s + jitter) before giving up on
  that subreddit. Verified live: with the fix, all 3 configured subreddits
  (Entrepreneur, smallbusiness, productivity) returned posts in one run,
  where previously all 3 hit the 429 WARNING path. `fetch_reddit_trends` still
  never raises; a subreddit that exhausts retries just contributes no posts.
- 2026-07-10: Phase 4 scheduling — hosting target = **Windows Task
  Scheduler on the user's laptop**; failure channel = **log-flag only**
  (no toast/email/push). Rationale: prototype-stage automation; zero
  infra spend, zero third-party accounts, and the user is on this
  laptop daily. Trade-off: a laptop asleep or off at 07:00 skips that
  day (Wake-to-Run + StartWhenAvailable narrow but don't close the
  window); silent failure surfaces via a file the user must
  proactively check. Escape hatch is a cloud VM + cron; the wrapper
  is Docker-agnostic and would port over unchanged. Multi-site was
  layered in: `scheduled-sites.json` (root) lists sites the daily run
  iterates. Retry policy per site: 3 attempts total, waits 60s / 300s.
  Failure of one site does not skip others; wrapper exit code = number
  of ultimately failing sites.
- 2026-07-10: Phase 3.8 code landed (Steps 3.8.2–3.8.4). Decisions:
  (a) HTTP client for the local provider is the `openai` Python SDK
  pointed at LM Studio via `base_url`, not raw `requests` — LM Studio is
  intentionally OpenAI-compatible so the tool-use JSON shape matches what
  the model was trained on, and `openai` is already a project dependency
  (used by `images.generate_openai_image`). (b) Fallback trigger set:
  connection error, timeout, any `openai.APIError`, empty tool call, wrong
  tool name, non-JSON arguments, or missing/empty required article field —
  all funnel through `LocalProviderError`. (c) Fallback is single-hop
  (local → Claude); Claude failures propagate. (d) Local timeout set to
  600s so first-token latency on a cold 35B model doesn't spuriously
  trigger fallback — fallback should mean "the local model can't do this
  today," not "the local model needs another few seconds to think." (e)
  When `LOCAL_MODEL_ENABLED=True` but the URL or name is missing,
  fallback to Claude with `reason=misconfigured` rather than raising —
  matches the "never block publishing on a provider issue" philosophy.
  `qwen/qwen3.6-35b-a3b` confirmed present on `/v1/models`; latency check
  and tool-use round-trip (`scripts/smoke-local-toolcall.py`) still owed
  by the user once the model is loaded into LM Studio's memory.
- 2026-07-11: Anti-AI-pattern work — randomness moved from prompt to code.
  Published articles were flagged as AI (GPTZero, human readers) and both
  sites clustered on the same categories/topics despite TOPIC.md rotation
  rules; LLMs can't self-randomize, so prompt-only rotation demonstrably
  failed. Changes: (a) `main.py` now rolls a random category up front
  (`_pick_random_category`, excludes Uncategorized) when neither `--topic`
  nor `--category` is given, and rolls per-run variation directives
  (`_roll_variation_directives`: length band 900-1300/1300-1800/1800-2400,
  FAQ ~1-in-3, one of six hook types) injected into the user message;
  (b) `generator.py` gained a `variation_directives` param and the
  base-rules length now defers to the directive; (c) STYLE.md loosened the
  sameness-manufacturing rules (keyphrase density to ~1 per 300-400 words,
  transition-word floor deleted, FAQ directive-gated, mandatory structural
  variance, burstiness section, closer rotation, expanded banned-word list,
  negative-parallelism hard cap); (d) TOPIC.md: category is pre-assigned,
  §7 rotation biases hardened into hard bans. Accepted trade-off: yellow
  Yoast scores where green forced robotic sameness.
- 2026-07-11: Second-pass editor agent added (`generator.revise_article`).
  User request: mimic real editorial review — a second agent audits every
  draft for helpfulness, redundancy, style-guide compliance, and SEO-field
  correctness before publish; doubled token cost accepted since generation
  will be local-model-first. Design: the draft article JSON is wrapped in a
  `reference_data type="draft_article"` block and sent through the same
  `_dispatch` local-with-Claude-fallback router (log lines now carry
  `stage=generate|revise`) under an editor system prompt that includes the
  site persona + STYLE.md but skips TOPIC.md/IMAGE_GENERATOR.md (topic is
  already fixed). Hard constraints: same topic/thesis/category (category is
  code-guarded — restored with a WARNING if the editor changes it), no new
  links and existing hrefs byte-identical, no invented facts, stay in the
  directive length band. The revised article re-enters the existing
  post-generation pipeline (sanitizer, em-dash strip, anchor validation,
  external-link attrs), so nothing the editor emits is trusted more than
  the writer's output. `--skip-review` on `python -m openclaw post`
  bypasses the pass; main.py logs the word-count delta.
- 2026-06-29: Swapped site persona from AnimeFancast.com to catfancast.com to escape anime IP/character-copyright risk and lean fully into copyright-free evergreen content. Code unchanged — the agent is already site-agnostic (categories, site name, link candidates, and SEO plugin are all discovered from `/wp-json/` at runtime). All `Instructions/*.md` content rules updated: DESCRIPTION.md rewritten for real cats only; TOPIC.md restructured from anime title-anchors to five parallel domain-anchor inventories (breeds, behaviors, biology, health & care, history & culture) with a heavier ~92/8 evergreen bias; IMAGE_GENERATOR.md worked example replaced (Maine Coon piece) and the Agent Workflow §5 inverted from "copyrighted characters preferred" to a hard ban on copyrighted fictional cats with real-cat-only depictions; STYLE.md banned-phrase example tweaked; CLAUDE.md SEO routing example + TOPIC.md description line updated. Historical references to animefancast.com (verified post URLs, completed Phase 3 records, prior decision-log entries) intentionally preserved as audit trail. `.env` to be repointed by user when catfancast.com is live; first run against the new site picks up the new categories/site-name automatically. The `openclaw-seo-meta` mu-plugin / installable plugin at `demo/openclaw-seo-meta/` should be installed on catfancast.com when ready, otherwise Routing + Y1/Y3/Y7/Y8 will SKIP/WARN as documented in §9.
- 2026-07-13: Phase 5 executed end-to-end. Full context in PLAN.md §11 Steps 5.1–5.8. Highlights of what changed vs. the July 11 plan: (a) subdomain suffix `.openclaw.local` → `.localhost` (hosts-file wildcards not supported on Windows; `.localhost` short-circuits to loopback for free in browsers/curl; a Python `openclaw/_localhost_dns.py` DNS shim closes the Python-side gap). (b) Repo topology "one private repo, branch-per-subsite, custom domain per branch" → "four public repos, one per subsite, free github.io URLs" (free-tier Pages doesn't work on private repos, user picked free URLs, cleaner 1:1 domain-to-repo mapping if custom domains land later). (c) Extensive Docker networking work landed to let Staatic crawl `<slug>.localhost:8088` from inside the container: `extra_hosts` on wordpress service, `network_mode: "service:wordpress"` on wpcli, a bind-mounted `apache/openclaw-multisite.conf` adding `Listen 8088` + `ServerAlias *.localhost`. (d) The user's `carterman82.github.io` repo has an account-level CNAME to `www.reggaefancast.com`, so all project Pages URLs 301-redirect there — transparent to internal-link rewriting, documented as fine.
- 2026-07-13: Phase 5 pilot rework planned (Steps 5.9–5.11 added). User rejected the first-round niches (`gardening`/`dogs`/`boardgames`/`coffee`) as too broad for the "fancast" family; also noted `dogfancast.com` already exists (name collision) and the default WordPress look isn't good enough. Rework: (a) delete + rebuild the four pilots with narrow-fandom niches and **original** brand names (not `X-fancast`) — proposed set: **Redstone Register** (Minecraft), **Sprue & Codex** (Warhammer 40K), **Slipstream Journal** (Formula 1), **Clack Report** (Mechanical keyboards). (b) Add Tech Tool Guide as a dedicated `techtools.localhost` subsite (rebrand from the current "Software Tool Guide" localhost persona) and add it to `DEPLOYABLE_SLUGS`. (c) Build an `openclaw-base` parent theme in the catfancast/animefancast editorial-magazine style (sticky nav + wordmark, full-width hero, card grid, optional sidebar, footer) + five new child themes overriding six semantic color slots and a font pair each. Execution paused pending user approval of Steps 5.9–5.11.
- 2026-07-13: Resumed Phase 3.8 (finish steps 3.8.1/3.8.5-3.8.7) and added Phase 3.9 (local image generation) in the same session, after the user pointed at two live LAN endpoints: Qwen3.6 via LM Studio (`http://192.168.0.200:1234/v1`) and Flux via the Draw Things app's HTTP API (`http://192.168.0.200:7860`). Draw Things exposes an Automatic1111-compatible `POST /sdapi/v1/txt2img` (confirmed via live GET-root probing plus WebSearch — `GET /` returns the loaded model's default params, not a generation call). Image fallback chain designed as local Flux -> OpenAI `gpt-image-2` -> Unsplash, mirroring the text router's "never raises, return None, try next" contract exactly (no new exception types needed). Chose `1024x576` (16:9, matches the generator's hard landscape rule) and a fixed negative prompt banning text/watermark/logo/signature, since Draw Things' API supports a negative prompt unlike OpenAI's. `LOCAL_IMAGE_TIMEOUT_SECONDS=300.0` (vs. 600.0 for text) as a starting guess for local Flux inference; to be revisited once real latency is observed. **Incident**: a single test `POST` against the Draw Things endpoint left both port 7860 and the unrelated port 1234 (LM Studio) refusing new connections, while the host still answered ping — read as the GPU/host getting pinned rendering the test image, not a code or network-config bug. User chose to check the machine themselves rather than have live verification continue; all code/config/doc work for both Phase 3.8's remaining steps and the new Phase 3.9 was completed regardless (nothing in either required the host to be up), with live verification (Step 3.8.1's tool-call round-trip, Step 3.8.5's 5-run quality gate, and Phase 3.9 Step 3.9.5) deferred until the user confirms the host is responsive again.
- 2026-07-14: Live verification of Phase 3.8/3.9 against the LAN host, once confirmed responsive. **Bug found and fixed**: `_generate_with_local` in `generator.py` (and the `smoke-local-toolcall.py` script) called the OpenAI-compatible endpoint with `tool_choice={"type":"function","function":{"name":tool_name}}`; this LM Studio server version rejects that with HTTP 400 ("Supported string values: none, auto, required"). Both call sites fixed to `tool_choice="required"` — equivalent here since only one tool is ever offered, and the pre-existing `call_name != tool_name` check still guards against a wrong tool. This would have silently broken the entire local-text primary path (100% fallback to Claude) had it shipped unverified — confirms the value of Step 3.8.1's "prove it before trusting it" gate. After the fix: `smoke-local-toolcall.py` PASS at 2.81s latency; `smoke-local-image.py` PASS at 109.39s latency (909KB landscape PNG, visually confirmed on-topic and uncorrupted). Full-pipeline testing (3 `--site localhost --draft` runs) showed local `generate`/`revise` succeeding 2/3 and 2/3 respectively, with the misses sharing one signature: `LocalProviderError: model returned no tool call (content preview: '' or '\n\n')`. Working theory: Qwen3.6 is a reasoning/thinking model, and its internal reasoning tokens occasionally consume the full `MAX_TOKENS=12000` budget on the large article-generation/revision prompts before it emits the tool call — the tiny 2-field smoke-test schema never triggers this. Not root-caused or fixed in this session (the router's fallback-to-Claude already absorbs it correctly per the fallback design); left as an open item for Step 3.8.5's formal 5-run quality gate to quantify and potentially address (e.g. raising `MAX_TOKENS` or disabling extended thinking on the local server). One run also stalled ~9.5 hours mid-request (`ConnectionResetError` after a long hang) — traced to the host machine sleeping mid-request, not a code or config defect; re-ran cleanly once the machine was awake. Both-flags-disabled run confirmed pre-3.8/3.9 behavior is unchanged (`provider=claude` both stages, `source=OpenAI` image). Phase 3.9 exit criteria met in full; Phase 3.8 Step 3.8.1 complete; Step 3.8.5's formal 5-run gate remains open, informed by (but not satisfied by) this session's 3 runs.
- 2026-07-14 (continuation): Qwen "no tool call" failure escalated from the earlier 2/3 rate to **3-for-3** on a single `--site localhost` run — `subreddit_select` (content preview `''`, ~18s), `generate` (`'\n\n'`, ~2m40s), `revise` (`''`, ~2m20s). All three stages completed with HTTP 200 and non-trivial latency (Qwen is spending compute) but returned empty `tool_calls`. Every stage fell back to Claude, so the run still published — but with zero benefit from having Qwen enabled. Because `scripts/smoke-local-toolcall.py` passed the same day at 2.81s using a trivial 2-field schema, the failure is not a transport or auth issue and cannot be reproduced by the current smoke test. **Working hypothesis** (to be falsified, not assumed): Qwen3.6 has a hybrid reasoning mode; if LM Studio serves it with thinking enabled, Qwen burns tokens on `<think>…</think>` before ever emitting a tool call, hits `MAX_TOKENS=12000`, and returns empty content + no `tool_calls`. Alternative candidates to rule out: prompt-length pressure (STYLE.md ~51k + TOPIC.md ~37k + IMAGE_GENERATOR.md ~10k + website_memory ~8k on `generate`), tool-schema complexity (`submit_article` has 15 required fields vs. smoke's 2), or LM Studio serving-side settings drift since 3.8.1's PASS. **Plan**: three new Phase 3.8 steps (3.8.5-3.8.7) added to run this to ground before the formal quality gate (renumbered 3.8.8) can be measured — reproduce the failure outside the publish pipeline with the real production schemas + prompts (3.8.5), persist the full raw response body on every future no-tool-call incident so scheduled runs leave a forensic trail instead of a lossy 200-char preview (3.8.6), and expose four new `.env` tuning knobs — `LOCAL_MODEL_TEMPERATURE`, `LOCAL_MODEL_TOP_P`, `LOCAL_MODEL_MAX_TOKENS`, `LOCAL_MODEL_DISABLE_THINKING` — so thinking can be turned off (and other levers pulled) without a code change (3.8.7). Previously-pending steps renumbered: quality gate → 3.8.8, regression check → 3.8.9, docs → 3.8.10. The router's fallback is doing exactly what it was designed to do, so this is not a user-visible outage; it is a "primary path is currently 0% effective" defect that Steps 3.8.5-3.8.7 need to close before the primary/fallback split is worth measuring.
- 2026-07-14 (Steps 3.8.5-3.8.7 resolution): **Root cause confirmed: thinking-mode token exhaustion, and it's non-deterministic.** `scripts/smoke-local-toolcall.py` was extended with a `--stages` flag reusing the real `subreddit_select`/`generate`/`revise` schemas and prompts, dumping full diagnostics (including LM Studio's `message.reasoning_content` field, which turned out to be the key signal) to `logs/qwen-smoke-<stage>.json`. Observed `reasoning_content` length ranged from 600 to ~52,700 chars across calls with similar prompt shapes — when it runs long, `completion_tokens` hits the ceiling, `finish_reason=length`, and both `content` and `tool_calls` come back empty, exactly the field-level signature of the production fallbacks. Length did not track cleanly with prompt size or schema complexity (the short-prompt/small-schema `subreddit_select` stage failed in production while the long-prompt/large-schema `generate`/`revise` stages sometimes passed in isolation), ruling out those two alternative hypotheses. Two suppression mechanisms were tested against this LM Studio build: the plan's originally-specified `extra_body={"chat_template_kwargs":{"enable_thinking":False}}` is silently ignored (identical behavior with the flag true/false); `extra_body={"reasoning_effort":"none"}` does suppress `reasoning_content` (confirmed empty) but reliably breaks `tool_choice="required"` grammar enforcement — 0/4 trials produced a tool call when present, the model just answers in prose. A third option, Qwen3's native `/no_think` inline suffix, partially suppressed reasoning and preserved tool-calling but was unreliable (~40-60% success across repeated trials) and was not adopted. **Decision**: since no suppression mechanism is both effective and safe, `LOCAL_MODEL_DISABLE_THINKING` (Step 3.8.7) ships defaulting to **`false`**, deviating from the plan's original `true` default; it's wired as an opt-in escape hatch using the `reasoning_effort` mechanism for a future LM Studio/model build that might handle it better. The practical fix that did ship: `LOCAL_MODEL_MAX_TOKENS` (new `.env` knob, default 12000) threaded through both `generator.py::_generate_with_local` and `trends.py::_select_subreddits_local`, which also fixed a pre-existing bug where `trends.py` hardcoded `_SUBREDDIT_SELECT_MAX_TOKENS=2048` — below even the low end of observed reasoning lengths, so that stage was essentially guaranteed to fail regardless of the thinking-mode question. Step 3.8.6 shipped `openclaw/_local_diagnostics.py::dump_fallback_response`, called from both call sites before every fallback-triggering raise, writing `logs/qwen-fallback-YYYY-MM-DD-HHMMSS-<stage>.json` sidecars with the full raw response (verified live: three real dumps captured from a `--site localhost --draft` run, each showing `finish_reason=length`, `completion_tokens` pinned near 12000, and a populated `reasoning_content`). **Net outcome**: with all three 3.8.7 knobs in place, a full end-to-end run (`logs/_e2e-run-1.log`) still fell back on all three stages (subreddit_select, generate, revise) — the router/fallback contract held and the post published cleanly via Claude, but the "local as primary" goal was not achieved in this session. Step 3.8.8's quality gate (4-of-5 local successes) remains blocked; next options are a future LM Studio/model build with working thinking-mode control, or formally downgrading Qwen3.6 to advisory-only and keeping Claude as primary.

## 13. Open Questions

- Theme: **superseded 2026-07-13**. Step 5.11 will replace the Twenty Twenty-Five parent + palette-only child theme approach with a dedicated `openclaw-base` parent theme in the catfancast/animefancast editorial-magazine style.
- Version control remote: Openclaw's main repo lives at `github.com/carterman82/openclaw`. First-round Phase 5 static exports live in four sibling repos (`openclaw-{gardening,dogs,boardgames,coffee}`); those repos will be archived/deleted as Step 5.9 rebuilds them under the new brand slugs (`openclaw-{redstone,sprueandcodex,slipstream,clack}`).
- Analytics source for Phase 6 - Jetpack Stats vs Google Analytics 4 vs Plausible vs the site's existing analytics. Decide in §11.5 Step 6.1.
- ~~Custom-domain source for Phase 5 pilot subsites~~ — RESOLVED 2026-07-13: chose free `carterman82.github.io/openclaw-<slug>/` URLs.
- ~~Media handling for static export~~ — RESOLVED 2026-07-13: Staatic 1.12.5 bundles `/wp-content/uploads/` into per-subsite exports; verified in Step 5.4.
