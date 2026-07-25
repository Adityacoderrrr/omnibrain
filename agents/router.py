"""
Conditional routing logic for the OmniBrain LangGraph agentic orchestrator.
Determines next node execution targets for LangGraph StateGraph conditional edges.
"""

from typing import List, Union
from agents.state import AgentState
from agents.logger import get_logger

logger = get_logger("omnibrain.agents.router")

VALID_NODES = {"vision", "sql", "search"}


def route_decision(state: AgentState) -> Union[str, List[str]]:
    """
    Determines the next specialist agent node(s) based on supervisor selection.

    Args:
        state (AgentState): The current agent execution state.

    Returns:
        Union[str, List[str]]: Single agent name or list of agent names for parallel LangGraph execution.
    """
    selected_list = state.get("selected_agents", [])
    
    # Fallback to legacy single selected_agent if selected_agents list is unpopulated
    if not selected_list:
        legacy_single = state.get("selected_agent", "search")
        selected_list = [legacy_single] if legacy_single else ["search"]

    # Filter targets to ensure only valid graph nodes are returned
    valid_targets = [node for node in selected_list if node in VALID_NODES]

    if not valid_targets:
        logger.warning("No valid routing targets found in %s; defaulting to 'search'.", selected_list)
        return "search"

    if len(valid_targets) == 1:
        logger.info("Router directing execution to single specialist node: '%s'", valid_targets[0])
        return valid_targets[0]

    logger.info("Router directing parallel execution to specialist nodes: %s", valid_targets)
    return valid_targets
