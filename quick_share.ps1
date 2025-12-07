# Quick Cloudflare Tunnel Setup for One-Time Sharing
# This creates a temporary public URL for your Polish Art Database

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Polish Art Database - Quick Share via Cloudflare" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if cloudflared is installed
Write-Host "Checking for cloudflared..." -ForegroundColor Yellow
$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue

if (-not $cloudflared) {
    Write-Host "cloudflared not found. Installing..." -ForegroundColor Yellow
    Write-Host ""
    
    # Try winget first
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "Installing via winget..." -ForegroundColor Green
        winget install --id Cloudflare.cloudflared --silent
    } else {
        Write-Host "Please install cloudflared manually:" -ForegroundColor Red
        Write-Host "1. Download from: https://github.com/cloudflare/cloudflared/releases" -ForegroundColor White
        Write-Host "2. Or run: winget install Cloudflare.cloudflared" -ForegroundColor White
        exit 1
    }
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "Installation complete!" -ForegroundColor Green
    Write-Host ""
}

Write-Host "Starting FastAPI server on port 8000..." -ForegroundColor Yellow
$serverJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    python -m uvicorn main:app --host 0.0.0.0 --port 8000
}

# Wait for server to start
Write-Host "Waiting for server to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Check if server is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/artworks?page=1&page_size=1" -UseBasicParsing -ErrorAction Stop
    Write-Host "[OK] Server is running!" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Server failed to start. Check for errors above." -ForegroundColor Red
    Stop-Job -Job $serverJob
    Remove-Job -Job $serverJob
    exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Creating Cloudflare Tunnel..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your site will be accessible via a public HTTPS URL" -ForegroundColor White
Write-Host "This URL is temporary and will expire when you close this window" -ForegroundColor Yellow
Write-Host ""
Write-Host "Starting tunnel (this may take 10-15 seconds)..." -ForegroundColor Yellow
Write-Host ""

# Start cloudflare tunnel
try {
    cloudflared tunnel --url http://localhost:8000
} finally {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "  Cleaning up..." -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Stop the server
    Stop-Job -Job $serverJob -ErrorAction SilentlyContinue
    Remove-Job -Job $serverJob -ErrorAction SilentlyContinue
    
    Write-Host "Server stopped. Tunnel closed." -ForegroundColor Green
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
