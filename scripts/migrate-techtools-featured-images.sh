#!/bin/bash
# One-shot: for each techtools post whose _thumbnail_id points at a stale primary
# attachment ID, resolve the primary attachment's file path, wp media import it
# into techtools with --featured_image, and copy alt text over.
#
# Runs inside the wpcli container (entrypoint=bash). Invoked by the caller as:
#   docker compose run --rm --entrypoint bash wpcli /path/to/this/script.sh
#
# Idempotent: if a techtools post already has a valid techtools attachment as its
# thumbnail, it is skipped.

set -euo pipefail

PRIMARY="http://localhost:8088"
TARGET="http://techtools.localhost:8088"
UPLOADS_ROOT="/var/www/html/wp-content/uploads"

mapfile -t POST_IDS < <(wp post list --url="$TARGET" --post_type=post --post_status=publish --format=ids | tr ' ' '\n')

echo "Processing ${#POST_IDS[@]} techtools posts."

migrated=0
skipped=0
failed=0

for pid in "${POST_IDS[@]}"; do
    old_tid=$(wp post meta get "$pid" _thumbnail_id --url="$TARGET" 2>/dev/null || true)
    if [ -z "$old_tid" ]; then
        skipped=$((skipped+1))
        continue
    fi

    exists_on_target=$(wp post get "$old_tid" --url="$TARGET" --field=post_type 2>/dev/null || true)
    if [ "$exists_on_target" = "attachment" ]; then
        skipped=$((skipped+1))
        continue
    fi

    file_url=$(wp post get "$old_tid" --url="$PRIMARY" --field=guid 2>/dev/null || true)
    alt=$(wp post meta get "$old_tid" _wp_attachment_image_alt --url="$PRIMARY" 2>/dev/null || true)
    title=$(wp post get "$old_tid" --url="$PRIMARY" --field=post_title 2>/dev/null || true)
    if [ -z "$file_url" ]; then
        echo "  [FAIL] post=$pid old_tid=$old_tid — could not read primary attachment"
        failed=$((failed+1))
        continue
    fi

    rel_path=${file_url#*/wp-content/uploads/}
    local_path="$UPLOADS_ROOT/$rel_path"
    if [ ! -f "$local_path" ]; then
        echo "  [FAIL] post=$pid file=$local_path missing on disk"
        failed=$((failed+1))
        continue
    fi

    args=(--url="$TARGET" --post_id="$pid" --featured_image --porcelain)
    if [ -n "$title" ]; then args+=(--title="$title"); fi
    if [ -n "$alt" ]; then args+=(--alt="$alt"); fi

    new_id=$(wp media import "$local_path" "${args[@]}" 2>/dev/null || true)
    if [ -z "$new_id" ]; then
        echo "  [FAIL] post=$pid wp media import produced no ID"
        failed=$((failed+1))
        continue
    fi

    migrated=$((migrated+1))
    echo "  post=$pid old_tid=$old_tid → new_tid=$new_id ($rel_path)"
done

echo
echo "Migrated: $migrated | Skipped: $skipped | Failed: $failed"
