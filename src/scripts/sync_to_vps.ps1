# Quick Database Sync to VPS
# Usage: .\scripts\sync_to_vps.ps1 [VPS_USER@VPS_HOST]
# Example: .\scripts\sync_to_vps.ps1 polishart@polishart.mcqueeney.org

param(
    [Parameter(Mandatory=$false)]
    [string]$Target = "polishart@lostpolishart.mcqueeney.org"
)

$ErrorActionPreference = "Stop"

Write-Host "==> Polish Art VPS Database Sync" -ForegroundColor Cyan
Write-Host "Target: $Target" -ForegroundColor Yellow

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
}

# Build server export database
Write-Host "`n==> Building server export database..." -ForegroundColor Cyan
python src/scripts/build_and_sync_server_db.py --output data/server_export.db --strip-images-unless-include

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to build server export database" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "data/server_export.db")) {
    Write-Host "ERROR: server_export.db was not created" -ForegroundColor Red
    exit 1
}

# Get file size for confirmation
$fileSize = (Get-Item "data/server_export.db").Length / 1MB
Write-Host "Export size: $($fileSize.ToString('F2')) MB" -ForegroundColor Green

# Transfer to VPS
Write-Host "`n==> Transferring to VPS..." -ForegroundColor Cyan
scp data/server_export.db "${Target}:polish_art/data/artworks.db"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to transfer database" -ForegroundColor Red
    exit 1
}

# Restart service on VPS
Write-Host "`n==> Restarting polish-art service..." -ForegroundColor Cyan
ssh $Target 'sudo systemctl restart polish-art && sudo systemctl status polish-art --no-pager'

if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Service restart may have failed. Check status manually." -ForegroundColor Yellow
} else {
    Write-Host "`n==> Sync complete!" -ForegroundColor Green
    Write-Host "Check https://lostpolishart.mcqueeney.org/ to verify" -ForegroundColor Cyan
}
