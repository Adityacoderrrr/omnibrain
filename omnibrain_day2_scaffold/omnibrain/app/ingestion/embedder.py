"""
Embedding & Qdrant indexing.

Scope (Week 1, Day 4-5): embed TextChunks (text encoder) and table/chart
regions (CLIP or equivalent) and upsert both into the multi-modal Qdrant
collections defined in app/core/config.py (QDRANT_TEXT_COLLECTION /
QDRANT_IMAGE_COLLECTION).

Not yet implemented — scaffolding committed on Day 2. Qdrant client wiring
below is functional (collection bootstrap); embed/upsert logic lands next.
"""

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import get_settings


def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def ensure_collections(vector_size_text: int = 1536, vector_size_image: int = 512) -> None:
    """
    Idempotently create the text and image collections if they don't exist yet.
    Default vector sizes assume an OpenAI text embedding model (1536-d) and a
    CLIP ViT-B/32 image encoder (512-d) — adjust once models are finalized.
    """
    settings = get_settings()
    client = get_qdrant_client()

    existing = {c.name for c in client.get_collections().collections}

    if settings.qdrant_text_collection not in existing:
        client.create_collection(
            collection_name=settings.qdrant_text_collection,
            vectors_config=VectorParams(size=vector_size_text, distance=Distance.COSINE),
        )

    if settings.qdrant_image_collection not in existing:
        client.create_collection(
            collection_name=settings.qdrant_image_collection,
            vectors_config=VectorParams(size=vector_size_image, distance=Distance.COSINE),
        )


def embed_and_upsert_text_chunks(chunks: list) -> None:
    """TODO (Day 4): embed TextChunks and upsert into the text collection."""
    raise NotImplementedError("Text embedding lands on Day 4 of Week 1.")


def embed_and_upsert_image_regions(regions: list) -> None:
    """TODO (Day 5): embed table/chart regions via CLIP and upsert into the image collection."""
    raise NotImplementedError("Image embedding lands on Day 5 of Week 1.")
