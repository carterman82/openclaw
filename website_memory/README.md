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
readability targets, image prompt formula, topic-selection framework) still
live in `Instructions/STYLE.md`, `Instructions/IMAGE_GENERATOR.md`, and
`Instructions/TOPIC.md`. Only the site-specific persona lives here.

## Adding a new site

1. Copy an existing file as a starting template: `cp catfancast.com.md newsite.com.md`.
2. Rewrite the persona for the new site (real subject matter, audience,
   green-light / red-light topic lists).
3. Add the corresponding `{SLUG}_WP_BASE_URL`, `{SLUG}_WP_USERNAME`,
   `{SLUG}_WP_APP_PASSWORD` block to `.env` (see `.env.example`).
4. Run `python -m openclaw post --site {slug} --draft` to verify.
