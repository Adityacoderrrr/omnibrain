"""
Unit and integration tests for the OmniBrain LangGraph intelligence layer.
Tests Supervisor JSON routing, Specialist Agent nodes, SQL Safety validation, Reducer consolidation, and End-to-End StateGraph execution.
"""

import pytest
from agents.state import AgentState
from agents.supervisor import supervisor
from agents.router import route_decision
from agents.search_agent import search_agent
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


def test_supervisor_routing_decisions():
    """Verify that the supervisor correctly assigns selected_agents based on query analysis."""
    state_sql: AgentState = {
        "question": "show me US database record values for cloud subscriptions",
        "document_id": "doc-123"
    }
    res_sql = supervisor(state_sql)
    assert "sql" in res_sql["selected_agents"]
    assert res_sql["selected_agent"] == "sql"

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


def test_search_agent_node():
    """Verify Search Agent node executes successfully and populates agent_responses."""
    state: AgentState = {
        "question": "What is the revenue growth rate?",
        "document_id": "doc-123"
    }
    res = search_agent(state)
    assert res["response"] is not None
    assert "search" in res.get("agent_responses", {})
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
    assert "Vision Agent" in res["agent_trace"][0]


def test_sql_agent_node():
    """Verify SQL Agent node generates safe text-to-SQL queries and executes against database."""
    state: AgentState = {
        "question": "What is the total revenue in the database?",
        "document_id": "doc-123"
    }
    res = sql_agent(state)
    assert "SELECT" in res["sql_query"]
    assert res["sql_result"] is not None
    assert "sql" in res.get("agent_responses", {})
    assert "SQL Agent" in res["agent_trace"][0]
    assert len(res["citations"]) == 1
    assert res["citations"][0]["source_type"] == "sql"


def test_reducer_node_single_and_multi():
    """Verify Reducer node correctly handles single responses, multi-agent outputs, and citation deduplication."""
    state_single: AgentState = {
        "question": "Test query",
        "agent_responses": {"search": "Single search answer"},
        "citations": [
            {"page": 1, "source_type": "text", "snippet": "dup"},
            {"page": 1, "source_type": "text", "snippet": "dup"}
        ]
    }
    res_single = reducer(state_single)
    assert res_single["response"] == "Single search answer"
    assert len(res_single["citations"]) == 1

    state_multi: AgentState = {
        "question": "Compare chart sales with SQL revenue",
        "agent_responses": {
            "search": "Revenue grew by 15%",
            "sql": "Total revenue is $150,000"
        },
        "citations": []
    }
    res_multi = reducer(state_multi)
    assert res_multi["response"] is not None
    assert "Consolidated Findings" in res_multi["response"] or len(res_multi["response"]) > 0


@pytest.mark.anyio
async def test_end_to_end_graph_workflow():
    """Verify that compiling and invoking the StateGraph works end-to-end through LangGraph execution."""
    initial_state: AgentState = {
        "question": "What is total sales revenue in the sql table?",
        "document_id": "doc-123"
    }
    
    final_state = await supervisor_graph.ainvoke(initial_state)
    
    assert final_state["selected_agent"] == "sql"
    assert "SELECT" in final_state["sql_query"]
    assert final_state["response"] is not None
    assert len(final_state["citations"]) == 1
    assert len(final_state["agent_trace"]) >= 1
