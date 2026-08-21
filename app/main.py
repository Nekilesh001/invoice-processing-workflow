from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown events."""
    try:
        init_db()
    except Exception as e:
        print(f"[WARN] Database initialization warning on startup: {str(e)}")
    yield


app = FastAPI(
    title="AI Invoice Processing & Verification Platform API",
    description="Production-grade AI Invoice Processing System with Document OCR, LLM Extraction, Business Validation, Agentic AI Tooling, and Human Review Queue.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include master API router
app.include_router(api_router)

# Mount Web Frontend if built dist directory exists
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="static_assets")

    @app.get("/", tags=["Frontend"])
    def read_root():
        """Serves the React Web Frontend single page application."""
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/favicon.svg", tags=["Frontend"])
    def read_favicon():
        """Serves web app favicon icon."""
        fav_path = os.path.join(frontend_dist, "favicon.svg")
        if os.path.exists(fav_path):
            return FileResponse(fav_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for container / server monitoring."""
    return {"status": "HEALTHY", "service": "AI Invoice Processing Platform"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
