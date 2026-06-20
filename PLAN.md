# PLAN - WordPress Sandbox + Openclaw Agent

> Living handoff for future LLM sessions.
> Last updated: 2026-06-20.

## 1. Current State

Openclaw is a WordPress prototype article site plus a Python agent that uses
Claude to generate evergreen articles and publish them through the WordPress
REST API.

Completed:
- Phase 1: local Docker WordPress site is running and REST publishing works.
- Phase 2: `python -m openclaw post` generates and publishes articles end to end.

Current active work:
- Phase 3: add featured images and contextual links.

Future:
- Phase 4: schedule daily publishing at 07:00 America/Denver.
- Phase 5: make the agent analytics-aware.

Content rules:
- Evergreen informational articles.
- Target length: 700-1200 words.
- No reader comments.
- No featured images yet; planned for Phase 3.
- Categories are discovered from the configured WordPress site at runtime.

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

## 9. Phase 4 Plan - Scheduling

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
- [ ] Decision recorded in §11 with date, choice, and rationale.
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
  §11.

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
- [ ] §11 decision log has entries for hosting target and notification
  channel.

Phase 4 exit criteria:
- 7 consecutive scheduled days produce 7 distinct published articles with
  no manual intervention.
- At least one transient failure (real or simulated) has been recovered by
  the retry logic.

## 10. Phase 5 Plan - Analytics-Aware Agent

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
- [ ] Source decision recorded in §11 with date, choice, rationale (cost,
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
- [ ] §11 decision log entry for the chosen source and how performance is
  surfaced to the generator.

Phase 5 exit criteria:
- The agent has run for 14+ analytics-informed days without scheduling
  regressions, and the weekly review documents whether the signal
  influenced topic choice and whether average traffic moved.

## 11. Decision Log

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

## 12. Open Questions

- Theme: current default block theme is acceptable; revisit if visual polish matters.
- Hosting target for Phase 4 - Windows Task Scheduler (laptop) vs cloud VM vs GitHub Actions. Decide in §9 Step 4.1.
- Notification channel for Phase 4 - Windows Toast vs email vs push service. Decide in §9 Step 4.4.
- Version control remote: local-only or GitHub?
- Analytics source for Phase 5 - Jetpack Stats vs Google Analytics 4 vs Plausible vs the site's existing analytics. Decide in §10 Step 5.1.
