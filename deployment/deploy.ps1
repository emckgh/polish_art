# Deployment Script for Polish Looted Art Discovery Engine
# Deploys the application to a remote Linux VPS

param(
    [switch]$FirstRun,
    [switch]$UpdateOnly,
    [switch]$SyncDB
)

Write-Host "=== Polish Art Discovery Engine - Deployment ===" -ForegroundColor Cyan
Write-Host ""

# Load deployment configuration from .deploy.yaml
$deployConfigPath = Join-Path $PSScriptRoot "..\..deploy.yaml"
if (Test-Path $deployConfigPath) {
    $deployConfig = Get-Content $deployConfigPath | Select-String -Pattern "Server IP Address: ([\d\.]+)" | ForEach-Object { $_.Matches.Groups[1].Value }
    if ($deployConfig) {
        $serverIP = $deployConfig
    } else {
        $serverIP = "178.63.149.123"
    }
} else {
    $serverIP = "178.63.149.123"
}

$serverUser = "root"
$appUser = "polishart"
$appPath = "/opt/polish_art"
$domain = "polishart.mcqueeney.org"

$sshKeyPath = "$env:USERPROFILE\.ssh\id_rsa"

# Check SSH key exists
if (-not (Test-Path $sshKeyPath)) {
    Write-Host "ERROR: SSH key not found at $sshKeyPath" -ForegroundColor Red
    Write-Host "Run .\deployment\setup_ssh_key.ps1 first" -ForegroundColor Yellow
    exit 1
}

Write-Host "Connecting to server: $serverIP" -ForegroundColor Green
Write-Host ""

if ($FirstRun) {
    Write-Host "=== First-time server setup ===" -ForegroundColor Yellow
    Write-Host "This will:" -ForegroundColor White
    Write-Host "  - Update system packages" -ForegroundColor Gray
    Write-Host "  - Install Python, Nginx, PostgreSQL, Redis" -ForegroundColor Gray
    Write-Host "  - Create dedicated user account ($appUser)" -ForegroundColor Gray
    Write-Host "  - Configure firewall (UFW)" -ForegroundColor Gray
    Write-Host "  - Clone repository" -ForegroundColor Gray
    Write-Host "  - Set up Python virtual environment" -ForegroundColor Gray
    Write-Host "  - Create systemd service" -ForegroundColor Gray
    Write-Host "  - Configure Nginx reverse proxy" -ForegroundColor Gray
    Write-Host "  - Set up fail2ban security" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Duration: ~10-15 minutes" -ForegroundColor Yellow
    Write-Host ""
    $confirm = Read-Host "Continue? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "Deployment cancelled." -ForegroundColor Red
        exit
    }
    
    # Upload and run the server setup script
    Write-Host ""
    Write-Host "Uploading setup script..." -ForegroundColor Green
    scp -i $sshKeyPath .\deployment\server_setup.sh ${serverUser}@${serverIP}:/tmp/
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to upload setup script" -ForegroundColor Red
        Write-Host "Make sure you can SSH to the server: ssh -i $sshKeyPath $serverUser@$serverIP" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "Running server setup (this will take 10-15 minutes)..." -ForegroundColor Green
    Write-Host "Installing system packages, Python dependencies, and PyTorch..." -ForegroundColor Yellow
    Write-Host ""
    
    ssh -i $sshKeyPath ${serverUser}@${serverIP} "chmod +x /tmp/server_setup.sh && /tmp/server_setup.sh"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: Server setup failed" -ForegroundColor Red
        Write-Host "Check the error messages above for details" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host ""
    Write-Host "=== First-time setup complete! ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: Next steps:" -ForegroundColor Yellow
    Write-Host "1. Configure API keys and secrets:" -ForegroundColor White
    Write-Host "   ssh -i $sshKeyPath $serverUser@$serverIP 'nano $appPath/.env'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Test the application:" -ForegroundColor White
    Write-Host "   http://$serverIP" -ForegroundColor Gray
    Write-Host "   http://$serverIP/docs (API documentation)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Import initial data (from your local machine):" -ForegroundColor White
    Write-Host "   python scripts\import_looted_art.py" -ForegroundColor Gray
    Write-Host "   Then sync to server (see --SyncDB option)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Set up domain and SSL:" -ForegroundColor White
    Write-Host "   - Point $domain to $serverIP" -ForegroundColor Gray
    Write-Host "   - Run: .\deployment\setup_ssl.ps1 -Domain '$domain' -Email 'your@email.com'" -ForegroundColor Gray
    Write-Host ""
    exit 0
}

if ($SyncDB) {
    Write-Host "=== Database Sync ===" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Building server export..." -ForegroundColor Green
    
    # Build server export locally
    python scripts\build_and_sync_server_db.py --output data\server_export.db
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to build server export" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Uploading database to server..." -ForegroundColor Green
    scp -i $sshKeyPath data\server_export.db ${serverUser}@${serverIP}:${appPath}/data/artworks.db
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to upload database" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Restarting application..." -ForegroundColor Green
    ssh -i $sshKeyPath ${serverUser}@${serverIP} "sudo systemctl restart polish-art"
    
    Write-Host ""
    Write-Host "=== Database sync complete! ===" -ForegroundColor Green
    Write-Host ""
    exit 0
}

# Regular deployment/update
Write-Host "=== Deploying application updates ===" -ForegroundColor Green
Write-Host ""

$deployCommands = @"
# Navigate to app directory
cd $appPath || exit 1

# Pull latest changes
echo 'Pulling latest code...'
sudo -u $appUser git pull

# Update Python dependencies
echo 'Updating Python dependencies...'
sudo -u $appUser $appPath/.venv/bin/pip install -r requirements.txt

# Restart service
echo 'Restarting application...'
sudo systemctl restart polish-art

# Wait a moment for service to start
sleep 2

# Check service status
sudo systemctl status polish-art --no-pager

echo ''
echo '=== Deployment Complete ==='
"@

ssh -i $sshKeyPath ${serverUser}@${serverIP} $deployCommands

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "WARNING: Deployment may have issues" -ForegroundColor Yellow
    Write-Host "Check the logs: ssh $serverUser@$serverIP 'sudo journalctl -u polish-art -n 50'" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=== Deployment Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Application is running at:" -ForegroundColor Cyan
Write-Host "  http://$serverIP" -ForegroundColor Yellow
Write-Host "  http://$serverIP/docs (API docs)" -ForegroundColor Yellow
if ($domain -ne "polishart.mcqueeney.org") {
    Write-Host "  https://$domain (if SSL configured)" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "View logs: ssh $serverUser@$serverIP 'sudo journalctl -u polish-art -f'" -ForegroundColor Cyan
