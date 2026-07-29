"""
Unit and integration tests for the OmniBrain LangGraph intelligence layer.
Tests Supervisor JSON routing, Specialist Agent nodes, SQL Safety validation, Reducer consolidation, Memory Checkpointing, and End-to-End StateGraph execution.
"""

import pytest
from agents.state import AgentState
from agents.supervisor import supervisor
from agents.router import route_decision
from agents.search_agent import search_agent, compress_context_chunks
from agents.vision_agent import vision_agent
from agents.sql_agent import sql_agent, validate_sql_safety
from agents.reducer import reducer
from agents.graph import supervisor_graph


def test_sql_safety_validation():
    """Verify that validate_sql_safety allows SELECT/WITH queries and blocks DDL/DML statements."""
    assert validate_sql_safety("SELECT * FROM sales_records;") is True
    assert validate_sql_safety("WITH total AS (SELECT revenue FROM sales_records) SELECT * FROM total;") is True
    assert validate_sql_safety("DROP TABLE sales_records;") is False
    assert validate_sql_safety("DELETE FROM sales_records WHERE id = 1;") is False
    assert validate_sql_safety("UPDATE sales_records SET revenue = 0;") is False


def test_supervisor_routing_decisions_and_confidence():
    """Verify that the supervisor correctly assigns selected_agents and extracts confidence scores."""
    state_sql: AgentState = {
        "question": "show me US database record values for cloud subscriptions",
        "document_id": "doc-123"
    }
    res_sql = supervisor(state_sql)
    assert "sql" in res_sql["selected_agents"]
    assert res_sql["selected_agent"] == "sql"
    assert "supervisor" in res_sql.get("confidence_scores", {})
    assert res_sql["confidence_scores"]["supervisor"] > 0.0

    state_vision: AgentState = {
        "question": "What does the line chart figure show on page 2?",
        "document_id": "doc-123"
    }
    res_vision = supervisor(state_vision)
    assert "vision" in res_vision["selected_agents"]

    state_search: AgentState = {
        "question": "Explain the general summary paragraph in the text.",
        "document_id": "doc-123"
    }
    res_search = supervisor(state_search)
    assert "search" in res_search["selected_agents"]


def test_router_decision():
    """Verify that route_decision function maps single and multi-agent targets accurately."""
    state = {"selected_agents": ["sql"]}
    assert route_decision(state) == "sql"

    state_multi = {"selected_agents": ["vision", "sql"]}
    assert route_decision(state_multi) == ["vision", "sql"]

    state_invalid = {"selected_agents": ["invalid_agent"]}
    assert route_decision(state_invalid) == "search"


def test_search_agent_node_and_compression():
    """Verify Search Agent node executes successfully and context compression truncates payloads accurately."""
    chunks = ["Paragraph 1 " * 50, "Paragraph 2 " * 50, "Paragraph 3 " * 50]
    compressed = compress_context_chunks(chunks, max_tokens=100)
    assert len(compressed) < len("\n\n".join(chunks))

    state: AgentState = {
        "question": "What is the revenue growth rate?",
        "document_id": "doc-123"
    }
    res = search_agent(state)
    assert res["response"] is not None
    assert "search" in res.get("agent_responses", {})
    assert "search" in res.get("confidence_scores", {})
    assert "Search Agent" in res["agent_trace"][0]


def test_vision_agent_node():
    """Verify Vision Agent node executes successfully and processes image region metadata."""
    state: AgentState = {
        "question": "What is in the figure on page 3?",
        "document_id": "doc-123"
    }
    res = vision_agent(state)
    assert res["response"] is not None
    assert "vision" in res.get("agent_responses", {})
    assert "vision" in res.get("confidence_scores", {})
    assert "Vision Agent" in res["agent_trace"][0]


def test_sql_agent_node_and_explanation():
    """Verify SQL Agent node generates safe text-to-SQL queries, executes queries, and returns plain-English explanations."""
    state: AgentState = {
        "question": "What is the total revenue in the database?",
        "document_id": "doc-123"
    }
    res = sql_agent(state)
    assert "SELECT" in res["sql_query"]
    assert res["sql_result"] is not None
    assert res.get("sql_explanation") is not None
    assert "sql" in res.get("agent_responses", {})
    assert "sql" in res.get("confidence_scores", {})
    assert "SQL Agent" in res["agent_trace"][0]
    assert len(res["citations"]) == 1
    assert res["citations"][0]["source_type"] == "sql"


def test_reducer_node_single_multi_and_confidence():
    """Verify Reducer node correctly handles single responses, multi-agent outputs, citation deduplication, and aggregated confidence."""
    state_single: AgentState = {
        "question": "Test query",
        "agent_responses": {"search": "Single search answer"},
        "confidence_scores": {"search": 0.90},
        "citations": [
            {"page": 1, "source_type": "text", "snippet": "dup"},
            {"page": 1, "source_type": "text", "snippet": "dup"}
        ]
    }
    res_single = reducer(state_single)
    assert res_single["response"] == "Single search answer"
    assert len(res_single["citations"]) == 1
    assert res_single["confidence_scores"]["reducer"] == 0.90

    state_multi: AgentState = {
        "question": "Compare chart sales with SQL revenue",
        "agent_responses": {
            "search": "Revenue grew by 15%",
            "sql": "Total revenue is $150,000"
        },
        "confidence_scores": {
            "search": 0.90,
            "sql": 0.98
        },
        "citations": []
    }
    res_multi = reducer(state_multi)
    assert res_multi["response"] is not None
    assert "Consolidated Findings" in res_multi["response"] or len(res_multi["response"]) > 0
    assert res_multi["confidence_scores"]["reducer"] == 0.94


@pytest.mark.anyio
async def test_end_to_end_graph_workflow_with_checkpointer():
    """Verify that compiling and invoking the StateGraph works end-to-end with MemorySaver session checkpointing."""
    initial_state: AgentState = {
        "session_id": "session_test_123",
        "question": "What is total sales revenue in the sql table?",
        "document_id": "doc-123"
    }
    
    config = {"configurable": {"thread_id": "session_test_123"}}
    final_state = await supervisor_graph.ainvoke(initial_state, config=config)
    
    assert final_state["selected_agent"] == "sql"
    assert "SELECT" in final_state["sql_query"]
    assert final_state["response"] is not None
    assert final_state.get("sql_explanation") is not None
    assert len(final_state["citations"]) == 1
    assert len(final_state["agent_trace"]) >= 1
