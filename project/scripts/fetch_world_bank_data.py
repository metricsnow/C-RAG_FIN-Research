#!/usr/bin/env python3
"""
Command-line script to fetch World Bank economic data.

Usage:
    python scripts/fetch_world_bank_data.py \\
        --indicators NY.GDP.MKTP.CD SP.POP.TOTL
    python scripts/fetch_world_bank_data.py \\
        --indicators NY.GDP.MKTP.CD --countries USA CHN --start-year 2020
    python scripts/fetch_world_bank_data.py --search "gdp"
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# noqa: E402 - imports after path modification
from app.ingestion.world_bank_fetcher import (  # noqa: E402
    WorldBankFetcher,
    WorldBankFetcherError,
)
from app.utils.config import config  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def main():
    """Main function for World Bank data fetching script."""
    parser = argparse.ArgumentParser(
        description="Fetch World Bank economic data indicators"
    )
    parser.add_argument(
        "--indicators",
        nargs="+",
        help="World Bank indicator codes (e.g., NY.GDP.MKTP.CD for GDP)",
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        help="Country ISO codes (e.g., USA CHN)",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        help="Start year for data",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        help="End year for data",
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Search for indicators by keyword",
    )
    parser.add_argument(
        "--list-countries",
        action="store_true",
        help="List available countries",
    )

    args = parser.parse_args()

    # Check if World Bank is enabled
    if not config.world_bank_enabled:
        logger.error(
            "World Bank integration is disabled. "
            "Set WORLD_BANK_ENABLED=true in .env file."
        )
        sys.exit(1)

    try:
        fetcher = WorldBankFetcher(
            rate_limit_delay=config.world_bank_rate_limit_seconds
        )

        # List countries
        if args.list_countries:
            logger.info("Fetching available countries...")
            countries = fetcher.get_countries()
            print(f"\nFound {len(countries)} countries:\n")
            for country in countries[:50]:  # Show first 50
                print(
                    f"  {country.get('country_code', 'N/A'):<5} - "
                    f"{country.get('name', 'N/A')}"
                )
            if len(countries) > 50:
                print(f"\n  ... and {len(countries) - 50} more countries")
            return

        # Search indicators
        if args.search:
            logger.info(f"Searching for indicators: '{args.search}'")
            results = fetcher.search_indicators(args.search, limit=20)
            print(f"\nFound {len(results)} indicators:\n")
            for result in results:
                code = result.get("indicator_code", "N/A")
                name = result.get("name", "N/A")
                print(f"  {code:<20} - {name}")
            return

        # Fetch indicators
        if not args.indicators:
            parser.error(
                "--indicators is required (or use --search or --list-countries)"
            )

        logger.info(f"Fetching {len(args.indicators)} World Bank indicators...")
        indicator_data = fetcher.fetch_multiple_indicators(
            args.indicators,
            country_codes=args.countries,
            start_year=args.start_year,
            end_year=args.end_year,
        )

        # Display results
        print(f"\nFetched {len(indicator_data)} indicators:\n")
        for indicator_code, data in indicator_data.items():
            if data.get("error"):
                print(f"  {indicator_code}: ERROR - {data.get('error')}")
            elif data.get("data") is None:
                print(f"  {indicator_code}: No data available")
            else:
                metadata = data.get("metadata", {})
                data_df = data.get("data")
                import pandas as pd

                if isinstance(data_df, pd.DataFrame) and not data_df.empty:
                    print(
                        f"  {indicator_code}: {metadata.get('name', 'N/A')}\n"
                        f"    Shape: {data_df.shape}\n"
                        f"    Unit: {metadata.get('unit', 'N/A')}"
                    )
                else:
                    name = metadata.get("name", "N/A")
                    print(f"  {indicator_code}: {name} - Data fetched")

    except WorldBankFetcherError as e:
        logger.error(f"World Bank fetching error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
