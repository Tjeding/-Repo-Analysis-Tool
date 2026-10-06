"""RAT backend entry point.

Run with:  uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import authors, metrics, repositories
from app.config import settings

app = FastAPI(title=settings.app_name, version=settings.version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repositories.router, prefix="/api/repositories", tags=["repositories"])
app.include_router(authors.router, prefix="/api/authors", tags=["authors"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])


@app.get("/api/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}
