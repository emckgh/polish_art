# Quick checks for LAN access to the Polish Art server.
# Run on the HOST machine (where the server runs).
# Usage: .\scripts\check_lan_access.ps1

$port = 8000
$issues = @()
$ok = @()

# 1. Is anything listening on port 8000?
$listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if (-not $listeners) {
    $issues += "Nothing is listening on port $port. Start the server: python -m uvicorn src.main:app --host 0.0.0.0 --port $port"
} else {
    $addr = ($listeners | Select-Object -First 1).LocalAddress
    if ($addr -eq '127.0.0.1' -or $addr -eq '::1') {
        $issues += "Server is bound to $addr only. Restart with --host 0.0.0.0 so other devices can connect."
    } else {
        $ok += "Server is listening on $addr (OK for LAN)"
    }
}

# 2. Firewall rule for inbound TCP 8000
$rule = Get-NetFirewallRule -DisplayName "Polish Art Server (TCP 8000)" -ErrorAction SilentlyContinue
if (-not $rule -or ($rule.Enabled -eq $false)) {
    $issues += "No enabled firewall rule for inbound TCP $port. Run as Administrator: .\scripts\allow_firewall_port_8000.ps1"
} else {
    $ok += "Firewall rule 'Polish Art Server (TCP 8000)' exists and is enabled"
}

# 3. Wi-Fi IPv4 (for the URL to give others)
$wifi = Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "*Wi*" -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike "169.*" } | Select-Object -First 1
if ($wifi) {
    $lanUrl = "http://$($wifi.IPAddress):$port/"
    $ok += "LAN URL for other devices: $lanUrl"
} else {
    $issues += "Could not detect Wi-Fi IPv4. Run ipconfig and use the IPv4 Address under Wireless LAN adapter."
}

# 4. Local health check
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:$port/health" -UseBasicParsing -TimeoutSec 2
    $ok += "Server responds on localhost (status $($r.StatusCode))"
} catch {
    $issues += "Server did not respond at http://127.0.0.1:$port/health — is it running?"
}

# Report
Write-Host "`n--- LAN access check ---`n" -ForegroundColor Cyan
if ($ok.Count -gt 0) {
    foreach ($o in $ok) { Write-Host "  [OK] $o" -ForegroundColor Green }
}
if ($issues.Count -gt 0) {
    Write-Host ""
    foreach ($i in $issues) { Write-Host "  [!!] $i" -ForegroundColor Yellow }
    Write-Host ""
    exit 1
}
Write-Host "`nNo issues found. Other users should use the LAN URL above.`n" -ForegroundColor Green
exit 0
