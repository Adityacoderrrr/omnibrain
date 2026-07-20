from typing import TypedDict, List, Dict, Any, Annotated
import operator


class AgentState(TypedDict):
    """
    State definition for the OmniBrain agentic pipeline.
    """
    # Core user request information
    question: str
    document_id: str

    # Orchestrator routing decision
    selected_agent: str

    # Structured or unstructured content retrieved during the execution
    retrieved_docs: List[str]
    retrieved_images: List[Dict[str, Any]]

    # SQL metadata if routing to SQL agent
    sql_query: str
    sql_result: str

    # Final generated answer
    response: str

    # Extracted source citations
    citations: List[Dict[str, Any]]

    # Trace of execution steps. Uses operator.add to append entries.
    agent_trace: Annotated[List[str], operator.add]