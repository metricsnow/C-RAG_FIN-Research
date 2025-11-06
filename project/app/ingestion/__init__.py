"""
Document ingestion pipeline module.

Handles loading and processing of financial documents (PDF, Markdown, text).
"""

from app.ingestion.document_loader import (
    DocumentIngestionError,
    DocumentLoader,
)
from app.ingestion.edgar_fetcher import (
    EdgarFetcher,
    EdgarFetcherError,
    create_edgar_fetcher,
)
from app.ingestion.pipeline import (
    IngestionPipeline,
    IngestionPipelineError,
    create_pipeline,
)
from app.ingestion.stock_data_normalizer import StockDataNormalizer
from app.ingestion.transcript_fetcher import (
    TranscriptFetcher,
    TranscriptFetcherError,
)
from app.ingestion.transcript_parser import (
    TranscriptParser,
    TranscriptParserError,
)
from app.ingestion.yfinance_fetcher import (
    YFinanceFetcher,
    YFinanceFetcherError,
)

# Enhanced EDGAR parsers (TASK-032)
try:
    from app.ingestion.def14a_parser import Def14AParser, Def14AParserError
    from app.ingestion.form4_parser import Form4Parser, Form4ParserError
    from app.ingestion.forms1_parser import FormS1Parser, FormS1ParserError
    from app.ingestion.xbrl_parser import XBRLParser, XBRLParserError

    ENHANCED_PARSERS_AVAILABLE = True
except ImportError:
    ENHANCED_PARSERS_AVAILABLE = False
    # Define placeholders for type checking
    Def14AParser = None
    Def14AParserError = None
    Form4Parser = None
    Form4ParserError = None
    FormS1Parser = None
    FormS1ParserError = None
    XBRLParser = None
    XBRLParserError = None

__all__ = [
    "DocumentLoader",
    "DocumentIngestionError",
    "IngestionPipeline",
    "IngestionPipelineError",
    "create_pipeline",
    "EdgarFetcher",
    "EdgarFetcherError",
    "create_edgar_fetcher",
    "YFinanceFetcher",
    "YFinanceFetcherError",
    "StockDataNormalizer",
    "TranscriptFetcher",
    "TranscriptFetcherError",
    "TranscriptParser",
    "TranscriptParserError",
    "ENHANCED_PARSERS_AVAILABLE",
]

# Add enhanced parsers to __all__ if available
if ENHANCED_PARSERS_AVAILABLE:
    __all__.extend(
        [
            "Def14AParser",
            "Def14AParserError",
            "Form4Parser",
            "Form4ParserError",
            "FormS1Parser",
            "FormS1ParserError",
            "XBRLParser",
            "XBRLParserError",
        ]
    )
