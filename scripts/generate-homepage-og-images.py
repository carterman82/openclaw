"""
generate-homepage-og-images.py — Phase 7 Step 7.4 homepage og:image fix.

`scripts/audit-static-seo.py` flags 5 fails: the homepage on each pilot
subsite has no og:image because Yoast has nothing to fall back to on a
non-singular page (post pages already get og:image from their featured
image). This uploads a pre-made brand logo (`logos/<slug>infoverse.png`)
to each site's media library, sets it as the Yoast homepage social image
(`wpseo_titles` -> `open_graph_frontpage_image[_id]`), and redeploys the
static export.

The logos are hand-designed Info Verse brand marks (1254x1254 PNG each) —
they match the 2026-07-22 brand rename (`<Niche> Info Verse`) and share
one visual family across the five subsites, which is what social share
previews should telegraph.

Idempotent: re-running uploads a new attachment (WP appends `-1`, `-2` to
the filename on collision) and overwrites the Yoast option to point at
the newest one. Safe to re-run.

Usage:
    python scripts/generate-homepage-og-images.py               # all 5 sites
    python scripts/generate-homepage-og-images.py --site coffee
    python scripts/generate-homepage-og-images.py --skip-deploy  # upload + set option, no git push
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import openclaw  # noqa: F401  (installs the *.localhost DNS shim)
from openclaw.main import _activate_site
from openclaw.config import Config
from openclaw.publisher import upload_media
from openclaw.deploy import DEPLOYABLE_SLUGS, trigger_staatic_export, commit_and_push

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOGO_DIR = _PROJECT_ROOT / "logos"

# One brand logo per subsite; alt text used for both the WP attachment
# alt field and the og:image alt fallback.
LOGOS: dict[str, dict[str, str]] = {
    "gardening":  {"file": "gardeninginfoverse.png",  "alt": "Gardening Info Verse logo"},
    "dogs":       {"file": "dogsinfoverse.png",       "alt": "Dogs Info Verse logo"},
    "boardgames": {"file": "boardgamesinfoverse.png", "alt": "Boardgames Info Verse logo"},
    "coffee":     {"file": "coffeeinfoverse.png",     "alt": "Coffee Info Verse logo"},
    "techtools":  {"file": "techtoolsinfoverse.png",  "alt": "Tech Tool Guide logo"},
}


def _set_yoast_frontpage_image(slug: str, url: str, attachment_id: int) -> bool:
    ok = True
    for key, value in (
        ("open_graph_frontpage_image", url),
        ("open_graph_frontpage_image_id", str(attachment_id)),
    ):
        cmd = [
            "docker", "compose", "run", "--rm", "wpcli",
            "option", "patch", "update", "wpseo_titles", key, value,
            f"--url={slug}.localhost:8088",
        ]
        result = subprocess.run(
            cmd, cwd=str(_PROJECT_ROOT), capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"  [FAIL] option patch {key}: {result.stderr.strip()[:300]}")
            ok = False
    return ok


def process_site(slug: str, skip_deploy: bool) -> bool:
    spec = LOGOS.get(slug)
    if not spec:
        print(f"[{slug}] no LOGOS entry — skipping.")
        return False
    logo_path = _LOGO_DIR / spec["file"]
    if not logo_path.exists():
        print(f"  [FAIL] logo not found: {logo_path}")
        return False
    print(f"\n{slug}: uploading homepage og:image ({spec['file']})...")

    _activate_site(slug)
    cfg = Config.load()

    image_bytes = logo_path.read_bytes()
    attachment_id = upload_media(
        image_bytes, f"{slug}-homepage-og.png", "image/png", spec["alt"],
    )
    media_resp = requests.get(
        f"{cfg.WP_BASE_URL}/wp-json/wp/v2/media/{attachment_id}",
        auth=(cfg.WP_USERNAME, cfg.WP_APP_PASSWORD), timeout=15,
    )
    media_resp.raise_for_status()
    source_url = media_resp.json()["source_url"]
    print(f"  [uploaded] attachment_id={attachment_id} url={source_url}")

    if not _set_yoast_frontpage_image(slug, source_url, attachment_id):
        return False
    print("  [set] wpseo_titles.open_graph_frontpage_image(_id)")

    if skip_deploy:
        return True
    if not trigger_staatic_export(slug):
        return False
    return commit_and_push(slug, "Step 7.4: homepage og:image")


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 Step 7.4 homepage og:image fix.")
    parser.add_argument(
        "--site", action="append", dest="sites", metavar="SLUG",
        help="Limit to this site slug (repeatable). Default: all 5 deployable pilots.",
    )
    parser.add_argument("--skip-deploy", action="store_true", help="Generate + set option only, no redeploy.")
    args = parser.parse_args()
    sites = args.sites or sorted(DEPLOYABLE_SLUGS)

    failures = []
    for slug in sites:
        if not process_site(slug, args.skip_deploy):
            failures.append(slug)

    if failures:
        print(f"\nFAILED: {failures}")
        return 1
    print("\nAll sites done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
