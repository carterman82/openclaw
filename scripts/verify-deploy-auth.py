"""
verify-deploy-auth.py — Phase 8 Step 8.6 GitHub Pages deploy-auth health check.

Runs `git ls-remote origin main` (a no-side-effect auth probe — read-only,
never pushes or writes anything) against each of the 6 deploy repos (the 5
pilot subsites + hub), using the same GITHUB_TOKEN + credential-injection
path as deploy.py's commit_and_push (Step 8.4). The point is to catch a
credential expiry (the original 2026-07-23 incident: GCM's cached PAT went
stale, silently killing 3 days of scheduled pushes) with a proactive
health-check run, instead of discovering it only after several days of
undeployed content.

Exit code is the number of repos that failed the probe (0 = all reachable).
Runnable ad-hoc, or wire up as a weekly Task Scheduler job alongside
run-openclaw.ps1.

Usage:
    python scripts/verify-deploy-auth.py                  # all 6 deploy repos
    python scripts/verify-deploy-auth.py --repo gardening
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import openclaw  # noqa: F401  (installs the *.localhost DNS shim)
from openclaw.main import _activate_site
from openclaw.deploy import DEPLOYABLE_SLUGS, _GH_OWNER, _get_github_token, _repo_name, _run_git

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# GITHUB_TOKEN is a bare, cross-site env var, but Config.load() (called
# inside _get_github_token()) also requires WP_BASE_URL/USERNAME/APP_PASSWORD
# to be set. Activating any one deployable site's prefix satisfies that
# requirement regardless of what's in the bare WP_* slots — the token itself
# doesn't vary by site.
_ARBITRARY_ACTIVATION_SLUG = "gardening"


def probe(slug: str, token: str) -> bool:
    repo = _repo_name(slug)
    remote = f"https://github.com/{_GH_OWNER}/{repo}.git"
    ok, out = _run_git(["ls-remote", remote, "main"], cwd=_PROJECT_ROOT, token=token)
    if ok:
        print(f"[OK]   {slug} ({repo}): {out.strip()[:80] or 'reachable, no output'}")
    else:
        print(f"[FAIL] {slug} ({repo}): {out.strip()[:300]}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 8 Step 8.6 deploy-auth health check.")
    parser.add_argument(
        "--repo", action="append", dest="slugs", metavar="SLUG",
        help="Limit to this deploy slug (repeatable). Default: all deployable slugs.",
    )
    args = parser.parse_args()
    slugs = args.slugs or sorted(DEPLOYABLE_SLUGS)

    _activate_site(_ARBITRARY_ACTIVATION_SLUG)
    token = _get_github_token()
    if not token:
        print("[FAIL] No push credential available — GITHUB_TOKEN is unset in .env "
              "and `gh auth token` failed (is `gh auth login` set up on this machine?).")
        return len(slugs)

    failures = [slug for slug in slugs if not probe(slug, token)]
    if failures:
        print(f"\n{len(failures)} of {len(slugs)} repo(s) failed: {failures}")
        return len(failures)
    print(f"\nAll {len(slugs)} repo(s) reachable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
