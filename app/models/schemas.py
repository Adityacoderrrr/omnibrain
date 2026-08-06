"""
Shared request/response models for the OmniBrain API.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    RECEIVED = "received"
    PARSING = "parsing"
    EMBEDDING = "embedding"
    READY = "ready"
    FAILED = "failed"


class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., description="Unique ID assigned to the uploaded document")
    filename: str
    status: DocumentStatus
    submitted_at: datetime


class DocumentStatusResponse(BaseModel):
    document_id: str
    status: DocumentStatus
    pages_processed: int | None = None
    total_pages: int | None = None


class QueryRequest(BaseModel):
    document_id: str = Field(..., description="ID of the ingested document to query against")
    question: str = Field(..., min_length=1, description="Natural language question from the analyst")
    session_id: str | None = Field(default=None, description="Optional session identifier for multi-turn conversation memory")
    request_id: str | None = Field(default=None, description="Optional unique request identifier for telemetry tracing")


class Citation(BaseModel):
    page: int
    source_type: str  # "text" | "table" | "chart" | "sql"
    snippet: str | None = None


class QueryResponse(BaseModel):
    document_id: str
    question: str
    answer: str
    session_id: str | None = None
    request_id: str | None = None
    sql_explanation: str | None = None
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    citations: list[dict] = []
    agent_trace: list[str] = Field(
        default_factory=list,
        description="Ordered list of agent/tool steps taken to answer this query.",
    )
    trace_details: dict = Field(default_factory=dict, description="Structured observability trace dictionary per agent node")
    token_analytics: dict = Field(default_factory=dict, description="Prompt, completion, and total token usage metrics")
    follow_up_questions: list[str] = Field(default_factory=list, description="Generated follow-up questions")
    reflection: dict = Field(default_factory=dict, description="Self-reflection and answer verification metrics")


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the document collection")
    description: str | None = Field(default="", description="Description of the collection")
    tags: list[str] = Field(default_factory=list)


class CollectionResponse(BaseModel):
    collection_id: str
    name: str
    description: str | None = ""
    tags: list[str] = []
    document_count: int = 0
    created_at: datetime


class DocumentRenameRequest(BaseModel):
    new_filename: str = Field(..., min_length=1)


class DocumentTagRequest(BaseModel):
    tags: list[str] = Field(default_factory=list)


class TraceItemResponse(BaseModel):
    request_id: str
    session_id: str
    timestamp: str
    question: str
    answer: str
    agent_trace: list[str]
    trace_details: dict
    token_analytics: dict
    execution_time_ms: float


class AnalyticsOverviewResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    total_queries: int
    total_documents: int
    total_tokens: int
    avg_latency_ms: float
    avg_confidence: float
    estimated_cost_usd: float
    agent_calls: dict[str, int]
    model_breakdown: dict[str, int]


