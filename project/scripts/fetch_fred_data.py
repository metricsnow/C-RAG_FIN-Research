#!/usr/bin/env python3
"""
Script to fetch and ingest FRED economic time series data.

Usage:
    python scripts/fetch_fred_data.py --series GDP UNRATE FEDFUNDS
    python scripts/fetch_fred_data.py --series GDP \
        --start-date 2020-01-01 --end-date 2024-12-31
    python scripts/fetch_fred_data.py --search "unemployment rate"
    python scripts/fetch_fred_data.py --series GDP --no-store
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
    """Main function to fetch and ingest FRED economic time series data."""
    parser = argparse.ArgumentParser(
        description="Fetch and ingest FRED economic time series data"
    )
    parser.add_argument(
        "--series",
        nargs="+",
        help="FRED series IDs (e.g., GDP UNRATE FEDFUNDS)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD format, optional)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date (YYYY-MM-DD format, optional)",
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Search for series by text (e.g., 'unemployment rate')",
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
    if not args.series and not args.search:
        parser.error("Either --series or --search must be provided")

    if args.series and args.search:
        parser.error("Cannot use both --series and --search at the same time")

    try:
        # Create pipeline
        logger.info("Initializing ingestion pipeline")
        pipeline = create_pipeline(collection_name=args.collection)

        # Handle search mode
        if args.search:
            logger.info(f"Searching FRED series: '{args.search}'")
            if pipeline.fred_fetcher is None:
                logger.error("FRED fetcher is not initialized")
                sys.exit(1)

            search_results = pipeline.fred_fetcher.search_series(args.search, limit=20)
            if not search_results:
                logger.warning(f"No series found for search: '{args.search}'")
                sys.exit(0)

            logger.info(f"Found {len(search_results)} series matching '{args.search}'")
            for result in search_results:
                logger.info(
                    f"  - {result['series_id']}: {result['title']} "
                    f"({result.get('frequency', 'N/A')})"
                )

            # Ask user if they want to fetch these series
            series_ids = [r["series_id"] for r in search_results]
            logger.info(f"\nFetching {len(series_ids)} series...")
        else:
            series_ids = args.series

        # Process FRED series
        logger.info(f"Processing {len(series_ids)} FRED series")
        ids = pipeline.process_fred_series(
            series_ids=series_ids,
            start_date=args.start_date,
            end_date=args.end_date,
            store_embeddings=not args.no_store,
        )

        if args.no_store:
            logger.info(
                f"Fetched and parsed {len(ids)} FRED series chunks (not stored)"
            )
        else:
            logger.info(
                f"Successfully processed and stored {len(ids)} FRED series chunks"
            )

    except IngestionPipelineError as e:
        logger.error(f"Pipeline error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
