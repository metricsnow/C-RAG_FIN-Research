"""
Document ingestion API request/response models.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class IngestionRequest(BaseModel):
    """Document ingestion request model."""

    file_path: Optional[str] = Field(
        None, description="Path to document file (if ingesting from file system)"
    )
    store_embeddings: bool = Field(
        True, description="Whether to store embeddings in ChromaDB"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "file_path": "data/documents/AAPL_10-K_2023.txt",
                "store_embeddings": True,
            }
        }


class IngestionResponse(BaseModel):
    """Document ingestion response model."""

    success: bool = Field(..., description="Whether ingestion was successful")
    chunk_ids: List[str] = Field(
        default_factory=list, description="List of chunk IDs created"
    )
    chunks_created: int = Field(..., ge=0, description="Number of chunks created")
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(None, description="Error message if ingestion failed")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "success": True,
                "chunk_ids": ["chunk_1", "chunk_2", "chunk_3"],
                "chunks_created": 3,
                "message": "Document ingested successfully",
                "error": None,
            }
        }
