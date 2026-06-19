# PLAN — WordPress Sandbox + Openclaw Agent

> Living reference for this project. Read this first at the start of a session.
> Last updated: 2026-06-19

## 1. About this project

A WordPress prototype article site with an **openclaw agent** — a Claude-powered
script that writes and publishes a new article on demand. Phase 1 stands up
the site. Phase 2 builds the agent and triggers it from the command line.
Future phases automate the daily 7:00 publish and add analytics-driven
behavior.

Articles are **evergreen informational pieces of 700–1200 words**, one per day,
no featured images, no reader comments. Each article belongs to one of four
predefined categories.

**"Openclaw"** in this document = a Python script using the Anthropic SDK
(`claude-sonnet-4-6`) plus the WordPress REST API. Rename if you have a
different tool in mind.

## 2. Stack & environment

- **Local dev (WordPress):** Docker (`docker-compose.yml` at the project root) — `wordpress:6.7-php8.3-apache` + `mariadb:11` + `wordpress:cli-php8.3` sidecar. Site at `http://localhost:8088`, bound to `127.0.0.1` only. *(Pivoted from Local by WP Engine on 2026-06-09 — see §4.)*
- **Host OS:** Windows 11
- **WordPress versions:** Pinned by Docker images: WordPress 6.7 on PHP 8.3 Apache, MariaDB 11, and `wordpress:cli-php8.3`.
- **Agent runtime:** Python 3.11+ (Anthropic SDK supports modern Python; pinning 3.11+ for type hints)
- **Agent → WP auth:** WordPress Application Passwords (built into WP 5.6+)
- **Secrets:** `.env` file at the project root, loaded with `python-dotenv`, never committed
- **Hosting target:** Not decided yet (local-only for now)
- **Version control:** Local `.git` exists, but no remote has been chosen yet.

## 3. Repository layout

This directory (`D:\Claude\Wordpress`) holds the **agent code, plans, Docker
configuration, and notes**. WordPress core files and the database live in Docker
named volumes (`openclaw_wp_data`, `openclaw_db_data`), except for the tracked
local mu-plugin under `wp-content/mu-plugins/`.

Current layout:

```
D:\Claude\Wordpress\
├── PLAN.md                  # this file
├── CLAUDE.md                # session preamble for Claude Code
├── README.md                # human-facing quickstart
├── .env                     # secrets (NOT committed)
├── .env.example             # template, committed
├── .gitignore
├── docker-compose.yml
├── requirements.txt
├── wp-content/
│   └── mu-plugins/
│       └── allow-app-passwords-on-localhost.php
└── openclaw/
    ├── __init__.py
    ├── __main__.py          # enables python -m openclaw
    ├── constants.py         # shared allowed category list
    ├── main.py              # CLI entrypoint
    ├── generator.py         # Claude article generation
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
- 2026-06-09: Added mu-plugin `wp-content/mu-plugins/allow-app-passwords-on-localhost.php` that forces `wp_is_application_passwords_available` to `true` — WP core gates Application Passwords behind `is_ssl()`, but we're on plain-HTTP `http://localhost:8088`.
- 2026-06-09: Used a `+alias` (`clayton.bolz+openclaw@gmail.com`) for the `openclaw-agent` user's email — keeps the agent identifiable in any future mail (notifications, password resets) without provisioning a second inbox.
- 2026-06-09: **Switched the agent's LLM provider from Anthropic Claude (`claude-opus-4-7`) to OpenAI `gpt-4o`** — user preference; OpenAI API key supplied separately. The earlier "Python for the agent — Anthropic SDK is first-class…" entry above is historical context, not current state.
- 2026-06-09: Will use **OpenAI Structured Outputs** (`response_format` with a `json_schema`) for the generator's reply — enforces the four-category enum and the `title` / `body_html` / `tags` shape at the API boundary, so Python only needs to `json.loads()` the response.
- 2026-06-09: **Reverted the agent's LLM provider from OpenAI `gpt-4o` back to Anthropic `claude-sonnet-4-6`** — the OpenAI project hit `insufficient_quota` (429) and the user opted to switch back rather than top up. Picked Sonnet over Opus on cost grounds (~$0.02/article vs ~$0.10) with near-Opus quality for explainer text. The GPT-4o implementation in `openclaw/generator.py` is preserved as a commented block so flipping back is a re-uncomment.
- 2026-06-09: For Claude, structured output is implemented via **tool use** (`tools=[{...}], tool_choice={"type":"tool", "name":"submit_article"}`) — the tool's `input_schema` enforces the four-category enum and required fields, equivalent to OpenAI's Structured Outputs but using Anthropic's native idiom.
- 2026-06-18: Phase 2 complete. `publisher.py` caches the category name→ID map from a single GET on first call; tags are looked up by exact-name search and created on miss. `main.py` uses `argparse` with a `post` subcommand; `__main__.py` enables `python -m openclaw`. Logging via Python `logging` at INFO by default, DEBUG via `--verbose` or `LOG_LEVEL` env var. Typical end-to-end runtime is ~60–70 s, dominated by external API/network latency.
- 2026-06-19: Bound WordPress to `127.0.0.1:8088` and made the Application Password mu-plugin repo-owned via a Docker bind mount — keeps the plain-HTTP app-password workaround local-only and reproducible after `docker compose down -v`.
- 2026-06-19: Moved the allowed category tuple into `openclaw/constants.py` — keeps generator, publisher, and CLI category validation on the same source of truth.
- 2026-06-19: Added recent-title de-duplication before generation — Anthropic Messages calls are already stateless, but the model was converging on honey when asked to pick its own topic. `main.py` now fetches recent WP post titles and passes them to `generate_article()` as an explicit "avoid these subjects" list when `--topic` is omitted.
- 2026-06-18: Made categories dynamic — `main.py` calls `publisher.get_category_names()` at startup to fetch the live WP category list; that list is passed into `generate_article()` so the Claude tool schema and system prompt reflect whatever categories actually exist on the configured site. `constants.py` is kept as an offline fallback. Enables pointing the agent at any WP site without code changes — only `.env` needs updating.
- 2026-06-18: Site-aware topic selection — `publisher.get_site_name()` fetches the WP site name from `/wp-json/` (public, no auth). When `--topic` is omitted, the user message now reads "Write one evergreen article suited to the audience of '{site_name}'" so Claude steers topics toward the site's theme automatically.

## 5. Roadmap

- **Phase 1 — Website (this plan, §6)**: Docker WordPress site running, comments disabled, categories created, dedicated agent user with REST API access.
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

### Step 1.1 — Prepare Docker WordPress stack

**Done looks like:** Docker is installed and can run the `wordpress`, `mariadb`,
and `wpcli` services from `docker-compose.yml`.

**Verification:**
- [x] Docker is installed and available from PowerShell
- [x] `docker-compose.yml` exists at the project root
- [x] Compose project includes `wordpress`, `db`, and `wpcli` services
- [x] WordPress port is bound to `127.0.0.1:8088`
- [x] `wp-content/mu-plugins/allow-app-passwords-on-localhost.php` is tracked in this repo and mounted into the WordPress container

### Step 1.2 — Create the WordPress site with wp-cli

**Done looks like:** The Docker stack is running, WordPress is installed, and
`http://localhost:8088/wp-admin/` accepts the local admin credentials.

**Verification:**
- [x] Stack started with `docker compose up -d`
- [x] WordPress core installed via `docker compose run --rm wpcli core install ...`
- [x] WordPress admin username and password saved in `CREDENTIALS.local.txt`
- [x] Site URL is `http://localhost:8088`
- [x] The URL loads the default WP front page in a browser
- [x] `wp-admin` login works
- [x] WordPress files and DB persist in Docker named volumes

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
default that ships with the Docker WordPress image (Twenty Twenty-Five or
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
- [x] Authenticated `curl -u openclaw-agent:<app-password> -X POST /wp/v2/posts ... categories:[2]` returned **HTTP 201** with new post id=7, status=draft
- [x] Draft visible in `wp post list --post_status=draft` (wp-cli equivalent of the admin Drafts view): ID 7, "API test", post_author=2, draft
- [x] Draft's author was id=2 (`openclaw-agent`)
- [x] Cleanup: `DELETE /wp/v2/posts/7?force=true` (authenticated) returned 200 `{"deleted":true,...}`
- [x] *Unauthenticated* POST returned **401** `rest_cannot_create` — auth is enforced

**Phase-1 caveat captured during 1.11:** WP core requires HTTPS for Application Passwords. On plain-HTTP localhost we mount the tracked mu-plugin `wp-content/mu-plugins/allow-app-passwords-on-localhost.php`, which enables Application Passwords for this loopback-only dev site. Without it every authenticated REST call 401s. Logged in §4.

**Phase 1 exit criteria:** All 1.1–1.11 checks pass. Site runs, admin works,
the four categories exist, comments are off, and the agent user can post via
the REST API. Now you're ready to write code.

---

## 7. Phase 2 — Build the openclaw agent (manual command)

> **Status (2026-06-18):** Phase 2 **complete**. All 2.1–2.9 verified.
> `python -m openclaw post` generates and publishes a real article end-to-end.
> Ready for Phase 3 (scheduling).

Goal: `python -m openclaw post` generates one evergreen 700–1200 word article
with Claude, assigns it to one of the four predefined categories, and
publishes it to the WordPress site as a published post (not a draft).

### Step 2.1 — Initialize the project structure

**Done looks like:** Directories and implementation files exist matching the
layout in §3. You can `cd D:\Claude\Wordpress` and see the tree.

**Verification:**
- [x] `openclaw/` directory created
- [x] `openclaw/__init__.py` exists (empty)
- [x] `openclaw/main.py`, `generator.py`, `publisher.py`, `config.py`, `constants.py`, and `__main__.py` created
- [x] `.env.example` created with placeholder keys (see step 2.3)
- [x] `.gitignore` created including `.env`, `__pycache__/`, `.venv/`, `*.pyc`, `CREDENTIALS.local.txt`
- [x] `git init` run (commit 3fbd83d as the initial commit)
- [x] Initial commit made with just the scaffolding (no secrets — verified via `git ls-files`)

### Step 2.2 — Set up Python environment and dependencies

**Done looks like:** A virtual environment exists in the project, activated
in your shell, with `anthropic`, `requests`, and `python-dotenv` installed.
(`openai` is also installed because the GPT-4o code path in `generator.py`
is preserved as a commented block — see §4 swap history.)

**Verification:**
- [x] `python --version` reports 3.11 or newer — actually 3.13.0
- [x] `python -m venv .venv` succeeded
- [x] `.venv\Scripts\Activate.ps1` activates the venv (`$env:VIRTUAL_ENV` set)
- [x] `pip install anthropic requests python-dotenv` succeeds
- [x] `pip freeze > requirements.txt` produces a file with all packages pinned
- [x] `python -c "import anthropic, requests, dotenv; print('ok')"` prints `ok`
- [x] `.venv/` is in `.gitignore` (git status doesn't list it)

### Step 2.3 — Configure secrets (`.env` and `.env.example`)

**Done looks like:** A real `.env` (not committed) holds the live credentials,
and a committed `.env.example` documents the required keys.

**Verification:**
- [x] `.env.example` contains keys (with dummy values): `ANTHROPIC_API_KEY`, `WP_BASE_URL`, `WP_USERNAME`, `WP_APP_PASSWORD` (plus optional commented-out `OPENAI_API_KEY` for the GPT-4o fallback)
- [x] `.env` contains the same keys with real values
- [x] `ANTHROPIC_API_KEY` starts with `sk-ant-`
- [x] `WP_BASE_URL` is `http://localhost:8088` (no trailing slash) — Docker stack URL per the §4 pivot
- [x] `WP_USERNAME` is `openclaw-agent`
- [x] `WP_APP_PASSWORD` is the 24-char password from step 1.10
- [x] `.env` is in `.gitignore` and `git status` does NOT show it (verified via `git check-ignore .env` → matches `.gitignore:2`)
- [x] `python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(bool(os.getenv('ANTHROPIC_API_KEY')))"` prints `True`

### Step 2.4 — Build the article generator (`generator.py`)

**Done looks like:** A function `generate_article(topic: str | None = None,
category: str | None = None) -> dict` returns `{"title": str, "body_html":
str, "category": str, "tags": list[str]}` by calling Claude. Both `topic`
and `category` are optional; if omitted the agent picks. The returned
`category` is always one of the four allowed values.

**Verification:**
- [x] `generator.py` defines `generate_article` with the signature above
- [x] Uses `claude-sonnet-4-6` via the `anthropic` SDK (`Anthropic().messages.create(...)`)
- [x] Prompt instructs the model to: (a) write **evergreen** content (no "this week", "yesterday", "currently", "recently" — content must read well a year from now); (b) pick one category from the closed list {Science, History, How Things Work, Concepts}; (c) target 700–1200 words; (d) return strict JSON with all four fields
- [x] Uses **Claude tool-use** with a single tool `submit_article` and `tool_choice={"type":"tool","name":"submit_article"}` — the tool's `input_schema` enforces `title:str`, `body_html:str`, `category:enum[Science,History,How Things Work,Concepts]`, `tags:list[str]`. (Anthropic's equivalent of OpenAI Structured Outputs.)
- [x] Defensive check: assert returned `category` is in the allowed list before publishing, in case tool-use ever drifts
- [x] REPL probe: `generate_article('the giant panda thumb')` → title `"The Giant Panda's \"Thumb\"..."`, category `Science`, 899 words HTML (verified)
- [x] Word count of `body_html` (stripping tags) in 700–1200 for **3/3 sample runs** (899, 857, 892)
- [x] Output `body_html` contains real HTML tags (`<p>`, `<h2>`, `<ul>`, etc.), not markdown
- [x] Function works with both args omitted (Claude picks topic AND category — verified run 3 chose "Why Honey Never Spoils" / Science)
- [x] No `ANTHROPIC_API_KEY` is hardcoded — read via `config.py` (`Config.load()`)

### Step 2.5 — Build the WordPress publisher (`publisher.py`)

**Done looks like:** A function `publish_post(title: str, body_html: str,
category: str, tags: list[str], status: str = "publish") -> dict` POSTs to
`/wp-json/wp/v2/posts` and returns the created post's JSON (including the
post URL). `category` must be one of the four allowed names; the function
looks up its WP ID and never creates new categories.

**Verification:**
- [x] `publisher.py` defines `publish_post` with the signature above
- [x] Module loads the four category name→ID mappings on first call (single GET to `/wp-json/wp/v2/categories`) and caches them
- [x] Passing a `category` not in {Science, History, How Things Work, Concepts} raises a clear `ValueError` BEFORE making any HTTP request
- [x] Uses `requests` with HTTP Basic Auth `(WP_USERNAME, WP_APP_PASSWORD)`
- [x] Tags handled correctly: looks up or creates each tag, passes tag IDs to the post body (WP API requires IDs, not names)
- [x] Raises a clear exception on non-2xx responses (include status code + response body in the message)
- [x] Calling `publish_post("Manual unit test", "<p>hi</p>", "Concepts", ["test"], status="draft")` from a Python REPL returns a dict with a `link` field
- [x] That draft appears in `wp-admin` under the `openclaw-agent` author, in the Concepts category
- [x] The draft has the `test` tag assigned
- [x] Cleanup: delete the draft via UI or a one-liner

### Step 2.6 — Build the CLI entrypoint (`main.py`)

**Done looks like:** `python -m openclaw post` runs the full pipeline:
generate → publish → print the new post URL. Optional flags to override
topic, category, and draft-vs-publish.

**Verification:**
- [x] `main.py` parses args with `argparse` (subcommand `post`, optional `--topic`, optional `--category` constrained to the four allowed values, optional `--draft` flag for safe testing)
- [x] `python -m openclaw post --topic "the history of the paperclip" --category History --draft` succeeds
- [x] Invalid `--category Foo` exits with a clear error (argparse `choices=`)
- [x] Final printed line is the new post's URL
- [x] Exit code is 0 on success
- [x] Exit code is non-zero on any failure (caught and reported with a clear message)
- [x] `python -m openclaw post --help` shows usage including the allowed category list
- [x] Running with an obviously bad API key fails fast with a clear error (not a stack trace dump)

### Step 2.7 — Add structured logging

**Done looks like:** Each run writes a timestamped log line per major step
(loaded config, called Claude, posted to WP, success/failure). Errors include
the full exception.

**Verification:**
- [x] Python `logging` module configured (not bare `print`)
- [x] Log level controllable via env var (`LOG_LEVEL`) or `--verbose` flag
- [x] One log line for: "config loaded", "calling Claude (topic=…, category=…)", "Claude returned (title=…, category=…, words=…)", "POST to WP", "published (url=…)"
- [x] Errors logged with `logger.exception(...)` so the traceback is captured
- [x] Default log format includes timestamp and level
- [x] No secrets (API key, app password) ever appear in the logs — grep the output to confirm

### Step 2.8 — End-to-end real run

**Done looks like:** `python -m openclaw post` (no flags) produces a real
published article on the site, viewable in a browser at its permalink, with
a Claude-written title and body, assigned to one of the four categories,
within the word count range.

**Verification:**
- [x] Run completed successfully (actual observed runs around 60–70s, dominated by external API/network latency)
- [x] New post visible on the site's front page
- [x] Post URL loads cleanly (no broken HTML, no `&lt;p&gt;` escape issues)
- [x] Author is `openclaw-agent`
- [x] Post is assigned to **exactly one** category, and it's one of Science / History / How Things Work / Concepts
- [x] Word count of the published body is between 700 and 1200 (935 and 1033 words verified)
- [x] Title is coherent and not "Untitled" or a JSON fragment
- [x] Body has paragraphs / headings — not one wall of text
- [x] Body contains no time-anchored phrases ("this week", "yesterday", "currently", "recently") — confirms the evergreen instruction took
- [x] No secrets in the terminal output
- [x] Run it twice; two distinct posts appear (no caching collisions)

### Step 2.9 — Document the command

**Done looks like:** A short `README.md` (or an updated section in this file)
gives someone enough to run the agent on a fresh checkout.

**Verification:**
- [x] `README.md` exists at the project root
- [x] Documents: prerequisites (Python, Docker), setup (venv, install, `.env`), and the command (`python -m openclaw post`)
- [x] Documents the optional `--topic`, `--category`, `--draft`, and `--verbose` flags
- [x] Lists the four allowed category values
- [x] Links to PLAN.md for the bigger picture
- [x] Says explicitly: never commit `.env`
- [x] Following the README from scratch on a fresh machine would produce a working agent (mental walkthrough is enough; don't actually wipe your machine)

**Phase 2 exit criteria:** All 2.1–2.9 checks pass. Running
`python -m openclaw post` from the project root publishes a fresh evergreen
article in one of the four categories. Now you're ready to schedule it
(Phase 3) and eventually feed analytics back in (Phase 4).

---

## 7b. External WordPress site — setup & verification

Goal: point the agent at an existing WP site by updating `.env` only.
No code changes are needed; all categories are fetched from the target site
at runtime.

### Step E.1 — Create an Application Password on the target site

**Done looks like:** A dedicated Application Password exists for a user with
at least the **Author** role. The password is stored in `.env`.

**Verification:**
- [ ] WP Admin → Users → (select user) → confirm the "Username" field (login name, NOT display name or email) — this is `WP_USERNAME`
- [ ] User role is **Author** or higher (Author can create/publish posts; Contributor cannot publish; Subscriber cannot create posts)
- [ ] Application Passwords section visible on the user profile page (requires HTTPS on the site — no mu-plugin needed unlike the local HTTP setup)
- [ ] New password created (name it `openclaw-cli`) and copied immediately from the modal
- [ ] `.env` updated:
  - `WP_BASE_URL` = site URL, no trailing slash (e.g. `https://example.com`)
  - `WP_USERNAME` = WP login name (slug) exactly as shown in the "Username" field
  - `WP_APP_PASSWORD` = the generated password (spaces optional; 24 chars)

### Step E.2 — Verify REST API authentication

Run these one-liners to confirm credentials work before running the agent:

```powershell
# Should print your username and roles (not 401)
.venv\Scripts\python.exe -c @"
import requests, os
from dotenv import load_dotenv; load_dotenv()
r = requests.get(os.getenv('WP_BASE_URL').rstrip('/') + '/wp-json/wp/v2/users/me',
    auth=(os.getenv('WP_USERNAME'), os.getenv('WP_APP_PASSWORD')))
print(r.status_code, r.json().get('slug',''), r.json().get('roles',''), r.json().get('code',''))
"@
```

**Verification:**
- [ ] `GET /wp-json/wp/v2/users/me` returns **200** with your username slug and role (e.g. `200 clayton ['author']`)
- [ ] Role shown is `author`, `editor`, or `administrator` (not `subscriber` or `contributor`)

```powershell
# Should print the site's categories (not 401)
.venv\Scripts\python.exe -c "from openclaw.publisher import get_category_names; print(get_category_names())"
```

- [ ] `get_category_names()` prints the category names from the target site

### Step E.3 — Verify post creation (draft)

```powershell
python -m openclaw post --draft
```

**Verification:**
- [ ] Exit code 0
- [ ] Final line printed is the draft URL on the target site
- [ ] Log shows `WARNING Cannot create tag` lines if user lacks `manage_categories` — this is acceptable; tags are skipped gracefully
- [ ] Log does NOT show `ERROR Run failed`
- [ ] Draft appears in WP Admin → Posts → Drafts on the target site
- [ ] Draft author is the `WP_USERNAME` user
- [ ] Draft assigned to one of the site's real categories

---

## 8. Open questions

- Theme — defaulting to whatever block theme ships with WP for now; revisit if visual polish becomes a priority.
- Hosting target — still TBD; pick before Phase 3 if you want the scheduler running somewhere reliable (cloud VM beats your laptop).
- Version control remote — local-only or GitHub? Required answer before pushing any commits.
- Analytics source for Phase 4 — Jetpack Stats? Google Analytics? Plausible? Native WP doesn't track views.
