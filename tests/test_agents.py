"""
Unit and integration tests for the OmniBrain LangGraph intelligence layer.
"""

import pytest
from agents.state import AgentState
from agents.supervisor import supervisor
from agents.router import route_decision
from agents.search_agent import search_agent
from agents.vision_agent import vision_agent
from agents.sql_agent import sql_agent
from agents.reducer import reducer
from agents.graph import supervisor_graph


def test_supervisor_routing_decisions():
    """Verify that the supervisor correctly routes questions based on keywords."""
    state_sql: AgentState = {
        "question": "show me US database record values for cloud subscriptions",
        "document_id": "doc-123",
        "selected_agent": "",
        "retrieved_docs": [],
        "retrieved_images": [],
        "sql_query": "",
        "sql_result": "",
        "response": "",
        "citations": [],
        "agent_trace": []
    }
    res_sql = supervisor(state_sql)
    assert res_sql["selected_agent"] == "sql"
    assert "Supervisor routed query to: sql agent" in res_sql["agent_trace"]

    state_vision: AgentState = {
        "question": "What does the line chart show on page 2?",
        "document_id": "doc-123",
        "selected_agent": "",
        "retrieved_docs": [],
        "retrieved_images": [],
        "sql_query": "",
        "sql_result": "",
        "response": "",
        "citations": [],
        "agent_trace": []
    }
    res_vision = supervisor(state_vision)
    assert res_vision["selected_agent"] == "vision"

    state_search: AgentState = {
        "question": "Explain the general summary paragraph.",
        "document_id": "doc-123",
        "selected_agent": "",
        "retrieved_docs": [],
        "retrieved_images": [],
        "sql_query": "",
        "sql_result": "",
        "response": "",
        "citations": [],
        "agent_trace": []
    }
    res_search = supervisor(state_search)
    assert res_search["selected_agent"] == "search"


def test_router_decision():
    """Verify that route_decision function correctly maps selected_agent to routing paths."""
    state = {"selected_agent": "sql"}
    assert route_decision(state) == "sql"

    state_invalid = {"selected_agent": "invalid_agent"}
    assert route_decision(state_invalid) == "search"


def test_search_agent_node():
    """Verify Search Agent node executes successfully and returns expected responses."""
    state: AgentState = {
        "question": "What is the revenue growth rate?",
        "document_id": "doc-123",
        "selected_agent": "search",
        "retrieved_docs": [],
        "retrieved_images": [],
        "sql_query": "",
        "sql_result": "",
        "response": "",
        "citations": [],
        "agent_trace": []
    }
    res = search_agent(state)
    assert res["response"] is not None
    assert "Search Agent" in res["agent_trace"][0]


def test_vision_agent_node():
    """Verify Vision Agent node executes successfully and processes image region metadata."""
    state: AgentState = {
        "question": "What is in the figure on page 3?",
        "document_id": "doc-123",
        "selected_agent": "vision",
        "retrieved_docs": [],
        "retrieved_images": [],
        "sql_query": "",
        "sql_result": "",
        "response": "",
        "citations": [],
        "agent_trace": []
    }
    res = vision_agent(state)
    assert res["response"] is not None
    assert "Vision Agent" in res["agent_trace"][0]


def test_sql_agent_node():
    """Verify SQL Agent node executes text-to-SQL logic against target engine."""
    state: AgentState = {
        "question": "What is the total revenue in the database?",
        "document_id": "doc-123",
        "selected_agent": "sql",
        "retrieved_docs": [],
        "retrieved_images": [],
        "sql_query": "",
        "sql_result": "",
        "response": "",
        "citations": [],
        "agent_trace": []
    }
    res = sql_agent(state)
    assert "SELECT" in res["sql_query"]
    assert res["sql_result"] is not None
    assert "SQL Agent" in res["agent_trace"][0]
    assert len(res["citations"]) == 1
    assert res["citations"][0]["source_type"] == "sql"


def test_reducer_node():
    """Verify Reducer node correctly formats empty responses and filters duplicate citations."""
    state: AgentState = {
        "question": "Test query",
        "document_id": "doc-123",
        "selected_agent": "search",
        "retrieved_docs": ["text chunk 1"],
        "retrieved_images": [],
        "sql_query": "",
        "sql_result": "",
        "response": "Final Answer text",
        "citations": [
            {"page": 1, "source_type": "text", "snippet": "dup"},
            {"page": 1, "source_type": "text", "snippet": "dup"}
        ],
        "agent_trace": ["Specialist Trace"]
    }
    res = reducer(state)
    assert res["response"] == "Final Answer text"
    assert len(res["citations"]) == 1
    assert res["agent_trace"] == ["Reducer: Consolidated final response and citations"]


@pytest.mark.anyio
async def test_end_to_end_graph_workflow():
    """Verify that compiling and invoking the StateGraph works end-to-end."""
    initial_state: AgentState = {
        "question": "What is total sales revenue in the sql table?",
        "document_id": "doc-123",
        "selected_agent": "",
        "retrieved_docs": [],
        "retrieved_images": [],
        "sql_query": "",
        "sql_result": "",
        "response": "",
        "citations": [],
        "agent_trace": []
    }
    
    # ainvoke returns the final state from LangGraph
    final_state = await supervisor_graph.ainvoke(initial_state)
    
    assert final_state["selected_agent"] == "sql"
    assert "SELECT" in final_state["sql_query"]
    assert final_state["response"] is not None
    assert len(final_state["citations"]) == 1
    # Check that reducer and supervisor traces are both present
    assert len(final_state["agent_trace"]) >= 2
