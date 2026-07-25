"""
Supervisor node of the OmniBrain AI Intelligence Layer.
Uses LLM-driven structured JSON classification to determine optimal specialist agent assignments.
"""

from typing import List, Dict, Any
from agents.state import AgentState
from agents.prompts import SUPERVISOR_PROMPT
from agents.llm import invoke_llm_json
from agents.logger import get_logger, log_agent_execution
from agents.utils import ExecutionTimer, sanitize_prompt_input

logger = get_logger("omnibrain.agents.supervisor")

VALID_AGENTS = {"vision", "sql", "search"}


def supervisor(state: AgentState) -> AgentState:
    """
    Supervisor node:
    - Sanitizes input user question.
    - Prompts LLM for structured JSON decision indicating required specialist agents.
    - Decides between single agent, multiple agents, or fallback search agent.
    - Updates AgentState with selected_agents list and telemetry trace.

    Args:
        state (AgentState): Current execution state.

    Returns:
        AgentState: Updated state with supervisor decision.
    """
    with ExecutionTimer() as timer:
        question = sanitize_prompt_input(state.get("question", ""))
        logger.info("Supervisor parsing query: '%s'", question)

        if not question:
            logger.warning("Empty question provided to supervisor; defaulting to 'search'.")
            state["selected_agents"] = ["search"]
            state["selected_agent"] = "search"
            state["routing_reasoning"] = "Fallback default due to missing user query."
            state["agent_trace"] = ["Supervisor: Failed - empty question prompt"]
            return state

        try:
            # Execute LLM routing call with structured JSON response wrapper
            decision_json = invoke_llm_json(
                prompt=f"User Question: {question}",
                system_prompt=SUPERVISOR_PROMPT
            )

            raw_selected = decision_json.get("selected_agents", [])
            reasoning = decision_json.get("reasoning", "LLM routing classification completed.")

            # Handle case where LLM returns single string instead of list
            if isinstance(raw_selected, str):
                raw_selected = [raw_selected]

            # Filter valid specialist agents
            valid_selected: List[str] = [
                ag.lower().strip() for ag in raw_selected 
                if isinstance(ag, str) and ag.lower().strip() in VALID_AGENTS
            ]

            if not valid_selected:
                logger.warning("No valid specialist agents extracted from decision: %s. Fallback to 'search'.", raw_selected)
                valid_selected = ["search"]
                reasoning += " (Fallback to search agent due to unparseable decision)."

            # Update State
            state["selected_agents"] = valid_selected
            state["selected_agent"] = valid_selected[0]  # Primary legacy field
            state["routing_reasoning"] = reasoning
            
            trace_msg = f"Supervisor routed query to agents: {valid_selected} | Reasoning: {reasoning}"
            state["agent_trace"] = [trace_msg]
            logger.info(trace_msg)

            log_agent_execution(
                logger=logger,
                agent_name="supervisor",
                query=question,
                execution_time_ms=timer.elapsed_ms,
                status="SUCCESS",
                extra_metadata={"selected_agents": valid_selected, "reasoning": reasoning}
            )

        except Exception as exc:
            logger.exception("Failed in supervisor node: %s", exc)
            state["selected_agents"] = ["search"]
            state["selected_agent"] = "search"
            state["routing_reasoning"] = f"Fallback error recovery: {str(exc)}"
            state["agent_trace"] = [f"Supervisor error fallback: {str(exc)}"]

            log_agent_execution(
                logger=logger,
                agent_name="supervisor",
                query=question,
                execution_time_ms=timer.elapsed_ms,
                status="FALLBACK",
                extra_metadata={"error": str(exc)}
            )

    return state
