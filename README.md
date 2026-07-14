# OmniBrain

> **Agentic Multi-Modal RAG Orchestrator**

OmniBrain is an intelligent document analysis system that leverages **Large Language Models (LLMs)** and **Agentic AI** to perform advanced reasoning over multimodal documents. Unlike traditional Retrieval-Augmented Generation (RAG) systems that primarily process text, OmniBrain is designed to understand and retrieve information from text, tables, charts, graphs, and images within a single document.

Powered by a **LangGraph-based agentic architecture**, the system dynamically coordinates multiple specialized AI agents—including Search, Vision, and SQL Agents—to solve complex queries by retrieving information from different sources. Semantic text retrieval is performed using **Qdrant/FAISS**, while visual content is interpreted through **Vision-Language Models (GPT-4o/LLaVA)**. For structured information, the SQL Agent queries relevant databases to support data-driven reasoning.

To ensure trustworthy and reliable responses, OmniBrain integrates **Self-RAG**, **Langfuse**, and **NeMo Guardrails** for intelligent retrieval refinement, execution monitoring, and hallucination prevention. Every response is grounded in retrieved context and supported with citations, providing users with transparent and verifiable results.

---

## Key Features

-  Multi-modal PDF ingestion
-  Semantic retrieval over text and images
-  LangGraph-powered multi-agent orchestration
-  Vision-Language reasoning for charts, graphs, and tables
-  Text-to-SQL querying for structured data
-  Self-RAG for retrieval refinement
-  Hallucination prevention using NeMo Guardrails
-  LLM observability with Langfuse
-  Citation-backed, context-grounded responses

---

## Tech Stack

**AI Engineering**
- LangGraph
- GPT-4o / LLaVA
- CLIP
- Qdrant / FAISS
- Langfuse
- NeMo Guardrails

**Backend**
- FastAPI

**Frontend**
- Streamlit

---

Pipeline : 
                    User Query
                         │
                         ▼
               Agent / Planner (LLM)
                         │
      ┌──────────────────┼──────────────────┐
      │                  │                  │
      ▼                  ▼                  ▼
Understand Intent   Break into Tasks   Decide Tools
      │                  │                  │
      └──────────────────┼──────────────────┘
                         ▼
               Query Rewriting Agent
                         │
                         ▼
             Hybrid Retrieval Engine
      (Vector DB + BM25 + SQL + APIs + Web)
                         │
                         ▼
                 Reranking Model
                         │
                         ▼
              Context Evaluation Agent
                         │
        Enough Information?
              │                │
             YES              NO
              │                │
              ▼                ▼
        Answer Agent      Search Again
              │                │
              └────────────────┘
                         │
                         ▼
          Verification / Reflection Agent
                         │
          Fact Check • Citation Check
                         │
                         ▼
                Final Response
## Objective

To develop a production-grade Agentic AI system capable of autonomous reasoning across multimodal enterprise documents by combining semantic retrieval, visual understanding, and structured data querying, while delivering reliable, context-aware, and citation-backed responses.
