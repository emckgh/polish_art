#!/usr/bin/env python3
"""
Deploy the app to PythonAnywhere: create a small DB extract, upload it, and print
the exact commands to run on PythonAnywhere to finish setup.

Usage (from project root):
  python scripts/deploy_to_pa.py

Requires in env/.env:
  - PA_USERNAME: your PythonAnywhere username
  - PA_API_TOKEN: API token (for uploading the DB)

Optional: PA_HOST (default www.pythonanywhere.com; use eu.pythonanywhere.com for EU).
"""
import os
import subprocess
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / "env" / ".env")
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTRACT_DB = PROJECT_ROOT / "data" / "artworks_extract.db"


def main() -> int:
    username = os.getenv("PA_USERNAME", "").strip()
    if not username:
        print("Set PA_USERNAME in env/.env (your PythonAnywhere username).", file=sys.stderr)
        return 1

    # 1. Create small extract for PA (under upload limit)
    print("Creating DB extract (100 artworks, no image blobs)...")
    r = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "extract_db_sample.py"),
            "--limit", "100",
            "--output", str(EXTRACT_DB),
        ],
        cwd=PROJECT_ROOT,
    )
    if r.returncode != 0:
        return r.returncode

    # 2. Upload DB to PythonAnywhere
    print("Uploading DB to PythonAnywhere...")
    env = os.environ.copy()
    env["DB_PATH"] = str(EXTRACT_DB)
    r = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "sync_db_to_pa.py")],
        cwd=PROJECT_ROOT,
        env=env,
    )
    if r.returncode != 0:
        return r.returncode

    # 3. Print commands to run on PythonAnywhere
    home = f"/home/{username}"
    venv_path = f"{home}/.virtualenvs/polish_art_venv"
    app_dir = f"{home}/polish_art"
    db_path = f"{app_dir}/data/artworks.db"
    db_url = f"sqlite:///{db_path}"
    domain = f"{username}.pythonanywhere.com"
    uvicorn_cmd = (
        f"{venv_path}/bin/uvicorn --app-dir {app_dir} --uds ${{DOMAIN_SOCKET}} src.main:app"
    )

    print()
    print("=" * 60)
    print("ON PYTHONANYWHERE: open a Bash console and run the following.")
    print("(If the repo is not there yet: clone or upload it to ~/polish_art first.)")
    print("=" * 60)
    print()
    print(f"cd {app_dir}")
    print("mkvirtualenv polish_art_venv --python=python3.10")
    print("workon polish_art_venv")
    print("pip install -r requirements.txt")
    print("mkdir -p data")
    print("mkdir -p env")
    print(f'echo "DATABASE_URL={db_url}" > env/.env')
    print('echo "READ_ONLY=true" >> env/.env')
    print("pip install --upgrade pythonanywhere")
    print(f"pa website create --domain {domain} --command '{uvicorn_cmd}'")
    print()
    print("If the site already exists, just reload after code/DB changes:")
    print(f"  pa website reload --domain {domain}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
