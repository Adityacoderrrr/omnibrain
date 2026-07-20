"""
Query routes.

Integrates the compiled LangGraph supervisor orchestration pipeline to answer queries
about uploaded documents using text, image, or database specialists.
"""

from fastapi import APIRouter, HTTPException

from app.api.routes.documents import _DOCUMENT_REGISTRY
from app.models.schemas import QueryRequest, QueryResponse, Citation
from agents.graph import supervisor_graph

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query_document(request: QueryRequest) -> QueryResponse:
    if request.document_id not in _DOCUMENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Unknown document_id")

    # Construct the initial state input for the LangGraph pipeline
    initial_state = {
        "question": request.question,
        "document_id": request.document_id,
        "selected_agent": "",
        "retrieved_docs": [],
        "retrieved_images": [],
        "sql_query": "",
        "sql_result": "",
        "response": "",
        "citations": [],
        "agent_trace": [],
    }

    try:
        # Asynchronously invoke the LangGraph execution flow
        result = await supervisor_graph.ainvoke(initial_state)
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
        citations=formatted_citations,
        agent_trace=result.get("agent_trace", []),
    )

