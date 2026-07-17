from .state import AgentState

def reducer(state: AgentState):
    """
    Merge responses from multiple agents.
    """

    return state