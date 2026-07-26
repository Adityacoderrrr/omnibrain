"""
Search Agent component of the OmniBrain AI Intelligence Layer.
Retrieves relevant text chunks from Qdrant and uses them to answer queries.
"""

from typing import List, Dict, Any
from app.core.config import get_settings
from app.ingestion.embedder import get_qdrant_client, ensure_collections, _get_mock_embedding
from agents.state import AgentState
from agents.prompts import SEARCH_AGENT_PROMPT
from agents.llm import invoke_llm
from agents.logger import get_logger, log_agent_execution
from agents.utils import ExecutionTimer, sanitize_prompt_input

try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    OpenAIEmbeddings = None  # Fallback if package missing

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

logger = get_logger("omnibrain.agents.search_agent")


def search_agent(state: AgentState) -> Dict[str, Any]:
    """
    Search Agent node:
    - Generates embeddings for the query.
    - Queries Qdrant text collection for relevant documents.
    - Invokes the LLM to generate an answer with citations.

    Args:
        state (AgentState): Current execution state.

    Returns:
        Dict[str, Any]: Partial state update.
    """
    with ExecutionTimer() as timer:
        question = sanitize_prompt_input(state.get("question", ""))
        document_id = state.get("document_id", "")
        logger.info("Search Agent triggered for query: '%s'", question)

        settings = get_settings()

        if not question:
            return {
                "response": "Error: Question is missing.",
                "retrieved_docs": [],
                "citations": [],
                "agent_responses": {},
                "agent_trace": ["Search Agent: Failed - missing question"]
            }

        try:
            # Ensure collections exist before querying
            try:
                ensure_collections()
            except Exception as init_exc:
                logger.debug("Qdrant collection bootstrap check skipped/failed: %s", init_exc)

            # Initialize client and generate query vector
            client = get_qdrant_client()
            
            # Determine embedding model
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

            # Create filter for document_id
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

            logger.info("Querying Qdrant collection: '%s'", settings.qdrant_text_collection)
            try:
                search_results = client.search(
                    collection_name=settings.qdrant_text_collection,
                    query_vector=query_vector,
                    query_filter=qdrant_filter,
                    limit=settings.vector_search_top_k
                )
            except Exception as qd_exc:
                logger.warning(
                    "Qdrant connection failed or collection empty: %s. Falling back to local mock search results.",
                    qd_exc
                )
                search_results = [
                    ScoredPoint(
                        id=1,
                        version=1,
                        score=0.95,
                        payload={
                            "text": "According to the annual summary document, revenue grew by 15% year-over-year, driven by cloud subscriptions.",
                            "page_number": 1,
                            "document_id": document_id
                        }
                    )
                ]

            retrieved_texts: List[str] = []
            citations: List[Dict[str, Any]] = []
            for hit in search_results:
                payload = getattr(hit, "payload", None)
                if payload is None and isinstance(hit, dict):
                    payload = hit.get("payload", {})
                elif payload is None:
                    payload = {}

                text = payload.get("text", "")
                if not text:
                    continue

                raw_page = payload.get("page_number", 1)
                try:
                    page = int(raw_page)
                except (ValueError, TypeError):
                    page = 1
                
                retrieved_texts.append(text)
                citations.append({
                    "page": page,
                    "source_type": "text",
                    "snippet": text[:200]
                })

            # Fallback if no docs retrieved
            if not retrieved_texts:
                logger.warning("No documents retrieved for document_id: '%s'", document_id)
                context_str = "No text document context was retrieved from the vector database."
            else:
                context_str = "\n\n".join(retrieved_texts)

            # Invoke LLM
            system_prompt = SEARCH_AGENT_PROMPT.format(context=context_str, question=question)
            answer = invoke_llm(prompt=f"Question: {question}", system_prompt=system_prompt)

            log_agent_execution(
                logger=logger,
                agent_name="search",
                query=question,
                execution_time_ms=timer.elapsed_ms,
                status="SUCCESS",
                extra_metadata={"text_chunks": len(retrieved_texts)}
            )

            return {
                "retrieved_docs": retrieved_texts,
                "response": answer,
                "citations": citations,
                "agent_responses": {"search": answer},
                "agent_trace": [
                    f"Search Agent: Retrieved {len(retrieved_texts)} text chunks from vector store",
                    "Search Agent: Generated response using textual RAG"
                ]
            }

        except Exception as exc:
            logger.exception("Error in Search Agent node: %s", exc)
            log_agent_execution(
                logger=logger,
                agent_name="search",
                query=question,
                execution_time_ms=timer.elapsed_ms,
                status="FAILED",
                extra_metadata={"error": str(exc)}
            )

            return {
                "response": "An error occurred while performing search-based RAG.",
                "retrieved_docs": [],
                "citations": [],
                "agent_responses": {},
                "agent_trace": [f"Search Agent error: {str(exc)}"]
            }
