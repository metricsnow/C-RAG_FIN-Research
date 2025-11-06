"""
IMF Data Portal API fetcher.

Fetches global economic data from IMF Data Portal API including World Economic Outlook,
International Financial Statistics, GDP, inflation, unemployment, and trade balance
data for 188+ countries.
"""

import time
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class IMFFetcherError(Exception):
    """Custom exception for IMF fetcher errors."""

    pass


class IMFFetcher:
    """
    IMF Data Portal API fetcher.

    Fetches global economic data from IMF Data Portal API with proper rate limiting
    and error handling. Supports World Economic Outlook, International Financial
    Statistics, and other IMF databases.
    """

    # IMF Data Portal API base URL
    IMF_BASE_URL = "https://www.imf.org/external/datamapper/api/v1"

    def __init__(
        self,
        rate_limit_delay: Optional[float] = None,
    ):
        """
        Initialize IMF fetcher.

        Args:
            rate_limit_delay: Delay between requests in seconds (default: from config)
        """
        self.rate_limit_delay = (
            rate_limit_delay
            if rate_limit_delay is not None
            else config.imf_rate_limit_seconds
        )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                ),
                "Accept": "application/json",
            }
        )

        logger.info("IMF API client initialized")

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting delay between requests."""
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to IMF API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            IMFFetcherError: If request fails
        """
        url = f"{self.IMF_BASE_URL}/{endpoint}"
        try:
            self._apply_rate_limit()
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"IMF API request failed: {str(e)}")
            raise IMFFetcherError(f"IMF API request failed: {str(e)}") from e

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
            indicator_code: IMF indicator code (e.g., 'NGDP_RPCH' for GDP growth)
            country_codes: List of country ISO codes (e.g., ['US', 'CN'], optional)
            start_year: Start year (optional)
            end_year: End year (optional)

        Returns:
            Dictionary containing indicator data and metadata

        Raises:
            IMFFetcherError: If fetching fails
        """
        logger.info(f"Fetching IMF indicator: {indicator_code}")
        try:
            # IMF API endpoint structure: /indicators/{indicator_code}
            endpoint = f"indicators/{indicator_code}"
            params = {}

            if country_codes:
                params["countries"] = ",".join(country_codes)
            if start_year:
                params["startPeriod"] = str(start_year)
            if end_year:
                params["endPeriod"] = str(end_year)

            response_data = self._make_request(endpoint, params=params)

            if not response_data or "values" not in response_data:
                logger.warning(f"No data returned for indicator {indicator_code}")
                return {
                    "indicator_code": indicator_code,
                    "data": None,
                    "metadata": {},
                    "error": "No data available",
                }

            # Parse response data
            values = response_data.get("values", {})
            metadata = response_data.get("metadata", {})

            # Convert to DataFrame for easier handling
            data_list = []
            for country, country_data in values.items():
                if isinstance(country_data, dict):
                    for year, value in country_data.items():
                        data_list.append(
                            {
                                "country": country,
                                "year": int(year) if year.isdigit() else year,
                                "value": value,
                            }
                        )

            if not data_list:
                logger.warning(f"No data points found for indicator {indicator_code}")
                return {
                    "indicator_code": indicator_code,
                    "data": None,
                    "metadata": {},
                    "error": "No data available",
                }

            # Create DataFrame
            df = pd.DataFrame(data_list)
            df = df.pivot_table(
                index="year", columns="country", values="value", aggfunc="first"
            )

            logger.info(
                f"Successfully fetched {len(df)} years of data "
                f"for indicator {indicator_code}"
            )

            return {
                "indicator_code": indicator_code,
                "data": df,
                "metadata": metadata,
                "country_codes": country_codes,
                "start_year": start_year,
                "end_year": end_year,
            }

        except Exception as e:
            logger.error(
                f"Error fetching IMF indicator {indicator_code}: {str(e)}",
                exc_info=True,
            )
            raise IMFFetcherError(
                f"Error fetching IMF indicator {indicator_code}: {str(e)}"
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
            indicator_codes: List of IMF indicator codes
            country_codes: List of country ISO codes (optional)
            start_year: Start year (optional)
            end_year: End year (optional)

        Returns:
            Dictionary mapping indicator_code to indicator data

        Raises:
            IMFFetcherError: If fetching fails
        """
        logger.info(f"Fetching {len(indicator_codes)} IMF indicators")
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
            except IMFFetcherError as e:
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

    def get_available_indicators(self) -> List[Dict[str, Any]]:
        """
        Get list of available indicators from IMF Data Portal.

        Returns:
            List of indicator information dictionaries

        Raises:
            IMFFetcherError: If fetching fails
        """
        logger.info("Fetching IMF available indicators")
        try:
            response_data = self._make_request("indicators")

            if not response_data:
                logger.warning("No indicators data returned")
                return []

            # Parse indicators
            results = []
            for indicator_code, indicator_info in response_data.items():
                if isinstance(indicator_info, dict):
                    results.append(
                        {
                            "indicator_code": indicator_code,
                            "name": indicator_info.get("name", ""),
                            "description": indicator_info.get("description", ""),
                            "unit": indicator_info.get("unit", ""),
                        }
                    )

            logger.info(f"Found {len(results)} available indicators")
            return results

        except Exception as e:
            logger.error(f"Error fetching IMF indicators: {str(e)}", exc_info=True)
            raise IMFFetcherError(f"Error fetching IMF indicators: {str(e)}") from e

    def get_countries(self) -> List[Dict[str, Any]]:
        """
        Get list of countries available in IMF data.

        Returns:
            List of country information dictionaries

        Raises:
            IMFFetcherError: If fetching fails
        """
        logger.info("Fetching IMF countries list")
        try:
            response_data = self._make_request("countries")

            if not response_data:
                logger.warning("No countries data returned")
                return []

            # Parse countries
            results = []
            for country_code, country_info in response_data.items():
                if isinstance(country_info, dict):
                    results.append(
                        {
                            "country_code": country_code,
                            "name": country_info.get("name", ""),
                            "region": country_info.get("region", ""),
                        }
                    )

            logger.info(f"Found {len(results)} countries")
            return results

        except Exception as e:
            logger.error(f"Error fetching IMF countries: {str(e)}", exc_info=True)
            raise IMFFetcherError(f"Error fetching IMF countries: {str(e)}") from e

    def format_indicator_for_rag(self, indicator_data: Dict[str, Any]) -> str:
        """
        Format IMF indicator data for RAG ingestion.

        Args:
            indicator_data: Indicator data dictionary from fetch_indicator()

        Returns:
            Formatted text string for RAG
        """
        indicator_code = indicator_data.get("indicator_code", "Unknown")
        metadata = indicator_data.get("metadata", {})
        data = indicator_data.get("data")

        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            return f"IMF Indicator: {indicator_code}\nNo data available"

        # Build formatted text
        text_parts = [
            f"IMF Economic Data Indicator: {indicator_code}",
            f"Name: {metadata.get('name', 'N/A')}",
            f"Description: {metadata.get('description', 'N/A')}",
            f"Unit: {metadata.get('unit', 'N/A')}",
        ]

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
            # Handle other data types
            text_parts.append(
                f"\nData Points: {len(data) if hasattr(data, '__len__') else 'N/A'}"
            )

        return "\n".join(text_parts)

    def get_indicator_metadata(self, indicator_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from IMF indicator data.

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
            "source": "imf",
            "indicator_code": indicator_code,
            "name": metadata.get("name", ""),
            "description": metadata.get("description", ""),
            "unit": metadata.get("unit", ""),
            "country_codes": indicator_data.get("country_codes"),
            "start_year": indicator_data.get("start_year"),
            "end_year": indicator_data.get("end_year"),
            "data_points": data_points,
        }
