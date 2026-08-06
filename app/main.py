"""
OmniBrain FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, query, collections, tracing, analytics
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
        print(f"[OmniBrain] Note: Qdrant service unavailable on startup: {exc}. Fallback local memory search active.")
    yield  # app runs here


app = FastAPI(
    title="OmniBrain API",
    description="Agentic Multi-Modal RAG Orchestrator — enterprise backend service.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for custom frontend and external integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(query.router)
app.include_router(collections.router)
app.include_router(tracing.router)
app.include_router(analytics.router)


@app.get("/", tags=["root"])
async def root_index() -> dict:
    """Root route welcoming users and directing them to docs & frontend UI."""
    return {
        "name": "OmniBrain API",
        "status": "online",
        "version": "0.1.0",
        "docs_url": "http://127.0.0.1:8000/docs",
        "health_check": "http://127.0.0.1:8000/health",
        "instructions": "To launch the Streamlit Web Interface, run 'streamlit run frontend.py' and visit http://localhost:8501"
    }


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "env": settings.app_env}
