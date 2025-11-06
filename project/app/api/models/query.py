"""
Query API request/response models.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SourceMetadata(BaseModel):
    """Source document metadata for citations."""

    source: Optional[str] = Field(
        None, description="Source document path or identifier"
    )
    filename: Optional[str] = Field(None, description="Source filename")
    ticker: Optional[str] = Field(None, description="Ticker symbol if applicable")
    form_type: Optional[str] = Field(None, description="Form type (e.g., 10-K, 10-Q)")
    chunk_index: Optional[int] = Field(None, description="Chunk index in document")
    date: Optional[str] = Field(None, description="Document date")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "source": "data/documents/AAPL_10-K_2023.txt",
                "filename": "AAPL_10-K_2023.txt",
                "ticker": "AAPL",
                "form_type": "10-K",
                "chunk_index": 0,
                "date": "2023-09-30",
            }
        }


class QueryRequest(BaseModel):
    """RAG query request model."""

    question: str = Field(..., description="Natural language question", min_length=1)
    top_k: Optional[int] = Field(
        None, ge=1, le=20, description="Number of top chunks to retrieve (optional)"
    )
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Previous conversation messages for context (optional)",
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
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
            }
        }


class QueryResponse(BaseModel):
    """RAG query response model."""

    answer: str = Field(..., description="Generated answer")
    sources: List[SourceMetadata] = Field(
        default_factory=list, description="Source documents used"
    )
    chunks_used: int = Field(..., ge=0, description="Number of chunks used")
    error: Optional[str] = Field(None, description="Error message if query failed")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
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
            }
        }
