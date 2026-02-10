# Deploying to your own VPS (polishart.mcqueeney.org)

The app runs on your VPS as a **read-only** web server: it serves the UI and API from a synced SQLite database. All data updates (imports, Google Image Search, Vision API, etc.) run on your local machine; you periodically build a server export and sync it to the VPS.

---

## 1. DNS: polishart.mcqueeney.org → VPS

You host **mcqueeney.org** at Network Solutions (Dotster). Point the subdomain to your VPS IP.

**Steps (manual at Network Solutions):**

1. Log in to Network Solutions → **Manage Account** → **Domain Management** → select **mcqueeney.org** → **DNS** / **Advanced DNS** (or “Manage DNS”).
2. Add an **A** record:
   - **Host:** `polishart` (or whatever the UI uses for the subdomain; often just the subdomain name).
   - **Value / Points to:** your VPS public IPv4 address.
   - **TTL:** 300 for initial testing, then 3600.
3. Optional: add a **CNAME** for `www.polishart` → `polishart.mcqueeney.org` if you want www.
4. Save. Propagation is usually 5–30 minutes; can take up to 48 hours.

**On the VPS:** Configure the reverse proxy (Nginx or Caddy) with `server_name polishart.mcqueeney.org` so it accepts requests for this host (see Section 5).

---

## 2. One-time VPS setup

### 2.1 User and directory

Create a dedicated user (or use your own):

```bash
sudo adduser polishart
sudo su - polishart
```

App and repo will live under e.g. `/home/polishart/polish_art`.

### 2.2 Clone the repo

```bash
cd ~
git clone https://github.com/YOUR_USER/polish_art.git
cd polish_art
```

If the repo is private, use a deploy key or personal access token for cloning.

### 2.3 Python and virtualenv

```bash
python3 --version   # need 3.10+
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

For a **read-only** server you can use a slimmer install (no torch/CLIP) if you add a `requirements-web.txt`; otherwise the full `requirements.txt` is fine.

### 2.4 Environment variables

```bash
cp env/.env.example env/.env
```

Edit `env/.env` and set at least:

| Variable        | Example value |
|-----------------|----------------|
| `DATABASE_URL`  | `sqlite:////home/polishart/polish_art/data/artworks.db` |
| `READ_ONLY`     | `true` |

Use the **absolute path** to the synced DB file on the VPS. Four slashes in `sqlite:////` are correct for an absolute path. `READ_ONLY=true` opens SQLite in read-only mode and skips schema creation.

### 2.5 Data directory

```bash
mkdir -p data
# The artworks.db file is uploaded via rsync from your local machine (see Section 6).
```

---

## 3. Process manager (systemd)

Run uvicorn under systemd so it restarts on failure and on reboot.

Create a unit file, e.g. `/etc/systemd/system/polish-art.service`:

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

Adjust paths if your app lives elsewhere. Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable polish-art
sudo systemctl start polish-art
sudo systemctl status polish-art
```

---

## 4. Reverse proxy (Nginx or Caddy)

Run a reverse proxy in front of uvicorn so you can serve TLS (HTTPS) and optionally offload static files.

### Nginx (example)

Install Nginx, then add a server block for `polishart.mcqueeney.org`:

```nginx
server {
    listen 80;
    server_name polishart.mcqueeney.org;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then enable TLS with Let’s Encrypt (e.g. `certbot --nginx -d polishart.mcqueeney.org`).

### Caddy (example)

Caddy can obtain TLS certificates automatically:

```
polishart.mcqueeney.org {
    reverse_proxy 127.0.0.1:8000
}
```

---

## 5. Deploying code updates (Option A – manual)

From your local machine, to update the app on the VPS:

1. Push changes to GitHub: `git push`
2. SSH to the VPS and update the app:

   ```bash
   ssh polishart@YOUR_VPS_IP
   cd polish_art
   git pull
   source venv/bin/activate
   pip install -r requirements.txt
   sudo systemctl restart polish-art
   ```

---

## 6. Deploy script (Option B – one-liner)

A script on the VPS can do the same steps. From your **local** machine you run:

```bash
ssh polishart@YOUR_VPS_IP 'cd polish_art && ./scripts/deploy_vps.sh'
```

The script `scripts/deploy_vps.sh` (in the repo) runs: `git pull`, `pip install -r requirements.txt`, and restarts the systemd service. See the script for the exact service name and whether it uses `sudo`.

---

## 7. Database sync (local → VPS)

The database is **built and synced from your local machine**; the VPS only reads it.

### 7.1 Build server export locally

On your LAN machine, from the project root:

```bash
# Optional: add include_image_on_server column to your local DB (one-time) for per-artwork culling
python scripts/migrate_add_include_image_on_server.py

python scripts/build_and_sync_server_db.py --output data/server_export.db
```

Options (see script help) control culling: which artworks to include, whether to include `image_data` (by policy or column `include_image_on_server`), and whether to include vision detail tables. The script writes a single SQLite file (e.g. `data/server_export.db`).

### 7.2 Transfer to VPS

From your local machine:

```bash
rsync -avz data/server_export.db polishart@YOUR_VPS_IP:polish_art/data/artworks.db
```

Or with scp:

```bash
scp data/server_export.db polishart@YOUR_VPS_IP:polish_art/data/artworks.db
```

### 7.3 Restart the app on the VPS

So the app picks up the new file:

```bash
ssh polishart@YOUR_VPS_IP 'sudo systemctl restart polish-art'
```

You can combine 7.1–7.3 into a local script or run them after each sync.

---

## 8. Maintenance

- **Code:** Push to GitHub, then on the VPS run Option A or B (pull, pip install, restart).
- **Data:** Build server export locally, rsync to VPS `data/artworks.db`, restart the app.
- **Logs:** `sudo journalctl -u polish-art -f`
- **No writes on VPS:** Do not run import, scraping, or Vision API on the VPS; run them locally and sync the DB.
