# Quick Deployment Guide for Polish Art Discovery Engine

This guide provides the **fastest path** to deploying your application to your VPS at **178.63.149.123**.

## Prerequisites

- ✅ VPS server: 178.63.149.123 (root access)
- ✅ Windows machine with PowerShell
- ✅ Git installed locally
- ⚠️ Domain: polishart.mcqueeney.org (optional, for HTTPS)

---

## Quick Start (3 Steps)

### Step 1: Set Up SSH Keys (2 minutes)

```powershell
cd C:\dev\polish_art
.\deployment\setup_ssh_key.ps1
```

**Follow the instructions** to add your public key to the server. Then test:

```powershell
ssh -i $env:USERPROFILE\.ssh\id_rsa root@178.63.149.123
```

If this works without a password, proceed to Step 2.

---

### Step 2: Deploy to Server (10-15 minutes)

**First-time deployment:**

```powershell
.\deployment\deploy.ps1 -FirstRun
```

This will:
- Install all system dependencies (Python, Nginx, PostgreSQL, Redis)
- Create dedicated user account
- Clone repository
- Install Python packages (including PyTorch)
- Configure systemd service
- Set up Nginx reverse proxy
- Configure firewall and security

**After completion, your app will be running at:**
- http://178.63.149.123 (via Nginx)
- http://178.63.149.123:8000 (direct)
- http://178.63.149.123/docs (API documentation)

---

### Step 3: Configure Application (5 minutes)

**Edit environment variables:**

```powershell
ssh -i $env:USERPROFILE\.ssh\id_rsa root@178.63.149.123
nano /opt/polish_art/.env
```

**Update these values:**
```ini
# Database password
DATABASE_URL=postgresql://polishart:YOUR_SECURE_PASSWORD@localhost/polishart_db

# Security key (generate with: openssl rand -hex 32)
SECRET_KEY=your_generated_secret_key_here

# CORS origins (add your domain)
CORS_ORIGINS=http://localhost,https://polishart.mcqueeney.org

# Google Vision API (if using)
GOOGLE_APPLICATION_CREDENTIALS=/opt/polish_art/google-credentials.json

# Enable/disable features
ENABLE_GOOGLE_VISION=false
ENABLE_COMPUTER_VISION=true
```

**Save and restart:**
```bash
sudo systemctl restart polish-art
sudo systemctl status polish-art
```

**Exit SSH:**
```bash
exit
```

---

## Optional: Domain & HTTPS Setup

### Configure DNS

Point your domain to the server:

**At Network Solutions (Dotster):**
1. Log in → Manage Domain → mcqueeney.org → DNS Management
2. Add A record:
   - Host: `polishart`
   - Points to: `178.63.149.123`
   - TTL: `3600`
3. Save and wait 5-30 minutes for propagation

**Verify DNS:**
```powershell
nslookup polishart.mcqueeney.org
```

### Install SSL Certificate

```powershell
.\deployment\setup_ssl.ps1 -Domain "polishart.mcqueeney.org" -Email "your@email.com"
```

**Your app is now at:** https://polishart.mcqueeney.org 🎉

---

## Deploying Updates

### Update Code Only

After pushing changes to GitHub:

```powershell
.\deployment\deploy.ps1
```

### Sync Database from Local

After making local data changes:

```powershell
.\deployment\deploy.ps1 -SyncDB
```

This will:
1. Build server export locally (with optional image culling)
2. Upload to VPS
3. Restart the application

---

## Monitoring & Maintenance

### View Logs

**Real-time logs:**
```powershell
ssh root@178.63.149.123 'sudo journalctl -u polish-art -f'
```

**Last 100 lines:**
```powershell
ssh root@178.63.149.123 'sudo journalctl -u polish-art -n 100'
```

### Service Management

```bash
# Check status
sudo systemctl status polish-art

# Restart
sudo systemctl restart polish-art

# Stop
sudo systemctl stop polish-art

# Start
sudo systemctl start polish-art
```

### Check Resources

```bash
# CPU and memory usage
htop

# Disk space
df -h

# Database size
du -sh /var/lib/polish_art/artworks.db

# Service memory
sudo systemctl status polish-art
```

---

## Troubleshooting

### Application Won't Start

**Check logs:**
```bash
sudo journalctl -u polish-art -n 50
```

**Common issues:**
- Missing `.env` file or API keys
- Python dependency errors
- Port 8000 already in use
- Database connection issues

**Solution:**
```bash
cd /opt/polish_art
sudo -u polishart .venv/bin/pip install -r requirements.txt
sudo systemctl restart polish-art
```

### Can't Connect to Server

**Check SSH:**
```powershell
ssh -v -i $env:USERPROFILE\.ssh\id_rsa root@178.63.149.123
```

**Check firewall:**
```bash
sudo ufw status
```

**Ensure ports are open:**
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)
- 8000 (API, optional)

### SSL Issues

**Check certificate:**
```bash
sudo certbot certificates
```

**Renew manually:**
```bash
sudo certbot renew --force-renewal
```

**Check Nginx:**
```bash
sudo nginx -t
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log
```

### Database Sync Fails

**Check local database exists:**
```powershell
ls data\artworks.db
```

**Rebuild local database:**
```powershell
python scripts\import_looted_art.py
```

**Check server disk space:**
```bash
df -h
```

---

## Architecture Overview

### Server Layout

```
/opt/polish_art/              # Application root
├── .venv/                    # Python virtual environment
├── src/                      # Application code
├── data/                     # SQLite database
├── static/                   # Frontend files
├── .env                      # Configuration (sensitive!)
└── requirements.txt          # Python dependencies

/etc/systemd/system/polish-art.service    # Systemd service
/etc/nginx/sites-available/polish-art     # Nginx config
/var/lib/polish_art/                      # Database storage
```

### Data Flow

**Local Machine (Your Windows PC):**
- Scraping scripts
- Data imports
- Vision API calls
- Database building

**VPS Server (178.63.149.123):**
- FastAPI web application
- Read-only database
- Public web interface
- API endpoints

**Sync Process:**
1. Build/update local database
2. Export server version (with optional culling)
3. Upload to VPS via rsync/scp
4. Restart application

---

## Security Best Practices

### Server Security

- ✅ SSH key authentication only (passwords disabled)
- ✅ Firewall (UFW) configured
- ✅ Fail2ban for brute force protection
- ✅ Automatic security updates enabled
- ✅ Non-root user for application
- ✅ Systemd security features (PrivateTmp, ProtectSystem)

### Application Security

- ✅ Read-only database on server
- ✅ CORS configured
- ✅ Rate limiting via Nginx
- ✅ Security headers (X-Frame-Options, etc.)
- ⚠️ Update SECRET_KEY in `.env`
- ⚠️ Use HTTPS in production

### Backup Strategy

**Backup these directories regularly:**

**On your local machine:**
- `data/artworks.db` - Main database
- `data/*.json` - Scraped data
- `.env` - Configuration

**On the server (optional):**
```bash
# Backup script
rsync -avz root@178.63.149.123:/opt/polish_art/data/ ./backups/server-$(date +%Y%m%d)/
```

---

## Cost Estimate

**VPS Server:**
- Current plan: PLAN 1TB at Hetzner (~$20-30/month)

**API Costs (if enabled):**
- Google Vision API: $1.50 per 1,000 images (first 1,000 free/month)
- Google Custom Search: Free tier (100 queries/day)

**Total: ~$30-50/month** (mostly server, minimal API costs)

---

## Support

**Deployment Issues:**
1. Check this README's Troubleshooting section
2. Review logs: `sudo journalctl -u polish-art -n 100`
3. Check main documentation: `docs/deploy-vps.md`

**Application Issues:**
1. Check main README: `README.md`
2. Review architecture: `docs/architecture.md`
3. Test locally first

---

## Quick Reference

**All deployment commands from C:\dev\polish_art:**

```powershell
# First time
.\deployment\setup_ssh_key.ps1                               # Step 1
.\deployment\deploy.ps1 -FirstRun                            # Step 2
ssh root@178.63.149.123 'nano /opt/polish_art/.env'         # Step 3

# Optional SSL
.\deployment\setup_ssl.ps1 -Domain "polishart.mcqueeney.org" -Email "your@email.com"

# Regular use
.\deployment\deploy.ps1                                      # Update code
.\deployment\deploy.ps1 -SyncDB                              # Sync database

# Monitoring
ssh root@178.63.149.123 'sudo journalctl -u polish-art -f'  # View logs
ssh root@178.63.149.123 'sudo systemctl status polish-art'  # Check status
```

---

**Ready to deploy?** Start with Step 1! 🚀
