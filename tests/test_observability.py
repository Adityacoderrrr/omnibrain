"""
Tests for Observability, Reflection Node, Tracing & Analytics endpoints.
"""

import pytest
from agents.reflection import reflection
from app.api.routes.tracing import record_trace, _TRACE_STORE


def test_reflection_node():
    state = {
        "question": "What is revenue?",
        "response": "Revenue grew by 15%.",
        "retrieved_docs": ["Revenue grew by 15%."],
        "citations": [{"document_name": "doc1.pdf", "page": 1, "snippet": "Revenue grew by 15%."}],
    }
    updated_state = reflection(state)
    assert "reflection" in updated_state
    assert updated_state["reflection"]["groundedness_score"] >= 0.80
    assert updated_state["reflection"]["verification_status"] == "PASSED"


def test_trace_recording():
    record_trace(
        request_id="req_test_1",
        session_id="sess_test_1",
        question="Test Q",
        answer="Test A",
        agent_trace=["Supervisor", "Search", "Reducer", "Reflection"],
        trace_details={},
        token_analytics={"total_tokens": 150},
    )
    assert "req_test_1" in _TRACE_STORE
    assert _TRACE_STORE["req_test_1"]["question"] == "Test Q"
