from agents.state import AgentState
from agents.supervisor import supervisor
from agents.search_agents import search_agent

state: AgentState = {
    "question": "What is revenue?",
    "retrieved_docs": [],
    "response": ""
}

state = supervisor(state)
state = search_agent(state)

print(state)