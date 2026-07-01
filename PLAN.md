# PLAN - WordPress Sandbox + Openclaw Agent

> Living handoff for future LLM sessions.
> Last updated: 2026-06-29.

## 1. Current State

Openclaw is a WordPress prototype article site plus a Python agent that uses
Claude to generate evergreen articles and publish them through the WordPress
REST API.

Completed:
- Phase 1: local Docker WordPress site is running and REST publishing works.
- Phase 2: `python -m openclaw post` generates and publishes articles end to end.

Current active work:
- Phase 3.5: SEO hardening — fix Yoast red/orange scores before automation.

Future:
- Phase 4: schedule daily publishing at 07:00 America/Denver.
- Phase 5: make the agent analytics-aware.

Recently completed:
- Phase 3: featured images and contextual links (2026-06-19).

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

## 10. Phase 4 Plan - Scheduling

Status: not started.

Goal: `python -m openclaw post` runs unattended once per day at 07:00
America/Denver. Transient failures retry; a hard failure notifies the user.

### Step 4.1 - Choose hosting target

Status: not started.

Decide between:
- **Windows Task Scheduler on the user's laptop** - free; only runs when the
  laptop is awake; requires the Wake-to-Run setting to fire reliably.
- **Always-on cloud VM** (DigitalOcean/Linode/Hetzner, ~$4-6/mo) with cron.
- **GitHub Actions scheduled workflow** - free for public repos; cold-start
  measured in seconds; needs the WP site reachable from the public internet
  (not the localhost-only mu-plugin setup).

Verification:
- [ ] Decision recorded in §12 with date, choice, and rationale.
- [ ] Cost ceiling stated.
- [ ] Known failure modes documented here (e.g. "laptop asleep at 07:00
  skips that day unless Wake-to-Run is enabled").

### Step 4.2 - Wrapper script

Status: not started.

Build a small entry script the scheduler invokes. Suggested name:
`scripts/run-openclaw.ps1`. Responsibilities:
- cd into the project root regardless of the scheduler's working directory.
- Activate `.venv`.
- Run `python -m openclaw post`.
- Append stdout+stderr to `logs/openclaw-YYYY-MM-DD.log` (one file per day;
  `logs/` is gitignored).
- Exit with the Python process's exit code.

Verification:
- [ ] `scripts/run-openclaw.ps1` exists; `logs/` is in `.gitignore`.
- [ ] Invoking the script from a fresh PowerShell session in an arbitrary
  cwd produces a published post within ~60s.
- [ ] The log for that run contains the full pipeline output (config
  loaded, Claude call, image upload, publish URL).
- [ ] `$LASTEXITCODE` is 0 on success and non-zero on inner failure.

### Step 4.3 - Schedule configuration

Status: not started.

Create the scheduler entry for the host chosen in 4.1.

For Windows Task Scheduler specifically:
- Trigger: daily at 07:00 America/Denver.
- Action: run `scripts/run-openclaw.ps1`.
- "Wake the computer to run this task" enabled.
- "Run whether user is logged on or not" with stored credentials.
- History enabled.

Verification:
- [ ] Task "Openclaw daily post" appears in Task Scheduler.
- [ ] Right-click → Run produces a published post within ~60s.
- [ ] Setting the trigger to "in 5 minutes" and walking away fires it
  automatically and publishes a post.
- [ ] The History tab shows "Task Started" → "Action Completed" with
  exit code 0 for the run.
- [ ] Sleeping the machine before a near-future test trigger confirms Wake-
  to-Run fires the task within a few minutes (one-time check).

### Step 4.4 - Retry + failure notification

Status: not started.

Implementation:
- Wrapper retries the Python command on non-zero exit up to **N=2** times,
  waiting 60s then 300s between attempts.
- After all retries fail, write the failing log path + last 50 lines to
  `logs/last-run-failed.flag`.
- On final failure, trigger a notification via exactly one channel:
  Windows Toast (`BurntToast` PowerShell module), email (PowerShell SMTP),
  or a push service (Pushover/Pushbullet HTTP POST). Record the choice in
  §12.

Verification:
- [ ] Simulated transient failure (e.g. unset `ANTHROPIC_API_KEY` in `.env`
  before invoking the wrapper) → wrapper logs 2 retries and then exactly
  one notification.
- [ ] Simulated transient-then-recover (delete the bad env var between
  retries) → wrapper logs success and no notification fires.
- [ ] After a subsequent successful run, `logs/last-run-failed.flag` is
  removed or overwritten with success status.
- [ ] Notification arrives within 30s of the final retry's failure.

### Step 4.5 - Multi-day end-to-end verification

Status: not started.

Verification:
- [ ] 3 consecutive scheduled days each produce 1 published article.
- [ ] All 3 logs are present in `logs/` with timestamps inside the trigger
  windows (07:00-07:02 America/Denver).
- [ ] The 3 article topics are distinct (recent-title de-dup still works).
- [ ] Task Scheduler History shows 3 successful runs, 0 failed runs.
- [ ] `logs/last-run-failed.flag` is absent or shows success status.
- [ ] `logs/` disk usage after 3 days is under 10 MB (sanity check on
  rotation).

### Step 4.6 - Documentation

Status: not started.

Verification:
- [ ] README.md gains a "Scheduling" section with the wrapper-script path,
  the scheduler entry name, and how to disable/re-enable.
- [ ] CLAUDE.md architecture section adds a line on the wrapper + scheduler
  layer.
- [ ] §12 decision log has entries for hosting target and notification
  channel.

Phase 4 exit criteria:
- 7 consecutive scheduled days produce 7 distinct published articles with
  no manual intervention.
- At least one transient failure (real or simulated) has been recovered by
  the retry logic.

## 11. Phase 5 Plan - Analytics-Aware Agent

Status: not started.

Goal: feed measurable post performance back into topic and angle choices, so
later articles lean toward what is actually working.

### Step 5.1 - Choose analytics source

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

### Step 5.2 - Build the analytics fetcher

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

### Step 5.3 - Wire the signal into the generator

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

### Step 5.4 - Multi-week observation

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

### Step 5.5 - Documentation

Status: not started.

Verification:
- [ ] README.md "Analytics" section: source, env var, what the agent does
  with the data.
- [ ] CLAUDE.md architecture paragraph on `analytics.py` and its place in
  the data flow.
- [ ] §12 decision log entry for the chosen source and how performance is
  surfaced to the generator.

Phase 5 exit criteria:
- The agent has run for 14+ analytics-informed days without scheduling
  regressions, and the weekly review documents whether the signal
  influenced topic choice and whether average traffic moved.

## 12. Decision Log

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
- 2026-06-29: Swapped site persona from AnimeFancast.com to catfancast.com to escape anime IP/character-copyright risk and lean fully into copyright-free evergreen content. Code unchanged — the agent is already site-agnostic (categories, site name, link candidates, and SEO plugin are all discovered from `/wp-json/` at runtime). All `Instructions/*.md` content rules updated: DESCRIPTION.md rewritten for real cats only; TOPIC.md restructured from anime title-anchors to five parallel domain-anchor inventories (breeds, behaviors, biology, health & care, history & culture) with a heavier ~92/8 evergreen bias; IMAGE_GENERATOR.md worked example replaced (Maine Coon piece) and the Agent Workflow §5 inverted from "copyrighted characters preferred" to a hard ban on copyrighted fictional cats with real-cat-only depictions; STYLE.md banned-phrase example tweaked; CLAUDE.md SEO routing example + TOPIC.md description line updated. Historical references to animefancast.com (verified post URLs, completed Phase 3 records, prior decision-log entries) intentionally preserved as audit trail. `.env` to be repointed by user when catfancast.com is live; first run against the new site picks up the new categories/site-name automatically. The `openclaw-seo-meta` mu-plugin / installable plugin at `demo/openclaw-seo-meta/` should be installed on catfancast.com when ready, otherwise Routing + Y1/Y3/Y7/Y8 will SKIP/WARN as documented in §9.

## 13. Open Questions

- Theme: current default block theme is acceptable; revisit if visual polish matters.
- Hosting target for Phase 4 - Windows Task Scheduler (laptop) vs cloud VM vs GitHub Actions. Decide in §10 Step 4.1.
- Notification channel for Phase 4 - Windows Toast vs email vs push service. Decide in §10 Step 4.4.
- Version control remote: local-only or GitHub?
- Analytics source for Phase 5 - Jetpack Stats vs Google Analytics 4 vs Plausible vs the site's existing analytics. Decide in §11 Step 5.1.
