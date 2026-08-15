"""
Search Agent component of the OmniBrain AI Intelligence Layer.
Retrieves relevant text chunks from Qdrant vector database and uses them for semantic RAG synthesis with context compression.
"""

import logging
from typing import List, Dict, Any, Optional
from app.core.config import get_settings
from app.ingestion.embedder import get_qdrant_client, _get_mock_embedding
from agents.state import AgentState
from agents.prompts import SEARCH_AGENT_PROMPT
from agents.llm import invoke_llm
from agents.logger import get_logger, log_agent_execution
from agents.utils import ExecutionTimer, sanitize_prompt_input, estimate_token_count

try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    OpenAIEmbeddings = None

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

logger: logging.Logger = get_logger("omnibrain.agents.search_agent")


def compress_context_chunks(chunks: List[str], max_tokens: int = 1500) -> str:
    """
    Compresses retrieved context text chunks to remain under specified token window limit.

    Args:
        chunks (List[str]): List of retrieved text chunks.
        max_tokens (int): Maximum token budget.

    Returns:
        str: Compressed context payload.
    """
    selected: List[str] = []
    current_tokens = 0

    for chunk in chunks:
        chunk_tokens = estimate_token_count(chunk)
        if current_tokens + chunk_tokens > max_tokens:
            break
        selected.append(chunk)
        current_tokens += chunk_tokens

    return "\n\n".join(selected) if selected else (chunks[0][:500] if chunks else "")


def search_agent(state: AgentState) -> AgentState:
    """
    Search Agent node:
    - Generates 1536-d text embedding for user question.
    - Queries Qdrant text collection with optional document_id metadata filter.
    - Compresses context payload to enforce token budget constraints.
    - Invokes LLM for text RAG generation.
    - Updates state retrieved_docs, agent_responses['search'], response, citations, and confidence_scores.

    Args:
        state (AgentState): Current execution state.

    Returns:
        AgentState: Updated execution state.
    """
    with ExecutionTimer() as timer:
        question = sanitize_prompt_input(state.get("question", ""))
        document_id = state.get("document_id", "")
        logger.info("Search Agent triggered for query: '%s'", question)

        settings = get_settings()

        if not question:
            state["response"] = "Error: Question is missing."
            state["retrieved_docs"] = []
            state["citations"] = []
            state["agent_trace"] = ["Search Agent: Failed - missing question"]
            return state

        try:
            client = get_qdrant_client()
            
            # Step 1: Generate Embedding Vector
            query_vector = None
            if OpenAIEmbeddings is not None and settings.openai_api_key and settings.openai_api_key != "mock-key":
                try:
                    embeddings_model = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
                    query_vector = embeddings_model.embed_query(question)
                except Exception as emb_exc:
                    logger.warning("OpenAIEmbeddings generation failed: %s. Falling back to mock embedding.", emb_exc)
                    query_vector = None

            if query_vector is None:
                query_vector = _get_mock_embedding(question, size=settings.embedding_dimension_text)

            # Step 2: Build Filter Criteria
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

            # Step 3: Perform Hybrid Retrieval (Vector + BM25 RRF)
            logger.info("Performing hybrid search over Qdrant & BM25 index...")
            try:
                from app.ingestion.hybrid_retriever import hybrid_retrieve
                comp_chunks, raw_fused = hybrid_retrieve(
                    query=question,
                    document_id=document_id,
                    top_k=settings.vector_search_top_k,
                )
            except Exception as hr_exc:
                logger.warning("Hybrid retrieval error: %s. Falling back to vector search.", hr_exc)
                comp_chunks = []

            retrieved_texts: List[str] = []
            citations: List[Dict[str, Any]] = []
            search_results: List[Any] = []

            if comp_chunks:
                for chunk in comp_chunks:
                    text = chunk.get("text", "")
                    if not text:
                        continue
                    filename = chunk.get("filename") or chunk.get("document_id") or "Document"
                    page = chunk.get("page_number", 1)
                    retrieved_texts.append(f"[Source: {filename} | Page {page}]\n{text}")
                    citations.append({
                        "document_name": filename,
                        "page": page,
                        "source_type": "text",
                        "snippet": chunk.get("snippet") or text[:200]
                    })
            else:
                try:
                    search_results = client.search(
                        collection_name=settings.qdrant_text_collection,
                        query_vector=query_vector,
                        query_filter=qdrant_filter,
                        limit=settings.vector_search_top_k
                    )
                except Exception as qd_exc:
                    logger.warning("Qdrant search failed or collection empty: %s.", qd_exc)
                    search_results = []

                for hit in search_results:
                    payload = getattr(hit, "payload", None) or (hit.get("payload") if isinstance(hit, dict) else {}) or {}
                    text = payload.get("text", "")
                    if not text:
                        continue
                    filename = payload.get("filename", payload.get("document_id", "Document"))
                    try:
                        page = int(payload.get("page_number", 1))
                    except (ValueError, TypeError):
                        page = 1
                    retrieved_texts.append(f"[Source: {filename} | Page {page}]\n{text}")
                    citations.append({
                        "document_name": filename,
                        "page": page,
                        "source_type": "text",
                        "snippet": text[:200]
                    })

            if retrieved_texts:
                context_str = compress_context_chunks(retrieved_texts, max_tokens=1500)
            else:
                context_str = "No relevant document text retrieved."

            # Step 4: Invoke RAG LLM
            if not retrieved_texts:
                answer = "I don't have enough information in the uploaded enterprise documents to answer this question."
            else:
                system_prompt = SEARCH_AGENT_PROMPT.format(context=context_str, question=question)
                answer = invoke_llm(prompt=f"Question: {question}", system_prompt=system_prompt)

            # Update State
            agent_responses = state.get("agent_responses") or {}
            agent_responses["search"] = answer
            state["agent_responses"] = agent_responses

            confidence_map = state.get("confidence_scores") or {}
            confidence_map["search"] = 0.92 if retrieved_texts else 0.0
            state["confidence_scores"] = confidence_map

            metrics_map = state.get("execution_metrics") or {}
            metrics_map["search_ms"] = round(timer.elapsed_ms, 2)
            state["execution_metrics"] = metrics_map

            # Compute Token & Observability Metrics
            system_prompt_str = SEARCH_AGENT_PROMPT.format(context=context_str, question=question) if retrieved_texts else ""
            prompt_tokens = estimate_token_count(system_prompt_str)
            answer_tokens = estimate_token_count(answer)
            
            token_analytics_map = state.get("token_analytics") or {}
            token_analytics_map["prompt_tokens"] = token_analytics_map.get("prompt_tokens", 0) + prompt_tokens
            token_analytics_map["completion_tokens"] = token_analytics_map.get("completion_tokens", 0) + answer_tokens
            token_analytics_map["total_tokens"] = token_analytics_map.get("prompt_tokens", 0) + token_analytics_map.get("completion_tokens", 0)
            state["token_analytics"] = token_analytics_map

            from app.ingestion.bm25_indexer import bm25_indexer
            total_indexed_chunks = getattr(bm25_indexer, "total_docs", len(retrieved_texts))

            top_sim = round(max([c.get("similarity", 0.92) for c in (comp_chunks or [])] + [getattr(h, "score", 0.0) for h in (search_results or [])] + [0.0]), 2) if retrieved_texts else 0.0
            chunk_previews = []
            for idx, c in enumerate((comp_chunks or [])[:5]):
                chunk_previews.append({
                    "page": c.get("page_number", 1),
                    "section": c.get("filename", document_id or "Document"),
                    "similarity": round(c.get("rrf_score", 0.90), 3),
                    "snippet": (c.get("text") or "")[:180]
                })

            trace_details_map = state.get("trace_details") or {}
            trace_details_map["search"] = {
                "collection": settings.qdrant_text_collection,
                "chunks_searched": max(total_indexed_chunks, len(retrieved_texts)),
                "top_k": settings.vector_search_top_k,
                "retrieved_count": len(retrieved_texts),
                "top_similarity": top_sim,
                "chunk_previews": chunk_previews,
                "prompt_sent": system_prompt_str[:300],
                "context_used": context_str[:300],
                "generated_answer": answer,
                "confidence": 0.92 if retrieved_texts else 0.0,
                "execution_time_ms": round(timer.elapsed_ms, 2)
            }
            state["trace_details"] = trace_details_map

            state["retrieved_docs"] = retrieved_texts
            state["response"] = answer
            state["citations"] = citations
            state["agent_trace"] = [
                f"Search Agent: Retrieved {len(retrieved_texts)} text chunks from index",
                "Search Agent: Synthesized textual RAG response"
            ]

            log_agent_execution(
                logger=logger,
                agent_name="search",
                query=question,
                execution_time_ms=timer.elapsed_ms,
                status="SUCCESS",
                extra_metadata={"retrieved_chunks": len(retrieved_texts)}
            )

        except Exception as exc:
            logger.exception("Error in Search Agent node: %s", exc)
            state["response"] = "An error occurred while performing search-based RAG."
            state["retrieved_docs"] = []
            state["citations"] = []
            state["agent_trace"] = [f"Search Agent error: {str(exc)}"]

            log_agent_execution(
                logger=logger,
                agent_name="search",
                query=question,
                execution_time_ms=timer.elapsed_ms,
                status="FAILED",
                extra_metadata={"error": str(exc)}
            )

    return state
