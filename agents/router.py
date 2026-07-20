"""
Conditional routing logic for the OmniBrain LangGraph agentic orchestrator.
"""

import logging
from .state import AgentState

logger = logging.getLogger("omnibrain.agents.router")


def route_decision(state: AgentState) -> str:
    """
    Determine the next specialist agent node based on the supervisor's routing choice.

    Args:
        state (AgentState): The current agent execution state.

    Returns:
        str: The name of the next specialist node to invoke ('vision', 'sql', or 'search').
    """
    selected = state.get("selected_agent", "search")
    logger.info("Router evaluating selected agent: '%s'", selected)

    if selected in ["vision", "sql", "search"]:
        return selected

    logger.warning("Unrecognized selected agent '%s'; defaulting routing path to 'search'.", selected)
    return "search"
