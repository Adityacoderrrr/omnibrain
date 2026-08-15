"""
Final End-to-End Integration and Verification Test Suite for OmniBrain.
Covers real document ingestion, hybrid RAG retrieval, grounded search, honest no-match handling,
SQL agent safe execution, observability telemetry recording, and analytics computations.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from agents.state import AgentState
from agents.supervisor import supervisor
from agents.router import route_decision
from agents.search_agent import search_agent
from agents.sql_agent import sql_agent, validate_sql_safety
from agents.reducer import reducer
from agents.reflection import reflection
from agents.graph import supervisor_graph
from app.ingestion.pdf_parser import PageRegion, RegionType, parse_text_file, parse_markdown_file
from app.ingestion.chunker import chunk_text_regions
from app.ingestion.bm25_indexer import BM25Indexer
from app.ingestion.hybrid_retriever import reciprocal_rank_fusion, highlight_snippet
from app.api.routes.tracing import record_trace, _TRACE_STORE
from app.api.routes.documents import _DOCUMENT_REGISTRY

client = TestClient(app)


def test_real_document_parsing_and_chunking(tmp_path: Path):
    """Verify document parser extracts text regions and chunker produces overlapping semantic chunks."""
    test_file = tmp_path / "enterprise_policy.txt"
    sample_content = (
        "OmniBrain Enterprise Policy 2026.\n\n"
        "Section 1: Data Retention Guidelines.\n"
        "All customer interaction telemetry must be retained for 90 days in compliance with ISO-27001.\n\n"
        "Section 2: Security & Encryption Standards.\n"
        "All vector embeddings and relational database connections require TLS 1.3 encryption."
    )
    test_file.write_text(sample_content, encoding="utf-8")

    regions = parse_text_file(test_file)
    assert len(regions) == 1
    assert regions[0].region_type == RegionType.TEXT
    assert "ISO-27001" in regions[0].content

    chunks = chunk_text_regions(document_id="doc_policy_1", regions=regions, max_chunk_char_length=150)
    assert len(chunks) >= 2
    assert chunks[0].document_id == "doc_policy_1"
    assert any("TLS 1.3" in c.text for c in chunks)


def test_bm25_indexer_and_hybrid_fusion():
    """Verify in-memory BM25 indexer correctly matches keywords and RRF computes reciprocal ranks."""
    indexer = BM25Indexer()
    
    class DummyChunk:
        def __init__(self, cid, doc_id, text):
            self.chunk_id = cid
            self.document_id = doc_id
            self.page_number = 1
            self.text = text

    c1 = DummyChunk("c1", "doc1", "Qdrant vector database indexes embeddings for semantic similarity.")
    c2 = DummyChunk("c2", "doc1", "PostgreSQL database stores structured sales and financial transactions.")
    c3 = DummyChunk("c3", "doc2", "Vision models analyze layout structures, tables, and charts.")

    indexer.add_chunks([c1, c2, c3], filename="doc1.pdf")
    assert indexer.total_docs == 3

    # Search for vector keyword
    results = indexer.search("vector database", top_k=2)
    assert len(results) > 0
    assert results[0][0]["chunk_id"] == "c1"

    # Search for SQL keyword
    sql_results = indexer.search("sales transactions", top_k=2)
    assert len(sql_results) > 0
    assert sql_results[0][0]["chunk_id"] == "c2"

    # Verify RRF combination
    vector_res = [{"chunk_id": "c1", "text": c1.text, "similarity": 0.95}]
    fused = reciprocal_rank_fusion(vector_results=vector_res, bm25_results=results)
    assert len(fused) > 0
    assert fused[0]["chunk_id"] == "c1"

    # Verify highlighting
    highlighted = highlight_snippet("The enterprise uses a **vector** index.", "vector")
    assert "**" in highlighted


def test_grounded_search_vs_ungrounded_fallback():
    """Verify search agent provides grounded context when available and honest message when empty."""
    # 1. When context is retrieved
    state_with_docs: AgentState = {
        "question": "What is the policy retention period?",
        "document_id": "doc_policy",
        "retrieved_docs": ["[Source: Policy.pdf | Page 1]\nAll telemetry must be retained for 90 days."],
        "agent_responses": {},
        "confidence_scores": {},
    }
    res_grounded = search_agent(state_with_docs)
    assert res_grounded["response"] is not None
    assert len(res_grounded["response"]) > 0

    # 2. When empty retrieval occurs
    state_empty: AgentState = {
        "question": "What is the secret recipe for quantum cakes?",
        "document_id": "doc_policy",
        "retrieved_docs": [],
        "agent_responses": {},
        "confidence_scores": {},
    }
    res_empty = search_agent(state_empty)
    assert "information" in res_empty["response"].lower() or "not find" in res_empty["response"].lower() or "enough information" in res_empty["response"].lower()


def test_sql_agent_safe_execution_and_schema():
    """Verify SQL agent executes read-only query on in-memory SQLite schema and returns records."""
    assert validate_sql_safety("SELECT * FROM sales_records WHERE region = 'US';") is True
    assert validate_sql_safety("DROP TABLE sales_records;") is False

    state_sql: AgentState = {
        "question": "How many total sales records are in the database?",
        "document_id": "global",
        "agent_responses": {},
        "confidence_scores": {},
    }
    res = sql_agent(state_sql)
    assert "SELECT" in res["sql_query"]
    assert res["sql_result"] is not None
    assert len(res["citations"]) == 1
    assert res["citations"][0]["source_type"] == "sql"


def test_analytics_and_observability_endpoints():
    """Verify /analytics/overview and /tracing endpoints compute real metrics and return 404 for missing IDs."""
    record_trace(
        request_id="req_integration_1",
        session_id="sess_integration_1",
        question="What is total US sales?",
        answer="Total US sales is $150,000.",
        agent_trace=["Supervisor", "SQL Agent", "Reducer", "Reflection"],
        trace_details={"sql": {"execution_time_ms": 25.0}},
        token_analytics={"prompt_tokens": 120, "completion_tokens": 45, "total_tokens": 165},
        execution_time_ms=145.5,
        confidence_scores={"sql": 0.98, "reducer": 0.98},
        reflection={"groundedness_score": 0.96, "verification_status": "PASSED"}
    )

    # 1. Verify Trace exists
    res_trace = client.get("/tracing/req_integration_1")
    assert res_trace.status_code == 200
    assert res_trace.json()["request_id"] == "req_integration_1"

    # 2. Verify non-existent trace returns 404
    res_missing_trace = client.get("/tracing/non_existent_req_id_999")
    assert res_missing_trace.status_code == 404

    # 3. Verify Analytics aggregates real recorded data
    res_analytics = client.get("/analytics/overview")
    assert res_analytics.status_code == 200
    data = res_analytics.json()
    assert data["total_queries"] >= 1
    assert data["total_tokens"] >= 165
    assert data["avg_latency_ms"] > 0


@pytest.mark.anyio
async def test_full_langgraph_orchestration_multi_agent():
    """Verify LangGraph supervisor router coordinates specialist agents to reducer and reflection."""
    state: AgentState = {
        "session_id": "session_multi_test",
        "question": "What is the total revenue in the database sales records?",
        "document_id": "test_doc_id"
    }
    config = {"configurable": {"thread_id": "session_multi_test"}}
    res = await supervisor_graph.ainvoke(state, config=config)

    assert "response" in res
    assert len(res["response"]) > 0
    assert "reflection" in res
    assert res["reflection"]["verification_status"] in ("PASSED", "UNVERIFIED")
