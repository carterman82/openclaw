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
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
_EXPORT_ROOT: Path = _PROJECT_ROOT / "staatic-exports"
_WORKTREE_ROOT: Path = _PROJECT_ROOT / ".gh-worktree"
_GH_OWNER = "carterman82"
_GH_REPO_PREFIX = "openclaw-"

# Only the pilot subsites that live on the local multisite deploy to GitHub.
# Other slugs (catfancast, localhost as primary) are skipped by the wiring in
# main.py so this list stays authoritative and predictable.
DEPLOYABLE_SLUGS: frozenset[str] = frozenset({
    "gardening", "dogs", "boardgames", "coffee",
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


def _run_git(args: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SEC,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return False, f"{type(exc).__name__}: {exc}"
    out = (r.stdout + r.stderr).strip()
    return r.returncode == 0, out


def _ensure_worktree(slug: str) -> Path | None:
    """Clone the deploy repo once; reuse the working tree on subsequent runs."""
    _WORKTREE_ROOT.mkdir(parents=True, exist_ok=True)
    wt = _WORKTREE_ROOT / f"{_GH_REPO_PREFIX}{slug}"
    remote = f"https://github.com/{_GH_OWNER}/{_GH_REPO_PREFIX}{slug}.git"
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


def deploy_after_publish(slug: str, post_title: str) -> bool:
    """Full post-publish deploy chain. Skips silently for non-pilot slugs."""
    if not is_deployable(slug):
        logger.debug("Skipping deploy for non-pilot slug %r.", slug)
        return False
    if not trigger_staatic_export(slug):
        return False
    return commit_and_push(slug, post_title)
