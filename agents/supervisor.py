from .state import AgentState

def supervisor(state: AgentState):
    """
    Decide which agent should handle the query.
    """
    print("Supervisor received:", state["question"])

    return state