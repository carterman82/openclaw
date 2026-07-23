"""Post-publish deploy hook: Staatic export -> git push to GitHub Pages repo.

Phase 5: after `python -m openclaw post --site <slug>` publishes a new article
to the local Docker WP multisite, this module:

1. Triggers a Staatic export via `docker compose run --rm wpcli staatic publish
   --url=http://<slug>.localhost:8088`. Files land in
   `staatic-exports/<slug>/` on the host (bind-mounted from the container).
2. Syncs `staatic-exports/<slug>/` into a persistent working tree at
   `.gh-worktree/openclaw-<slug>/` (cloned once, then reused each run), commits,
   and pushes to the `main` branch of `carterman82/openclaw-<slug>`.
3. GitHub Pages, already enabled at repo creation, rebuilds within ~1-2 min.

Both `trigger_staatic_export` and `commit_and_push` graceful-fail (return False,
log a WARNING, never raise) so a failed deploy never rolls back a successful WP
publish.

Configuration lives in the module-level constants below rather than `.env` —
the local Docker multisite pilot is inherently machine-local, and threading
these through `Config` would clutter the config surface for the (external)
remote WP sites (`--site catfancast`).
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent


def _resolve_git_exe() -> str:
    """Find git.exe by absolute path.

    Task Scheduler runs this script with a PATH that doesn't include the
    user-profile Git install directory (unlike an interactive shell), so
    `subprocess.run(["git", ...])` fails with WinError 2 on every scheduled
    run even though `docker` (machine-wide PATH) resolves fine. Resolve once
    at import time and use the absolute path everywhere.
    """
    found = shutil.which("git")
    if found:
        return found
    # Under Task Scheduler, %LOCALAPPDATA% and %USERPROFILE% may resolve to
    # the service principal's profile (not the interactive user's), so the
    # env-var-driven candidates below miss the real install. Also include
    # the observed absolute path for this machine as a last-ditch check.
    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "cmd" / "git.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Git" / "cmd" / "git.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Git" / "cmd" / "git.exe",
        Path(os.environ.get("USERPROFILE", "")) / "AppData" / "Local" / "Programs" / "Git" / "cmd" / "git.exe",
        Path(r"C:\Users\carte\AppData\Local\Programs\Git\cmd\git.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    logger.warning(
        "Could not resolve git.exe via PATH or common install locations; "
        "falling back to bare 'git' (will likely fail under Task Scheduler)."
    )
    return "git"


_GIT_EXE: str = _resolve_git_exe()
_EXPORT_ROOT: Path = _PROJECT_ROOT / "staatic-exports"
_WORKTREE_ROOT: Path = _PROJECT_ROOT / ".gh-worktree"
_GH_OWNER = "carterman82"
_GH_REPO_PREFIX = "openclaw-"

# Custom domain for each pilot subsite on GitHub Pages.
# A CNAME file with this value is written into the worktree on every deploy
# so Staatic republishes can't wipe it.  Update here when subdomains change.
_SLUG_TO_DOMAIN: dict[str, str] = {
    "gardening":  "gardening.info-verse.org",
    "dogs":       "dogs.info-verse.org",
    "boardgames": "boardgames.info-verse.org",
    "coffee":     "coffee.info-verse.org",
    "techtools":  "techtools.info-verse.org",
    # Hub sits on the naked apex; carterman82.github.io (the user-site repo)
    # is the source of truth for info-verse.org because Namecheap doesn't do
    # ALIAS records at the apex — pointing four GH Pages A records at the
    # apex lands users on whichever repo owns the apex CNAME.
    "hub":        "info-verse.org",
}

# Per-slug repo override. Absent slugs fall back to the historical
# `openclaw-<slug>` pattern under _GH_OWNER. Kept as a hook for the case
# where a slug's serving repo diverges from the default naming — currently
# empty (hub now uses openclaw-hub like the five pilots, since the
# alternative — reusing the carterman82.github.io user-site repo — would
# have wiped its existing content and broken www.reggaefancast.com).
_SLUG_TO_REPO: dict[str, str] = {}

# Only the pilot subsites that live on the local multisite deploy to GitHub.
# Other slugs (catfancast, localhost as primary) are skipped by the wiring in
# main.py so this list stays authoritative and predictable.
DEPLOYABLE_SLUGS: frozenset[str] = frozenset({
    "gardening", "dogs", "boardgames", "coffee", "techtools",
    "hub",
})

_STAATIC_TIMEOUT_SEC = 300
_GIT_TIMEOUT_SEC = 180


def is_deployable(slug: str | None) -> bool:
    return bool(slug) and slug in DEPLOYABLE_SLUGS


def trigger_staatic_export(slug: str) -> bool:
    """Run `wp staatic publish` for the given subsite. Return True on success."""
    url = f"http://{slug}.localhost:8088"
    cmd = [
        "docker", "compose", "run", "--rm", "wpcli",
        "staatic", "publish", f"--url={url}",
    ]
    logger.info("Triggering Staatic export for %r (%s).", slug, url)
    try:
        result = subprocess.run(
            cmd,
            cwd=str(_PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=_STAATIC_TIMEOUT_SEC,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        logger.warning("Staatic export failed to start (%s): %s", type(exc).__name__, exc)
        return False
    if result.returncode != 0:
        logger.warning(
            "Staatic export exited %d. stdout tail: %s ; stderr tail: %s",
            result.returncode,
            result.stdout[-400:].strip(),
            result.stderr[-400:].strip(),
        )
        return False
    export_dir = _EXPORT_ROOT / slug
    if not export_dir.exists() or not any(export_dir.iterdir()):
        logger.warning("Staatic reported success but %s is empty.", export_dir)
        return False
    logger.info("Staatic export OK: %s", export_dir)
    return True


# Per-invocation git overrides so deploy works regardless of which principal
# runs the process (interactive user vs. Task Scheduler service account) and
# regardless of what's in that principal's global git config.
#
# safe.directory=*  neutralises Git's "dubious ownership" refusal when the
#   .gh-worktree/ dirs were created by a different user (e.g. an interactive
#   catch-up push while the scheduler runs as SYSTEM).
# user.name / user.email
#   the service principal has no global identity, so `git commit` fails with
#   "Author identity unknown"; hardcode a stable openclaw identity that
#   matches what earlier interactive commits used (github.com noreply address
#   for carterman82) so commit history stays consistent across principals.
_GIT_C_OVERRIDES = (
    "-c", "safe.directory=*",
    "-c", "user.name=Carter",
    "-c", "user.email=67517982+carterman82@users.noreply.github.com",
)


def _run_git(args: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            [_GIT_EXE, *_GIT_C_OVERRIDES, *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SEC,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return False, f"{type(exc).__name__}: {exc}"
    out = (r.stdout + r.stderr).strip()
    return r.returncode == 0, out


def _repo_name(slug: str) -> str:
    """Return the GitHub repo name for `slug`. Overrides via _SLUG_TO_REPO win."""
    return _SLUG_TO_REPO.get(slug, f"{_GH_REPO_PREFIX}{slug}")


def _ensure_worktree(slug: str) -> Path | None:
    """Clone the deploy repo once; reuse the working tree on subsequent runs."""
    _WORKTREE_ROOT.mkdir(parents=True, exist_ok=True)
    repo = _repo_name(slug)
    wt = _WORKTREE_ROOT / repo
    remote = f"https://github.com/{_GH_OWNER}/{repo}.git"
    if not (wt / ".git").exists():
        logger.info("Cloning deploy repo for %r into %s.", slug, wt)
        if wt.exists():
            shutil.rmtree(wt, ignore_errors=True)
        ok, out = _run_git(["clone", remote, str(wt)], cwd=_PROJECT_ROOT)
        if not ok:
            logger.warning("git clone failed for %r: %s", slug, out[-400:])
            return None
    else:
        ok, out = _run_git(["fetch", "origin", "main"], cwd=wt)
        if not ok:
            logger.warning("git fetch failed for %r: %s", slug, out[-400:])
            return None
        ok, out = _run_git(["reset", "--hard", "origin/main"], cwd=wt)
        if not ok:
            logger.warning("git reset failed for %r: %s", slug, out[-400:])
            return None
    return wt


def _sync_export_into_worktree(export_dir: Path, worktree: Path) -> None:
    """Mirror export_dir into worktree, preserving .git and .nojekyll."""
    # Delete every path in the worktree except .git (and .nojekyll, which we
    # re-copy from the export if present, otherwise regenerate).
    for entry in worktree.iterdir():
        if entry.name == ".git":
            continue
        if entry.is_dir():
            shutil.rmtree(entry, ignore_errors=True)
        else:
            try:
                entry.unlink()
            except OSError:
                pass
    for entry in export_dir.iterdir():
        dest = worktree / entry.name
        if entry.is_dir():
            shutil.copytree(entry, dest)
        else:
            shutil.copy2(entry, dest)
    # Ensure .nojekyll (GH Pages Jekyll-skip flag) exists.
    (worktree / ".nojekyll").touch()


def commit_and_push(slug: str, post_title: str) -> bool:
    """Copy export -> worktree, commit, push. Return True on success."""
    export_dir = _EXPORT_ROOT / slug
    if not export_dir.exists():
        logger.warning("No export directory at %s; skipping deploy.", export_dir)
        return False
    worktree = _ensure_worktree(slug)
    if worktree is None:
        return False
    _sync_export_into_worktree(export_dir, worktree)
    domain = _SLUG_TO_DOMAIN.get(slug)
    if domain:
        (worktree / "CNAME").write_text(domain + "\n")
    ok, _ = _run_git(["add", "-A"], cwd=worktree)
    if not ok:
        logger.warning("git add failed for %r.", slug)
        return False
    ok, status = _run_git(["status", "--porcelain"], cwd=worktree)
    if not ok:
        logger.warning("git status failed for %r.", slug)
        return False
    if not status.strip():
        logger.info("No changes to deploy for %r.", slug)
        return True
    msg = f"Publish: {post_title} [{slug}]"
    ok, out = _run_git(["commit", "-m", msg], cwd=worktree)
    if not ok:
        logger.warning("git commit failed for %r: %s", slug, out[-400:])
        return False
    ok, out = _run_git(["push", "origin", "main"], cwd=worktree)
    if not ok:
        logger.warning("git push failed for %r: %s", slug, out[-400:])
        return False
    logger.info("Deployed %r: %s", slug, msg)
    return True


def refresh_hub(reason: str = "subsite publish") -> bool:
    """Re-export + re-push the hub aggregation site.

    Called after any non-hub deployable subsite publishes so the info-verse.org
    home page's card feed reflects the new post within one publish cycle
    instead of waiting up to 6 hours for the per-subsite REST-fetch transient
    to expire. Also invalidates the hub's cached feed transients before the
    Staatic crawl so the new post is picked up on the first render.

    Fail-soft — a hub refresh error must not fail the subsite deploy that
    triggered it. Callers ignore the return value.
    """
    logger.info("Refreshing hub aggregation site (reason=%s).", reason)

    # Bust the hub's cached subsite feeds so the Staatic crawl re-fetches
    # from every subsite's live REST API. Safe to skip if wp-cli refuses
    # (fresh install, plugin not yet registering the command, etc.).
    flush_cmd = [
        "docker", "compose", "run", "--rm", "wpcli",
        "openclaw", "hub_flush_cache", "--url=hub.localhost:8088",
    ]
    try:
        subprocess.run(
            flush_cmd,
            cwd=str(_PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        logger.warning("Hub cache flush failed to start (%s): %s", type(exc).__name__, exc)

    if not trigger_staatic_export("hub"):
        return False
    return commit_and_push("hub", f"Refresh feed ({reason})")


def deploy_after_publish(slug: str, post_title: str) -> bool:
    """Full post-publish deploy chain. Skips silently for non-pilot slugs."""
    if not is_deployable(slug):
        logger.debug("Skipping deploy for non-pilot slug %r.", slug)
        return False
    if not trigger_staatic_export(slug):
        return False
    ok = commit_and_push(slug, post_title)
    # Piggyback: after any non-hub subsite deploy succeeds, refresh the hub
    # so its aggregation feed reflects the new post. A hub refresh failure
    # never rolls back the subsite deploy — refresh_hub is fail-soft and its
    # return value is intentionally ignored.
    if ok and slug != "hub":
        try:
            refresh_hub(reason=f"{slug} publish: {post_title}")
        except Exception as exc:  # noqa: BLE001 — belt-and-braces
            logger.warning("Hub refresh raised %s: %s", type(exc).__name__, exc)
    return ok
