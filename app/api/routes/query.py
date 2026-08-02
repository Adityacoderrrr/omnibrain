"""
Query routes.

Integrates the compiled LangGraph supervisor orchestration pipeline to answer queries
about uploaded documents using text, image, or database specialists.
"""

import uuid
from fastapi import APIRouter, HTTPException

from app.api.routes.documents import _DOCUMENT_REGISTRY
from app.models.schemas import QueryRequest, QueryResponse, Citation
from agents.graph import supervisor_graph

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query_document(request: QueryRequest) -> QueryResponse:
    if request.document_id not in _DOCUMENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Unknown document_id")

    session_id = request.session_id or f"session_{request.document_id}"
    request_id = request.request_id or f"req_{uuid.uuid4().hex[:8]}"

    # Construct the initial state input for the LangGraph pipeline
    initial_state = {
        "session_id": session_id,
        "request_id": request_id,
        "question": request.question,
        "document_id": request.document_id,
        "selected_agent": "",
        "selected_agents": [],
        "retrieved_docs": [],
        "retrieved_images": [],
        "sql_query": "",
        "sql_result": "",
        "sql_explanation": "",
        "agent_responses": {},
        "confidence_scores": {},
        "execution_metrics": {},
        "response": "",
        "citations": [],
        "agent_trace": [],
        "errors": [],
    }

    # Pass thread_id to LangGraph checkpointer for session state recovery
    config = {"configurable": {"thread_id": session_id}}

    try:
        # Asynchronously invoke the LangGraph execution flow
        result = await supervisor_graph.ainvoke(initial_state, config=config)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred in the agentic orchestration graph: {exc}"
        )

    # Convert dictionary-based citations in the state to model objects
    formatted_citations = [
        Citation(
            page=cit.get("page", 1),
            source_type=cit.get("source_type", "text"),
            snippet=cit.get("snippet")
        )
        for cit in result.get("citations", [])
    ]

    return QueryResponse(
        document_id=result.get("document_id", request.document_id),
        question=result.get("question", request.question),
        answer=result.get("response", "Could not synthesize response."),
        session_id=session_id,
        request_id=request_id,
        sql_explanation=result.get("sql_explanation"),
        confidence_scores=result.get("confidence_scores", {}),
        citations=result.get("citations", []),
        agent_trace=result.get("agent_trace", []),
        trace_details=result.get("trace_details", {}),
        token_analytics=result.get("token_analytics", {}),
    )

