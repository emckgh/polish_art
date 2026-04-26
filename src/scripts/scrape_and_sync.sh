#!/usr/bin/env bash
# Weekly scrape-and-sync runner for the Linux box.
#
# Run via cron (every Monday at 03:00):
#   0 3 * * 1  /mnt/data/polish_art/src/scripts/scrape_and_sync.sh
#
# First-time use: run with --seed to populate scraper_targets from JSON:
#   ./src/scripts/scrape_and_sync.sh --seed
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
# Use SSH config Host so IdentityFile applies (see ~/.ssh/config polishart-vps)
VPS="polishart-vps"
LOG_DIR="$REPO/logs"
LOG="$LOG_DIR/scrape_and_sync.log"
EXPORT_DB="$REPO/data/server_export.db"

SEED=false
FORCE=false
for arg in "$@"; do
    case "$arg" in
        --seed) SEED=true ;;
        --force) FORCE=true ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

mkdir -p "$LOG_DIR"
exec >> "$LOG" 2>&1

echo ""
echo "=== $(date -u '+%Y-%m-%d %H:%M UTC') scrape_and_sync starting ==="

cd "$REPO"

PY="$REPO/.venv/bin/python"
if [ ! -x "$PY" ]; then
    echo "ERROR: venv not found at $PY — run: python3 -m venv .venv && .venv/bin/pip install -r requirements-scraper.txt" >&2
    exit 1
fi

# Optionally seed scraper_targets on first run
if [ "$SEED" = true ]; then
    echo "--- Seeding scraper targets from JSON ---"
    "$PY" -m src.scripts.run_weekly_scrape --seed --force
elif [ "$FORCE" = true ]; then
    echo "--- Running forced scrape (all active targets) ---"
    "$PY" -m src.scripts.run_weekly_scrape --force
else
    echo "--- Running scheduled scrape (due targets only) ---"
    "$PY" -m src.scripts.run_weekly_scrape
fi

# Build pruned export DB for the VPS
echo "--- Building server export DB ---"
"$PY" src/scripts/build_and_sync_server_db.py \
    --output "$EXPORT_DB" \
    --strip-images-unless-include

EXPORT_SIZE_MB=$(du -m "$EXPORT_DB" | cut -f1)
echo "Export size: ${EXPORT_SIZE_MB} MB"

# Push to VPS — atomic: rsync writes to a temp file then renames
echo "--- Syncing to VPS ---"
rsync -az --progress \
    --temp-file="polish_art/data/artworks.db.tmp" \
    "$EXPORT_DB" \
    "$VPS:polish_art/data/artworks.db"

# Restart the app service on the VPS
echo "--- Restarting polish-art service ---"
ssh "$VPS" 'sudo systemctl restart polish-art && sudo systemctl is-active polish-art'

echo "=== $(date -u '+%Y-%m-%d %H:%M UTC') scrape_and_sync complete ==="
