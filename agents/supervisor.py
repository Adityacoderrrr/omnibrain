"""
Supervisor node of the OmniBrain AI Intelligence Layer.
Uses LLM-driven structured JSON classification to determine optimal specialist agent assignments and confidence scores.
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
    - Prompts LLM for structured JSON decision indicating required specialist agents and confidence score.
    - Decides between single agent, multiple agents, or fallback search agent.
    - Updates AgentState with selected_agents list, confidence_scores, and telemetry trace.

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
            state["confidence_scores"] = {"supervisor": 0.0}
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
            
            try:
                confidence = float(decision_json.get("confidence", 0.90))
            except (ValueError, TypeError):
                confidence = 0.90

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
                confidence = 0.50
                reasoning += " (Fallback to search agent due to unparseable decision)."

            # Update State
            state["selected_agents"] = valid_selected
            state["selected_agent"] = valid_selected[0]  # Primary legacy field
            state["routing_reasoning"] = reasoning
            
            confidence_map = state.get("confidence_scores") or {}
            confidence_map["supervisor"] = confidence
            state["confidence_scores"] = confidence_map

            metrics_map = state.get("execution_metrics") or {}
            metrics_map["supervisor_ms"] = round(timer.elapsed_ms, 2)
            state["execution_metrics"] = metrics_map

            trace_msg = f"Supervisor routed query to agents: {valid_selected} (Confidence: {confidence:.2f}) | Reasoning: {reasoning}"
            state["agent_trace"] = [trace_msg]
            logger.info(trace_msg)

            log_agent_execution(
                logger=logger,
                agent_name="supervisor",
                query=question,
                execution_time_ms=timer.elapsed_ms,
                status="SUCCESS",
                extra_metadata={"selected_agents": valid_selected, "confidence": confidence, "reasoning": reasoning}
            )

        except Exception as exc:
            logger.exception("Failed in supervisor node: %s", exc)
            state["selected_agents"] = ["search"]
            state["selected_agent"] = "search"
            state["routing_reasoning"] = f"Fallback error recovery: {str(exc)}"
            
            confidence_map = state.get("confidence_scores") or {}
            confidence_map["supervisor"] = 0.0
            state["confidence_scores"] = confidence_map

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
