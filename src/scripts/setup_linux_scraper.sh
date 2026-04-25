#!/usr/bin/env bash
# Run on the Linux box to set up the scraper environment from scratch.
# Assumes artworks.db is already at /mnt/usb/data/artworks.db
# Usage: bash setup_linux_scraper.sh
set -euo pipefail

REPO_URL="https://github.com/mcqueeney/polish_art.git"   # update if different
REPO_DIR="/mnt/usb/dasein/polish_art"
DATA_DIR="$REPO_DIR/data"
DB_SOURCE="/mnt/usb/data/artworks.db"
VPS_KEY="$HOME/.ssh/polishart_vps_ed25519"
VPS_HOST="polishart@lostpolishart.mcqueeney.org"
CRON_SCHEDULE="0 3 * * *"   # daily at 03:00

echo ""
echo "=== Polish Art Linux Scraper Setup ==="
echo ""

# ── 1. Clone repo ──────────────────────────────────────────────────────────
if [ -d "$REPO_DIR/.git" ]; then
    echo "[1/6] Repo already cloned — pulling latest..."
    git -C "$REPO_DIR" pull
else
    echo "[1/6] Cloning repo to $REPO_DIR..."
    git clone "$REPO_URL" "$REPO_DIR"
fi

# ── 2. Python venv ─────────────────────────────────────────────────────────
echo "[2/6] Setting up Python venv (scraper-only deps)..."
# Remove any partial venv from a previous failed attempt
rm -rf "$REPO_DIR/.venv"
python3 -m venv "$REPO_DIR/.venv"
source "$REPO_DIR/.venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$REPO_DIR/requirements-scraper.txt"
echo "      venv ready."

# ── 3. Copy DB ─────────────────────────────────────────────────────────────
echo "[3/6] Copying artworks.db into repo..."
mkdir -p "$DATA_DIR"
if [ -f "$DB_SOURCE" ]; then
    cp "$DB_SOURCE" "$DATA_DIR/artworks.db"
    echo "      Copied $(du -m "$DATA_DIR/artworks.db" | cut -f1) MB."
else
    echo "      WARNING: $DB_SOURCE not found — skipping copy."
    echo "      You will need to copy artworks.db to $DATA_DIR/artworks.db manually."
fi

# ── 4. SSH key for VPS ─────────────────────────────────────────────────────
echo "[4/6] Setting up SSH key for VPS..."
if [ ! -f "$VPS_KEY" ]; then
    ssh-keygen -t ed25519 -f "$VPS_KEY" -C "linux-scraper" -N ""
    echo ""
    echo "      *** ACTION REQUIRED ***"
    echo "      Run this command to authorize the key on the VPS (needs polishart password once):"
    echo ""
    echo "      ssh-copy-id -i $VPS_KEY.pub $VPS_HOST"
    echo ""
    echo "      Then re-run this script, or continue manually."
else
    echo "      Key already exists at $VPS_KEY"
fi

# Add SSH config entry if not already there
if ! grep -q "polishart-vps" "$HOME/.ssh/config" 2>/dev/null; then
    mkdir -p "$HOME/.ssh"
    cat >> "$HOME/.ssh/config" << EOF

Host polishart-vps
  HostName lostpolishart.mcqueeney.org
  User polishart
  IdentityFile $VPS_KEY
  IdentitiesOnly yes
EOF
    echo "      Added polishart-vps to ~/.ssh/config"
fi

# ── 5. Make script executable ──────────────────────────────────────────────
echo "[5/6] Making scrape_and_sync.sh executable..."
chmod +x "$REPO_DIR/src/scripts/scrape_and_sync.sh"

# ── 6. Cron entry ──────────────────────────────────────────────────────────
echo "[6/6] Setting up daily cron job..."
CRON_CMD="$CRON_SCHEDULE  $REPO_DIR/src/scripts/scrape_and_sync.sh"

if crontab -l 2>/dev/null | grep -qF "scrape_and_sync.sh"; then
    echo "      Cron entry already exists — skipping."
else
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "      Added: $CRON_CMD"
fi

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Verify SSH to VPS works:    ssh polishart-vps 'echo ok'"
echo "Seed targets + first run:   $REPO_DIR/src/scripts/scrape_and_sync.sh --seed"
echo "Check cron:                 crontab -l"
echo "Monitor logs:               tail -f $REPO_DIR/logs/scrape_and_sync.log"
echo ""
