"""Main FastAPI application entry point."""
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from src.api.routes import router
from src.api.auth_routes import auth_router
from src.api.scraper_status_auth import require_scraper_status_user

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_SCRAPER_STATUS_HTML = _STATIC_DIR / "status.html"


app = FastAPI(
    title="Polish Looted Art Discovery Engine",
    description="API for browsing looted Polish artworks",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)
app.include_router(auth_router)

# Scraper status page (auth required; must be before /static mount)
@app.get("/static/status.html", dependencies=[Depends(require_scraper_status_user)])
async def scraper_status_page():
    return FileResponse(
        _SCRAPER_STATUS_HTML,
        media_type="text/html; charset=utf-8",
    )

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


@app.get("/")
async def root():
    """Redirect root to static index."""
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
