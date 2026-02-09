#!/bin/bash
# Server Setup Script for Polish Looted Art Discovery Engine
# This runs on the remote Linux server

set -e  # Exit on error

echo "=== Server Setup for Polish Art Discovery Engine ==="
echo ""

# Configuration
APP_USER="polishart"
APP_PATH="/opt/polish_art"
PYTHON_VERSION="3.11"
DB_PATH="/var/lib/polish_art"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Step 1: Update system packages${NC}"
apt-get update
apt-get upgrade -y

echo ""
echo -e "${GREEN}Step 2: Install system dependencies${NC}"
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    nginx \
    ufw \
    certbot \
    python3-certbot-nginx \
    fail2ban \
    unattended-upgrades \
    redis-server \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    build-essential \
    cmake \
    libopencv-dev \
    python3-opencv \
    tesseract-ocr \
    libtesseract-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgl1-mesa-glx

echo ""
echo -e "${GREEN}Step 3: Configure PostgreSQL${NC}"
sudo -u postgres psql -c "CREATE USER polishart WITH PASSWORD 'secure_password_change_me';" || true
sudo -u postgres psql -c "CREATE DATABASE polishart_db OWNER polishart;" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE polishart_db TO polishart;"

echo ""
echo -e "${GREEN}Step 4: Configure Redis${NC}"
systemctl enable redis-server
systemctl start redis-server
# Secure Redis
echo "bind 127.0.0.1" >> /etc/redis/redis.conf
systemctl restart redis-server

echo ""
echo -e "${GREEN}Step 5: Create dedicated user account${NC}"
if id "$APP_USER" &>/dev/null; then
    echo "User $APP_USER already exists"
else
    useradd -m -s /bin/bash $APP_USER
    echo "Created user: $APP_USER"
fi

echo ""
echo -e "${GREEN}Step 6: Create data directories${NC}"
mkdir -p $DB_PATH
chown $APP_USER:$APP_USER $DB_PATH
chmod 750 $DB_PATH

echo ""
echo -e "${GREEN}Step 7: Configure firewall${NC}"
# Reset firewall
ufw --force reset

# Allow SSH, HTTP, HTTPS, API
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp  # FastAPI (for testing)

# Enable firewall
ufw --force enable
ufw status

echo ""
echo -e "${GREEN}Step 8: Clone repository${NC}"
if [ -d "$APP_PATH" ]; then
    echo "Directory $APP_PATH already exists"
    cd $APP_PATH
    sudo -u $APP_USER git pull
else
    mkdir -p $APP_PATH
    cd $APP_PATH
    sudo -u $APP_USER git clone https://github.com/emckgh/polish_art.git .  # Update with your repo URL
fi

echo ""
echo -e "${GREEN}Step 9: Set up Python virtual environment${NC}"
sudo -u $APP_USER python3 -m venv $APP_PATH/.venv
sudo -u $APP_USER $APP_PATH/.venv/bin/pip install --upgrade pip wheel setuptools
echo "Installing dependencies (this may take 10-15 minutes for PyTorch)..."
sudo -u $APP_USER $APP_PATH/.venv/bin/pip install -r $APP_PATH/requirements.txt

echo ""
echo -e "${GREEN}Step 10: Create .env file${NC}"
if [ ! -f "$APP_PATH/.env" ]; then
    echo "Creating .env file..."
    cat > $APP_PATH/.env << 'EOL'
# Database Configuration
DATABASE_URL=postgresql://polishart:secure_password_change_me@localhost/polishart_db
SQLITE_DB_PATH=/var/lib/polish_art/artworks.db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Google Vision API (if used)
GOOGLE_APPLICATION_CREDENTIALS=/opt/polish_art/google-credentials.json

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=52428800  # 50MB

# Security
SECRET_KEY=generate_a_secure_random_key_here
CORS_ORIGINS=http://localhost,https://your-domain.com

# Feature Flags
ENABLE_COMPUTER_VISION=true
ENABLE_GOOGLE_VISION=false
ENABLE_CACHING=true
EOL
    chown $APP_USER:$APP_USER $APP_PATH/.env
    chmod 600 $APP_PATH/.env
    echo -e "${YELLOW}IMPORTANT: Edit $APP_PATH/.env and update passwords/keys!${NC}"
else
    echo ".env file already exists"
fi

echo ""
echo -e "${GREEN}Step 11: Initialize database${NC}"
sudo -u $APP_USER $APP_PATH/.venv/bin/python -c "from src.repositories.sqlite_repository import SQLiteRepository; SQLiteRepository('/var/lib/polish_art/artworks.db')" || true

echo ""
echo -e "${GREEN}Step 12: Create systemd service${NC}"
cat > /etc/systemd/system/polish-art.service << EOL
[Unit]
Description=Polish Looted Art Discovery Engine
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_PATH
Environment="PATH=$APP_PATH/.venv/bin"
Environment="PYTHONPATH=$APP_PATH"
ExecStart=$APP_PATH/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DB_PATH

# Resource limits
LimitNOFILE=65536
MemoryMax=2G

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
systemctl enable polish-art
systemctl start polish-art

echo ""
echo -e "${GREEN}Step 13: Configure Nginx reverse proxy${NC}"
cat > /etc/nginx/sites-available/polish-art << 'EOL'
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

upstream polish_art_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name _;  # Replace with your domain
    
    client_max_body_size 50M;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # API endpoints
    location /api {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://polish_art_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running CV operations
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }
    
    # Static files
    location /static {
        alias /opt/polish_art/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Root and other paths
    location / {
        proxy_pass http://polish_art_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOL

# Enable site
ln -sf /etc/nginx/sites-available/polish-art /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
nginx -t
systemctl restart nginx

echo ""
echo -e "${GREEN}Step 14: Configure fail2ban${NC}"
cat > /etc/fail2ban/jail.local << 'EOL'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
EOL

systemctl enable fail2ban
systemctl restart fail2ban

echo ""
echo -e "${GREEN}Step 15: Disable password authentication (SSH keys only)${NC}"
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "1. Edit $APP_PATH/.env and update passwords/keys"
echo "2. Point your domain to this server's IP"
echo "3. Run SSL setup: certbot --nginx -d your-domain.com"
echo "4. Import initial data: cd $APP_PATH && .venv/bin/python scripts/import_looted_art.py"
echo ""
echo "Service status:"
systemctl status polish-art --no-pager
echo ""
echo "Access the application at:"
echo "  - Direct: http://$(curl -s ifconfig.me):8000"
echo "  - Via Nginx: http://$(curl -s ifconfig.me)"
echo "  - API docs: http://$(curl -s ifconfig.me)/docs"
echo ""
echo -e "${YELLOW}IMPORTANT: Configure passwords and keys in $APP_PATH/.env${NC}"
