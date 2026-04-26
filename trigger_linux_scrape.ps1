# Trigger a full scrape + VPS sync on the Linux box (runs in background there).
# Usage: .\trigger_linux_scrape.ps1              # due targets only
#        .\trigger_linux_scrape.ps1 -Force      # all 100 sites now

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Key = "$env:USERPROFILE\.ssh\linux_box_ed25519"
$Linux = "dasein@100.64.90.50"
$Repo = "/mnt/usb/dev/polish_art"

$extra = if ($Force) { "--force" } else { "" }

Write-Host "Starting scrape_and_sync on Linux box ($extra)..." -ForegroundColor Cyan
Write-Host "Log: $Repo/logs/scrape_and_sync.log" -ForegroundColor Yellow

$remote = "cd $Repo && nohup ./src/scripts/scrape_and_sync.sh $extra </dev/null >/dev/null 2>&1 & echo Started. Tail: tail -f $Repo/logs/scrape_and_sync.log"
ssh -i $Key $Linux $remote
