"""
World Bank Open Data API fetcher.

Fetches global economic data from World Bank Open Data API including GDP,
inflation, unemployment, trade balance, and other indicators for 188+ countries.
"""

import time
from typing import Any, Dict, List, Optional

import pandas as pd
import world_bank_data as wb

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WorldBankFetcherError(Exception):
    """Custom exception for World Bank fetcher errors."""

    pass


class WorldBankFetcher:
    """
    World Bank Open Data API fetcher.

    Fetches global economic data from World Bank Open Data API with proper
    rate limiting and error handling. Supports 188+ countries and thousands
    of economic indicators including GDP, inflation, unemployment, trade balance.
    """

    def __init__(
        self,
        rate_limit_delay: Optional[float] = None,
    ):
        """
        Initialize World Bank fetcher.

        Args:
            rate_limit_delay: Delay between requests in seconds (default: from config)
        """
        self.rate_limit_delay = (
            rate_limit_delay
            if rate_limit_delay is not None
            else config.world_bank_rate_limit_seconds
        )

        try:
            # Test API access by fetching countries list
            _ = wb.get_countries()
            logger.info("World Bank API client initialized successfully")
        except Exception as e:
            logger.warning(
                f"World Bank API initialization warning: {str(e)}. "
                "API may still work, but some features may be limited."
            )

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting delay between requests."""
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)

    def fetch_indicator(
        self,
        indicator_code: str,
        country_codes: Optional[List[str]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Fetch indicator data by indicator code.

        Args:
            indicator_code: World Bank indicator code (e.g., 'NY.GDP.MKTP.CD' for GDP)
            country_codes: List of country ISO codes (e.g., ['USA', 'CHN'], optional)
            start_year: Start year (optional)
            end_year: End year (optional)

        Returns:
            Dictionary containing indicator data and metadata

        Raises:
            WorldBankFetcherError: If fetching fails
        """
        logger.info(f"Fetching World Bank indicator: {indicator_code}")
        try:
            self._apply_rate_limit()

            # Fetch indicator data
            if country_codes:
                # Fetch for specific countries
                data = wb.get_series(indicator_code, country=country_codes)
            else:
                # Fetch for all countries
                data = wb.get_series(indicator_code)

            if data is None or (isinstance(data, pd.DataFrame) and data.empty):
                logger.warning(f"No data returned for indicator {indicator_code}")
                return {
                    "indicator_code": indicator_code,
                    "data": None,
                    "metadata": {},
                    "error": "No data available",
                }

            # Filter by year range if specified
            if start_year or end_year:
                if isinstance(data, pd.DataFrame):
                    if start_year:
                        data = data[data.index >= start_year]
                    if end_year:
                        data = data[data.index <= end_year]

            # Fetch indicator metadata
            self._apply_rate_limit()
            try:
                indicators = wb.get_indicators(indicator_code)
                if indicators is not None and not indicators.empty:
                    indicator_info = indicators.iloc[0].to_dict()
                    metadata = {
                        "name": indicator_info.get("name", ""),
                        "source": indicator_info.get("source", ""),
                        "topic": indicator_info.get("topic", ""),
                        "unit": indicator_info.get("unit", ""),
                        "note": indicator_info.get("note", ""),
                    }
                else:
                    metadata = {}
            except Exception as e:
                logger.warning(
                    f"Failed to fetch indicator info for {indicator_code}: {str(e)}"
                )
                metadata = {}

            # Get data shape info
            if isinstance(data, pd.DataFrame):
                data_points = len(data) * len(data.columns) if not data.empty else 0
            else:
                data_points = len(data) if hasattr(data, "__len__") else 0

            logger.info(
                f"Successfully fetched {data_points} data points "
                f"for indicator {indicator_code}"
            )

            return {
                "indicator_code": indicator_code,
                "data": data,
                "metadata": metadata,
                "country_codes": country_codes,
                "start_year": start_year,
                "end_year": end_year,
            }

        except Exception as e:
            logger.error(
                f"Error fetching World Bank indicator {indicator_code}: {str(e)}",
                exc_info=True,
            )
            raise WorldBankFetcherError(
                f"Error fetching World Bank indicator {indicator_code}: {str(e)}"
            ) from e

    def fetch_multiple_indicators(
        self,
        indicator_codes: List[str],
        country_codes: Optional[List[str]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch multiple indicators.

        Args:
            indicator_codes: List of World Bank indicator codes
            country_codes: List of country ISO codes (optional)
            start_year: Start year (optional)
            end_year: End year (optional)

        Returns:
            Dictionary mapping indicator_code to indicator data

        Raises:
            WorldBankFetcherError: If fetching fails
        """
        logger.info(f"Fetching {len(indicator_codes)} World Bank indicators")
        results = {}

        for indicator_code in indicator_codes:
            try:
                result = self.fetch_indicator(
                    indicator_code,
                    country_codes=country_codes,
                    start_year=start_year,
                    end_year=end_year,
                )
                results[indicator_code] = result
            except WorldBankFetcherError as e:
                logger.warning(f"Failed to fetch indicator {indicator_code}: {str(e)}")
                results[indicator_code] = {
                    "indicator_code": indicator_code,
                    "data": None,
                    "metadata": {},
                    "error": str(e),
                }

        successful_count = len(
            [r for r in results.values() if r.get("data") is not None]
        )
        logger.info(
            f"Successfully fetched {successful_count} out of "
            f"{len(indicator_codes)} indicators"
        )
        return results

    def search_indicators(
        self, search_text: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for indicators by keyword.

        Args:
            search_text: Search query text
            limit: Maximum number of results to return (default: 20)

        Returns:
            List of indicator information dictionaries

        Raises:
            WorldBankFetcherError: If search fails
        """
        logger.info(f"Searching World Bank indicators: '{search_text}'")
        try:
            self._apply_rate_limit()

            # Search for indicators
            search_results = wb.search_indicators(search_text)

            if search_results is None or search_results.empty:
                logger.info(f"No indicators found for search: '{search_text}'")
                return []

            # Convert to list of dictionaries
            results = []
            for _, row in search_results.head(limit).iterrows():
                results.append(
                    {
                        "indicator_code": row.get("id", ""),
                        "name": row.get("name", ""),
                        "source": row.get("source", ""),
                        "topic": row.get("topic", ""),
                    }
                )

            logger.info(f"Found {len(results)} indicators matching '{search_text}'")
            return results

        except Exception as e:
            logger.error(
                f"Error searching World Bank indicators: {str(e)}", exc_info=True
            )
            raise WorldBankFetcherError(
                f"Error searching World Bank indicators: {str(e)}"
            ) from e

    def get_countries(self) -> List[Dict[str, Any]]:
        """
        Get list of countries available in World Bank data.

        Returns:
            List of country information dictionaries

        Raises:
            WorldBankFetcherError: If fetching fails
        """
        logger.info("Fetching World Bank countries list")
        try:
            self._apply_rate_limit()

            countries = wb.get_countries()

            if countries is None or countries.empty:
                logger.warning("No countries data returned")
                return []

            # Convert to list of dictionaries
            results = []
            for _, row in countries.iterrows():
                results.append(
                    {
                        "country_code": row.get("id", ""),
                        "name": row.get("name", ""),
                        "region": row.get("region", ""),
                        "income_level": row.get("incomeLevel", ""),
                    }
                )

            logger.info(f"Found {len(results)} countries")
            return results

        except Exception as e:
            logger.error(
                f"Error fetching World Bank countries: {str(e)}", exc_info=True
            )
            raise WorldBankFetcherError(
                f"Error fetching World Bank countries: {str(e)}"
            ) from e

    def format_indicator_for_rag(self, indicator_data: Dict[str, Any]) -> str:
        """
        Format World Bank indicator data for RAG ingestion.

        Args:
            indicator_data: Indicator data dictionary from fetch_indicator()

        Returns:
            Formatted text string for RAG
        """
        indicator_code = indicator_data.get("indicator_code", "Unknown")
        metadata = indicator_data.get("metadata", {})
        data = indicator_data.get("data")

        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            return f"World Bank Indicator: {indicator_code}\nNo data available"

        # Build formatted text
        text_parts = [
            f"World Bank Economic Data Indicator: {indicator_code}",
            f"Name: {metadata.get('name', 'N/A')}",
            f"Source: {metadata.get('source', 'N/A')}",
            f"Topic: {metadata.get('topic', 'N/A')}",
            f"Unit: {metadata.get('unit', 'N/A')}",
        ]

        if metadata.get("note"):
            text_parts.append(f"Note: {metadata.get('note', '')[:500]}")

        # Add data summary
        if isinstance(data, pd.DataFrame):
            text_parts.append("\nData Coverage:")
            text_parts.append(f"  Countries: {len(data.columns)}")
            text_parts.append(f"  Years: {len(data.index)}")
            text_parts.append(f"  Total Data Points: {len(data) * len(data.columns)}")

            # Add recent data points (last 5 years, top 10 countries by latest value)
            if not data.empty:
                text_parts.append("\nRecent Data (Latest Year, Top Countries):")
                latest_year = data.index.max()
                latest_data = (
                    data.loc[latest_year].dropna().sort_values(ascending=False)
                )
                for country, value in latest_data.head(10).items():
                    text_parts.append(f"  {country}: {value}")

                # Add summary statistics
                text_parts.append("\nSummary Statistics (All Countries, All Years):")
                text_parts.append(f"  Mean: {data.values.flatten().mean():.2f}")
                text_parts.append(f"  Min: {data.values.flatten().min():.2f}")
                text_parts.append(f"  Max: {data.values.flatten().max():.2f}")
        else:
            # Handle Series or other data types
            text_parts.append(
                f"\nData Points: {len(data) if hasattr(data, '__len__') else 'N/A'}"
            )

        return "\n".join(text_parts)

    def get_indicator_metadata(self, indicator_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from World Bank indicator data.

        Args:
            indicator_data: Indicator data dictionary from fetch_indicator()

        Returns:
            Metadata dictionary for ChromaDB storage
        """
        indicator_code = indicator_data.get("indicator_code", "")
        metadata = indicator_data.get("metadata", {})
        data = indicator_data.get("data")

        # Calculate data points
        if isinstance(data, pd.DataFrame):
            data_points = len(data) * len(data.columns) if not data.empty else 0
        elif data is not None and hasattr(data, "__len__"):
            data_points = len(data)
        else:
            data_points = 0

        return {
            "source": "world_bank",
            "indicator_code": indicator_code,
            "name": metadata.get("name", ""),
            "source_name": metadata.get("source", ""),
            "topic": metadata.get("topic", ""),
            "unit": metadata.get("unit", ""),
            "country_codes": indicator_data.get("country_codes"),
            "start_year": indicator_data.get("start_year"),
            "end_year": indicator_data.get("end_year"),
            "data_points": data_points,
        }
