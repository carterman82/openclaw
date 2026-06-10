# PLAN — WordPress Sandbox + Openclaw Agent

> Living reference for this project. Read this first at the start of a session.
> Last updated: 2026-06-09

## 1. About this project

A WordPress prototype article site with an **openclaw agent** — a GPT-4o-powered
script that writes and publishes a new article on demand. Phase 1 stands up
the site. Phase 2 builds the agent and triggers it from the command line.
Future phases automate the daily 7:00 publish and add analytics-driven
behavior.

Articles are **evergreen informational pieces of 700–1200 words**, one per day,
no featured images, no reader comments. Each article belongs to one of four
predefined categories.

**"Openclaw"** in this document = a Python script using the OpenAI SDK
(GPT-4o) plus the WordPress REST API. Rename if you have a different tool in
mind.

## 2. Stack & environment

- **Local dev (WordPress):** Docker (`docker-compose.yml` at the project root) — `wordpress:6.7-php8.3-apache` + `mariadb:11` + `wordpress:cli-php8.3` sidecar. Site at `http://localhost:8088`. *(Pivoted from Local by WP Engine on 2026-06-09 — see §4.)*
- **Host OS:** Windows 11
- **WordPress versions:** Accept Local's defaults (PHP / MySQL / Nginx)
- **Agent runtime:** Python 3.11+ (OpenAI SDK supports modern Python; pinning 3.11+ for type hints)
- **Agent → WP auth:** WordPress Application Passwords (built into WP 5.6+)
- **Secrets:** `.env` file at the project root, loaded with `python-dotenv`, never committed
- **Hosting target:** Not decided yet (local-only for now)
- **Version control:** Not initialized yet (recommended before Phase 2 begins)

## 3. Repository layout

This directory (`D:\Claude\Wordpress`) holds the **agent code, plans, and
notes** — not the WordPress install itself. WordPress lives where Local puts
it, expected to be:
`C:\Users\carte\Local Sites\openclaw-sandbox\app\public\`

Target layout once Phase 2 is underway:

```
D:\Claude\Wordpress\
├── PLAN.md                  # this file
├── CLAUDE.md                # session preamble for Claude Code
├── README.md                # optional, human-facing quickstart
├── .env                     # secrets (NOT committed)
├── .env.example             # template, committed
├── .gitignore
├── pyproject.toml           # or requirements.txt
└── openclaw/
    ├── __init__.py
    ├── main.py              # CLI entrypoint
    ├── generator.py         # GPT-4o article generation
    ├── publisher.py         # WordPress REST API client
    └── config.py            # env loading + defaults
```

## 4. Architecture decisions (running log)

Append decisions here as they're made. Format: `- YYYY-MM-DD: decision — why`

- 2026-06-09: Local by WP Engine for local dev — easiest WP setup on Windows
- 2026-06-09: Python for the agent — Anthropic SDK is first-class in Python and easy to schedule on Windows
- 2026-06-09: WordPress REST API + Application Passwords for posting — no plugin install needed, well-documented
- 2026-06-09: Manual CLI trigger for Phase 2, automation deferred to Phase 3 — keeps the first version simple to debug
- 2026-06-09: Content focus = evergreen informational articles — sandbox needs a focused-enough prompt to produce coherent output without dating itself
- 2026-06-09: Site title "Openclaw", slug `openclaw-sandbox`, tagline "A Claude-powered article experiment." — honest about what it is during the sandbox phase
- 2026-06-09: Timezone `America/Denver` — user's local; matters for the future 07:00 schedule
- 2026-06-09: Comments disabled site-wide — AI-authored site, no moderation overhead, no spam plugin needed
- 2026-06-09: No featured images in Phase 2 — keeps the agent simple; revisit later if visual polish matters
- 2026-06-09: Article length 700–1200 words — sweet spot for evergreen explainers; cost-efficient
- 2026-06-09: Four fixed categories (Science, History, How Things Work, Concepts) — prevents category sprawl; agent picks one per post from this closed list
- 2026-06-09: **Pivoted from Local by WP Engine to Docker** for the dev stack — Local install requires GUI clicks I can't drive, Docker was already installed and lets the assistant drive the full Phase 1 setup via wp-cli. Steps 1.1 and 1.2 in §6 still apply by intent; the mechanism is now `docker compose up -d` + `wp core install`. Live URL is `http://localhost:8088` (local-only, not internet-accessible).
- 2026-06-09: Added mu-plugin `wp-content/mu-plugins/allow-app-passwords-on-localhost.php` that forces `wp_is_application_passwords_available` to `true` — WP core gates Application Passwords behind `is_ssl()`, but we're on plain-HTTP `http://localhost:8088`. The mu-plugin lives inside the `wp_data` Docker volume; to recreate after a `docker compose down -v`, re-run the file write. Safe in this dev setup because the port is bound to loopback only.
- 2026-06-09: Used a `+alias` (`clayton.bolz+openclaw@gmail.com`) for the `openclaw-agent` user's email — keeps the agent identifiable in any future mail (notifications, password resets) without provisioning a second inbox.
- 2026-06-09: **Switched the agent's LLM provider from Anthropic Claude (`claude-opus-4-7`) to OpenAI `gpt-4o`** — user preference; OpenAI API key supplied separately. The earlier "Python for the agent — Anthropic SDK is first-class…" entry above is historical context, not current state.
- 2026-06-09: Will use **OpenAI Structured Outputs** (`response_format` with a `json_schema`) for the generator's reply — enforces the four-category enum and the `title` / `body_html` / `tags` shape at the API boundary, so Python only needs to `json.loads()` the response.

## 5. Roadmap

- **Phase 1 — Website (this plan, §6)**: Local WP install running, comments disabled, categories created, dedicated agent user with REST API access.
- **Phase 2 — Openclaw agent, manual (this plan, §7)**: `python -m openclaw post` writes and publishes an article.
- **Phase 3 — Automation (future)**: Windows Task Scheduler runs the command daily at 07:00 America/Denver. Add retry/error notifications.
- **Phase 4 — Analytics-aware agent (future)**: Agent reads post analytics (specifics TBD — likely WP stats, Google Analytics, or Jetpack) and adjusts topics/style.

---

## 6. Phase 1 — Build the website

Each step lists **what "done" looks like** and a **verification checklist**.
Check items off as you go. Do steps in order.

> **Status (2026-06-09):** Phase 1 **complete**. All 1.1 – 1.11 verified. Site
> live at `http://localhost:8088`. Admin + agent credentials + Application
> Password recorded in `CREDENTIALS.local.txt` (uncommitted). Ready for Phase 2.

### Step 1.1 — Install Local by WP Engine

**Done looks like:** Local is installed and launches without errors. The
dashboard shows zero sites (or your existing ones).

**Verification:**
- [ ] Installer downloaded from https://localwp.com
- [ ] Installer ran to completion with no errors
- [ ] Local launches from the Start menu
- [ ] Dashboard ("Local Sites" sidebar) is visible
- [ ] "+" (Create new site) button is clickable
- [ ] Local's version number is visible in `Help → About` (record it in §4 if you care about pinning)

### Step 1.2 — Create the WordPress site

**Done looks like:** A new site named **`openclaw-sandbox`** appears in
Local's sidebar. Clicking "WP Admin" opens `wp-admin` in the browser at
`http://openclaw-sandbox.local/wp-admin/` and you can log in.

**Verification:**
- [ ] New site created with exact name `openclaw-sandbox` (lowercase, hyphenated — this becomes the URL)
- [ ] "Preferred" environment chosen (Local's default is fine)
- [ ] WordPress admin username and password saved somewhere outside the repo (e.g., your password manager)
- [ ] Local shows the site's URL as `http://openclaw-sandbox.local`
- [ ] The URL loads the default WP front page in a browser
- [ ] `wp-admin` login works
- [ ] Local's "Site folder" link opens the install (path expected to be `C:\Users\carte\Local Sites\openclaw-sandbox\app\public\` — confirm and update §3 if different)

### Step 1.3 — Configure site identity and timezone

**Done looks like:** `Settings → General` shows the real title, tagline, and
**timezone set to America/Denver** (critical for the future 07:00 schedule).

**Verification:**
- [ ] Site Title is exactly: **Openclaw**
- [ ] Tagline is exactly: **A Claude-powered article experiment.**
- [ ] Timezone in `Settings → General` is set to **America/Denver** (Mountain Time), not UTC
- [ ] Date format and time format set to something readable
- [ ] Week starts on the day you prefer (defaults to Monday — fine)
- [ ] Settings saved (page reload still shows your values)
- [ ] Front page header now reflects the new title

### Step 1.4 — Configure permalinks

**Done looks like:** `Settings → Permalinks` is set to **Post name**. A test
URL looks like `/sample-post/`, not `/?p=123`.

**Verification:**
- [ ] `Settings → Permalinks` opened
- [ ] "Post name" option selected
- [ ] Settings saved
- [ ] Visiting an existing post URL in a browser shows the post (no 404)
- [ ] The URL in the address bar uses the slug, not `?p=`

### Step 1.5 — Choose and activate a theme

**Done looks like:** Any default block theme is active. The front page lists
recent posts cleanly. Theme is intentionally a soft choice — pick the newest
default that ships with the WP version Local installed (Twenty Twenty-Five or
similar) and move on.

**Verification:**
- [ ] Theme activated in `Appearance → Themes` (any block theme that ships with WP)
- [ ] Front page renders without PHP warnings
- [ ] The default sample post is visible on the front page
- [ ] Single-post view (click into the post) renders correctly
- [ ] Mobile view (browser dev tools, narrow width) looks acceptable
- [ ] No console errors on the front page (F12 → Console)

### Step 1.6 — Disable comments site-wide

**Done looks like:** New posts default to comments-off, and any existing
sample posts have their comments closed. No reader can leave a comment
anywhere on the site.

**Verification:**
- [ ] `Settings → Discussion` opened
- [ ] "Allow people to submit comments on new posts" — **unchecked**
- [ ] "Allow link notifications from other blogs (pingbacks and trackbacks) on new posts" — **unchecked** (optional but cleaner)
- [ ] Settings saved
- [ ] `Posts → All Posts → select all → Bulk actions → Edit → Comments: Do not allow` applied to any existing posts
- [ ] Open a published post on the front-end in a browser — no comment form visible at the bottom
- [ ] Open `wp-admin → Comments` — page exists but is empty / no incoming pipeline

### Step 1.7 — Create the four categories

**Done looks like:** Exactly four categories exist in `Posts → Categories`:
**Science**, **History**, **How Things Work**, **Concepts**. No others (you
can delete the default "Uncategorized" or leave it unused — the agent will
never select it).

**Verification:**
- [ ] `Posts → Categories` opened
- [ ] Category "Science" created (slug auto-generates as `science`)
- [ ] Category "History" created (slug `history`)
- [ ] Category "How Things Work" created (slug `how-things-work`)
- [ ] Category "Concepts" created (slug `concepts`)
- [ ] All four appear in the categories list
- [ ] On `Posts → Add New`, all four are visible in the Categories panel of the editor
- [ ] (Optional) "Uncategorized" is either deleted or renamed — note that WP requires *some* default category, so if you can't delete it, change the default in `Settings → Writing → Default Post Category` to one of the four

### Step 1.8 — Publish a manual test article

**Done looks like:** A post you wrote by hand appears on the front page and
at its own URL, assigned to **exactly one** of the four real categories. This
proves the publishing pipeline works before the agent gets involved.

**Verification:**
- [ ] New post created in `Posts → Add New` with title "Manual test post"
- [ ] Body has at least a paragraph of content (anything)
- [ ] Exactly **one** category assigned, chosen from Science / History / How Things Work / Concepts
- [ ] At least one tag assigned (any string)
- [ ] Post status set to "Published"
- [ ] Front page shows the post
- [ ] Direct URL (`/manual-test-post/`) loads the post
- [ ] Post appears in `Posts → All Posts` with "Published" status and the correct category column
- [ ] Front-end post page does NOT show a comment form (confirms step 1.6 took effect)

### Step 1.9 — Create the `openclaw-agent` WordPress user

**Done looks like:** A dedicated WP user account exists for the agent, with
the **Author** role (can write/publish own posts, cannot administer the site).

**Verification:**
- [x] User created via wp-cli (`wp user create`) — equivalent to `Users → Add New`; username `openclaw-agent`, ID 2
- [x] Email is a real address you control — `clayton.bolz+openclaw@gmail.com` (+alias)
- [x] Role set to **Author** — confirmed via `wp user list-caps`
- [x] A strong password generated and saved in `CREDENTIALS.local.txt`
- [x] User appears in `wp user list` (the wp-cli equivalent of `Users → All Users`)
- [x] Login as `openclaw-agent` confirmed: `POST /wp-login.php` returns 302 → `/wp-admin/` with a valid `wordpress_logged_in` cookie
- [x] N/A in CLI flow — no admin browser session to log back into

### Step 1.10 — Generate an Application Password for the agent

**Done looks like:** A 24-character application password for `openclaw-agent`
is generated, copied **once**, and stored somewhere safe (it goes into `.env`
during Phase 2 step 2.3 — for now keep it in your password manager).

**Verification:**
- [x] N/A in CLI flow — `wp user application-password create` is the wp-cli equivalent
- [x] N/A in CLI flow
- [x] New password created with name `openclaw-cli` (`wp user application-password create openclaw-agent openclaw-cli --porcelain`)
- [x] 24-char password captured immediately from `--porcelain` stdout
- [x] Password saved in `CREDENTIALS.local.txt` under "Agent Application Password"
- [x] App password listed in `wp user application-password list openclaw-agent` (uuid + name + created timestamp)

### Step 1.11 — Verify the REST API end-to-end with curl

**Done looks like:** From a terminal, you can both **list** posts (public)
and **create** a draft post (authenticated as the agent) using only the
Application Password. No code yet — just curl.

**Verification:** (host is now `http://localhost:8088` after the Docker pivot)
- [x] `curl http://localhost:8088/wp-json/wp/v2/posts` returned 200 + JSON array containing the manual test post (id 6)
- [x] `curl http://localhost:8088/wp-json/wp/v2/categories` returned the four categories with IDs: **Science=2, History=3, How Things Work=4, Concepts=5** (plus Uncategorized=1, unused)
- [x] Authenticated `curl -u openclaw-agent:Ri8pzd5mswcrPJmu4bmOvoQg -X POST /wp/v2/posts ... categories:[2]` returned **HTTP 201** with new post id=7, status=draft
- [x] Draft visible in `wp post list --post_status=draft` (wp-cli equivalent of the admin Drafts view): ID 7, "API test", post_author=2, draft
- [x] Draft's author was id=2 (`openclaw-agent`)
- [x] Cleanup: `DELETE /wp/v2/posts/7?force=true` (authenticated) returned 200 `{"deleted":true,...}`
- [x] *Unauthenticated* POST returned **401** `rest_cannot_create` — auth is enforced

**Phase-1 caveat captured during 1.11:** WP core requires HTTPS for Application Passwords. On plain-HTTP localhost we installed `wp-content/mu-plugins/allow-app-passwords-on-localhost.php` (one-liner: `add_filter('wp_is_application_passwords_available', '__return_true');`). Without it every authenticated REST call 401s. Logged in §4.

**Phase 1 exit criteria:** All 1.1–1.11 checks pass. Site runs, admin works,
the four categories exist, comments are off, and the agent user can post via
the REST API. Now you're ready to write code.

---

## 7. Phase 2 — Build the openclaw agent (manual command)

Goal: `python -m openclaw post` generates one evergreen 700–1200 word article
with Claude, assigns it to one of the four predefined categories, and
publishes it to the WordPress site as a published post (not a draft).

### Step 2.1 — Initialize the project structure

**Done looks like:** Directories and empty/stub files exist matching the
layout in §3. You can `cd D:\Claude\Wordpress` and see the tree.

**Verification:**
- [ ] `openclaw/` directory created
- [ ] `openclaw/__init__.py` exists (can be empty)
- [ ] `openclaw/main.py`, `generator.py`, `publisher.py`, `config.py` created (stub OK)
- [ ] `.env.example` created with placeholder keys (see step 2.3)
- [ ] `.gitignore` created including `.env`, `__pycache__/`, `.venv/`, `*.pyc`
- [ ] `git init` run if you want version control (recommended)
- [ ] Initial commit made with just the scaffolding (no secrets)

### Step 2.2 — Set up Python environment and dependencies

**Done looks like:** A virtual environment exists in the project, activated
in your shell, with `openai`, `requests`, and `python-dotenv` installed.

**Verification:**
- [ ] `python --version` reports 3.11 or newer
- [ ] `python -m venv .venv` succeeded
- [ ] `.venv\Scripts\Activate.ps1` activates the venv (prompt shows `(.venv)`)
- [ ] `pip install openai requests python-dotenv` succeeds
- [ ] `pip freeze > requirements.txt` produces a file with all three packages pinned
- [ ] `python -c "import openai, requests, dotenv; print('ok')"` prints `ok`
- [ ] `.venv/` is in `.gitignore` (git status doesn't list it)

### Step 2.3 — Configure secrets (`.env` and `.env.example`)

**Done looks like:** A real `.env` (not committed) holds the live credentials,
and a committed `.env.example` documents the required keys.

**Verification:**
- [ ] `.env.example` contains keys (with dummy values): `OPENAI_API_KEY`, `WP_BASE_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`
- [ ] `.env` contains the same keys with real values
- [ ] `OPENAI_API_KEY` starts with `sk-` (or `sk-proj-`)
- [ ] `WP_BASE_URL` is `http://openclaw-sandbox.local` (no trailing slash)
- [ ] `WP_USERNAME` is `openclaw-agent`
- [ ] `WP_APP_PASSWORD` is the 24-char password from step 1.10 (spaces stripped or preserved — WP accepts both)
- [ ] `.env` is in `.gitignore` and `git status` does NOT show it
- [ ] `python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(bool(os.getenv('OPENAI_API_KEY')))"` prints `True`

### Step 2.4 — Build the article generator (`generator.py`)

**Done looks like:** A function `generate_article(topic: str | None = None,
category: str | None = None) -> dict` returns `{"title": str, "body_html":
str, "category": str, "tags": list[str]}` by calling GPT-4o. Both `topic`
and `category` are optional; if omitted the agent picks. The returned
`category` is always one of the four allowed values.

**Verification:**
- [ ] `generator.py` defines `generate_article` with the signature above
- [ ] Uses `gpt-4o` via the `openai` SDK (`OpenAI().chat.completions.create(...)`)
- [ ] Prompt instructs the model to: (a) write **evergreen** content (no "this week", "yesterday", "currently", "recently" — content must read well a year from now); (b) pick one category from the closed list {Science, History, How Things Work, Concepts}; (c) target 700–1200 words; (d) return strict JSON with all four fields
- [ ] Uses **OpenAI Structured Outputs** (`response_format={"type":"json_schema", "json_schema": {...}}`) — schema requires `title:str`, `body_html:str`, `category:enum[Science,History,How Things Work,Concepts]`, `tags:list[str]` — so manual schema validation is unnecessary; just `json.loads(response.choices[0].message.content)`
- [ ] Defensive check is still cheap: assert returned `category` is in the allowed list before publishing, in case Structured Outputs ever drifts
- [ ] `python -c "from openclaw.generator import generate_article; import json; r = generate_article('the giant panda thumb'); print(r['title'], r['category'], len(r['body_html']))"` prints a title, a valid category, and a non-trivial HTML length
- [ ] Word count of `body_html` (stripping tags) falls in 700–1200 for at least 3 out of 3 sample runs
- [ ] Output `body_html` contains actual HTML tags (`<p>`, `<h2>`, etc.), not markdown
- [ ] Function works with both args omitted (GPT-4o picks topic AND category)
- [ ] No `OPENAI_API_KEY` is hardcoded — it's read via `config.py` or env

### Step 2.5 — Build the WordPress publisher (`publisher.py`)

**Done looks like:** A function `publish_post(title: str, body_html: str,
category: str, tags: list[str], status: str = "publish") -> dict` POSTs to
`/wp-json/wp/v2/posts` and returns the created post's JSON (including the
post URL). `category` must be one of the four allowed names; the function
looks up its WP ID and never creates new categories.

**Verification:**
- [ ] `publisher.py` defines `publish_post` with the signature above
- [ ] Module loads the four category name→ID mappings on first call (single GET to `/wp-json/wp/v2/categories`) and caches them
- [ ] Passing a `category` not in {Science, History, How Things Work, Concepts} raises a clear `ValueError` BEFORE making any HTTP request
- [ ] Uses `requests` with HTTP Basic Auth `(WP_USERNAME, WP_APP_PASSWORD)`
- [ ] Tags handled correctly: looks up or creates each tag, passes tag IDs to the post body (WP API requires IDs, not names)
- [ ] Raises a clear exception on non-2xx responses (include status code + response body in the message)
- [ ] Calling `publish_post("Manual unit test", "<p>hi</p>", "Concepts", ["test"], status="draft")` from a Python REPL returns a dict with a `link` field
- [ ] That draft appears in `wp-admin` under the `openclaw-agent` author, in the Concepts category
- [ ] The draft has the `test` tag assigned
- [ ] Cleanup: delete the draft via UI or a one-liner

### Step 2.6 — Build the CLI entrypoint (`main.py`)

**Done looks like:** `python -m openclaw post` runs the full pipeline:
generate → publish → print the new post URL. Optional flags to override
topic, category, and draft-vs-publish.

**Verification:**
- [ ] `main.py` parses args with `argparse` (subcommand `post`, optional `--topic`, optional `--category` constrained to the four allowed values, optional `--draft` flag for safe testing)
- [ ] `python -m openclaw post --topic "the history of the paperclip" --category History --draft` succeeds
- [ ] Invalid `--category Foo` exits with a clear error (argparse `choices=`)
- [ ] Final printed line is the new post's URL
- [ ] Exit code is 0 on success
- [ ] Exit code is non-zero on any failure (caught and reported with a clear message)
- [ ] `python -m openclaw post --help` shows usage including the allowed category list
- [ ] Running with an obviously bad API key fails fast with a clear error (not a stack trace dump)

### Step 2.7 — Add structured logging

**Done looks like:** Each run writes a timestamped log line per major step
(loaded config, called Claude, posted to WP, success/failure). Errors include
the full exception.

**Verification:**
- [ ] Python `logging` module configured (not bare `print`)
- [ ] Log level controllable via env var or `--verbose` flag
- [ ] One log line for: "config loaded", "calling Claude (topic=…, category=…)", "Claude returned (title=…, category=…, words=…)", "POST to WP", "published (url=…)"
- [ ] Errors logged with `logger.exception(...)` so the traceback is captured
- [ ] Default log format includes timestamp and level
- [ ] No secrets (API key, app password) ever appear in the logs — grep the output to confirm

### Step 2.8 — End-to-end real run

**Done looks like:** `python -m openclaw post` (no flags) produces a real
published article on the site, viewable in a browser at its permalink, with
a Claude-written title and body, assigned to one of the four categories,
within the word count range.

**Verification:**
- [ ] Run completed in under 60 seconds
- [ ] New post visible on the site's front page
- [ ] Post URL loads cleanly (no broken HTML, no `&lt;p&gt;` escape issues)
- [ ] Author is `openclaw-agent`
- [ ] Post is assigned to **exactly one** category, and it's one of Science / History / How Things Work / Concepts
- [ ] Word count of the published body is between 700 and 1200
- [ ] Title is coherent and not "Untitled" or a JSON fragment
- [ ] Body has paragraphs / headings — not one wall of text
- [ ] Body contains no time-anchored phrases ("this week", "yesterday", "currently", "recently") — confirms the evergreen instruction took
- [ ] No secrets in the terminal output
- [ ] Run it twice; two distinct posts appear (no caching collisions)

### Step 2.9 — Document the command

**Done looks like:** A short `README.md` (or an updated section in this file)
gives someone enough to run the agent on a fresh checkout.

**Verification:**
- [ ] `README.md` exists at the project root
- [ ] Documents: prerequisites (Python, Local), setup (venv, install, `.env`), and the command (`python -m openclaw post`)
- [ ] Documents the optional `--topic`, `--category`, `--draft`, and `--verbose` flags
- [ ] Lists the four allowed category values
- [ ] Links to PLAN.md for the bigger picture
- [ ] Says explicitly: never commit `.env`
- [ ] Following the README from scratch on a fresh machine would produce a working agent (mental walkthrough is enough; don't actually wipe your machine)

**Phase 2 exit criteria:** All 2.1–2.9 checks pass. Running
`python -m openclaw post` from the project root publishes a fresh evergreen
article in one of the four categories. Now you're ready to schedule it
(Phase 3) and eventually feed analytics back in (Phase 4).

---

## 8. Open questions

- Theme — defaulting to whatever block theme ships with WP for now; revisit if visual polish becomes a priority.
- Hosting target — still TBD; pick before Phase 3 if you want the scheduler running somewhere reliable (cloud VM beats your laptop).
- Version control remote — local-only or GitHub? Required answer before pushing any commits.
- Analytics source for Phase 4 — Jetpack Stats? Google Analytics? Plausible? Native WP doesn't track views.
