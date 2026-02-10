"""Placeholder auth routes. When AUTH_ENABLED=true, replace with real login/logout/session logic."""
import os

from fastapi import APIRouter

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


def _auth_enabled() -> bool:
    return os.environ.get("AUTH_ENABLED", "").strip().lower() in ("1", "true", "yes")


@auth_router.post("/login")
async def login():
    """Login (placeholder). When AUTH_ENABLED=true, implement username/password and session cookie."""
    if not _auth_enabled():
        return {"detail": "Auth is disabled", "auth_enabled": False}
    return {"detail": "Auth not implemented yet", "auth_enabled": True}


@auth_router.post("/logout")
async def logout():
    """Logout (placeholder). When AUTH_ENABLED=true, clear session and cookie."""
    if not _auth_enabled():
        return {"detail": "Auth is disabled", "auth_enabled": False}
    return {"detail": "Auth not implemented yet", "auth_enabled": True}


@auth_router.get("/me")
async def me():
    """Current user (placeholder). When AUTH_ENABLED=true, return user from session."""
    if not _auth_enabled():
        return {"detail": "Auth is disabled", "user": None}
    return {"detail": "Auth not implemented yet", "user": None}
