# Quick Deployment Guide

**VPS Details:**
- Host: `178.63.149.123`
- Domain: `lostpolishart.mcqueeney.org` (configure DNS to point to this IP)
- User: `root` (will create `polishart` user during setup)

---

## Step 1: SSH Access Test

```powershell
ssh root@178.63.149.123
```

Password: *(from `.deploy.yaml`)*

If this works, proceed to Step 2.

---

## Step 2: Initial VPS Setup

**Run these commands on the VPS (after SSH):**

```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3 python3-venv python3-pip git nginx certbot python3-certbot-nginx

# Create app user
adduser polishart
# (Press Enter through prompts, or set a password)
usermod -aG sudo polishart

# Switch to app user
su - polishart
cd ~

# Clone repository (it will prompt for GitHub credentials if private)
git clone https://github.com/emckgh/polish_art.git
cd polish_art

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data env

# Create environment file
cat > env/.env << 'EOF'
DATABASE_URL=sqlite:////home/polishart/polish_art/data/artworks.db
READ_ONLY=true
EOF

# Exit back to root
exit
```

---

## Step 3: Create Systemd Service

**Still on VPS as root:**

```bash
cat > /etc/systemd/system/polish-art.service << 'EOF'
[Unit]
Description=Polish Art FastAPI
After=network.target

[Service]
User=polishart
WorkingDirectory=/home/polishart/polish_art
EnvironmentFile=/home/polishart/polish_art/env/.env
ExecStart=/home/polishart/polish_art/venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable polish-art
systemctl start polish-art
systemctl status polish-art
```

**Expected:** Status shows "active (running)" in green.

---

## Step 4: Configure Nginx

```bash
cat > /etc/nginx/sites-available/polishart << 'EOF'
server {
    listen 80;
    server_name lostpolishart.mcqueeney.org;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/polishart /etc/nginx/sites-enabled/

# Test and restart
nginx -t
systemctl restart nginx
```

**Test:** Open `http://178.63.149.123/health` in browser - should show `{"status":"healthy"}`

---

## Step 5: Configure DNS (Before HTTPS)

**In your DNS provider (for mcqueeney.org domain):**

Add an A record:
- Name: `lostpolishart`
- Type: `A`
- Value: `178.63.149.123`
- TTL: `300` (or default)

Wait 5-10 minutes for DNS propagation.

**Test:** `ping lostpolishart.mcqueeney.org` should resolve to `178.63.149.123`

---

## Step 6: Enable HTTPS

**Once DNS is working:**

```bash
certbot --nginx -d lostpolishart.mcqueeney.org
```

Follow prompts:
- Enter email for renewal notifications
- Agree to terms
- Choose: **Yes** to redirect HTTP to HTTPS

**Test:** Open `https://lostpolishart.mcqueeney.org/health` - should show green lock

---

## Step 7: Transfer Database

**On your local Windows machine:**

```powershell
cd c:\Dev\polish_art
.\.venv\Scripts\Activate.ps1

# Build server database (strips large images)
python scripts/build_and_sync_server_db.py --output data/server_export.db --strip-images-unless-include

# Transfer to VPS
scp data/server_export.db polishart@178.63.149.123:polish_art/data/artworks.db

# Restart service
ssh polishart@178.63.149.123 'sudo systemctl restart polish-art'
```

**Test:** Open `https://lostpolishart.mcqueeney.org/` - should show artwork list

---

## Verification Checklist

- [ ] `https://lostpolishart.mcqueeney.org/` loads main page with artworks
- [ ] `https://lostpolishart.mcqueeney.org/health` returns `{"status":"healthy"}`
- [ ] SSL shows green lock (valid certificate)
- [ ] `ssh polishart@178.63.149.123 'sudo systemctl status polish-art'` shows "active (running)"

---

## Future Updates

**Update code:**
```bash
# Local: git push
# VPS:
ssh polishart@178.63.149.123
su - polishart
cd polish_art
git pull
source venv/bin/activate
pip install -r requirements.txt
exit
sudo systemctl restart polish-art
exit
```

**Update database (from local machine):**
```powershell
.\scripts\sync_to_vps.ps1 polishart@178.63.149.123
```

---

## Troubleshooting

**Service not starting:**
```bash
ssh root@178.63.149.123
journalctl -u polish-art -n 50
```

**Check app directly:**
```bash
ssh polishart@178.63.149.123
curl http://127.0.0.1:8000/health
```

**Nginx issues:**
```bash
ssh root@178.63.149.123
nginx -t
tail /var/log/nginx/error.log
```
