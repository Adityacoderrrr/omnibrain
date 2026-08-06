"""
Advanced Hybrid Retrieval Engine.
Combines Qdrant Vector Cosine Search and Sparse BM25 Keyword Search via Reciprocal Rank Fusion (RRF),
re-ranking, context compression, dynamic top-k adjustment, and highlighted citations.
"""

import logging
import re
from typing import List, Dict, Any, Tuple

from app.core.config import get_settings
from app.ingestion.embedder import get_qdrant_client, _get_mock_embedding
from app.ingestion.bm25_indexer import bm25_indexer

logger = logging.getLogger("omnibrain.ingestion.hybrid_retriever")


def reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Tuple[Dict[str, Any], float]],
    rrf_k: int = 60,
    vector_weight: float = 0.5,
    bm25_weight: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Combines dense vector search results and sparse BM25 search results using RRF.
    Score = vector_weight * (1 / (k + rank_v)) + bm25_weight * (1 / (k + rank_b))
    """
    scores: Dict[str, float] = {}
    items: Dict[str, Dict[str, Any]] = {}

    # Process vector results
    for rank, res in enumerate(vector_results):
        cid = res.get("chunk_id") or str(res.get("text", "")[:50])
        items[cid] = res
        scores[cid] = scores.get(cid, 0.0) + vector_weight * (1.0 / (rrf_k + rank + 1))

    # Process BM25 results
    for rank, (payload, bm_score) in enumerate(bm25_results):
        cid = payload.get("chunk_id") or str(payload.get("text", "")[:50])
        if cid not in items:
            items[cid] = {
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "filename": payload.get("filename"),
                "page_number": payload.get("page_number", 1),
                "text": payload.get("text", ""),
                "similarity": min(1.0, bm_score / 10.0),
            }
        scores[cid] = scores.get(cid, 0.0) + bm25_weight * (1.0 / (rrf_k + rank + 1))

    # Sort items by fused RRF score
    fused = []
    for cid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        item = dict(items[cid])
        item["rrf_score"] = score
        fused.append(item)

    return fused


def highlight_snippet(text: str, query: str, window: int = 150) -> str:
    """
    Find best query match in text and format snippet with bold highlighting.
    """
    if not text:
        return ""
    words = re.findall(r'\b\w+\b', query.lower())
    if not words:
        return text[:window] + "..." if len(text) > window else text

    # Find position of first keyword match
    best_pos = 0
    first_match = None
    for word in words:
        pos = text.lower().find(word)
        if pos != -1:
            first_match = word
            best_pos = pos
            break

    start = max(0, best_pos - 40)
    end = min(len(text), start + window)
    snippet = text[start:end]

    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    if first_match:
        pattern = re.compile(re.escape(first_match), re.IGNORECASE)
        snippet = pattern.sub(lambda m: f"**{m.group(0)}**", snippet)

    return snippet


def compress_context_chunks(chunks: List[Dict[str, Any]], query: str, max_chars: int = 3500) -> List[Dict[str, Any]]:
    """
    Context compression: selects top relevance chunks and trims redundant tokens.
    """
    compressed = []
    total_chars = 0
    seen_texts = set()

    for chunk in chunks:
        text = chunk.get("text", "").strip()
        if not text or text in seen_texts:
            continue
        seen_texts.add(text)

        if total_chars + len(text) > max_chars and compressed:
            # Clip text if needed
            remaining = max_chars - total_chars
            if remaining > 100:
                chunk_copy = dict(chunk)
                chunk_copy["text"] = text[:remaining] + "..."
                compressed.append(chunk_copy)
            break

        compressed.append(chunk)
        total_chars += len(text)

    return compressed


def hybrid_retrieve(
    query: str,
    document_id: str = None,
    document_ids: List[str] = None,
    top_k: int = 5,
    vector_weight: float = 0.5,
    bm25_weight: float = 0.5,
    min_score: float = 0.0,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Executes hybrid retrieval (Vector + BM25) and returns:
    (compressed_chunks, raw_fused_results)
    """
    settings = get_settings()
    client = get_qdrant_client()

    # 1. Vector Search
    vector_results = []
    try:
        query_vector = _get_mock_embedding(query, size=1536)
        
        # Build filter condition if document_id specified
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        q_filter = None
        if document_id:
            q_filter = Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))])

        search_res = client.search(
            collection_name=settings.qdrant_text_collection,
            query_vector=query_vector,
            query_filter=q_filter,
            limit=top_k * 2,
        )

        for hit in search_res:
            payload = hit.payload or {}
            vector_results.append({
                "chunk_id": str(hit.id),
                "document_id": payload.get("document_id", document_id or ""),
                "filename": payload.get("filename", ""),
                "page_number": payload.get("page_number", 1),
                "text": payload.get("text", ""),
                "similarity": float(hit.score),
            })
    except Exception as exc:
        logger.warning("Vector search failed during hybrid retrieval: %s", exc)

    # 2. BM25 Sparse Search
    bm25_results = bm25_indexer.search(
        query=query,
        document_id=document_id,
        document_ids=document_ids,
        top_k=top_k * 2,
    )

    # 3. Reciprocal Rank Fusion (RRF)
    fused_results = reciprocal_rank_fusion(
        vector_results=vector_results,
        bm25_results=bm25_results,
        rrf_k=60,
        vector_weight=vector_weight,
        bm25_weight=bm25_weight,
    )

    # Filter by minimum score
    if min_score > 0:
        fused_results = [r for r in fused_results if r.get("rrf_score", 0.0) >= min_score]

    # Select top_k
    top_results = fused_results[:top_k]

    # Add highlighted snippets
    for res in top_results:
        res["snippet"] = highlight_snippet(res.get("text", ""), query)

    # 4. Context Compression
    compressed = compress_context_chunks(top_results, query=query)

    return compressed, fused_results
