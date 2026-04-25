# One-time setup: authorizes this machine's SSH key on the Linux box,
# then pushes artworks.db to it.
#
# Run from a regular PowerShell window (will prompt for dasein's password once).
# Usage: .\setup_linux_box.ps1

$ErrorActionPreference = "Stop"

$LINUX_HOST  = "100.64.90.50"
$LINUX_USER  = "dasein"
$LINUX_DEST  = "/mnt/usb/data/artworks.db"
$KEY_FILE    = "$env:USERPROFILE\.ssh\linux_box_ed25519"
$PUB_KEY     = Get-Content "$KEY_FILE.pub"
$DB_PATH     = "C:\Dev\polish_art\data\artworks.db"

Write-Host ""
Write-Host "==> Step 1: Authorizing SSH key on $LINUX_USER@$LINUX_HOST" -ForegroundColor Cyan
Write-Host "    (You will be prompted for $LINUX_USER's password once)" -ForegroundColor Yellow

# Push the public key to authorized_keys on the Linux box
$remote_cmd = "mkdir -p ~/.ssh && echo '$PUB_KEY' >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys && echo KEY_OK"
$result = ssh -o StrictHostKeyChecking=accept-new "${LINUX_USER}@${LINUX_HOST}" $remote_cmd

if ($result -notmatch "KEY_OK") {
    Write-Host "ERROR: Could not add key to authorized_keys. Output: $result" -ForegroundColor Red
    exit 1
}
Write-Host "    Key authorized." -ForegroundColor Green

Write-Host ""
Write-Host "==> Step 2: Pushing artworks.db ($([math]::Round((Get-Item $DB_PATH).Length / 1MB, 0)) MB) to Linux box..." -ForegroundColor Cyan

scp -O -i "$KEY_FILE" "$DB_PATH" "${LINUX_USER}@${LINUX_HOST}:${LINUX_DEST}"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: SCP failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==> Done! artworks.db is on the Linux box at $LINUX_DEST" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps on the Linux box:" -ForegroundColor Cyan
Write-Host "  cd /mnt/usb/polish_art  (or wherever you cloned the repo)" -ForegroundColor White
Write-Host "  python3 -m venv .venv && source .venv/bin/activate" -ForegroundColor White
Write-Host "  pip install -r requirements.txt" -ForegroundColor White
Write-Host "  cp $LINUX_DEST data/artworks.db" -ForegroundColor White
Write-Host "  ./src/scripts/scrape_and_sync.sh --seed" -ForegroundColor White
