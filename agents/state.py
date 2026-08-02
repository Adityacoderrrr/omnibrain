"""
Shared State definition for OmniBrain LangGraph agentic orchestrator.
Defines typing schema for multi-agent parallel execution, session history, confidence scoring, citations, and execution telemetry.
"""

from typing import TypedDict, List, Dict, Any, Annotated
import operator


def merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries for parallel LangGraph updates."""
    res = dict(a or {})
    if b:
        res.update(b)
    return res


def take_last(a: str, b: str) -> str:
    """Take the last non-empty string for parallel updates."""
    if b is not None:
        return b
    return a


def combine_citations(old: List[Dict[str, Any]], new: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Combine and deduplicate citations for parallel and sequential LangGraph state updates."""
    combined = (old or []) + (new or [])
    unique_citations: List[Dict[str, Any]] = []
    seen_keys = set()

    for cit in combined:
        if isinstance(cit, dict):
            page = cit.get("page", 1)
            stype = cit.get("source_type", "unknown")
            snip = str(cit.get("snippet", ""))[:100]
            key = (page, stype, snip)

            if key not in seen_keys:
                seen_keys.add(key)
                unique_citations.append(cit)

    return unique_citations


def combine_lists(old: List[Any], new: List[Any]) -> List[Any]:
    """Combine lists preserving uniqueness and order for LangGraph state updates."""
    combined = list(old or [])
    for item in (new or []):
        if item not in combined:
            combined.append(item)
    return combined


class AgentState(TypedDict, total=False):
    """
    State dictionary maintained across the OmniBrain LangGraph pipeline execution.
    Passed between Supervisor, Router, Specialist Agents, and Reducer.
    """
    # Session & Request Identifiers
    session_id: Annotated[str, take_last]
    request_id: Annotated[str, take_last]

    # Core User Request & Multi-Turn History
    question: Annotated[str, take_last]
    document_id: Annotated[str, take_last]
    conversation_history: Annotated[List[Dict[str, str]], combine_lists]

    # Supervisor & Routing Decision (Supports single or multi-agent selection)
    selected_agent: Annotated[str, take_last]  # Primary or legacy agent name for backward compatibility ('search', 'vision', 'sql')
    selected_agents: Annotated[List[str], combine_lists]  # List of specialist agents to execute in parallel
    routing_reasoning: Annotated[str, take_last]  # Structured explanation from Supervisor LLM

    # Retrieved Context Artifacts
    retrieved_docs: Annotated[List[str], combine_lists]
    retrieved_images: Annotated[List[Dict[str, Any]], combine_lists]

    # SQL Execution State
    sql_query: Annotated[str, take_last]
    sql_result: Annotated[str, take_last]
    sql_explanation: Annotated[str, take_last]

    # Specialist Agent Outputs (Mapped by agent name: 'search', 'vision', 'sql')
    agent_responses: Annotated[Dict[str, str], merge_dicts]

    # Confidence Scores & Execution Metrics
    confidence_scores: Annotated[Dict[str, float], merge_dicts]
    execution_metrics: Annotated[Dict[str, float], merge_dicts]

    # Final Synthesized Response & Source Attributions
    response: Annotated[str, take_last]
    citations: Annotated[List[Dict[str, Any]], combine_citations]

    # Execution Trace Telemetry & Error Tracking (Appended atomically using operator.add)
    agent_trace: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]
    trace_details: Annotated[Dict[str, Any], merge_dicts]
    token_analytics: Annotated[Dict[str, int], merge_dicts]

