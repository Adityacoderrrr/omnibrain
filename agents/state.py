from typing import TypedDict, List


class AgentState(TypedDict):
    # User input
    question: str

    # Retrieved text chunks
    retrieved_docs: List[str]

    # Agent selected by supervisor
    selected_agent: str

    # Final response
    response: str
