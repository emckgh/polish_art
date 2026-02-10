#!/usr/bin/env python3
"""
Capture application screenshots for the funding overview PowerPoint.

Starts the app (optional), opens the list and detail pages in a browser,
and saves PNGs to docs/slideshow/ for use by create_funding_overview_pptx.py.

Usage:
  # Server must be running at http://localhost:8000
  python scripts/screenshot_for_pptx.py

  # Start server automatically, capture, then stop
  python scripts/screenshot_for_pptx.py --start-server

  # Custom base URL
  python scripts/screenshot_for_pptx.py --base-url http://127.0.0.1:8000
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SLIDESHOW_DIR = PROJECT_ROOT / "docs" / "slideshow"
DEFAULT_BASE_URL = "http://localhost:8000"


def wait_for_server(base_url: str, timeout: float = 15.0) -> bool:
    """Return True when server responds to /health."""
    import urllib.request
    import urllib.error
    health = f"{base_url.rstrip('/')}/health"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health, timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def start_server() -> subprocess.Popen:
    """Start uvicorn in the background. Caller must terminate the process."""
    venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    if not venv_python.exists():
        raise SystemExit("Virtual environment not found at .venv")
    proc = subprocess.Popen(
        [str(venv_python), "-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


def capture_screenshots(base_url: str, headless: bool = True) -> None:
    from playwright.sync_api import sync_playwright

    SLIDESHOW_DIR.mkdir(parents=True, exist_ok=True)
    list_path = SLIDESHOW_DIR / "screenshot_list.png"
    detail_path = SLIDESHOW_DIR / "screenshot_detail.png"

    # Viewport sized for slide (roughly 5:3)
    viewport = {"width": 1200, "height": 720}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(viewport=viewport)
        page = context.new_page()

        base = base_url.rstrip("/")

        # --- List page ---
        print(f"Opening list page: {base}/")
        page.goto(f"{base}/", wait_until="networkidle", timeout=15000)
        page.wait_for_selector("#artworkTable", timeout=10000)
        page.wait_for_timeout(1500)  # let table and stats settle
        page.screenshot(path=str(list_path), type="png")
        print(f"Saved: {list_path}")

        # --- Detail page: click first row to get an artwork id ---
        first_row = page.locator("#artworkTable tbody tr.clickable-row").first
        if first_row.count() == 0:
            print("No artwork rows found; using a fixed detail URL for screenshot.")
            page.goto(f"{base}/static/detail.html?id=d67df9ef-4486-4cb1-8f33-90bfee43f3d1", wait_until="networkidle", timeout=15000)
        else:
            first_row.click()
            page.wait_for_load_state("networkidle", timeout=10000)

        page.wait_for_selector(".detail-container", timeout=10000)
        page.wait_for_timeout(1000)
        # Optional: switch to Vision tab for a more interesting screenshot
        vision_tab = page.locator('[data-tab="vision"]')
        if vision_tab.count() > 0:
            vision_tab.click()
            page.wait_for_timeout(1500)
        page.screenshot(path=str(detail_path), type="png")
        print(f"Saved: {detail_path}")

        browser.close()

    print("Done. Run 'python scripts/create_funding_overview_pptx.py' to regenerate the PowerPoint.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture app screenshots for the funding PPTX.")
    parser.add_argument("--start-server", action="store_true", help="Start uvicorn, capture, then stop.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"App base URL (default: {DEFAULT_BASE_URL}).")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window.")
    args = parser.parse_args()

    server_process = None
    if args.start_server:
        print("Starting server...")
        server_process = start_server()
        if not wait_for_server(args.base_url):
            server_process.terminate()
            raise SystemExit("Server did not become ready in time.")
        print("Server ready.")

    try:
        capture_screenshots(args.base_url, headless=not args.no_headless)
    finally:
        if server_process is not None:
            server_process.terminate()
            print("Server stopped.")


if __name__ == "__main__":
    main()
