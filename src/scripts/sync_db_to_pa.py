#!/usr/bin/env python3
"""
Sync local data/artworks.db to PythonAnywhere (read-only deployment).

Usage:
  python scripts/sync_db_to_pa.py

Requires (for API upload):
  - PA_USERNAME: your PythonAnywhere username
  - PA_API_TOKEN: API token from Account → API token
  - PA_HOST (optional): "www.pythonanywhere.com" or "eu.pythonanywhere.com"

If these are not set, the script prints manual upload instructions.

After uploading, reload your web app on PythonAnywhere (pa website reload or Web tab).
"""
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / "env" / ".env")
except ImportError:
    pass

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = PROJECT_ROOT / "data" / "artworks.db"
PA_DEFAULT_PATH = "/home/{username}/polish_art/data/artworks.db"


def main() -> None:
    db_path = Path(os.getenv("DB_PATH", str(DEFAULT_DB)))
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path
    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    username = os.getenv("PA_USERNAME", "").strip()
    token = os.getenv("PA_API_TOKEN", "").strip()
    host = os.getenv("PA_HOST", "www.pythonanywhere.com").strip().rstrip("/")

    if username and token:
        upload_via_api(db_path, username, token, host)
    else:
        print_manual_instructions(db_path, username or "YOURUSERNAME")


def upload_via_api(db_path: Path, username: str, token: str, host: str) -> None:
    try:
        import requests
    except ImportError:
        print("Install requests to use API upload: pip install requests", file=sys.stderr)
        print_manual_instructions(db_path, username)
        sys.exit(1)

    dest_path = PA_DEFAULT_PATH.format(username=username)
    url = f"https://{host}/api/v0/user/{username}/files/path{dest_path}"
    headers = {"Authorization": f"Token {token}"}

    print(f"Uploading {db_path} ({db_path.stat().st_size / (1024*1024):.2f} MiB) to {dest_path} ...")
    with open(db_path, "rb") as f:
        content = f.read()

    # PA API expects multipart form with 'content' key (not raw body)
    r = requests.post(
        url,
        headers=headers,
        files={"content": (db_path.name, content, "application/octet-stream")},
        timeout=300,
    )
    if r.status_code in (200, 201):
        print("Upload OK. Reload your web app on PythonAnywhere.")
        return
    print(f"Upload failed: {r.status_code} {r.text}", file=sys.stderr)
    sys.exit(1)


def print_manual_instructions(db_path: Path, username: str) -> None:
    print("Manual upload:")
    print(f"  1. Open PythonAnywhere -> Files -> navigate to polish_art/data/")
    print(f"  2. Upload this file (overwrite artworks.db): {db_path}")
    print(f"  3. Reload the web app (Web tab or: pa website reload --domain {username}.pythonanywhere.com)")
    print()
    print("Optional: set PA_USERNAME and PA_API_TOKEN in env/.env (and PA_HOST for EU) to upload via API.")


if __name__ == "__main__":
    main()
