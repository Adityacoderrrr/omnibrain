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


class Citation(BaseModel):
    page: int
    source_type: str  # "text" | "table" | "chart" | "sql"
    snippet: str | None = None


class QueryResponse(BaseModel):
    document_id: str
    question: str
    answer: str
    citations: list[Citation] = []
    agent_trace: list[str] = Field(
        default_factory=list,
        description="Ordered list of agent/tool steps taken to answer this query (populated once the LangGraph supervisor is wired up in Week 2).",
    )
