# SSH Key Setup for Polish Art Deployment
# Generates SSH key and helps you add it to your server

Write-Host "=== SSH Key Setup for Polish Art VPS ===" -ForegroundColor Cyan
Write-Host ""

$sshDir = "$env:USERPROFILE\.ssh"
$keyPath = "$sshDir\id_rsa"
$pubKeyPath = "$sshDir\id_rsa.pub"

# Create .ssh directory if it doesn't exist
if (-not (Test-Path $sshDir)) {
    Write-Host "Creating .ssh directory..." -ForegroundColor Green
    New-Item -ItemType Directory -Path $sshDir | Out-Null
}

# Check if SSH key already exists
if (Test-Path $keyPath) {
    Write-Host "SSH key already exists at: $keyPath" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Do you want to use the existing key? (Y/N)"
    if ($response -ne "Y" -and $response -ne "y") {
        Write-Host "Please backup your existing key and delete it, then run this script again." -ForegroundColor Red
        exit
    }
} else {
    Write-Host "Generating new SSH key..." -ForegroundColor Green
    ssh-keygen -t rsa -b 4096 -f $keyPath -N '""'
    Write-Host "SSH key generated successfully!" -ForegroundColor Green
    Write-Host ""
}

# Display public key
Write-Host "=== Your Public Key ===" -ForegroundColor Cyan
Write-Host ""
$pubKey = Get-Content $pubKeyPath
Write-Host $pubKey -ForegroundColor Yellow
Write-Host ""

# Instructions
Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Copy the public key above and add it to your server:" -ForegroundColor Green
Write-Host ""
Write-Host "Method 1: Using ssh-copy-id (if available)" -ForegroundColor White
Write-Host "  ssh-copy-id -i $pubKeyPath root@178.63.149.123" -ForegroundColor Gray
Write-Host ""
Write-Host "Method 2: Manually" -ForegroundColor White
Write-Host "  1. SSH into your server:" -ForegroundColor Gray
Write-Host "     ssh root@178.63.149.123" -ForegroundColor Gray
Write-Host "  2. Create .ssh directory:" -ForegroundColor Gray
Write-Host "     mkdir -p ~/.ssh && chmod 700 ~/.ssh" -ForegroundColor Gray
Write-Host "  3. Add your public key:" -ForegroundColor Gray
Write-Host "     echo '$pubKey' >> ~/.ssh/authorized_keys" -ForegroundColor Gray
Write-Host "  4. Set permissions:" -ForegroundColor Gray
Write-Host "     chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Gray
Write-Host ""
Write-Host "After adding the key, test the connection:" -ForegroundColor Green
Write-Host "  ssh -i $keyPath root@178.63.149.123" -ForegroundColor Yellow
Write-Host ""
Write-Host "If the connection works without a password, you're ready for deployment!" -ForegroundColor Green
