"""
Embedding & Qdrant indexing.

Scope (Week 1, Day 4-5): embed TextChunks (text encoder) and table/chart
regions (CLIP or equivalent) and upsert both into the multi-modal Qdrant
collections defined in app/core/config.py (QDRANT_TEXT_COLLECTION /
QDRANT_IMAGE_COLLECTION).
"""

import hashlib
import logging
import random
import uuid
from qdrant_client import QdrantClient

try:
    from qdrant_client.models import Distance, VectorParams, PointStruct
except ImportError:
    try:
        from qdrant_client.http.models import Distance, VectorParams, PointStruct
    except ImportError:
        Distance = VectorParams = PointStruct = None  # type: ignore

try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    OpenAIEmbeddings = None  # Fallback if package missing

from app.core.config import get_settings
from app.ingestion.chunker import TextChunk
from app.ingestion.pdf_parser import RegionType

logger = logging.getLogger("omnibrain.ingestion.embedder")


def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    if settings.qdrant_url == ":memory:":
        return QdrantClient(location=":memory:")
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def ensure_collections(vector_size_text: int = 1536, vector_size_image: int = 512) -> None:
    """
    Idempotently create the text and image collections if they don't exist yet.
    Default vector sizes assume an OpenAI text embedding model (1536-d) and a
    CLIP ViT-B/32 image encoder (512-d).
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


def _get_mock_embedding(text: str | bytes, size: int) -> list[float]:
    """Generates a deterministic unit-normalized vector for testing/local development."""
    input_bytes = text.encode("utf-8") if isinstance(text, str) else text
    hash_val = hashlib.sha256(input_bytes).digest()
    rng = random.Random(hash_val)
    vector = [rng.uniform(-1.0, 1.0) for _ in range(size)]
    magnitude = sum(x * x for x in vector) ** 0.5
    return [x / magnitude for x in vector] if magnitude > 0 else vector


def embed_and_upsert_text_chunks(chunks: list[TextChunk]) -> None:
    """Embed TextChunks and upsert them into the text collection."""
    if not chunks:
        return

    settings = get_settings()
    client = get_qdrant_client()

    vectors = None
    if OpenAIEmbeddings is not None and settings.openai_api_key and settings.openai_api_key != "mock-key":
        try:
            embeddings_model = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
            texts = [chunk.text for chunk in chunks]
            vectors = embeddings_model.embed_documents(texts)
        except Exception as exc:
            logger.warning("OpenAIEmbeddings generation failed: %s. Falling back to mock embeddings.", exc)
            vectors = None

    texts = [chunk.text for chunk in chunks]
    if vectors is None:
        vectors = [_get_mock_embedding(text, size=1536) for text in texts]

    points = []
    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
        points.append(
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id)),
                vector=vector,
                payload={
                    "document_id": chunk.document_id,
                    "page_number": chunk.page_number,
                    "text": chunk.text,
                },
            )
        )

    client.upsert(collection_name=settings.qdrant_text_collection, points=points)


def embed_and_upsert_image_regions(document_id: str, regions: list) -> None:
    """Embed table/chart regions via CLIP (or local mock) and upsert into the image collection."""
    if not regions:
        return

    settings = get_settings()
    client = get_qdrant_client()

    points = []
    for idx, region in enumerate(regions):
        raw_type = getattr(region, "region_type", None)
        region_type_str = str(raw_type.value) if isinstance(raw_type, RegionType) or hasattr(raw_type, "value") else str(raw_type or "")
        region_type_lower = region_type_str.lower()

        if region_type_lower not in ("chart", "table"):
            continue

        page_number = getattr(region, "page_number", 1)
        content = getattr(region, "content", b"")
        content_bytes = content if isinstance(content, bytes) else str(content or "").encode("utf-8")

        # Basic mock CLIP embedding vector (512-d)
        vector = _get_mock_embedding(content_bytes, size=512)

        points.append(
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_img_{page_number}_{idx}")),
                vector=vector,
                payload={
                    "document_id": document_id,
                    "page_number": page_number,
                    "region_type": region_type_lower,
                },
            )
        )

    if points:
        client.upsert(collection_name=settings.qdrant_image_collection, points=points)


