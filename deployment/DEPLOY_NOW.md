# Deploy Now - Simple Instructions

DNS is configured ✓ (`lostpolishart.mcqueeney.org` → `178.63.149.123`)

## Step 1: SSH into VPS

```bash
ssh root@178.63.149.123
```

Password: `nPD3VWUPVX8FK4rKKjUS` (from `.deploy.yaml`)

---

## Step 2: Run Deployment Script

Copy and paste this entire block into your VPS terminal:

```bash
curl -sL https://raw.githubusercontent.com/emckgh/polish_art/master/deployment/vps_setup.sh | bash
```

**OR** if the file isn't on GitHub yet, manually copy the script:

```bash
cat > deploy.sh << 'SCRIPTEND'
#!/bin/bash
set -e
DOMAIN="lostpolishart.mcqueeney.org"
APP_USER="polishart"
REPO_URL="https://github.com/emckgh/polish_art.git"

echo "==> Updating system..."
apt update && apt upgrade -y

echo "==> Installing dependencies..."
apt install -y python3 python3-venv python3-pip git nginx certbot python3-certbot-nginx

echo "==> Creating user $APP_USER..."
if ! id "$APP_USER" &>/dev/null; then
    adduser --disabled-password --gecos "" $APP_USER
    usermod -aG sudo $APP_USER
fi

echo "==> Setting up application..."
sudo -u $APP_USER bash << 'EOF'
cd ~
if [ -d "polish_art" ]; then
    cd polish_art && git pull
else
    git clone https://github.com/emckgh/polish_art.git
    cd polish_art
fi
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
mkdir -p data env
cat > env/.env << 'ENVEOF'
DATABASE_URL=sqlite:////home/polishart/polish_art/data/artworks.db
READ_ONLY=true
ENVEOF
EOF

echo "==> Creating systemd service..."
cat > /etc/systemd/system/polish-art.service << 'SERVICEEOF'
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
SERVICEEOF

systemctl daemon-reload
systemctl enable polish-art
systemctl start polish-art
sleep 3
systemctl status polish-art --no-pager

echo "==> Configuring Nginx..."
cat > /etc/nginx/sites-available/polishart << 'NGINXEOF'
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
NGINXEOF

ln -sf /etc/nginx/sites-available/polishart /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

echo ""
echo "✓ Deployment complete! Next steps:"
echo "1. Enable HTTPS: certbot --nginx -d lostpolishart.mcqueeney.org"
echo "2. Sync database from local machine"
SCRIPTEND

chmod +x deploy.sh
./deploy.sh
```

---

## Step 3: Enable HTTPS

Still on the VPS, run:

```bash
certbot --nginx -d lostpolishart.mcqueeney.org
```

- Enter your email for renewal notifications
- Agree to terms: `Y`
- Redirect HTTP to HTTPS: `Yes` (or option 2)

**Test:** Open https://lostpolishart.mcqueeney.org/health (should show `{"status":"healthy"}`)

---

## Step 4: Sync Database

**Back on your local Windows machine:**

```powershell
cd c:\Dev\polish_art
.\.venv\Scripts\Activate.ps1

# Build server database
python scripts/build_and_sync_server_db.py --output data/server_export.db --strip-images-unless-include

# Transfer to VPS
scp data/server_export.db polishart@lostpolishart.mcqueeney.org:polish_art/data/artworks.db

# Restart service
ssh polishart@lostpolishart.mcqueeney.org 'sudo systemctl restart polish-art'
```

**OR use the sync script:**

```powershell
.\scripts\sync_to_vps.ps1
```

---

## Step 5: Verify

Open in browser:
- https://lostpolishart.mcqueeney.org/ (should show artwork list)
- https://lostpolishart.mcqueeney.org/health (should show `{"status":"healthy"}`)

✓ **Done!**

---

## Troubleshooting

**Service not running:**
```bash
ssh root@178.63.149.123
journalctl -u polish-art -n 50
```

**Check app directly:**
```bash
ssh root@178.63.149.123
curl http://127.0.0.1:8000/health
```

**Nginx errors:**
```bash
nginx -t
tail /var/log/nginx/error.log
```
