# Polish Looted Art Finder — System Spec

*Reflects actual implemented state as of April 2026.*

---

## 1. Mission

Automate the continuous surveillance of auction houses, galleries, and online marketplaces for potential matches to looted Polish artworks. The system combines Google Cloud Vision API reverse image search, web scraping, and computer vision similarity matching to surface leads for human curator review.

**Operational target:** One curator, 30–60 minutes/day, reviewing machine-filtered findings.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────┐
│  LOCAL MACHINE (Windows)                            │
│                                                     │
│  data/artworks.db  ◄──  Scrapers, Vision API,       │
│                         CV pipeline, imports         │
│        │                                            │
│   sync_to_vps.ps1 (scp + systemctl restart)         │
└────────────────┬────────────────────────────────────┘
                 │ scp artworks.db
                 ▼
┌─────────────────────────────────────────────────────┐
│  VPS  (178.63.149.123)                              │
│                                                     │
│  Caddy (TLS, reverse proxy)                         │
│    ├── lostpolishart.mcqueeney.org → :PORT (app)    │
│    └── golfpool.mcqueeney.org      → :8001          │
│                                                     │
│  uvicorn / FastAPI  (polish-art.service)            │
│    └── data/artworks.db  (read-only SQLite)         │
└─────────────────────────────────────────────────────┘
```

**Key design principle:** The VPS is read-only. All data work (scraping, Vision API, CV feature extraction, imports) runs locally. The DB is built and synced to the server on demand.

---

## 3. Server Infrastructure

### 3.1 VPS

| Property | Value |
|---|---|
| IP | 178.63.149.123 |
| SSH user | `polishart` |
| Hostname | `lostpolishart.mcqueeney.org` |
| App directory | `/home/polishart/polish_art/` |
| Python venv | `/home/polishart/polish_art/venv/` |
| Database (server) | `/home/polishart/polish_art/data/artworks.db` |
| Caddy config | `/etc/caddy/Caddyfile` |
| Systemd unit | `polish-art.service` |

### 3.2 Systemd Service

Unit: `/etc/systemd/system/polish-art.service`

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

Override (`/etc/systemd/system/polish-art.service.d/override.conf`) — applied 2026-04-18:

```ini
[Service]
Restart=always
RestartSec=5
```

Service is `enabled` (survives reboots) and configured to auto-restart within 5 seconds on crash.

### 3.3 Caddy (Reverse Proxy)

Caddy provides automatic TLS via Let's Encrypt and routes traffic to multiple apps on the same VPS.

Current `/etc/caddy/Caddyfile`:

```
golfpool.mcqueeney.org {
    reverse_proxy 127.0.0.1:8001
}
```

Entry for `lostpolishart.mcqueeney.org` added 2026-04-18. Current Caddyfile:

```
golfpool.mcqueeney.org {
    reverse_proxy 127.0.0.1:8001
}

lostpolishart.mcqueeney.org {
    reverse_proxy 127.0.0.1:8000
}
```

### 3.4 VPS Sizing

| Resource | Current minimum | Notes |
|---|---|---|
| vCPU | 1 | One uvicorn worker is enough for single-user load |
| RAM | 1 GB | OS ~250 MB + Python/uvicorn ~200 MB + headroom |
| Disk | 10–60 GB | ~30–35 GB needed at full 65k artwork scale |

Do **not** run batch jobs (Vision API, scraping, CLIP extraction) on the VPS. Run them locally and sync the DB.

### 3.5 Reliability Checklist

| Item | Status |
|---|---|
| `systemctl enable polish-art` | Done ✓ |
| `Restart=always` + `RestartSec=5` override | Done ✓ |
| Caddy entry for `lostpolishart.mcqueeney.org` | Done ✓ |
| External uptime monitor (UptimeRobot) | Pending |
| `/health` endpoint | Done ✓ (`GET /api/health`) |

---

## 4. Environment Configuration

File: `/home/polishart/polish_art/env/.env`

```env
DATABASE_URL=sqlite:////home/polishart/polish_art/data/artworks.db
READ_ONLY=true
```

`READ_ONLY=true` opens SQLite in read-only mode and skips schema creation on startup.

Auth is **disabled** by default (`AUTH_ENABLED=false`). See Section 10 for the planned design.

---

## 5. Data Pipeline

### 5.1 Sources

- **Polish Ministry of Culture war loss registry** — ~65,000 object records
- **lootedart.gov.pl** — scraped via `src/scripts/scrape_lootedart_gov_pl.py`
- **Auction houses / galleries** — scraped via `src/scrapers/auction_spider.py` (requests + BeautifulSoup)
- **Google Vision API** — reverse image search for finding artworks in the wild

### 5.2 Local Data Workflow

```
Scrape / import
      │
      ▼
data/artworks.db  (master local DB)
      │
      ├── Vision API batch search  (batch_vision_search.py)
      ├── CV feature extraction    (extract_features.py)
      └── build_and_sync_server_db.py
                │
                ▼
         data/server_export.db  →  scp →  VPS artworks.db
```

### 5.3 DB Export (build_and_sync_server_db.py)

Builds a pruned SQLite export for the VPS. Run locally before each sync.

```powershell
python src/scripts/build_and_sync_server_db.py `
    --output data/server_export.db `
    --strip-images-unless-include
```

| Flag | Effect |
|---|---|
| `--strip-all-images` | No image blobs (smallest export) |
| `--strip-images-unless-include` | Keep images where `include_image_on_server = 1` |
| `--strip-images-unless-interesting` | Keep images for artworks with Vision API hits |
| `--no-vision-detail` | Omit match/entity rows, keep summary |
| `--no-image-features` | Omit `image_features` table |
| `--no-matches` | Omit matches table |
| `--no-provenances` | Omit provenances table |

### 5.4 Full Sync (sync_to_vps.ps1)

Automates build + transfer + restart:

```powershell
.\src\scripts\sync_to_vps.ps1
# or with explicit target:
.\src\scripts\sync_to_vps.ps1 polishart@lostpolishart.mcqueeney.org
```

Steps performed:
1. Activates `.venv`
2. Runs `build_and_sync_server_db.py --strip-images-unless-include`
3. SCPs `data/server_export.db` → `polish_art/data/artworks.db`
4. SSHs in and runs `sudo systemctl restart polish-art`

### 5.5 Linux Box (Automated Scraper Host)

The weekly scrape runs on a dedicated Linux machine with ample local disk (external drive). It is **not** internet-facing — all connections are outbound SSH/rsync to the VPS, which works through NAT without any firewall changes.

```
Linux Box (behind ISP NAT)
├── data/artworks.db        ← master DB, full size
├── cron (Monday 03:00)
│   └── src/scripts/scrape_and_sync.sh
│       ├── run_weekly_scrape.py   → scrapes targets, writes to artworks.db
│       ├── build_and_sync_server_db.py → data/server_export.db (pruned)
│       └── rsync + ssh systemctl restart → VPS
│
VPS (lostpolishart.mcqueeney.org)
└── data/artworks.db  ← read-only export, small
```

#### One-Time Linux Box Setup

**1. Clone the repo** onto the external drive:
```bash
git clone git@github.com:youruser/polish_art.git /mnt/data/polish_art
cd /mnt/data/polish_art
```

**2. Create venv and install dependencies:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**3. Bootstrap the master DB** from the Windows machine (one-time transfer):
```bash
scp WINDOWS_HOST:/path/to/polish_art/data/artworks.db /mnt/data/polish_art/data/
```
Alternatively, run the full Ministry of Culture import pipeline to build from scratch.

**4. Set up passwordless SSH to the VPS:**
```bash
ssh-keygen -t ed25519 -C "linux-scraper"
ssh-copy-id polishart@lostpolishart.mcqueeney.org
# Verify:
ssh polishart@lostpolishart.mcqueeney.org 'echo ok'
```

**5. Ensure the VPS allows passwordless `systemctl restart`** (see Section 5.6).

**6. Seed scraper targets** (first run only):
```bash
./src/scripts/scrape_and_sync.sh --seed
```

**7. Make the script executable and add the cron entry:**
```bash
chmod +x src/scripts/scrape_and_sync.sh
crontab -e
```
Add this line (adjust path if needed):
```
0 3 * * 1  /mnt/data/polish_art/src/scripts/scrape_and_sync.sh
```

#### Ongoing use

| Task | Command |
|---|---|
| Manual full run | `./src/scripts/scrape_and_sync.sh` |
| First-time seed + run | `./src/scripts/scrape_and_sync.sh --seed` |
| Check logs | `tail -f logs/scrape_and_sync.log` |
| Single target test | `python -m src.scripts.run_weekly_scrape --target-id <uuid> --force` |

The Windows machine retains `sync_to_vps.ps1` for ad-hoc manual syncs (e.g. after importing new Ministry of Culture records on Windows).

### 5.6 VPS: Passwordless sudo for Service Restart

The Linux box (and Windows machine) both SSH in to restart the app after a sync. The `polishart` user needs a narrow passwordless sudo rule on the VPS.

Create `/etc/sudoers.d/polishart` on the VPS:
```
polishart ALL=(ALL) NOPASSWD: /bin/systemctl restart polish-art
```

Apply and verify:
```bash
sudo visudo -c -f /etc/sudoers.d/polishart     # syntax check
sudo chmod 440 /etc/sudoers.d/polishart
# Test from your local machine:
ssh polishart@lostpolishart.mcqueeney.org 'sudo systemctl restart polish-art && sudo systemctl is-active polish-art'
```

---

## 6. Application Layer (FastAPI)

### 6.1 Stack

- **Framework:** FastAPI + uvicorn
- **Entry point:** `src/main.py`
- **API prefix:** `/api`
- **Static files:** `static/` (HTML, CSS, JS)

### 6.2 API Endpoints

#### Artworks

| Method | Path | Description |
|---|---|---|
| GET | `/api/artworks` | Paginated list (`page`, `page_size`) |
| GET | `/api/artworks/{id}` | Single artwork |
| GET | `/api/artworks/search/query?q=` | Search by title / artist |
| GET | `/api/artworks/{id}/image` | Binary image (JPEG/PNG); cached 24h |
| GET | `/api/artworks/{id}/features` | CV feature vector |
| GET | `/api/artworks/{id}/similar` | Similar artworks (`method`: hash/clip/hybrid) |
| GET | `/api/artworks/duplicates/detect` | Duplicate detection by perceptual hash |

#### Vision API

| Method | Path | Description |
|---|---|---|
| GET | `/api/vision/stats` | Request counts, unique artworks, cost |
| GET | `/api/vision/cost-summary` | Total units used, estimated USD cost |
| GET | `/api/vision/findings` | Interesting results (paginated) |
| GET | `/api/vision/artwork-status` | Per-artwork search status |
| GET | `/api/vision/artwork/{id}/searches` | Search history for one artwork |
| GET | `/api/vision/request/{id}` | Full detail for one Vision request |
| GET | `/api/vision/domains/suspicious` | Flagged domains |
| GET | `/api/vision/domains/{category}` | Domain stats by category (auction/marketplace/museum/social/academic/other) |

#### Scraper Management

| Method | Path | Description |
|---|---|---|
| GET | `/api/scraper/targets` | List auction house targets (`category`, `active_only`) |
| POST | `/api/scraper/targets` | Add a target |
| PATCH | `/api/scraper/targets/{id}` | Update / enable / disable a target |
| GET | `/api/scraper/urls` | Crawl URL log (paginated, filterable by domain) |
| GET | `/api/scraper/stats` | Aggregate crawl statistics |

#### Evaluator Feedback

| Method | Path | Description |
|---|---|---|
| POST | `/api/feedback` | Submit curator judgment (not_a_match, comment) |
| GET | `/api/feedback` | List all feedback |
| GET | `/api/feedback/{artwork_id}` | Feedback for one artwork |

---

## 7. Database Schema

Single SQLite file (`data/artworks.db` locally, `data/artworks.db` on VPS).

### Core Tables

**`artworks`**

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| title | VARCHAR(500) | |
| artist_name | VARCHAR(200) | |
| creation_year | INTEGER | |
| description | TEXT | |
| status | VARCHAR(50) | e.g. "lost", "found" |
| image_url | VARCHAR(500) | Source URL |
| image_data | BLOB | Binary image bytes (stored locally) |
| image_mime_type | VARCHAR(50) | e.g. "image/jpeg" |
| image_hash | VARCHAR(64) | SHA-256 for deduplication |
| include_image_on_server | BOOLEAN | Controls server export culling |
| last_known_location | VARCHAR(200) | |
| last_known_date | DATETIME | |
| created_at / updated_at | DATETIME | |

**`image_features`** (CV pipeline output)

| Column | Notes |
|---|---|
| phash / dhash / ahash | Perceptual hashes (hex strings) |
| clip_embedding | 512-dim CLIP vector (JSON) |
| width_pixels / height_pixels / aspect_ratio | Dimensions |
| sharpness_score / contrast_score / brightness_avg | Quality metrics |
| is_grayscale | Boolean |
| dominant_colors | JSON array of 5 RGB tuples |
| model_version / extraction_timestamp | Versioning |

### Vision API Tables

| Table | Contents |
|---|---|
| `vision_api_requests` | All API calls — summary stats, cost units, `has_interesting_results` flag |
| `vision_api_matches` | Image matches (only for interesting results) |
| `vision_api_entities` | Web entities / labels (only for interesting results) |
| `vision_api_domain_stats` | Aggregated domain intelligence |

### Scraper Tables

| Table | Contents |
|---|---|
| `scraper_targets` | Auction house / gallery targets with frequency settings |
| `scraped_urls` | Crawl log with domain, phash, `was_interesting` flag |

### Feedback Table

`evaluator_feedback` — curator decisions (`not_a_match`, `comment`, `created_by`) keyed by `artwork_id`.

---

## 8. Computer Vision Pipeline

Implemented in `src/cv_pipeline/`. All processing runs locally, results stored in `image_features`.

### 8.1 Perceptual Hashing (`perceptual_hasher.py`)

Three complementary algorithms:
- **pHash** (DCT-based) — robust to rotation and scaling
- **dHash** (gradient-based) — detects geometric transformations
- **aHash** (average-based) — fast duplicate detection

Similarity via Hamming distance: identical < 5, very similar < 10, similar < 15.

### 8.2 CLIP Embeddings (`clip_embedder.py`)

- Model: `openai/clip-vit-base-patch32`
- Output: 512-dimensional semantic embedding
- Similarity: cosine similarity (high ≥ 0.90, medium ≥ 0.80, low ≥ 0.70)
- Auto device detection (CUDA/CPU)

### 8.3 Image Analyzer (`image_analyzer.py`)

Extracts: dimensions, format, file size, color space, sharpness (Laplacian variance), contrast, brightness, grayscale flag, 5 dominant RGB colors (K-means).

### 8.4 CLI

```powershell
python src/scripts/extract_features.py        # Process all artworks
```

Processing time: ~3–4 seconds per image. CLIP model loads once at startup (~2 s). Storage: ~12 KB per artwork.

---

## 9. Vision API Surveillance

### 9.1 Interest Scoring

Results are stored in detail only when they score ≥ 15:

| Signal | Points |
|---|---|
| Full match | +10 each |
| Partial match (suggests provenance hiding) | +5 each |
| Similar match | +2 each |
| Auction domain (Christie's, Sotheby's, etc.) | +20 |
| Marketplace domain (eBay, Etsy, Allegro) | +15 |
| Suspicious domain pattern | +10 |

~5–15% of searches produce detailed stored results; all searches are logged with summary stats.

### 9.2 Domain Categories

`auction` · `marketplace` · `museum` · `social` · `academic` · `other`

### 9.3 CLI Batch Search

```powershell
# Single artwork
python src/scripts/batch_vision_search.py --artwork-id "uuid"

# All unsearched (limit 50)
python src/scripts/batch_vision_search.py --unsearched --limit 50

# Cost summary
python src/scripts/batch_vision_search.py --cost-summary

# Interesting findings
python src/scripts/batch_vision_search.py --show-findings --limit 20
```

### 9.4 Costs

| Volume | Cost |
|---|---|
| First 1,000 requests/month | Free |
| After free tier | ~$1.50 per 1,000 requests |
| Full DB scan (7,341 artworks) | ~$11 |
| Monthly re-scan of suspicious artworks | ~$2–5 |
| Full 65k DB × 15 scans/year | ~$975k requests → ~$3,400/year |

---

## 10. Image Storage

Images are downloaded at scrape time and stored as BLOBs in `artworks.image_data`.

- **Max size:** 10 MB per image
- **Validation:** Content-Type must start with `image/`; HTML responses are rejected
- **Deduplication:** SHA-256 hash stored in `image_hash`
- **Rate limiting:** 2 seconds between HTTP requests during download
- **Caching headers on API:** `Cache-Control: public, max-age=86400`, `ETag: <first 32 chars of hash>`

Images are selectively included in the server export via the `include_image_on_server` column flag and `--strip-images-unless-include` export option.

---

## 11. Scraping

### Spider

`src/scrapers/auction_spider.py` — Scrapy-based spider for auction house and gallery sites.

### Scraper Targets

Managed in the `scraper_targets` table and via `/api/scraper/targets`. Each target has:
- `base_url`, `category`, `country`
- `scrape_frequency_days` (default 7)
- `last_scraped_at`, `is_active`

### Weekly Scrape Script

```powershell
python src/scripts/run_weekly_scrape.py
```

### Anti-Detection

- 1 request per 5 seconds per site
- User-agent rotation
- `robots.txt` compliance
- Circuit breaker after 10 consecutive failures

---

## 12. Auth (Planned, Not Implemented)

Auth is disabled by default (`AUTH_ENABLED=false`). When enabled:

- **Mechanism:** Session-based (HTTP-only cookie), not JWT
- **Tables:** `users` (id, username, password_hash), `sessions` (token, expires_at)
- **Protected routes:** `/api/vision/*` and write endpoints when `AUTH_ENABLED=true`
- **Implementation:** `src/auth.py` with `passlib`/`bcrypt`, `get_current_user` FastAPI dependency

No routes are currently protected. The design is backward-compatible — enabling auth requires only setting the env var and adding the dependency to chosen routes.

---

## 13. Operational Workflow

### Daily (Automated — not yet wired up)

Per the Executive Summary target state:
- 2 AM–6 AM: Vision API scans 2,000 high-priority artworks; spiders visit 20+ sites
- 9 AM: Curator receives email: "N findings require review"
- Curator reviews findings in the web UI (side-by-side: registry artwork vs. found image)
- Curator marks: approve / reject / false positive / monitor

### On-Demand (Current workflow)

```powershell
# 1. Scrape new auction listings
python src/scripts/run_weekly_scrape.py

# 2. Run Vision API on unsearched artworks
python src/scripts/batch_vision_search.py --unsearched --limit 50

# 3. Extract CV features for new artworks
python src/scripts/extract_features.py

# 4. Sync to server
.\src\scripts\sync_to_vps.ps1
```

---

## 14. Monitoring & Troubleshooting

### Uptime Monitoring (Pending)

Sign up at [UptimeRobot](https://uptimerobot.com) (free tier, 5-minute checks):
- Monitor: `https://lostpolishart.mcqueeney.org`
- Alert: email on down/up events

### Key Commands on VPS

```bash
# Service status
sudo systemctl status polish-art --no-pager

# Live logs
sudo journalctl -u polish-art -f

# Last 100 log lines
sudo journalctl -u polish-art -n 100 --no-pager

# Check what ports are bound
ss -tlnp

# Test app directly (bypassing Caddy)
curl http://127.0.0.1:8000/api/artworks?page=1&page_size=1

# Caddy status
sudo systemctl status caddy --no-pager

# Reload Caddy config
sudo systemctl reload caddy

# DB integrity check
sqlite3 /home/polishart/polish_art/data/artworks.db "PRAGMA integrity_check;"
```

### Common Issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Site unreachable, app running | Caddy misconfiguration | Check Caddyfile has the site's block; `sudo systemctl reload caddy` |
| App crashes repeatedly | OOM kill | Check `journalctl -k \| grep -i oom`; add swap |
| App crashes after DB sync | SQLite lock race | `Restart=always` brings it back; sync during low traffic |
| Scraper returns 403 | Site blocking | Check `robots.txt`; increase delay; rotate user-agent |

---

## 15. Scaling Estimates (One Year, Full Database)

| Scenario | Artworks | Storage | Vision API requests/yr |
|---|---|---|---|
| Current | ~1,376 | ~620 MB | ~20k |
| Full Polish DB | ~65,000 | ~35 GB | ~975k |
| Upper bound | ~100,000 | ~54 GB | ~1.5M |

At 65k artworks, plan **50–60 GB** disk including indexes and backups.

At full scale, the VPS should be upgraded to 4 vCPU / 16 GB RAM if batch jobs run on the same machine, or kept at 1 vCPU / 1 GB if the server remains read-only.

---

## 16. Future Roadmap

| Phase | Description | Status |
|---|---|---|
| Phase 1 | Data ingestion, FastAPI, image storage, CV pipeline | Complete ✓ |
| Phase 2 Step 1 | Perceptual hashing + CLIP feature extraction | Complete ✓ |
| Phase 2 Step 2 | Similarity search API endpoints | Complete ✓ |
| Phase 3 | Auction scraping at scale (20+ sites) | In progress |
| Phase 4 | Automated weekly scheduling via Linux box cron + scrape_and_sync.sh | Complete ✓ |
| Phase 5 | Curator review interface with feedback loop | Partial (feedback API exists) |
| Phase 6 | ML classification trained on curator feedback | Pending (needs 3–6 months data) |
| Auth | Session-based login for write endpoints | Designed, not implemented |
| Monitoring | UptimeRobot + `/health` endpoint | Pending |
| Caddy fix | Add `lostpolishart.mcqueeney.org` to Caddyfile | Complete ✓ |
