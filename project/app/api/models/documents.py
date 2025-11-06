"""
Document management API request/response models.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentMetadata(BaseModel):
    """Document metadata model."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "chunk_1",
                "metadata": {
                    "source": "data/documents/AAPL_10-K_2023.txt",
                    "filename": "AAPL_10-K_2023.txt",
                    "ticker": "AAPL",
                    "form_type": "10-K",
                    "chunk_index": 0,
                    "date": "2023-09-30",
                },
                "content": "Apple Inc. is a technology company...",
            }
        }
    )

    id: str = Field(..., description="Document chunk ID")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )
    content: Optional[str] = Field(None, description="Document content preview")


class DocumentListResponse(BaseModel):
    """Document list response model."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "documents": [
                    {
                        "id": "chunk_1",
                        "metadata": {"source": "data/documents/AAPL_10-K_2023.txt"},
                        "content": "Apple Inc. is a technology company...",
                    }
                ],
                "total": 1,
                "message": "Documents retrieved successfully",
            }
        }
    )

    documents: List[DocumentMetadata] = Field(
        default_factory=list, description="List of documents"
    )
    total: int = Field(..., ge=0, description="Total number of documents")
    message: str = Field(..., description="Status message")


class DocumentDetailResponse(BaseModel):
    """Document detail response model."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document": {
                    "id": "chunk_1",
                    "metadata": {"source": "data/documents/AAPL_10-K_2023.txt"},
                    "content": "Apple Inc. is a technology company...",
                },
                "message": "Document retrieved successfully",
                "error": None,
            }
        }
    )

    document: Optional[DocumentMetadata] = Field(None, description="Document details")
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(None, description="Error message if not found")
