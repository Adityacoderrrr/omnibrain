"""
Query routes.

Week 1, Day 2 scope: expose the /query contract the Streamlit UI and future
LangGraph supervisor will use, backed by a placeholder response. Real
routing to the Search / Vision / SQL agents is implemented in Week 2.
"""

from fastapi import APIRouter, HTTPException

from app.api.routes.documents import _DOCUMENT_REGISTRY
from app.models.schemas import QueryRequest, QueryResponse

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query_document(request: QueryRequest) -> QueryResponse:
    if request.document_id not in _DOCUMENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Unknown document_id")

    # TODO (Week 2): replace with LangGraph supervisor invocation, e.g.
    # result = await supervisor_graph.ainvoke({"question": request.question, "document_id": request.document_id})

    return QueryResponse(
        document_id=request.document_id,
        question=request.question,
        answer="Agentic reasoning pipeline not yet connected (arrives Week 2 — LangGraph supervisor).",
        citations=[],
        agent_trace=["placeholder: supervisor routing not yet implemented"],
    )
