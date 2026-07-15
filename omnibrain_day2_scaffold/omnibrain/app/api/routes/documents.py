"""
Document upload routes.

Week 1, Day 2 scope: accept an uploaded PDF asynchronously, persist it to disk,
and return a document_id + status the client can poll. The actual parsing /
chunking / embedding pipeline (app/ingestion/) is wired in on Day 3-5.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.core.config import get_settings
from app.models.schemas import DocumentStatus, DocumentStatusResponse, DocumentUploadResponse

router = APIRouter(prefix="/documents", tags=["documents"])

# In-memory registry for now — replaced by a real DB/queue once ingestion lands.
_DOCUMENT_REGISTRY: dict[str, dict] = {}

ALLOWED_CONTENT_TYPES = {"application/pdf"}


@router.post("/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """
    Accept a PDF upload asynchronously and queue it for ingestion.
    Returns immediately with a document_id; ingestion happens out-of-band.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported right now.")

    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    document_id = str(uuid.uuid4())
    destination = upload_dir / f"{document_id}.pdf"

    contents = await file.read()
    destination.write_bytes(contents)

    submitted_at = datetime.now(timezone.utc)
    _DOCUMENT_REGISTRY[document_id] = {
        "filename": file.filename,
        "status": DocumentStatus.RECEIVED,
        "submitted_at": submitted_at,
        "path": str(destination),
    }

    # TODO (Day 3+): enqueue background task -> app.ingestion pipeline
    # background_tasks.add_task(run_ingestion_pipeline, document_id)

    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        status=DocumentStatus.RECEIVED,
        submitted_at=submitted_at,
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str) -> DocumentStatusResponse:
    record = _DOCUMENT_REGISTRY.get(document_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Unknown document_id")

    return DocumentStatusResponse(
        document_id=document_id,
        status=record["status"],
    )
