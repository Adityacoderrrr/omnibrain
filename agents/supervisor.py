from .state import AgentState


def supervisor(state: AgentState) -> AgentState:
    """
    Decide which agent should handle the user's query.
    """

    question = state["question"].lower()

    # Route based on keywords
    if any(word in question for word in ["image", "graph", "chart", "figure", "diagram"]):
        state["selected_agent"] = "vision"

    elif any(word in question for word in ["database", "sql", "table", "record", "sales"]):
        state["selected_agent"] = "sql"

    else:
        state["selected_agent"] = "search"

    print(f"Supervisor selected: {state['selected_agent']} agent")

    return state