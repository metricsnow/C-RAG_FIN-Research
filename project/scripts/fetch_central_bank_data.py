#!/usr/bin/env python3
"""
Command-line script to fetch central bank data.

Fetches FOMC statements, minutes, and press conferences.

Usage:
    python scripts/fetch_central_bank_data.py --types fomc_statement
    python scripts/fetch_central_bank_data.py \\
        --types fomc_statement fomc_minutes --limit 5
    python scripts/fetch_central_bank_data.py --types all
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# noqa: E402 - imports after path modification
from app.ingestion.central_bank_fetcher import (  # noqa: E402
    CentralBankFetcher,
    CentralBankFetcherError,
)
from app.ingestion.pipeline import create_pipeline  # noqa: E402
from app.utils.config import config  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def main():
    """Main function for central bank data fetching script."""
    parser = argparse.ArgumentParser(
        description=(
            "Fetch central bank communications "
            "(FOMC statements, minutes, press conferences)"
        )
    )
    parser.add_argument(
        "--types",
        nargs="+",
        choices=["fomc_statement", "fomc_minutes", "fomc_press_conference", "all"],
        default=["all"],
        help="Communication types to fetch (default: all)",
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
        "--limit",
        type=int,
        help="Maximum number of communications per type (optional)",
    )
    parser.add_argument(
        "--store",
        action="store_true",
        help="Store fetched data in ChromaDB (default: False, just fetch and display)",
    )

    args = parser.parse_args()

    # Check if central bank integration is enabled
    if not config.central_bank_enabled:
        logger.error(
            "Central bank integration is disabled. "
            "Set CENTRAL_BANK_ENABLED=true in .env file."
        )
        sys.exit(1)

    try:
        # Normalize communication types
        comm_types = args.types
        if "all" in comm_types:
            comm_types = ["fomc_statement", "fomc_minutes", "fomc_press_conference"]

        if args.store:
            # Use pipeline to fetch and store
            logger.info("Fetching and storing central bank communications...")
            pipeline = create_pipeline()
            ids = pipeline.process_central_bank(
                comm_types=comm_types,
                start_date=args.start_date,
                end_date=args.end_date,
                limit=args.limit,
                store_embeddings=True,
            )
            logger.info(f"Successfully stored {len(ids)} chunks in ChromaDB")
            print(f"\n✅ Stored {len(ids)} document chunks in ChromaDB")
        else:
            # Just fetch and display
            logger.info("Fetching central bank communications...")
            fetcher = CentralBankFetcher(
                rate_limit_delay=config.central_bank_rate_limit_seconds,
                use_web_scraping=config.central_bank_use_web_scraping,
            )

            all_communications = []
            for comm_type in comm_types:
                logger.info(f"Fetching {comm_type}...")
                try:
                    if comm_type == "fomc_statement":
                        communications = fetcher.fetch_fomc_statements(
                            start_date=args.start_date,
                            end_date=args.end_date,
                            limit=args.limit,
                        )
                    elif comm_type == "fomc_minutes":
                        communications = fetcher.fetch_fomc_minutes(
                            start_date=args.start_date,
                            end_date=args.end_date,
                            limit=args.limit,
                        )
                    elif comm_type == "fomc_press_conference":
                        communications = fetcher.fetch_fomc_press_conferences(
                            start_date=args.start_date,
                            end_date=args.end_date,
                            limit=args.limit,
                        )
                    else:
                        logger.warning(f"Unknown communication type: {comm_type}")
                        continue

                    all_communications.extend(communications)
                    print(
                        f"\n✅ Fetched {len(communications)} {comm_type} communications"
                    )
                except CentralBankFetcherError as e:
                    logger.warning(f"Failed to fetch {comm_type}: {str(e)}")
                    print(f"\n❌ Failed to fetch {comm_type}: {e}")
                    continue

            # Display results
            if all_communications:
                print("\n📊 Summary:")
                print(f"  Total communications: {len(all_communications)}")
                for comm in all_communications[:10]:  # Show first 10
                    comm_type = comm.get("type", "unknown")
                    date = comm.get("date", "Unknown")
                    title = comm.get("title", "No title")
                    url = comm.get("url", "")
                    print(f"\n  [{comm_type}] {date}")
                    print(f"    Title: {title}")
                    if url:
                        print(f"    URL: {url}")
                    # Show forward guidance if available
                    content = comm.get("content", "")
                    forward_guidance = fetcher.extract_forward_guidance(content)
                    if forward_guidance:
                        print(
                            f"    Forward Guidance: "
                            f"{len(forward_guidance)} statements found"
                        )
                if len(all_communications) > 10:
                    remaining = len(all_communications) - 10
                    print(f"\n  ... and {remaining} more communications")
            else:
                print("\n⚠️  No communications fetched")

    except CentralBankFetcherError as e:
        logger.error(f"Central bank fetching error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
