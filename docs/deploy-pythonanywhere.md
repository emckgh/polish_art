# Deploying to PythonAnywhere (read-only)

The app runs on PythonAnywhere as a **read-only** site: it serves the UI and API from a single SQLite database. All data updates (imports, Google image search, Vision API, etc.) run on your local machine; you periodically sync the database file to PythonAnywhere.

## One-command deploy (from local)

From your project root, with `PA_USERNAME` and `PA_API_TOKEN` set in `env/.env`:

```bash
python scripts/deploy_to_pa.py
```

This will: create a small DB extract (100 artworks), upload it to PythonAnywhere, and print the exact Bash commands to run on PythonAnywhere to finish setup (clone/upload repo, virtualenv, pip install, env/.env, `pa website create`). Copy-paste those commands into a PythonAnywhere Bash console.

## Prerequisites

- PythonAnywhere account (free tier works; ASGI support is beta).
- API token (Account → API token) if you use the `pa` CLI.
- Local repo with `data/artworks.db` already created and populated (or an empty DB for first deploy).

## 1. Project layout on PythonAnywhere

1. Clone or upload the repo, e.g. to `/home/YOURUSERNAME/polish_art`.
2. Create the data directory and place the database there:
   ```bash
   mkdir -p /home/YOURUSERNAME/polish_art/data
   # Then upload data/artworks.db into that folder (see "Database sync" below).
   ```

## 2. Virtualenv and dependencies

In a Bash console on PythonAnywhere:

```bash
cd ~/polish_art
mkvirtualenv polish_art_venv --python=python3.10
workon polish_art_venv
pip install -r requirements.txt
```

Use your project path and venv name as needed. For a lighter install (no torch/transformers), you can use a slim `requirements-web.txt` if you add one; otherwise the full `requirements.txt` is fine.

## 3. Environment variables

Set these for the web app (e.g. `env/.env` under `~/polish_art`, or via PythonAnywhere’s “Web” → “Environment variables” if available):

| Variable        | Value (example) |
|----------------|------------------|
| `DATABASE_URL` | `sqlite:////home/YOURUSERNAME/polish_art/data/artworks.db` |
| `READ_ONLY`    | `true` |

Use your actual username and path. Four slashes in `sqlite:////` are correct for an absolute path. `READ_ONLY=true` disables schema creation and opens SQLite in read-only mode.

## 4. ASGI / uvicorn command

The app lives in `src.main:app`. From [PythonAnywhere’s ASGI help](https://help.pythonanywhere.com/pages/ASGICommandLine/), use a command like:

```bash
/home/YOURUSERNAME/.virtualenvs/polish_art_venv/bin/uvicorn --app-dir /home/YOURUSERNAME/polish_art --uds ${DOMAIN_SOCKET} src.main:app
```

Replace:

- `YOURUSERNAME` with your PythonAnywhere username.
- `polish_art_venv` with your virtualenv name if different.
- The path after `--app-dir` with your project root (the directory that contains `src`).

`--app-dir` sets the working directory so `static/` and relative paths resolve correctly.

## 5. Creating the website

1. In Bash, install the PythonAnywhere CLI (if you use it):
   ```bash
   pip install --upgrade pythonanywhere
   ```
2. Create the ASGI site (replace the domain and command with yours):
   ```bash
   pa website create --domain YOURUSERNAME.pythonanywhere.com --command '/home/YOURUSERNAME/.virtualenvs/polish_art_venv/bin/uvicorn --app-dir /home/YOURUSERNAME/polish_art --uds ${DOMAIN_SOCKET} src.main:app'
   ```
3. Or use the “Web” tab and the “ASGI” / manual configuration to paste the same uvicorn command.

After creation, the site is live at `YOURUSERNAME.pythonanywhere.com` (or your custom domain). Root `/` redirects to `/static/index.html`.

## 6. First deploy: database and reload

1. Upload (or sync) `data/artworks.db` into `~/polish_art/data/` (see “Database sync” below).
2. Reload the web app so it uses the new file:
   ```bash
   pa website reload --domain YOURUSERNAME.pythonanywhere.com
   ```
   Or use the “Web” tab reload button.

## 7. Small extract for test / upload limit

If the full `data/artworks.db` is too large for upload (e.g. over 100MB), create a small extract:

```bash
python scripts/extract_db_sample.py --limit 100 --output data/artworks_extract.db
```

This copies 100 artworks and all related rows; by default it sets `image_data` to NULL so the file stays small (e.g. ~1–2 MB). Use the extract as `artworks.db` on PythonAnywhere, or sync it and set `DATABASE_URL` to point at it.

Options: `--limit N`, `--no-strip-images` (keep images, larger file), `--output PATH`, `--source PATH`.

## 8. Database sync (local → PythonAnywhere)

**Option A – Manual**

1. Locally: run your scripts (import, vision search, etc.); when ready, take a copy of `data/artworks.db`.
2. On PythonAnywhere: open **Files**, go to `~/polish_art/data/`, upload the file and overwrite `artworks.db`.
3. Reload the web app (see above).

**Option B – Scripted (optional)**

From your local machine, run:

```bash
# Optional: set for API upload (otherwise the script prints manual steps)
export PA_USERNAME=your_pa_username
export PA_API_TOKEN=your_api_token
# export PA_HOST=eu.pythonanywhere.com   # if using EU

python scripts/sync_db_to_pa.py
```

See `scripts/sync_db_to_pa.py` for details. After upload, reload the web app on PythonAnywhere.

## 9. Maintenance

- **Update code**: pull or upload new code under `~/polish_art`, then reload the web app.
- **Update data**: sync `data/artworks.db` from local to PA (Option A or B), then reload the web app.
- **Logs**: e.g. `/var/log/YOURUSERNAME.pythonanywhere.com.error.log` and `.server.log` (see PA “Files” or docs).

Do **not** run import, scraping, or Vision API scripts on PythonAnywhere; run them locally and sync the DB.
