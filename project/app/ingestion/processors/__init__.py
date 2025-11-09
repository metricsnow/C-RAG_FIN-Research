"""
Data source processors for ingestion pipeline.

Provides specialized processors for different data source types.
"""

from app.ingestion.processors.alternative_data_processor import (
    AlternativeDataProcessor,
)
from app.ingestion.processors.base_processor import BaseProcessor
from app.ingestion.processors.document_processor import DocumentProcessor
from app.ingestion.processors.economic_data_processor import EconomicDataProcessor
from app.ingestion.processors.news_processor import NewsProcessor
from app.ingestion.processors.stock_processor import StockProcessor
from app.ingestion.processors.transcript_processor import TranscriptProcessor

__all__ = [
    "BaseProcessor",
    "DocumentProcessor",
    "StockProcessor",
    "TranscriptProcessor",
    "NewsProcessor",
    "EconomicDataProcessor",
    "AlternativeDataProcessor",
]
