"""
Shared State definition for OmniBrain LangGraph agentic orchestrator.
Defines typing schema for multi-agent parallel execution, routing, citations, and execution telemetry.
"""

from typing import TypedDict, List, Dict, Any, Annotated
import operator


class AgentState(TypedDict, total=False):
    """
    State dictionary maintained across the OmniBrain LangGraph pipeline execution.
    Passed between Supervisor, Router, Specialist Agents, and Reducer.
    """
    # Core User Request Metadata
    question: str
    document_id: str

    # Supervisor & Routing Decision (Supports single or multi-agent selection)
    selected_agent: str  # Primary or legacy agent name for backward compatibility ('search', 'vision', 'sql')
    selected_agents: List[str]  # List of specialist agents to execute in parallel
    routing_reasoning: str  # Structured explanation from Supervisor LLM

    # Retrieved Context Artifacts
    retrieved_docs: List[str]
    retrieved_images: List[Dict[str, Any]]

    # SQL Execution State
    sql_query: str
    sql_result: str

    # Specialist Agent Outputs (Mapped by agent name: 'search', 'vision', 'sql')
    agent_responses: Dict[str, str]

    # Final Synthesized Response & Source Attributions
    response: str
    citations: List[Dict[str, Any]]

    # Execution Trace Telemetry & Error Tracking (Appended atomically using operator.add)
    agent_trace: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]
