# website_memory/

Per-site persona files loaded into the Claude system prompt by
`openclaw.generator._load_description()`.

## Naming convention

One file per WordPress site: **`{hostname}.md`** where `{hostname}` is the
exact host component of the site's `WP_BASE_URL` (as parsed by
`urllib.parse.urlparse`).

Examples:

| `WP_BASE_URL`                    | Memory file                          |
|----------------------------------|--------------------------------------|
| `https://catfancast.com`         | `website_memory/catfancast.com.md`   |
| `https://www.example.com`        | `website_memory/www.example.com.md`  |
| `http://localhost:8088`          | `website_memory/localhost.md`        |

No www stripping, no aliasing, no case folding beyond what `urlparse` does.
If the hostname doesn't match a file here exactly, `_load_description` raises
`RuntimeError` naming the expected path — publishing without a site persona
would produce off-brand content silently, so this is a hard error.

## What goes in a site file

Everything that used to live in `Instructions/DESCRIPTION.md`: what the site
is, who the audience is, tone, green-light topic areas, red-light topics,
entity checklists, brand identity. See `catfancast.com.md` for the current
template.

The cross-site editorial rules (voice conventions, header hierarchy,
readability targets) still live in `Instructions/STYLE.md`. Topic-selection
frameworks and image-prompt guides are **per-site**, not cross-site — see
below.

## Per-site topic and image guides

Two more optional per-site files, same naming convention as the persona file:

- **`{hostname}.topic.md`** — governs *what* the agent writes about: anchor
  inventories, evergreen/trending ratios, angle types, duplicate/rotation
  rules. Loaded by `generator._load_topic_guide(site_host)`.
- **`{hostname}.image.md`** — governs the cover-image prompt formula for that
  site's subject matter (composition rules, reference banks, IP guardrails
  specific to the domain). Loaded by `generator._load_image_guide(site_host)`.

Both are optional — a missing file just means no extra topic/image guidance
is injected into the system prompt (base rules in `generator.py` still
apply). See `catfancast.com.topic.md` / `catfancast.com.image.md` and
`animefancast.com.topic.md` / `animefancast.com.image.md` for templates.
These used to be cross-site files under `Instructions/TOPIC.md` and
`Instructions/IMAGE_GENERATOR.md`; they were split per-site because a single
shared file forced every site to inherit cat-specific (or whichever site
authored it first) rules that didn't fit other domains.

## Adding a new site

1. Copy an existing file as a starting template: `cp catfancast.com.md newsite.com.md`.
2. Rewrite the persona for the new site (real subject matter, audience,
   green-light / red-light topic lists).
3. Optionally add `{hostname}.topic.md` and `{hostname}.image.md` following
   the pattern above — recommended for any site where topic selection needs
   its own anchor inventory/ratios or the cover art needs domain-specific
   composition/IP rules.
4. Add the corresponding `{SLUG}_WP_BASE_URL`, `{SLUG}_WP_USERNAME`,
   `{SLUG}_WP_APP_PASSWORD` block to `.env` (see `.env.example`).
5. Run `python -m openclaw post --site {slug} --draft` to verify.
