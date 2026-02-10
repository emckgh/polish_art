# Allow inbound TCP 8000 for Polish Art server (run as Administrator).
# Usage: Right-click PowerShell -> Run as Administrator, then:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
#   .\scripts\allow_firewall_port_8000.ps1

$ruleName = "Polish Art Server (TCP 8000)"
$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Rule '$ruleName' already exists. Remove it first if you need to recreate: Remove-NetFirewallRule -DisplayName '$ruleName'"
    exit 0
}

New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
Write-Host "Added firewall rule: $ruleName. You can now access the server from other devices at http://YOUR_IP:8000/"
