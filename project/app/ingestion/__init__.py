"""
Document ingestion pipeline module.

Handles loading and processing of financial documents (PDF, Markdown, text).
"""

from app.ingestion.document_loader import (
    DocumentIngestionError,
    DocumentLoader,
)

__all__ = ["DocumentLoader", "DocumentIngestionError"]

