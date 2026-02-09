# SSL/HTTPS Setup for Polish Art Deployment
# Configures domain and Let's Encrypt SSL certificate

param(
    [Parameter(Mandatory=$true)]
    [string]$Domain,
    
    [Parameter(Mandatory=$true)]
    [string]$Email
)

Write-Host "=== SSL Setup for Polish Art ===" -ForegroundColor Cyan
Write-Host ""

$serverIP = "178.63.149.123"
$serverUser = "root"
$appPath = "/opt/polish_art"

$sshKeyPath = "$env:USERPROFILE\.ssh\id_rsa"

# Check SSH key exists
if (-not (Test-Path $sshKeyPath)) {
    Write-Host "ERROR: SSH key not found at $sshKeyPath" -ForegroundColor Red
    exit 1
}

Write-Host "Setting up SSL for: $Domain" -ForegroundColor Green
Write-Host "Certificate email: $Email" -ForegroundColor Green
Write-Host ""

# Check DNS propagation
Write-Host "Checking DNS configuration..." -ForegroundColor Yellow
try {
    $dnsResult = Resolve-DnsName $Domain -ErrorAction Stop
    $resolvedIP = $dnsResult | Where-Object { $_.Type -eq "A" } | Select-Object -First 1 -ExpandProperty IPAddress
    
    if ($resolvedIP -eq $serverIP) {
        Write-Host "✓ DNS is correctly configured ($Domain → $serverIP)" -ForegroundColor Green
    } else {
        Write-Host "WARNING: DNS points to $resolvedIP but server is at $serverIP" -ForegroundColor Yellow
        Write-Host "SSL setup may fail. Continue anyway? (Y/N)" -ForegroundColor Yellow
        $response = Read-Host
        if ($response -ne "Y" -and $response -ne "y") {
            Write-Host "SSL setup cancelled." -ForegroundColor Red
            exit
        }
    }
} catch {
    Write-Host "WARNING: Could not resolve $Domain" -ForegroundColor Yellow
    Write-Host "Make sure DNS is configured before proceeding." -ForegroundColor Yellow
    Write-Host "Continue anyway? (Y/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -ne "Y" -and $response -ne "y") {
        Write-Host "SSL setup cancelled." -ForegroundColor Red
        exit
    }
}

Write-Host ""
Write-Host "Configuring server..." -ForegroundColor Green

$sslSetupCommands = @"
# Update Nginx configuration with domain
echo 'Updating Nginx configuration...'
sed -i 's/server_name _;/server_name $Domain;/' /etc/nginx/sites-available/polish-art
nginx -t || exit 1
systemctl reload nginx

# Install SSL certificate with Certbot
echo 'Installing SSL certificate...'
certbot --nginx -d $Domain --non-interactive --agree-tos --email $Email --redirect

# Verify certificate
certbot certificates

echo ''
echo '=== SSL Setup Complete ==='
echo 'Your application is now at: https://$Domain'
"@

ssh -i $sshKeyPath ${serverUser}@${serverIP} $sslSetupCommands

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== SSL Setup Complete! ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your application is now accessible at:" -ForegroundColor Cyan
    Write-Host "  https://$Domain" -ForegroundColor Yellow
    Write-Host "  https://$Domain/docs (API documentation)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Certificate will auto-renew. Test renewal:" -ForegroundColor Green
    Write-Host "  ssh $serverUser@$serverIP 'sudo certbot renew --dry-run'" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "ERROR: SSL setup failed" -ForegroundColor Red
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - DNS not properly configured" -ForegroundColor Gray
    Write-Host "  - Port 80/443 not accessible" -ForegroundColor Gray
    Write-Host "  - Firewall blocking Let's Encrypt" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Check server logs: ssh $serverUser@$serverIP 'sudo tail -f /var/log/letsencrypt/letsencrypt.log'" -ForegroundColor Yellow
}
