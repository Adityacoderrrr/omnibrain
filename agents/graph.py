"""
LangGraph compilation logic for the OmniBrain agentic pipeline.
Defines the state graph flow, node registrations, conditional routing edges, and graph compilation.
"""

from langgraph.graph import StateGraph, START, END
from agents.state import AgentState
from agents.supervisor import supervisor
from agents.search_agent import search_agent
from agents.vision_agent import vision_agent
from agents.sql_agent import sql_agent
from agents.reducer import reducer
from agents.router import route_decision
from agents.logger import get_logger

logger = get_logger("omnibrain.agents.graph")

# Step 1: Initialize StateGraph with AgentState schema
workflow = StateGraph(AgentState)

# Step 2: Register Node Executable Functions
workflow.add_node("supervisor", supervisor)
workflow.add_node("search", search_agent)
workflow.add_node("vision", vision_agent)
workflow.add_node("sql", sql_agent)
workflow.add_node("reducer", reducer)

# Step 3: Set Graph Entry Point
workflow.add_edge(START, "supervisor")

# Step 4: Configure Conditional Edges from Supervisor via Router
workflow.add_conditional_edges(
    "supervisor",
    route_decision,
    {
        "search": "search",
        "vision": "vision",
        "sql": "sql"
    }
)

# Step 5: Converge Specialist Nodes to Reducer
workflow.add_edge("search", "reducer")
workflow.add_edge("vision", "reducer")
workflow.add_edge("sql", "reducer")

# Step 6: Direct Reducer to Graph Termination (END)
workflow.add_edge("reducer", END)

# Step 7: Compile StateGraph Instance
supervisor_graph = workflow.compile()
logger.info("Compiled LangGraph supervisor_graph successfully.")
