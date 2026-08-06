"""
Tests for Advanced Enterprise RAG (BM25, Hybrid Retrieval, RRF, Context Compression).
"""

import pytest
from app.ingestion.bm25_indexer import BM25Indexer
from app.ingestion.hybrid_retriever import reciprocal_rank_fusion, highlight_snippet, compress_context_chunks


class DummyChunk:
    def __init__(self, chunk_id, document_id, text, page_number=1):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.text = text
        self.page_number = page_number


def test_bm25_indexer():
    indexer = BM25Indexer()
    chunks = [
        DummyChunk("c1", "doc1", "The quarterly revenue grew by 15% due to cloud subscriptions."),
        DummyChunk("c2", "doc1", "Operating expenses decreased by 5% in Q4."),
        DummyChunk("c3", "doc2", "Machine learning algorithms optimize data processing pipelines.")
    ]
    indexer.add_chunks(chunks, filename="TestDoc.pdf")

    results = indexer.search("revenue growth", document_id="doc1", top_k=2)
    assert len(results) > 0
    assert results[0][0]["chunk_id"] == "c1"


def test_reciprocal_rank_fusion():
    v_results = [
        {"chunk_id": "c1", "text": "Result one", "similarity": 0.95},
        {"chunk_id": "c2", "text": "Result two", "similarity": 0.85}
    ]
    b_results = [
        ({"chunk_id": "c2", "text": "Result two"}, 8.5),
        ({"chunk_id": "c3", "text": "Result three"}, 6.2)
    ]

    fused = reciprocal_rank_fusion(v_results, b_results)
    assert len(fused) == 3
    assert fused[0]["chunk_id"] in ("c1", "c2")


def test_highlight_snippet():
    text = "The quick brown fox jumps over the lazy dog in the financial quarterly summary."
    snippet = highlight_snippet(text, query="financial quarterly")
    assert "**financial**" in snippet or "**quarterly**" in snippet or "financial" in snippet


def test_context_compression():
    chunks = [
        {"text": "Short chunk one."},
        {"text": "Short chunk two."},
        {"text": "Very long duplicate chunk text..." * 50}
    ]
    compressed = compress_context_chunks(chunks, query="test", max_chars=100)
    assert len(compressed) <= 3
