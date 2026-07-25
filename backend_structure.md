# OmniBrain Backend Structure

```text
omnibrain-backend/
├── main.py                   # FastAPI entry point to serve the orchestrator
├── requirements.txt          # Dependencies (LangGraph, unstructured, qdrant-client, etc.)
├── .env                      # API keys (OpenAI, Langfuse) and DB connection strings
│
├── api/
│   └── routes.py             # HTTP endpoints (e.g., POST /query, POST /ingest)
│
├── core/
│   ├── config.py             # Loads environment variables securely
│   └── state.py              # Defines OmniBrainState (the LangGraph TypedDict)
│
├── ingestion/                # Phase 1: Data Pipeline
│   ├── parser.py             # Unstructured.io PDF dissection code (text, tables, images)
│   └── embedder.py           # Logic to call CLIP and OpenAI embedding models
│
├── database/                 # Phase 1 & 2: Storage & Retrieval
│   ├── qdrant_client.py      # Qdrant multi-vector setup and search functions
│   └── sql_db.py             # PostgreSQL connection for the historical stock data
│
├── agents/                   # Phase 2 & 3: The Brain & Workers
│   ├── supervisor.py         # LangGraph orchestrator (routing logic)
│   └── workers/
│       ├── search_agent.py   # RAG worker for semantic text
│       ├── vision_agent.py   # LLaVA/GPT-4o worker for charts and tables
│       └── sql_agent.py      # Text-to-SQL worker for database querying
│
├── guardrails/               # Phase 4: Security & Tracing
│   ├── config.yml            # NeMo Guardrails setup (model routing, toxicity)
│   └── rails.co              # Colang files defining strict conversational boundaries
│
└── data/                     # Local storage (should be in .gitignore)
    ├── raw_pdfs/             # Where the user uploads the 500-page financial PDF
    └── extracted_images/     # Where Unstructured saves the cropped charts
```
