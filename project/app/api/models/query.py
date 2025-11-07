"""
Query API request/response models.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SourceMetadata(BaseModel):
    """Source document metadata for citations."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "data/documents/AAPL_10-K_2023.txt",
                "filename": "AAPL_10-K_2023.txt",
                "ticker": "AAPL",
                "form_type": "10-K",
                "chunk_index": 0,
                "date": "2023-09-30",
            }
        }
    )

    source: Optional[str] = Field(
        None, description="Source document path or identifier"
    )
    filename: Optional[str] = Field(None, description="Source filename")
    ticker: Optional[str] = Field(None, description="Ticker symbol if applicable")
    form_type: Optional[str] = Field(None, description="Form type (e.g., 10-K, 10-Q)")
    chunk_index: Optional[int] = Field(None, description="Chunk index in document")
    date: Optional[str] = Field(None, description="Document date")


class QueryFilters(BaseModel):
    """Advanced query filters model."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date_from": "2023-01-01",
                "date_to": "2023-12-31",
                "document_type": "edgar_filing",
                "ticker": "AAPL",
                "form_type": "10-K",
                "source": "data/documents/AAPL_10-K_2023.txt",
            }
        }
    )

    date_from: Optional[str] = Field(
        None, description="Start date filter (ISO format: YYYY-MM-DD)"
    )
    date_to: Optional[str] = Field(
        None, description="End date filter (ISO format: YYYY-MM-DD)"
    )
    document_type: Optional[str] = Field(
        None, description="Document type filter (e.g., 'edgar_filing', 'news')"
    )
    ticker: Optional[str] = Field(
        None, description="Ticker symbol filter (e.g., 'AAPL', 'MSFT')"
    )
    form_type: Optional[str] = Field(
        None, description="Form type filter (e.g., '10-K', '10-Q')"
    )
    source: Optional[str] = Field(None, description="Source identifier filter")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Custom metadata filters"
    )


class QueryRequest(BaseModel):
    """RAG query request model."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "What was Apple's revenue in 2023?",
                "top_k": 5,
                "conversation_history": [
                    {"role": "user", "content": "Tell me about Apple"},
                    {
                        "role": "assistant",
                        "content": "Apple Inc. is a technology company...",
                    },
                ],
                "filters": {
                    "date_from": "2023-01-01",
                    "ticker": "AAPL",
                    "form_type": "10-K",
                },
                "enable_query_parsing": True,
            }
        }
    )

    question: str = Field(..., description="Natural language question", min_length=1)
    top_k: Optional[int] = Field(
        None, ge=1, le=20, description="Number of top chunks to retrieve (optional)"
    )
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Previous conversation messages for context (optional)",
    )
    filters: Optional[QueryFilters] = Field(
        None, description="Advanced query filters (optional)"
    )
    enable_query_parsing: Optional[bool] = Field(
        True,
        description="Enable automatic query parsing for filters and Boolean operators",
    )


class QueryResponse(BaseModel):
    """RAG query response model."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "Apple's revenue in 2023 was $383.3 billion...",
                "sources": [
                    {
                        "source": "data/documents/AAPL_10-K_2023.txt",
                        "filename": "AAPL_10-K_2023.txt",
                        "ticker": "AAPL",
                        "form_type": "10-K",
                        "chunk_index": 0,
                        "date": "2023-09-30",
                    }
                ],
                "chunks_used": 5,
                "error": None,
                "parsed_query": {
                    "query_text": "What was Apple's revenue in 2023?",
                    "boolean_operators": [],
                    "filters": {"ticker": "AAPL", "form_type": "10-K"},
                    "query_terms": ["apple", "revenue", "2023"],
                },
            }
        }
    )

    answer: str = Field(..., description="Generated answer")
    sources: List[SourceMetadata] = Field(
        default_factory=list, description="Source documents used"
    )
    chunks_used: int = Field(..., ge=0, description="Number of chunks used")
    error: Optional[str] = Field(None, description="Error message if query failed")
    parsed_query: Optional[Dict[str, Any]] = Field(
        None, description="Parsed query information (if query parsing enabled)"
    )
