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

## Multi-site setup (Phase 3.6)

You can keep credentials for multiple WordPress sites in one `.env` and pick
the active site at the CLI. The site's persona (what to write about, tone,
green/red-light topics) lives in a per-site file under `website_memory/`.

**1. Add a prefixed block to `.env`** — repeat the three `WP_*` vars with a
site slug prefix (uppercase, underscore-separated):

```env
# Cross-site keys (unchanged)
ANTHROPIC_API_KEY=sk-ant-…
UNSPLASH_ACCESS_KEY=…
OPENAI_API_KEY=sk-…

# Per-site: catfancast.com
CATFANCAST_WP_BASE_URL=https://catfancast.com
CATFANCAST_WP_USERNAME=openclaw-agent
CATFANCAST_WP_APP_PASSWORD=…

# Per-site: another
OTHERSITE_WP_BASE_URL=https://othersite.com
OTHERSITE_WP_USERNAME=openclaw-agent
OTHERSITE_WP_APP_PASSWORD=…
```

**2. Add the site's persona file** at `website_memory/{hostname}.md`, where
`{hostname}` matches the host of the site's `WP_BASE_URL` exactly (no www
stripping, no aliasing). E.g. `WP_BASE_URL=https://catfancast.com` →
`website_memory/catfancast.com.md`. See `website_memory/README.md` for the
naming rule and a template.

**3. Run with `--site`**:

```powershell
python -m openclaw post --site catfancast --draft
python -m openclaw post --site othersite --draft
```

If `--site` is omitted, the agent falls back to the bare `WP_*` env vars, so
existing single-site setups keep working with no change.

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
`gpt-image-2`) is wired in `openclaw/images.py` for one-line swap-in —
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

## SEO fields

Every generated article includes a full set of Yoast/RankMath SEO fields:

| Field | Rule |
|---|---|
| `focus_keyphrase` | 2–4 words; must appear in title, first sentence of body, slug, image alt, meta description |
| `seo_title` | Must start with the focus keyphrase; ≤ 60 characters |
| `meta_description` | 120–156 characters; contains focus keyphrase; reads like ad copy, not a restatement of title |
| `image_alt_text` | 8–125 characters; contains focus keyphrase; describes the actual image |
| `slug` | 3–6 hyphenated lowercase words; contains focus keyphrase; no stop words |
| `excerpt` | 150–160 characters; contains focus keyphrase; click-worthy without "In this article…" |

These are written to WordPress via the post `meta` field. On sites with the `openclaw-seo-meta` plugin (or an equivalent that registers the keys with `show_in_rest=true`), the values persist and round-trip cleanly. Without the plugin, the agent publishes the article anyway and logs a WARNING for each missing key.

Run `scripts/verify-seo.py` to programmatically check all 12 Yoast SEO + Readability conditions on a published post:

```powershell
python scripts/verify-seo.py <post_id>
python scripts/verify-seo.py --latest
```

Exit code 0 = no FAIL (WARNs and SKIPs are acceptable). On sites without the plugin, Routing and Y1/Y3/Y7/Y8 are automatically SKIP/WARN — the remaining content-shape checks (Y2, Y4–Y6, Y10–Y12) are fully verifiable.

## Scheduling (Phase 4)

The daily unattended run is driven by `scripts/run-openclaw.ps1`. It reads
`scheduled-sites.json` at the project root, iterates every entry with
`enabled=true`, and publishes one article per site.

**`scheduled-sites.json` schema** — an array of `{slug, enabled, notes}`
objects. `slug` matches the prefix used in `.env` (e.g. `catfancast` →
`CATFANCAST_WP_*`). Toggle a site off by setting `"enabled": false`; the
wrapper skips it entirely (no retries burned).

```json
[
  { "slug": "localhost",  "enabled": true,  "notes": "Local Docker dev site." },
  { "slug": "catfancast", "enabled": false, "notes": "Prod; disable until live." }
]
```

**Wrapper behavior:**
- Per-site retry policy: 3 attempts total, waiting 60s after attempt 1 and
  300s after attempt 2.
- Per-attempt log: `logs/openclaw-YYYY-MM-DD-<slug>.log` (gitignored).
- On final failure of any site, writes `logs/last-run-failed.flag` with the
  failing site list + last 50 lines of the most recent failing log. On a
  fully successful run, removes the flag if it exists.
- Exit code = number of sites that ultimately failed (0 = all passed).

**Manual invocations:**

```powershell
# One-shot smoke: override the sites list, publish as drafts.
.\scripts\run-openclaw.ps1 -Sites localhost -Draft

# Run against every enabled site in scheduled-sites.json.
.\scripts\run-openclaw.ps1
```

**Register the Task Scheduler entry (once)** — run in an elevated PowerShell:

```powershell
$Action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument '-NoProfile -ExecutionPolicy Bypass -File "D:\Claude\Wordpress\scripts\run-openclaw.ps1"' `
    -WorkingDirectory 'D:\Claude\Wordpress'

# Task Scheduler triggers use the machine's local time. Adjust to hit
# 07:00 America/Denver if the laptop is on a different zone.
$Trigger = New-ScheduledTaskTrigger -Daily -At 07:00

$Settings = New-ScheduledTaskSettingsSet `
    -WakeToRun `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

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
    -Description 'Runs run-openclaw.ps1 daily; one article per enabled site.'
```

**Disable / re-enable:**

```powershell
Disable-ScheduledTask -TaskName 'Openclaw daily post'
Enable-ScheduledTask  -TaskName 'Openclaw daily post'
Unregister-ScheduledTask -TaskName 'Openclaw daily post' -Confirm:$false
```

**Check for silent failures** — the daily run does not push a notification;
inspect the flag file after suspected misses:

```powershell
Get-Content .\logs\last-run-failed.flag
```

## Smoke Test

This calls Claude with the recent-title avoidance list and prints the proposed
title/category, but does not publish anything to WordPress:

```powershell
python scripts/smoke-trends.py
```

## Instructions for the generator

Cross-site editable markdown files in `Instructions/` plus one per-site
persona file in `website_memory/` are loaded by `openclaw/generator.py` at
runtime and appended to the Claude system prompt. Edit any of them freely to
retune the agent; changes take effect on the next run with no code change.

- `website_memory/{hostname}.md` — what THIS site is, target audience, tone,
  what to write, what to avoid. One file per site; picked at runtime from
  the hostname of `WP_BASE_URL`. See `website_memory/README.md`.
- `Instructions/STYLE.md` — voice/tone and copy-level conventions. Cross-site.
- `Instructions/TOPIC.md` — topic-selection framework. Cross-site (currently
  cat-domain-specific).
- `Instructions/IMAGE_GENERATOR.md` — rules and formula the agent follows
  when writing the per-article `image_prompt`. Cross-site.

Hard structural rules (article length, evergreen requirement, HTML format,
linking policy, tool schema) stay in `generator.py` and are not overridable
from these files.

## Switching to the GPT-4o backend

The `gpt-4o` implementation is preserved as a commented block in
`openclaw/generator.py`. Uncomment it and set `OPENAI_API_KEY` in `.env` to
revert. See PLAN.md §4 for the swap history.
