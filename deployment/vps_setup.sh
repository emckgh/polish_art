#!/bin/bash
#
# Polish Art VPS Deployment Script
# Run this on a fresh Ubuntu/Debian VPS as root
#
# Usage: bash vps_setup.sh
#

set -e  # Exit on any error

DOMAIN="lostpolishart.mcqueeney.org"
APP_USER="polishart"
APP_DIR="/home/$APP_USER/polish_art"
REPO_URL="https://github.com/emckgh/polish_art.git"

echo "=========================================="
echo "Polish Art VPS Deployment"
echo "Domain: $DOMAIN"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "ERROR: Please run as root"
   exit 1
fi

echo "==> Step 1: Updating system..."
apt update
apt upgrade -y

echo ""
echo "==> Step 2: Installing dependencies..."
apt install -y python3 python3-venv python3-pip git nginx certbot python3-certbot-nginx

echo ""
echo "==> Step 3: Creating app user..."
if id "$APP_USER" &>/dev/null; then
    echo "User $APP_USER already exists, skipping..."
else
    adduser --disabled-password --gecos "" $APP_USER
    usermod -aG sudo $APP_USER
    echo "User $APP_USER created"
fi

echo ""
echo "==> Step 4: Setting up application..."
sudo -u $APP_USER bash << 'USERSCRIPT'
cd ~
if [ -d "polish_art" ]; then
    echo "Repository already exists, pulling latest..."
    cd polish_art
    git pull
else
    echo "Cloning repository..."
    git clone https://github.com/emckgh/polish_art.git
    cd polish_art
fi

echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Creating directories..."
mkdir -p data env

echo "Creating environment file..."
cat > env/.env << 'EOF'
DATABASE_URL=sqlite:////home/polishart/polish_art/data/artworks.db
READ_ONLY=true
EOF

echo "Application setup complete"
USERSCRIPT

echo ""
echo "==> Step 5: Creating systemd service..."
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

systemctl daemon-reload
systemctl enable polish-art
systemctl start polish-art

echo "Waiting for service to start..."
sleep 3

if systemctl is-active --quiet polish-art; then
    echo "✓ Service is running"
else
    echo "✗ Service failed to start. Check logs with: journalctl -u polish-art -n 50"
    exit 1
fi

echo ""
echo "==> Step 6: Configuring Nginx..."
cat > /etc/nginx/sites-available/polishart << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

if [ -L /etc/nginx/sites-enabled/polishart ]; then
    echo "Nginx site already enabled, skipping..."
else
    ln -s /etc/nginx/sites-available/polishart /etc/nginx/sites-enabled/
fi

nginx -t
systemctl restart nginx

echo ""
echo "==> Testing HTTP access..."
sleep 2
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ App is responding on port 8000"
else
    echo "✗ App is not responding (HTTP $HTTP_CODE)"
    exit 1
fi

echo ""
echo "=========================================="
echo "HTTPS Setup"
echo "=========================================="
echo ""
echo "Run this command to enable HTTPS:"
echo ""
echo "  certbot --nginx -d $DOMAIN"
echo ""
echo "Then sync your database from local machine:"
echo ""
echo "  scp data/server_export.db $APP_USER@$DOMAIN:polish_art/data/artworks.db"
echo "  ssh $APP_USER@$DOMAIN 'sudo systemctl restart polish-art'"
echo ""
echo "Or use the sync script:"
echo ""
echo "  .\\scripts\\sync_to_vps.ps1"
echo ""
echo "=========================================="
echo "✓ Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Run certbot command above"
echo "2. Sync database from local machine"
echo "3. Visit https://$DOMAIN/"
echo ""
