# Auth design (future-ready, not implemented)

Auth is **disabled** by default. This document describes the intended design so it can be added later without reworking the app.

## Config

- **Env:** `AUTH_ENABLED=false` (default). When `true`, protected routes require a valid session.
- No change to current behavior until you set `AUTH_ENABLED=true` and implement the modules below.

## Model

- **Session-based auth** (HTTP-only cookie). Simpler than JWT for “simple” (revoke by deleting session; no token blacklist).
- **User:** `id`, `username`, `password_hash`, `created_at`. Single role for now: “viewer” (no login required for public) vs “admin” (future: protect write actions if any are exposed on the server).
- **Session:** `id`, `user_id`, `token` (random), `expires_at`; stored in the same SQLite DB (or Redis later). Table names: e.g. `users`, `sessions`.

## Interface (planned)

| Endpoint / page      | Purpose |
|----------------------|--------|
| `GET /login`         | Login page (static or SPA route). |
| `POST /api/auth/login` | Body: username, password. Server verifies, creates session, sets HTTP-only cookie, returns success or redirect. |
| `POST /api/auth/logout` | Clears session and cookie. |
| Protected routes     | Middleware or FastAPI dependency checks session cookie; if missing or invalid, return 401 or redirect to `/login`. Initially **no routes are protected**; when auth is enabled, attach the dependency to chosen routes (e.g. `/api/vision/*` or entire `/api` except health). |

## Front-end

- One “Login” link (hidden or minimal until auth is enabled).
- After login: optional “Logout” and display of username.
- No change to existing UI until auth is turned on.

## Implementation outline (when you add it)

1. **Backend module** (e.g. `src/auth.py`): password hashing (bcrypt or passlib), create/validate session, FastAPI dependency `get_current_user` (optional, returns `User` or `None`).
2. **Routes:** `POST /api/auth/login`, `POST /api/auth/logout`; optionally `GET /api/auth/me` returning current user when `AUTH_ENABLED=true`.
3. **Protection:** When `AUTH_ENABLED=true`, add a dependency to the router or to selected route handlers that calls `get_current_user` and returns 401 if missing.
4. **DB:** New tables `users`, `sessions`. Use Alembic migration or a one-off script (e.g. `scripts/migrate_add_auth_tables.py`).
5. **Placeholder behavior:** Until implementation, auth routes can return a JSON body like `{"detail": "Auth is disabled"}` and status 501 or 200 so the wiring is in place.
