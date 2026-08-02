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

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/markdown",
    "text/plain",
    "application/octet-stream",
}


def _run_ingestion(document_id: str, file_path: Path) -> None:
    """
    Background task: parse document → chunk text → embed and index in Qdrant.
    Marks the document status as READY on success or FAILED on error.
    """
    filename = _DOCUMENT_REGISTRY.get(document_id, {}).get("filename", document_id)
    try:
        _DOCUMENT_REGISTRY[document_id]["status"] = DocumentStatus.PARSING
        from app.ingestion.pdf_parser import parse_document
        regions = parse_document(file_path)

        page_numbers = {getattr(r, "page_number", 1) for r in regions}
        _DOCUMENT_REGISTRY[document_id]["page_count"] = len(page_numbers) if page_numbers else 1

        _DOCUMENT_REGISTRY[document_id]["status"] = DocumentStatus.EMBEDDING
        from app.ingestion.chunker import chunk_text_regions
        chunks = chunk_text_regions(document_id, regions)
        _DOCUMENT_REGISTRY[document_id]["chunk_count"] = len(chunks)

        from app.ingestion.embedder import embed_and_upsert_text_chunks, embed_and_upsert_image_regions
        embed_and_upsert_text_chunks(chunks, filename=filename)
        embed_and_upsert_image_regions(document_id, regions, filename=filename)

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
    Accept a document upload (PDF, DOCX, PPTX, MD, TXT) and queue it for ingestion.
    Returns immediately with a document_id; ingestion runs in the background.
    """
    ext = Path(file.filename or "").suffix.lower()
    if file.content_type not in ALLOWED_CONTENT_TYPES and ext not in (".pdf", ".docx", ".pptx", ".md", ".txt"):
        raise HTTPException(status_code=415, detail="Unsupported format. Upload PDF, DOCX, PPTX, MD, or TXT files.")

    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    document_id = str(uuid.uuid4())
    destination = upload_dir / f"{document_id}{ext or '.pdf'}"

    contents = await file.read()
    destination.write_bytes(contents)

    submitted_at = datetime.now(timezone.utc)
    _DOCUMENT_REGISTRY[document_id] = {
        "document_id": document_id,
        "filename": file.filename,
        "status": DocumentStatus.RECEIVED,
        "submitted_at": submitted_at,
        "path": str(destination),
        "file_size": len(contents),
        "page_count": 0,
        "chunk_count": 0,
    }

    # Kick off the full ingestion pipeline as a background task
    background_tasks.add_task(_run_ingestion, document_id, destination)

    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        status=DocumentStatus.RECEIVED,
        submitted_at=submitted_at,
    )



@router.get("", response_model=dict[str, list[dict]])
async def list_documents() -> dict[str, list[dict]]:
    """List all registered uploaded documents and their ingestion metadata."""
    docs = []
    for doc_id, meta in _DOCUMENT_REGISTRY.items():
        docs.append({
            "document_id": doc_id,
            "filename": meta.get("filename"),
            "status": meta.get("status"),
            "page_count": meta.get("page_count", 0),
            "chunk_count": meta.get("chunk_count", 0),
            "submitted_at": meta.get("submitted_at").isoformat() if isinstance(meta.get("submitted_at"), datetime) else str(meta.get("submitted_at")),
            "error": meta.get("error"),
        })
    return {"documents": docs}


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str) -> DocumentStatusResponse:
    record = _DOCUMENT_REGISTRY.get(document_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Unknown document_id")

    return DocumentStatusResponse(
        document_id=document_id,
        status=record["status"],
    )


@router.delete("/{document_id}", response_model=dict[str, str])
async def delete_document(document_id: str) -> dict[str, str]:
    """Delete a document record, remove local PDF file, and purge vectors from Qdrant."""
    record = _DOCUMENT_REGISTRY.get(document_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 1. Remove file from storage
    file_path = Path(record.get("path", ""))
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass

    # 2. Delete vectors from Qdrant
    from app.ingestion.embedder import delete_document_vectors
    delete_document_vectors(document_id)

    # 3. Delete from registry
    del _DOCUMENT_REGISTRY[document_id]

    return {"message": f"Document '{document_id}' successfully deleted."}


