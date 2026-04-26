"""HTTP Basic protection for the scraper status UI and /api/scraper/* endpoints.

Username: scraper. Password: SCRAPER_STATUS_PASSWORD env, or the default in code.
"""
import os
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

_STATUS_USER = "scraper"
_DEFAULT_PASSWORD = "art'smom1990"

http_basic = HTTPBasic()


def _status_password() -> str:
    return os.environ.get("SCRAPER_STATUS_PASSWORD", _DEFAULT_PASSWORD)


def _bytes_equal(a: str, b: str) -> bool:
    x = a.encode("utf-8")
    y = b.encode("utf-8")
    if len(x) != len(y):
        return False
    return secrets.compare_digest(x, y)


def require_scraper_status_user(
    credentials: HTTPBasicCredentials = Depends(http_basic),
) -> str:
    if not _bytes_equal(credentials.username, _STATUS_USER):
        _reject()
    if not _bytes_equal(credentials.password, _status_password()):
        _reject()
    return credentials.username


def _reject() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Basic"},
    )
