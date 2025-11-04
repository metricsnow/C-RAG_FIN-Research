"""
Document ingestion pipeline module.

Handles loading and processing of financial documents (PDF, Markdown, text).
"""

from app.ingestion.document_loader import (
    DocumentIngestionError,
    DocumentLoader,
)
from app.ingestion.pipeline import (
    IngestionPipeline,
    IngestionPipelineError,
    create_pipeline,
)
from app.ingestion.edgar_fetcher import (
    EdgarFetcher,
    EdgarFetcherError,
    create_edgar_fetcher,
)

__all__ = [
    "DocumentLoader",
    "DocumentIngestionError",
    "IngestionPipeline",
    "IngestionPipelineError",
    "create_pipeline",
    "EdgarFetcher",
    "EdgarFetcherError",
    "create_edgar_fetcher",
]

