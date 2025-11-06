#!/usr/bin/env python3
"""
Command-line script to fetch IMF economic data.

Usage:
    python scripts/fetch_imf_data.py --indicators NGDP_RPCH LUR
    python scripts/fetch_imf_data.py --indicators NGDP_RPCH \\
        --countries US CN --start-year 2020
    python scripts/fetch_imf_data.py --list-indicators
    python scripts/fetch_imf_data.py --list-countries
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# noqa: E402 - imports after path modification
from app.ingestion.imf_fetcher import IMFFetcher, IMFFetcherError  # noqa: E402
from app.utils.config import config  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def main():
    """Main function for IMF data fetching script."""
    parser = argparse.ArgumentParser(description="Fetch IMF economic data indicators")
    parser.add_argument(
        "--indicators",
        nargs="+",
        help="IMF indicator codes (e.g., NGDP_RPCH for GDP growth)",
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        help="Country ISO codes (e.g., US CN)",
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
        "--list-indicators",
        action="store_true",
        help="List available indicators",
    )
    parser.add_argument(
        "--list-countries",
        action="store_true",
        help="List available countries",
    )

    args = parser.parse_args()

    # Check if IMF is enabled
    if not config.imf_enabled:
        logger.error("IMF integration is disabled. Set IMF_ENABLED=true in .env file.")
        sys.exit(1)

    try:
        fetcher = IMFFetcher(rate_limit_delay=config.imf_rate_limit_seconds)

        # List indicators
        if args.list_indicators:
            logger.info("Fetching available indicators...")
            indicators = fetcher.get_available_indicators()
            print(f"\nFound {len(indicators)} indicators:\n")
            for indicator in indicators[:50]:  # Show first 50
                print(
                    f"  {indicator.get('indicator_code', 'N/A'):<20} - "
                    f"{indicator.get('name', 'N/A')}"
                )
            if len(indicators) > 50:
                print(f"\n  ... and {len(indicators) - 50} more indicators")
            return

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

        # Fetch indicators
        if not args.indicators:
            parser.error(
                "--indicators is required "
                "(or use --list-indicators or --list-countries)"
            )

        logger.info(f"Fetching {len(args.indicators)} IMF indicators...")
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

    except IMFFetcherError as e:
        logger.error(f"IMF fetching error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
