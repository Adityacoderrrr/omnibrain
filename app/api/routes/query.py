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

    # Record trace in observability store
    try:
        from app.api.routes.tracing import record_trace
        record_trace(
            request_id=request_id,
            session_id=session_id,
            question=request.question,
            answer=result.get("response", ""),
            agent_trace=result.get("agent_trace", []),
            trace_details=result.get("trace_details", {}),
            token_analytics=result.get("token_analytics", {}),
            execution_time_ms=sum(result.get("execution_metrics", {}).values()),
            confidence_scores=result.get("confidence_scores", {}),
            reflection=result.get("reflection", {}),
        )
    except Exception:
        pass

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
        follow_up_questions=result.get("follow_up_questions", []),
        reflection=result.get("reflection", {}),
    )


@router.post("/stream")
async def stream_query(request: QueryRequest):
    """
    Server-Sent Events (SSE) streaming endpoint for real-time response generation.
    Streams execution steps, intermediate node updates, and token tokens.
    """
    import asyncio
    import json
    from fastapi.responses import StreamingResponse

    async def event_generator():
        # Step 1: Initial event
        yield f"data: {json.dumps({'event': 'started', 'request_id': request.request_id or 'req_stream'})}\n\n"
        await asyncio.sleep(0.05)

        # Run query pipeline
        res = await query_document(request)

        # Step 2: Stream agent steps
        for step in res.agent_trace:
            yield f"data: {json.dumps({'event': 'step', 'step': step})}\n\n"
            await asyncio.sleep(0.05)

        # Step 3: Stream answer tokens in chunks
        answer = res.answer
        words = answer.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            yield f"data: {json.dumps({'event': 'token', 'text': chunk})}\n\n"
            await asyncio.sleep(0.02)

        # Step 4: Stream final completion payload
        final_payload = {
            "event": "done",
            "document_id": res.document_id,
            "session_id": res.session_id,
            "request_id": res.request_id,
            "confidence_scores": res.confidence_scores,
            "citations": res.citations,
            "follow_up_questions": res.follow_up_questions,
            "token_analytics": res.token_analytics,
            "reflection": res.reflection,
        }
        yield f"data: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


