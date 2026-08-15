"""
Observability & Tracing API endpoints.
Provides LangSmith/LangFuse style execution graph trace logging, telemetry inspection, and state diff visualization.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/tracing", tags=["tracing"])

# In-memory execution trace store
_TRACE_STORE: Dict[str, Dict[str, Any]] = {}


def record_trace(
    request_id: str,
    session_id: str,
    question: str,
    answer: str,
    agent_trace: List[str],
    trace_details: Dict[str, Any],
    token_analytics: Dict[str, Any],
    execution_time_ms: float = 0.0,
    confidence_scores: Dict[str, float] = None,
    reflection: Dict[str, Any] = None,
) -> None:
    """Record an execution trace into the observability store."""
    _TRACE_STORE[request_id] = {
        "request_id": request_id,
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": answer,
        "agent_trace": agent_trace,
        "trace_details": trace_details,
        "token_analytics": token_analytics,
        "execution_time_ms": execution_time_ms,
        "confidence_scores": confidence_scores or {},
        "reflection": reflection or {},
    }


@router.get("", response_model=dict[str, list[dict]])
async def list_traces() -> dict[str, list[dict]]:
    """List recent execution traces for observability dashboard."""
    traces = list(_TRACE_STORE.values())
    return {"traces": traces}


@router.get("/{request_id}", response_model=dict)
async def get_trace_details(request_id: str) -> dict:
    """Get full details of a specific execution trace including node steps and token analytics."""
    trace = _TRACE_STORE.get(request_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Execution trace '{request_id}' not found.")
    return trace
