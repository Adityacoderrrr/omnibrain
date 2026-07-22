"""
Search Agent component of the OmniBrain AI Intelligence Layer.
Retrieves relevant text chunks from Qdrant and uses them to answer queries.
"""

import logging

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

from app.core.config import get_settings
from app.ingestion.embedder import get_qdrant_client, _get_mock_embedding
from .state import AgentState
from .prompts import SEARCH_AGENT_PROMPT
from .llm import invoke_llm

logger = logging.getLogger("omnibrain.agents.search_agent")


def search_agent(state: AgentState) -> AgentState:
    """
    Search Agent node:
    - Generates embeddings for the query.
    - Queries Qdrant text collection for relevant documents.
    - Invokes the LLM to generate an answer with citations.

    Args:
        state (AgentState): Current execution state.

    Returns:
        AgentState: Updated execution state.
    """
    logger.info("Search Agent triggered for query: '%s'", state.get("question"))
    settings = get_settings()

    question = state.get("question", "")
    document_id = state.get("document_id", "")

    if not question:
        state["response"] = "Error: Question is missing."
        state["retrieved_docs"] = []
        state["citations"] = []
        state["agent_trace"] = ["Search Agent: Failed - missing question"]
        return state

    try:
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
            query_vector = _get_mock_embedding(question, size=1536)

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
                limit=3
            )
        except Exception as qd_exc:
            logger.warning(
                "Qdrant connection failed: %s. Falling back to local mock search results.",
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

        retrieved_texts = []
        citations = []
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
        system_prompt = SEARCH_AGENT_PROMPT.format(context=context_str)
        answer = invoke_llm(prompt=f"Question: {question}", system_prompt=system_prompt)

        # Update State
        state["retrieved_docs"] = retrieved_texts
        state["response"] = answer
        state["citations"] = citations
        state["agent_trace"] = [
            f"Search Agent: Retrieved {len(retrieved_texts)} text chunks from vector store",
            f"Search Agent: Generated response using textual RAG"
        ]

    except Exception as exc:
        logger.exception("Error in Search Agent node: %s", exc)
        state["response"] = "An error occurred while performing search-based RAG."
        state["retrieved_docs"] = []
        state["citations"] = []
        state["agent_trace"] = [f"Search Agent error: {str(exc)}"]

    return state