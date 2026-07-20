# 🧠 OmniBrain Project Structure

This document outlines the directory structure and architectural separation of concerns for the OmniBrain multi-modal RAG orchestrator.

## Directory Tree

```text
omnibrain/
├── config/
│   ├── __init__.py
│   ├── settings.py             # Parses environment variables & YAML configs
│   └── config.yaml             # Centralized LLM prompts, model names, and constants
│
├── logs/                       # Automated log sinks (ignored in git)
│   └── app.log                 # Active runtime application logs
│
├── frontend/
│   ├── app.py                  # Main Streamlit entrance
│   ├── components/             # Reusable UI parts (sidebar.py, result_tabs.py)
│   └── api_client.py           # Handles communication with the backend
│
├── backend/
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logger.py           # Standardized logging setup used across all agents
│   │
│   ├── orchestration/          # Multi-agent routing architecture
│   │   ├── __init__.py
│   │   ├── state.py            # Defines the global LangGraph state schema
│   │   ├── nodes.py            # Graph nodes (the business logic steps)
│   │   ├── router.py           # Supervisor routing logic and conditional edges
│   └── graph.py                # Compiles the state, nodes, and router
│   │
│   ├── agents/                 # Clean separation of specialized workers
│   │   ├── sql_agent.py
│   │   ├── vision_agent.py
│   │   └── search_agent.py
│   │
│   ├── rag/                    # Custom multi-modal file processors (PDF chunking, CLIP embeddings)
│   └── guardrails/             # NeMo Guardrail configurations for hallucination checks
│
├── data/                       # Local database fixtures and raw source files
├── .env.example                # Template for private credentials (API keys, DB URIs)
├── requirements.txt            # Python dependencies
└── README.md                   # Project overview and setup instructions
