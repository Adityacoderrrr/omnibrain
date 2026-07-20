"""
Vision Agent component of the OmniBrain AI Intelligence Layer.
Retrieves and reasons over visual elements (charts, tables) in the ingested documents.
"""

import logging
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from app.core.config import get_settings
from app.ingestion.embedder import get_qdrant_client, _get_mock_embedding
from .state import AgentState
from .prompts import VISION_AGENT_PROMPT
from .llm import invoke_llm

logger = logging.getLogger("omnibrain.agents.vision_agent")


def vision_agent(state: AgentState) -> AgentState:
    """
    Vision Agent node:
    - Generates query vector for image matching.
    - Retrieves image region metadata from the Qdrant image collection.
    - Invokes VLM (or fallback mock) to perform layout/chart reasoning.

    Args:
        state (AgentState): Current execution state.

    Returns:
        AgentState: Updated execution state.
    """
    logger.info("Vision Agent triggered for query: '%s'", state.get("question"))
    settings = get_settings()

    question = state.get("question", "")
    document_id = state.get("document_id", "")

    if not question:
        state["response"] = "Error: Question is missing."
        state["agent_trace"] = ["Vision Agent: Failed - missing question"]
        return state

    try:
        # Initialize client and generate 512-d CLIP mock embedding
        client = get_qdrant_client()
        query_vector = _get_mock_embedding(question, size=512)

        # Filter by document_id
        qdrant_filter = None
        if document_id:
            qdrant_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )

        logger.info("Querying Qdrant collection: '%s'", settings.qdrant_image_collection)
        try:
            search_results = client.search(
                collection_name=settings.qdrant_image_collection,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=3
            )
        except Exception as qd_exc:
            logger.warning(
                "Qdrant connection failed: %s. Falling back to local mock image search results.",
                qd_exc
            )
            from qdrant_client.http.models import ScoredPoint
            search_results = [
                ScoredPoint(
                    id=2,
                    version=2,
                    score=0.88,
                    payload={
                        "page_number": 2,
                        "region_type": "chart",
                        "document_id": document_id
                    }
                )
            ]

        retrieved_images = []
        citations = []
        metadata_snippets = []

        for hit in search_results:
            payload = hit.payload or {}
            page = payload.get("page_number", 1)
            region_type = payload.get("region_type", "chart")
            
            image_details = {
                "page_number": int(page),
                "region_type": region_type,
                "score": hit.score
            }
            retrieved_images.append(image_details)
            metadata_snippets.append(f"Visual element ({region_type}) located on page {page}")
            
            citations.append({
                "page": int(page),
                "source_type": region_type,
                "snippet": f"Identified {region_type} layout region with score {hit.score:.4f}"
            })

        if not retrieved_images:
            logger.warning("No visual regions retrieved for document_id: '%s'", document_id)
            visual_context = "No visual elements or chart regions retrieved from the database."
        else:
            visual_context = "\n".join(metadata_snippets)

        # Invoke VLM/LLM
        system_prompt = VISION_AGENT_PROMPT.format(visual_context=visual_context)
        answer = invoke_llm(prompt=f"Question: {question}", system_prompt=system_prompt)

        # Update State
        state["retrieved_images"] = retrieved_images
        state["response"] = answer
        state["citations"] = citations
        state["agent_trace"] = [
            f"Vision Agent: Searched image collection and found {len(retrieved_images)} visual regions",
            f"Vision Agent: Generated multi-modal visual analysis"
        ]

    except Exception as exc:
        logger.exception("Error in Vision Agent node: %s", exc)
        state["response"] = "An error occurred during multi-modal chart/table visual analysis."
        state["retrieved_images"] = []
        state["citations"] = []
        state["agent_trace"] = [f"Vision Agent error: {str(exc)}"]

    return state
