from .state import AgentState


def search_agent(state: AgentState) -> AgentState:
    """
    Search Agent:
    Uses retrieved documents to generate a response.
    """

    question = state["question"]
    retrieved_docs = state["retrieved_docs"]

    # Combine all retrieved documents into one context
    context = "\n".join(retrieved_docs)

    # Placeholder response (LLM integration will come later)
    state["response"] = (
        f"Question:\n{question}\n\n"
        f"Retrieved Context:\n{context}\n\n"
        f"Response:\n"
        f"This is a placeholder response generated using the retrieved documents."
    )

    print("Search Agent completed.")

    return state