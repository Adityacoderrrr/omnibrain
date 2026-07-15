"""
Document upload routes.

Week 1 scope: accept an uploaded PDF asynchronously, persist it to disk,
kick off the parse → chunk → embed ingestion pipeline as a background task,
and return a document_id + status the client can poll.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File

from app.core.config import get_settings
from app.models.schemas import DocumentStatus, DocumentStatusResponse, DocumentUploadResponse

router = APIRouter(prefix="/documents", tags=["documents"])

# In-memory registry — replaced by a real DB once needed.
_DOCUMENT_REGISTRY: dict[str, dict] = {}

ALLOWED_CONTENT_TYPES = {"application/pdf"}


def _run_ingestion(document_id: str, pdf_path: Path) -> None:
    """
    Background task: parse the PDF → chunk text → embed and index in Qdrant.
    Marks the document status as READY on success or FAILED on error.
    """
    try:
        _DOCUMENT_REGISTRY[document_id]["status"] = DocumentStatus.PARSING
        from app.ingestion.pdf_parser import parse_pdf
        regions = parse_pdf(pdf_path)

        _DOCUMENT_REGISTRY[document_id]["status"] = DocumentStatus.EMBEDDING
        from app.ingestion.chunker import chunk_text_regions
        chunks = chunk_text_regions(document_id, regions)

        from app.ingestion.embedder import embed_and_upsert_text_chunks, embed_and_upsert_image_regions
        embed_and_upsert_text_chunks(chunks)
        embed_and_upsert_image_regions(document_id, regions)

        _DOCUMENT_REGISTRY[document_id]["status"] = DocumentStatus.READY
    except Exception as exc:
        _DOCUMENT_REGISTRY[document_id]["status"] = DocumentStatus.FAILED
        _DOCUMENT_REGISTRY[document_id]["error"] = str(exc)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """
    Accept a PDF upload and queue it for ingestion.
    Returns immediately with a document_id; ingestion runs in the background.
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

    # Kick off the full ingestion pipeline as a background task
    background_tasks.add_task(_run_ingestion, document_id, destination)

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

