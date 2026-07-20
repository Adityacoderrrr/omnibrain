"""
LangGraph compilation logic for the OmniBrain agentic pipeline.
Defines the state graph flow, nodes, and routing transitions.
"""

import logging
from langgraph.graph import StateGraph, END

from .state import AgentState
from .supervisor import supervisor
from .search_agent import search_agent
from .vision_agent import vision_agent
from .sql_agent import sql_agent
from .reducer import reducer
from .router import route_decision

logger = logging.getLogger("omnibrain.agents.graph")

# Initialize the StateGraph with the AgentState schema
workflow = StateGraph(AgentState)

# Register the decision and execution nodes
workflow.add_node("supervisor", supervisor)
workflow.add_node("search", search_agent)
workflow.add_node("vision", vision_agent)
workflow.add_node("sql", sql_agent)
workflow.add_node("reducer", reducer)

# Define entry point
workflow.set_entry_point("supervisor")

# Configure conditional edges from supervisor based on router decision
workflow.add_conditional_edges(
    "supervisor",
    route_decision,
    {
        "search": "search",
        "vision": "vision",
        "sql": "sql"
    }
)

# specialists all converge to the reducer node
workflow.add_edge("search", "reducer")
workflow.add_edge("vision", "reducer")
workflow.add_edge("sql", "reducer")

# Reducer node completes execution
workflow.add_edge("reducer", END)

# Compile the graph
supervisor_graph = workflow.compile()
logger.info("Compiled LangGraph supervisor_graph successfully.")
