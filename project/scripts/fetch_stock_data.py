#!/usr/bin/env python3
"""
Script to fetch and ingest stock data using yfinance.

Fetches stock market data for specified tickers and stores it in ChromaDB
for querying through the RAG system.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ingestion.pipeline import (  # noqa: E402
    IngestionPipeline,
    IngestionPipelineError,
)
from app.utils.config import config  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def main():
    """Main function to fetch and ingest stock data."""
    parser = argparse.ArgumentParser(
        description="Fetch and ingest stock data using yfinance"
    )
    parser.add_argument(
        "tickers",
        nargs="+",
        help="Stock ticker symbols to fetch (e.g., AAPL MSFT GOOGL)",
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Skip historical price data (faster, less data)",
    )
    parser.add_argument(
        "--no-store",
        action="store_true",
        help="Don't store embeddings in ChromaDB (dry run)",
    )
    parser.add_argument(
        "--collection",
        default="documents",
        help="ChromaDB collection name (default: documents)",
    )

    args = parser.parse_args()

    # Check if yfinance is enabled
    if not config.yfinance_enabled:
        logger.error("yfinance integration is disabled in configuration")
        logger.error("Set YFINANCE_ENABLED=true in .env file to enable")
        sys.exit(1)

    logger.info(f"Fetching stock data for {len(args.tickers)} tickers: {args.tickers}")

    try:
        # Create ingestion pipeline
        pipeline = IngestionPipeline(collection_name=args.collection)

        # Process stock data
        chunk_ids = pipeline.process_stock_tickers(
            ticker_symbols=args.tickers,
            include_history=not args.no_history,
            store_embeddings=not args.no_store,
        )

        logger.info(f"Successfully processed {len(args.tickers)} tickers")
        logger.info(f"Total chunks created: {len(chunk_ids)}")

        if args.no_store:
            logger.info("Dry run completed - no data stored in ChromaDB")
        else:
            logger.info(f"Data stored in ChromaDB collection: {args.collection}")

        return 0

    except IngestionPipelineError as e:
        logger.error(f"Failed to process stock data: {str(e)}", exc_info=True)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
