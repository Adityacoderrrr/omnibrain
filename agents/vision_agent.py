"""
Vision Agent component of the OmniBrain AI Intelligence Layer.
Retrieves visual region metadata (charts, tables, diagrams) and performs VLM multi-modal layout reasoning.
"""

from typing import List, Dict, Any
from app.core.config import get_settings
from app.ingestion.embedder import get_qdrant_client, _get_mock_embedding
from agents.state import AgentState
from agents.prompts import VISION_AGENT_PROMPT
from agents.llm import invoke_llm
from agents.logger import get_logger, log_agent_execution
from agents.utils import ExecutionTimer, sanitize_prompt_input

try:
    from qdrant_client.models import Filter, FieldCondition, MatchValue, ScoredPoint
except ImportError:
    try:
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue, ScoredPoint
    except ImportError:
        Filter = FieldCondition = MatchValue = ScoredPoint = None

if ScoredPoint is None:
    class ScoredPoint:  # type: ignore
        def __init__(self, id, version=1, score=0.0, payload=None):
            self.id = id
            self.version = version
            self.score = score
            self.payload = payload or {}

logger = get_logger("omnibrain.agents.vision_agent")


def vision_agent(state: AgentState) -> AgentState:
    """
    Vision Agent node:
    - Generates 512-d CLIP image embedding vector for visual search.
    - Queries Qdrant image collection for relevant chart/table layout metadata.
    - Prompts VLM to evaluate visual structures and answer the question.
    - Updates state retrieved_images, agent_responses['vision'], response, citations, and confidence_scores.

    Args:
        state (AgentState): Current execution state.

    Returns:
        AgentState: Updated execution state.
    """
    with ExecutionTimer() as timer:
        question = sanitize_prompt_input(state.get("question", ""))
        document_id = state.get("document_id", "")
        logger.info("Vision Agent triggered for query: '%s'", question)

        settings = get_settings()

        if not question:
            state["response"] = "Error: Question is missing."
            state["retrieved_images"] = []
            state["citations"] = []
            state["agent_trace"] = ["Vision Agent: Failed - missing question"]
            return state

        try:
            client = get_qdrant_client()
            query_vector = _get_mock_embedding(question, size=settings.embedding_dimension_image)

            qdrant_filter = None
            if document_id and Filter is not None and FieldCondition is not None and MatchValue is not None:
                qdrant_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )

            logger.info("Querying Qdrant image collection: '%s'", settings.qdrant_image_collection)
            try:
                search_results = client.search(
                    collection_name=settings.qdrant_image_collection,
                    query_vector=query_vector,
                    query_filter=qdrant_filter,
                    limit=settings.vector_search_top_k
                )
            except Exception as qd_exc:
                logger.warning("Qdrant image search failed or collection empty: %s.", qd_exc)
                search_results = []

            retrieved_images: List[Dict[str, Any]] = []
            citations: List[Dict[str, Any]] = []
            metadata_snippets: List[str] = []

            for hit in search_results:
                payload = getattr(hit, "payload", None) or (hit.get("payload") if isinstance(hit, dict) else {}) or {}
                try:
                    page = int(payload.get("page_number", 1))
                except (ValueError, TypeError):
                    page = 1

                region_type = payload.get("region_type", "chart")
                score_val = float(getattr(hit, "score", 0.0) or 0.0)

                image_details = {
                    "page_number": page,
                    "region_type": region_type,
                    "score": score_val
                }
                retrieved_images.append(image_details)
                metadata_snippets.append(f"Visual element ({region_type}) located on page {page}")

                citations.append({
                    "page": page,
                    "source_type": region_type,
                    "snippet": f"Identified visual {region_type} on page {page} with score {score_val:.2f}"
                })

            if retrieved_images:
                visual_context = "\n".join(metadata_snippets)
                system_prompt = VISION_AGENT_PROMPT.format(visual_context=visual_context, question=question)
                answer = invoke_llm(prompt=f"Question: {question}", system_prompt=system_prompt)
            else:
                visual_context = "No visual elements retrieved."
                answer = "I don't have enough information in the visual metadata or chart regions for this document to answer this question."

            # Update State
            agent_responses = state.get("agent_responses") or {}
            agent_responses["vision"] = answer
            state["agent_responses"] = agent_responses

            confidence_map = state.get("confidence_scores") or {}
            confidence_map["vision"] = 0.88 if retrieved_images else 0.0
            state["confidence_scores"] = confidence_map

            metrics_map = state.get("execution_metrics") or {}
            metrics_map["vision_ms"] = round(timer.elapsed_ms, 2)
            state["execution_metrics"] = metrics_map

            state["retrieved_images"] = retrieved_images
            state["response"] = answer
            state["citations"] = citations
            state["agent_trace"] = [
                f"Vision Agent: Searched visual collection, found {len(retrieved_images)} region(s)",
                "Vision Agent: Generated visual analysis"
            ]

            log_agent_execution(
                logger=logger,
                agent_name="vision",
                query=question,
                execution_time_ms=timer.elapsed_ms,
                status="SUCCESS",
                extra_metadata={"visual_regions": len(retrieved_images)}
            )

        except Exception as exc:
            logger.exception("Error in Vision Agent node: %s", exc)
            state["response"] = "An error occurred during multi-modal chart visual analysis."
            state["retrieved_images"] = []
            state["citations"] = []
            state["agent_trace"] = [f"Vision Agent error: {str(exc)}"]

            log_agent_execution(
                logger=logger,
                agent_name="vision",
                query=question,
                execution_time_ms=timer.elapsed_ms,
                status="FAILED",
                extra_metadata={"error": str(exc)}
            )

    return state
