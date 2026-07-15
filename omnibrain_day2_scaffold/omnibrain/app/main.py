"""
OmniBrain FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.api.routes import documents, query
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="OmniBrain API",
    description="Agentic Multi-Modal RAG Orchestrator — backend service.",
    version="0.1.0",
)

app.include_router(documents.router)
app.include_router(query.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "env": settings.app_env}
