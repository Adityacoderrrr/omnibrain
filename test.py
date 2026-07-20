from agents.state import AgentState
from agents.supervisor import supervisor
from agents.search_agent import search_agent

state: AgentState = {
    "question": "What is revenue?",
    "document_id": "test-doc-id",
    "selected_agent": "",
    "retrieved_docs": [],
    "retrieved_images": [],
    "sql_query": "",
    "sql_result": "",
    "response": "",
    "citations": [],
    "agent_trace": []
}

state = supervisor(state)
state = search_agent(state)

print(state)