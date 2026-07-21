# OmniBrain — System Diagrams

Flow diagram, Data Flow Diagrams (Level 0 & 1), and UML diagrams (Use Case, Sequence, Class, Component, Deployment) for the OmniBrain Agentic Multi-Modal RAG Orchestrator...

All diagrams are written in [Mermaid](https://mermaid.js.org/) and render automatically on GitHub — no image files required.

---

## 📑 Table of Contents

1. [End-to-End System Flow Diagram](#1-end-to-end-system-flow-diagram)
2. [Data Flow Diagram — Level 0 (Context)](#2-data-flow-diagram--level-0-context)
3. [Data Flow Diagram — Level 1](#3-data-flow-diagram--level-1)
4. [UML Use Case Diagram](#4-uml-use-case-diagram)
5. [UML Sequence Diagram — Query Lifecycle](#5-uml-sequence-diagram--query-lifecycle)
6. [UML Class Diagram](#6-uml-class-diagram)
7. [UML Component Diagram](#7-uml-component-diagram)
8. [UML Deployment Diagram](#8-uml-deployment-diagram)

---

## 1. End-to-End System Flow Diagram

Covers both phases of the system: offline document ingestion and the live query-answering flow.

```mermaid
flowchart TD
    A["📥 Analyst uploads 500-page PDF"] --> B["FastAPI: POST /documents/upload"]
    B --> C["Ingestion Pipeline"]
    C --> C1["Parse & classify pages<br/>text / table / chart"]
    C1 --> C2["Chunk text +<br/>extract table/chart images"]
    C2 --> C3["Embed (text encoder + CLIP)"]
    C3 --> D[("Qdrant Vector Store<br/>text + image collections")]

    E["💬 Analyst asks a question"] --> F["FastAPI: POST /query"]
    F --> G["LangGraph Supervisor<br/>classifies & routes sub-tasks"]
    G --> H1["Search Agent<br/>semantic text retrieval"]
    G --> H2["Vision Agent<br/>VLM chart/table reasoning"]
    G --> H3["SQL Agent<br/>text-to-SQL"]
    H1 --> D
    H2 --> D
    H3 --> I[("Historical Stock DB")]

    H1 --> J["Synthesis / Reducer Node"]
    H2 --> J
    H3 --> J
    J --> K["Guardrails Check<br/>NeMo Guardrails: groundedness,<br/>hallucination, scope"]
    K -->|pass| L["Cited Investment Memo"]
    K -->|fail| M["Self-RAG retry:<br/>rewrite query & re-retrieve"]
    M --> G
    J --> N["Langfuse Trace Log<br/>tokens, latency, scores"]
    L --> O["📄 Response returned to Analyst"]

    style A fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    style E fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    style G fill:#1c3d5a,stroke:#0f2438,color:#ffffff
    style D fill:#fef9c3,stroke:#a16207,color:#422006
    style I fill:#fef9c3,stroke:#a16207,color:#422006
    style K fill:#dcfce7,stroke:#166534,color:#052e16
    style O fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
```

---

## 2. Data Flow Diagram — Level 0 (Context)

The system treated as a single process, showing only external entities and the data crossing the system boundary.

```mermaid
flowchart LR
    ANALYST(["👤 Quantitative Analyst"])
    MARKET[["📈 Historical Market<br/>Data Provider"]]

    SYS((("OmniBrain System<br/>Process 0")))

    ANALYST -->|"PDF document"| SYS
    ANALYST -->|"Natural language query"| SYS
    SYS -->|"Cited investment memo"| ANALYST

    SYS -->|"SQL query"| MARKET
    MARKET -->|"Price / volume data"| SYS

    style ANALYST fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    style MARKET fill:#ffedd5,stroke:#c2410c,color:#431407
    style SYS fill:#1c3d5a,stroke:#0f2438,color:#ffffff
```

---

## 3. Data Flow Diagram — Level 1

Process 0 decomposed into its five major sub-processes, with data stores shown as open cylinders.

```mermaid
flowchart TD
    ANALYST(["👤 Analyst"])
    MARKET[["📈 Market Data Provider"]]

    P1((("1.0<br/>Document Ingestion<br/>& Parsing")))
    P2((("2.0<br/>Multi-Modal Embedding<br/>& Indexing")))
    P3((("3.0<br/>Query Routing<br/>(Supervisor)")))
    P4((("4.0<br/>Evidence Retrieval<br/>(Search / Vision / SQL)")))
    P5((("5.0<br/>Response Synthesis<br/>& Guardrails")))

    D1[("D1 — Qdrant<br/>Vector Store")]
    D2[("D2 — Historical<br/>Stock DB")]
    D3[("D3 — Raw Document<br/>Storage")]
    D4[("D4 — Trace & Eval<br/>Store (Langfuse)")]

    ANALYST -->|"PDF upload"| P1
    P1 -->|"raw file"| D3
    P1 -->|"classified page regions"| P2
    P2 -->|"text + image embeddings"| D1

    ANALYST -->|"question"| P3
    P3 -->|"routed sub-tasks"| P4
    P4 -->|"similarity search"| D1
    D1 -->|"ranked chunks"| P4
    P4 -->|"SQL query"| D2
    D2 -->|"query results"| P4
    P4 -.->|"sync"| MARKET

    P4 -->|"evidence + citations"| P5
    P5 -->|"execution trace"| D4
    P5 -->|"cited memo"| ANALYST

    style ANALYST fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    style MARKET fill:#ffedd5,stroke:#c2410c,color:#431407
    style P1 fill:#1c3d5a,stroke:#0f2438,color:#ffffff
    style P2 fill:#1c3d5a,stroke:#0f2438,color:#ffffff
    style P3 fill:#1c3d5a,stroke:#0f2438,color:#ffffff
    style P4 fill:#1c3d5a,stroke:#0f2438,color:#ffffff
    style P5 fill:#1c3d5a,stroke:#0f2438,color:#ffffff
    style D1 fill:#fef9c3,stroke:#a16207,color:#422006
    style D2 fill:#fef9c3,stroke:#a16207,color:#422006
    style D3 fill:#fef9c3,stroke:#a16207,color:#422006
    style D4 fill:#fef9c3,stroke:#a16207,color:#422006
```

---

## 4. UML Use Case Diagram

Mermaid has no native use-case shape, so actors and use cases are represented with person nodes and stadium (rounded) nodes, grouped by system boundary.

```mermaid
flowchart LR
    ANALYST(["👤 Quantitative<br/>Analyst"])
    ADMIN(["🛠️ System<br/>Administrator"])

    subgraph SYSTEM["OmniBrain System Boundary"]
        direction TB
        UC1(["Upload Document"])
        UC2(["Ask Natural-Language<br/>Question"])
        UC3(["View Cited Answer"])
        UC4(["Click Citation →<br/>View Source Page/Chart"])
        UC5(["Trigger Self-RAG Retry<br/>(automatic)"])
        UC6(["Configure Guardrail<br/>Policies"])
        UC7(["Monitor Traces &<br/>Token Usage (Langfuse)"])
        UC8(["Manage Vector Index<br/>(Qdrant collections)"])
    end

    ANALYST --> UC1
    ANALYST --> UC2
    ANALYST --> UC3
    ANALYST --> UC4
    UC2 -.include.-> UC5
    ADMIN --> UC6
    ADMIN --> UC7
    ADMIN --> UC8

    style ANALYST fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    style ADMIN fill:#ffedd5,stroke:#c2410c,color:#431407
```

---

## 5. UML Sequence Diagram — Query Lifecycle

Traces a single `/query` request through the Supervisor, the three specialist agents, guardrails, and observability logging.

```mermaid
sequenceDiagram
    actor User as Analyst
    participant API as FastAPI
    participant Sup as Supervisor (LangGraph)
    participant Search as Search Agent
    participant Vision as Vision Agent
    participant SQL as SQL Agent
    participant GR as NeMo Guardrails
    participant LF as Langfuse

    User->>API: POST /query {document_id, question}
    API->>Sup: invoke(state)
    Sup->>Sup: classify sub-tasks by modality

    par parallel dispatch
        Sup->>Search: retrieve(question)
        Search-->>Sup: passages + page citations
    and
        Sup->>Vision: analyze(chart/table region)
        Vision-->>Sup: extracted values + citations
    and
        Sup->>SQL: generate_sql(question) & execute
        SQL-->>Sup: query results
    end

    Sup->>Sup: synthesize draft answer
    Sup->>GR: check groundedness / hallucination / scope
    alt evidence insufficient or ungrounded
        GR-->>Sup: flag — retry
        Sup->>Search: rewritten query (Self-RAG loop)
        Search-->>Sup: new passages
        Sup->>GR: re-check
    end
    GR-->>Sup: pass
    Sup->>LF: log trace (tokens, latency, scores)
    Sup-->>API: final answer + citations
    API-->>User: 200 OK — cited investment memo
```

---

## 6. UML Class Diagram

Core domain model spanning the ingestion schemas (`app/models`, `app/ingestion`) and the agent layer (`app/agents`).

```mermaid
classDiagram
    class Document {
        +str document_id
        +str filename
        +DocumentStatus status
        +datetime submitted_at
        +List~PageRegion~ regions
    }

    class PageRegion {
        +int page_number
        +RegionType region_type
        +tuple boundingBox
        +bytes~str content
    }

    class TextChunk {
        +str chunk_id
        +str document_id
        +int page_number
        +str text
        +List~float~ embedding
    }

    class Citation {
        +int page
        +str source_type
        +str snippet
    }

    class QueryRequest {
        +str document_id
        +str question
    }

    class QueryResponse {
        +str answer
        +List~Citation~ citations
        +List~str~ agent_trace
    }

    class SupervisorAgent {
        +route(query) SubTaskPlan
        +synthesize(results) QueryResponse
    }

    class SearchAgent {
        +retrieve(query) List~TextChunk~
    }

    class VisionAgent {
        +analyze(region) dict
    }

    class SQLAgent {
        +generateSQL(question) str
        +execute(sql) list
    }

    class GuardrailsService {
        +checkGroundedness(answer, evidence) bool
        +checkScope(question) bool
    }

    Document "1" *-- "many" PageRegion : contains
    Document "1" *-- "many" TextChunk : produces
    QueryResponse "1" *-- "many" Citation : includes
    SupervisorAgent --> SearchAgent : dispatches
    SupervisorAgent --> VisionAgent : dispatches
    SupervisorAgent --> SQLAgent : dispatches
    SupervisorAgent --> GuardrailsService : validates via
    SupervisorAgent ..> QueryResponse : produces
    QueryRequest ..> SupervisorAgent : triggers
```

---

## 7. UML Component Diagram

Logical software components and the interfaces between them (approximated with grouped subgraphs, since Mermaid has no native component-diagram type).

```mermaid
flowchart TB
    subgraph UI["Presentation Layer"]
        ST["Streamlit Chat UI"]
    end

    subgraph API_LAYER["API Layer"]
        API["FastAPI Backend<br/>(app/api/routes)"]
    end

    subgraph ORCH["Orchestration Layer"]
        LG["LangGraph Supervisor<br/>(app/agents)"]
        SA["Search Agent"]
        VA["Vision Agent"]
        QA["SQL Agent"]
    end

    subgraph DATA["Data Layer"]
        QD[("Qdrant<br/>Vector DB")]
        PG[("Postgres<br/>Historical Data")]
        FS[("File Storage<br/>storage/uploads")]
    end

    subgraph CROSS["Cross-Cutting Services"]
        GR["NeMo Guardrails"]
        LF["Langfuse Observability"]
        LLM["LLM / VLM Provider<br/>(GPT-4o class)"]
    end

    ST -->|REST calls| API
    API --> LG
    LG --> SA
    LG --> VA
    LG --> QA
    SA --> QD
    VA --> QD
    VA --> LLM
    QA --> PG
    API --> FS
    LG --> GR
    LG --> LF
    SA --> LLM
    QA --> LLM

    style UI fill:#eef2ff,stroke:#4338ca
    style API_LAYER fill:#e0e7ff,stroke:#4338ca
    style ORCH fill:#1c3d5a,stroke:#0f2438,color:#ffffff
    style DATA fill:#fef9c3,stroke:#a16207
    style CROSS fill:#dcfce7,stroke:#166534
```

---

## 8. UML Deployment Diagram

Physical/logical deployment nodes for a typical local-dev or containerized environment.

```mermaid
flowchart TB
    subgraph CLIENT["Client Device"]
        BROWSER["Web Browser"]
    end

    subgraph APPSERVER["Application Server<br/>(Docker host / VM)"]
        STAPP["Streamlit Container<br/>:8501"]
        APIAPP["FastAPI Container<br/>:8000 (Uvicorn)"]
        LGRUNTIME["LangGraph Runtime<br/>(in-process w/ FastAPI)"]
    end

    subgraph DATASERVER["Data Tier"]
        QDRANT["Qdrant Container<br/>:6333 / :6334"]
        POSTGRES["PostgreSQL<br/>:5432"]
    end

    subgraph EXTERNAL["External / Cloud Services"]
        OPENAI["LLM / VLM API<br/>(OpenAI-class provider)"]
        LANGFUSE_CLOUD["Langfuse Cloud<br/>(observability)"]
    end

    BROWSER -->|HTTPS| STAPP
    STAPP -->|REST/JSON| APIAPP
    APIAPP --> LGRUNTIME
    LGRUNTIME -->|gRPC/REST| QDRANT
    LGRUNTIME -->|SQL| POSTGRES
    LGRUNTIME -->|HTTPS API calls| OPENAI
    LGRUNTIME -->|trace export| LANGFUSE_CLOUD

    style CLIENT fill:#eef2ff,stroke:#4338ca
    style APPSERVER fill:#1c3d5a,stroke:#0f2438,color:#ffffff
    style DATASERVER fill:#fef9c3,stroke:#a16207
    style EXTERNAL fill:#ffedd5,stroke:#c2410c
```

---

## Notes

- All diagrams render natively when this file is viewed on GitHub — no export step needed.
- To preview locally before committing, paste any code block into the [Mermaid Live Editor](https://mermaid.live).
- The DFDs and Component/Deployment diagrams reflect the **target architecture** from the Week-wise Development Plan; several data flows (Vision Agent, SQL Agent, Guardrails, Langfuse) will only be fully live once their respective weeks land — see `OmniBrain_Day2_Scaffold_Explained.pdf` for what's implemented as of Day 2.
