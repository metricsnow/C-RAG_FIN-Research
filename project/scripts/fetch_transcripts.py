#!/usr/bin/env python3
"""
Script to fetch and ingest earnings call transcripts.

Usage:
    python scripts/fetch_transcripts.py --ticker AAPL
    python scripts/fetch_transcripts.py --ticker AAPL --date 2025-01-15
    python scripts/fetch_transcripts.py --tickers AAPL MSFT GOOGL
    python scripts/fetch_transcripts.py --ticker AAPL --source seeking_alpha
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ingestion.pipeline import (  # noqa: E402
    IngestionPipelineError,
    create_pipeline,
)
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def main():
    """Main function to fetch and ingest transcripts."""
    parser = argparse.ArgumentParser(
        description="Fetch and ingest earnings call transcripts"
    )
    parser.add_argument(
        "--ticker",
        type=str,
        help="Stock ticker symbol (e.g., AAPL, MSFT)",
    )
    parser.add_argument(
        "--tickers",
        type=str,
        nargs="+",
        help="Multiple stock ticker symbols",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Transcript date (YYYY-MM-DD format, optional)",
    )
    parser.add_argument(
        "--source",
        type=str,
        choices=["seeking_alpha", "yahoo_finance"],
        help="Preferred transcript source (optional)",
    )
    parser.add_argument(
        "--no-store",
        action="store_true",
        help="Fetch and parse but don't store in ChromaDB",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="documents",
        help="ChromaDB collection name (default: documents)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.ticker and not args.tickers:
        parser.error("Either --ticker or --tickers must be provided")

    # Get ticker list
    tickers = []
    if args.ticker:
        tickers.append(args.ticker.upper())
    if args.tickers:
        tickers.extend([t.upper() for t in args.tickers])

    if not tickers:
        parser.error("No tickers provided")

    # Create pipeline
    try:
        pipeline = create_pipeline(collection_name=args.collection)
        logger.info(f"Created ingestion pipeline for collection: {args.collection}")
    except Exception as e:
        logger.error(f"Failed to create pipeline: {str(e)}")
        sys.exit(1)

    # Process transcripts
    try:
        store_embeddings = not args.no_store
        logger.info(
            f"Processing transcripts for {len(tickers)} ticker(s): {', '.join(tickers)}"
        )
        if args.date:
            logger.info(f"Date filter: {args.date}")
        if args.source:
            logger.info(f"Source preference: {args.source}")

        chunk_ids = pipeline.process_transcripts(
            ticker_symbols=tickers,
            date=args.date,
            source=args.source,
            store_embeddings=store_embeddings,
        )

        logger.info(
            f"Successfully processed transcripts: {len(chunk_ids)} chunks created"
        )
        if store_embeddings:
            logger.info(f"Transcripts stored in ChromaDB collection: {args.collection}")
        else:
            logger.info("Transcripts processed but not stored (--no-store flag)")

        print(f"\n✓ Successfully processed {len(tickers)} transcript(s)")
        print(f"✓ Created {len(chunk_ids)} chunk(s)")
        if store_embeddings:
            print(f"✓ Stored in ChromaDB collection: {args.collection}")

    except IngestionPipelineError as e:
        logger.error(f"Pipeline error: {str(e)}")
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"\n✗ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
