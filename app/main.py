"""
OmniBrain FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes import documents, query
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bootstrap resources on startup; clean up on shutdown."""
    try:
        from app.ingestion.embedder import ensure_collections
        ensure_collections()
        print("[OmniBrain] Qdrant collections bootstrapped.")
    except Exception as exc:
        # Qdrant may not be running locally in all environments; warn but don't crash.
        print(f"[OmniBrain] Warning: could not reach Qdrant on startup: {exc}")
    yield  # app runs here


app = FastAPI(
    title="OmniBrain API",
    description="Agentic Multi-Modal RAG Orchestrator — backend service.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(documents.router)
app.include_router(query.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "env": settings.app_env}
