# Minimum VPS configuration (CPU / RAM)

For **one user at a time**, web app only (no batch jobs on the same box).

## Recommended minimum

| Resource | Minimum | Notes |
|----------|---------|--------|
| **vCPU** | **1** | One uvicorn worker; single user is single-threaded enough. |
| **RAM** | **1 GB** | Comfortable for OS + Python + FastAPI + SQLite + one request. |

## Why this is enough

- **App stack:** FastAPI + uvicorn (1 worker), SQLite (no separate process), no Redis/Celery in the request path.
- **Per request:** At most one artwork + one image BLOB in memory (~500 KB) or a page of metadata; similarity endpoints use **precomputed** CLIP embeddings from the DB and do **not** load the CLIP/torch model.
- **Rough usage:** OS ~250 MB, Python + uvicorn + app ~150–200 MB, request working set &lt;10 MB → **1 GB** leaves headroom.

## Bare minimum (not recommended)

- **512 MB RAM** can work if the OS is very light (e.g. minimal Alpine/Debian) and you run only the web app, but you have no headroom for spikes or concurrent requests. Prefer **1 GB**.

## If you also run batch jobs on the same VPS

- **Vision API batch**, **scraping**, or **feature extraction** (CLIP) on the same machine need more resources:
  - **2 GB RAM** (CLIP/torch load is ~500 MB–1 GB).
  - **2 vCPU** recommended so one request can still be served while a batch job runs.

Run batch jobs (import, Vision, `extract_features.py`) on your local machine or a separate worker and sync the DB to the VPS if you want to keep the VPS at 1 vCPU / 1 GB.
