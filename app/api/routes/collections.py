"""
Collections management routes.
Allows organizing uploaded documents into custom knowledge base collections.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.models.schemas import CollectionCreate, CollectionResponse
from app.api.routes.documents import _DOCUMENT_REGISTRY

router = APIRouter(prefix="/collections", tags=["collections"])

_COLLECTION_REGISTRY: dict[str, dict] = {}


@router.post("", response_model=CollectionResponse, status_code=201)
async def create_collection(payload: CollectionCreate) -> CollectionResponse:
    col_id = f"col_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    record = {
        "collection_id": col_id,
        "name": payload.name,
        "description": payload.description or "",
        "tags": payload.tags or [],
        "document_ids": [],
        "created_at": now,
    }
    _COLLECTION_REGISTRY[col_id] = record
    return CollectionResponse(
        collection_id=col_id,
        name=payload.name,
        description=payload.description,
        tags=payload.tags,
        document_count=0,
        created_at=now,
    )


@router.get("", response_model=dict[str, list[dict]])
async def list_collections() -> dict[str, list[dict]]:
    cols = []
    for col_id, item in _COLLECTION_REGISTRY.items():
        cols.append({
            "collection_id": col_id,
            "name": item.get("name"),
            "description": item.get("description"),
            "tags": item.get("tags", []),
            "document_count": len(item.get("document_ids", [])),
            "created_at": str(item.get("created_at")),
        })
    return {"collections": cols}


@router.delete("/{collection_id}", response_model=dict[str, str])
async def delete_collection(collection_id: str) -> dict[str, str]:
    if collection_id not in _COLLECTION_REGISTRY:
        raise HTTPException(status_code=404, detail="Collection not found")
    del _COLLECTION_REGISTRY[collection_id]
    return {"message": f"Collection '{collection_id}' deleted successfully"}
