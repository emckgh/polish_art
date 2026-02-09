# VPS Deployment Checklist for lostpolishart.mcqueeney.org

Use this checklist for deployment. Commands assume Ubuntu/Debian VPS.

---

## Pre-Deployment (Local Machine)

- [ ] Code pushed to GitHub: `git push`
- [ ] VPS IP address known: ________________
- [ ] SSH access verified: `ssh root@YOUR_VPS_IP` works
- [ ] Domain DNS configured (lostpolishart.mcqueeney.org → VPS IP)

---

## VPS Setup (One-Time)

**SSH into VPS:**
```bash
ssh root@YOUR_VPS_IP
```

### 1. Create User and Install Dependencies

```bash
# Create user
sudo adduser polishart
sudo usermod -aG sudo polishart

# Install packages
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx certbot python3-certbot-nginx

# Switch to app user
sudo su - polishart
cd ~
```

### 2. Clone Repository

```bash
git clone https://github.com/emckgh/polish_art.git
cd polish_art
```

### 3. Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir -p data env
```

### 4. Environment Configuration

```bash
nano env/.env
```

**Paste and modify:**
```
DATABASE_URL=sqlite:////home/polishart/polish_art/data/artworks.db
READ_ONLY=true
```

Save (Ctrl+O, Enter, Ctrl+X)

### 5. Systemd Service

```bash
exit  # Back to root/sudo user
sudo nano /etc/systemd/system/polish-art.service
```

**Paste:**
```ini
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
```

Save and enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable polish-art
sudo systemctl start polish-art
sudo systemctl status polish-art
```

**Expected:** Status shows "active (running)"

### 6. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/polishart
```

**Paste:**
```nginx
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
```

Enable and test:
```bash
sudo ln -s /etc/nginx/sites-available/polishart /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Test:** Open `http://lostpolishart.mcqueeney.org` in browser (should work, no HTTPS yet)

### 7. HTTPS Certificate

```bash
sudo certbot --nginx -d lostpolishart.mcqueeney.org
```

Follow prompts, choose redirect HTTP → HTTPS.

**Test:** Open `https://lostpolishart.mcqueeney.org` (should work with valid certificate)

---

## Database Sync (From Local Machine)

### First Sync

**On local Windows machine:**
```powershell
cd c:\Dev\polish_art
.\.venv\Scripts\Activate.ps1

# Build server export
python scripts/build_and_sync_server_db.py --output data/server_export.db --strip-images-unless-include

# Transfer to VPS (replace YOUR_VPS_IP)
scp data/server_export.db polishart@YOUR_VPS_IP:polish_art/data/artworks.db

# Restart app
ssh polishart@YOUR_VPS_IP 'sudo systemctl restart polish-art'
```

**Test:** Open `https://lostpolishart.mcqueeney.org/` - should show artwork list

---

## Verification

- [ ] `https://lostpolishart.mcqueeney.org/` loads main page
- [ ] `https://lostpolishart.mcqueeney.org/health` returns `{"status":"healthy"}`
- [ ] `https://lostpolishart.mcqueeney.org/api/artworks?page=1&page_size=5` returns JSON
- [ ] SSL certificate shows valid (green lock in browser)
- [ ] `ssh polishart@YOUR_VPS_IP 'sudo systemctl status polish-art'` shows running

---

## Future Updates

**Update code:**
```bash
# Local: git push
# VPS:
ssh polishart@YOUR_VPS_IP
cd polish_art
git pull
source venv/bin/activate
pip install -r requirements.txt
exit
sudo systemctl restart polish-art
```

**Update database:**
```powershell
# Local:
python scripts/build_and_sync_server_db.py --output data/server_export.db
scp data/server_export.db polishart@YOUR_VPS_IP:polish_art/data/artworks.db
ssh polishart@YOUR_VPS_IP 'sudo systemctl restart polish-art'
```

---

## Troubleshooting

**Service won't start:**
```bash
sudo journalctl -u polish-art -n 50
```

**Nginx errors:**
```bash
sudo nginx -t
sudo tail /var/log/nginx/error.log
```

**Check if app is listening:**
```bash
curl http://127.0.0.1:8000/health
```

Should return: `{"status":"healthy"}`
