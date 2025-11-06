#!/usr/bin/env python3
"""
Script to fetch and ingest economic calendar events.

Usage:
    python scripts/fetch_economic_calendar.py
    python scripts/fetch_economic_calendar.py \
        --start-date 2025-01-01 --end-date 2025-01-31
    python scripts/fetch_economic_calendar.py --country "united states"
    python scripts/fetch_economic_calendar.py --importance High
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
    """Main function to fetch and ingest economic calendar events."""
    parser = argparse.ArgumentParser(
        description="Fetch and ingest economic calendar events"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD format, optional, defaults to today)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date (YYYY-MM-DD format, optional, defaults to 30 days from start)",
    )
    parser.add_argument(
        "--country",
        type=str,
        help="Country code (e.g., 'united states', 'china', optional)",
    )
    parser.add_argument(
        "--importance",
        type=str,
        choices=["High", "Medium", "Low"],
        help="Filter by importance level (optional)",
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

    try:
        # Create pipeline
        logger.info("Initializing ingestion pipeline")
        pipeline = create_pipeline(collection_name=args.collection)

        # Process economic calendar
        logger.info("Processing economic calendar events")
        ids = pipeline.process_economic_calendar(
            start_date=args.start_date,
            end_date=args.end_date,
            country=args.country,
            importance=args.importance,
            store_embeddings=not args.no_store,
        )

        if args.no_store:
            logger.info(
                f"Fetched and parsed {len(ids)} economic calendar events (not stored)"
            )
        else:
            logger.info(
                f"Successfully processed and stored {len(ids)} "
                f"economic calendar event chunks"
            )

    except IngestionPipelineError as e:
        logger.error(f"Pipeline error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
