import logging
from .state import AgentState
from .prompts import SUPERVISOR_PROMPT
from .llm import invoke_llm

logger = logging.getLogger("omnibrain.agents.supervisor")


def supervisor(state: AgentState) -> AgentState:
    """
    Supervisor node that determines the best specialist agent to handle the query.

    Args:
        state (AgentState): The current agent execution state.

    Returns:
        AgentState: The updated state with the routing decision.
    """
    logger.info("Supervisor parsing query: '%s'", state.get("question"))
    try:
        question = state.get("question", "")
        if not question:
            raise ValueError("State key 'question' is missing or empty.")

        # Classify routing via LLM (or fallback mock engine)
        routing_decision = invoke_llm(prompt=question, system_prompt=SUPERVISOR_PROMPT)

        # Clean and normalize routing decision
        routing_decision = (routing_decision or "").strip().lower()
        if routing_decision not in ["vision", "sql", "search"]:
            logger.warning(
                "Invalid supervisor routing result: '%s'. Falling back to 'search'.",
                routing_decision
            )
            routing_decision = "search"

        state["selected_agent"] = routing_decision
        trace_msg = f"Supervisor routed query to: {routing_decision} agent"
        state["agent_trace"] = [trace_msg]
        logger.info(trace_msg)

    except Exception as exc:
        logger.exception("Failed in supervisor node: %s", exc)
        state["selected_agent"] = "search"
        state["agent_trace"] = ["Supervisor encountered error; fallback to search agent"]

    return state