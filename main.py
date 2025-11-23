"""Main FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from src.api.routes import router


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
