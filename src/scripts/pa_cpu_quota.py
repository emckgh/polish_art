#!/usr/bin/env python3
"""
Check PythonAnywhere CPU quota via the API.
Loads PA_USERNAME and PA_API_TOKEN from env/.env (or environment).
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / "env" / ".env")
except ImportError:
    pass

import requests

username = os.getenv("PA_USERNAME", "").strip()
token = os.getenv("PA_API_TOKEN", "").strip()
host = os.getenv("PA_HOST", "www.pythonanywhere.com").strip().rstrip("/")

if not username or not token:
    print("Set PA_USERNAME and PA_API_TOKEN in env/.env (or environment).")
    exit(1)

response = requests.get(
    f"https://{host}/api/v0/user/{username}/cpu/",
    headers={"Authorization": f"Token {token}"},
)
if response.status_code == 200:
    print("CPU quota info:")
    print(response.content.decode())
else:
    print(f"Got unexpected status code {response.status_code}: {response.content!r}")
