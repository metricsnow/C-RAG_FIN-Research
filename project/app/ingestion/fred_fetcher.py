"""
FRED API fetcher.

Fetches economic time series data from FRED (Federal Reserve Economic Data) API
to provide comprehensive macroeconomic indicators for financial analysis.
"""

import time
from typing import Any, Dict, List, Optional

from fredapi import Fred

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FREDFetcherError(Exception):
    """Custom exception for FRED fetcher errors."""

    pass


class FREDFetcher:
    """
    FRED API fetcher.

    Fetches economic time series data from FRED API with proper rate limiting
    and error handling. Supports 840,000+ time series including interest rates,
    exchange rates, inflation indicators, employment data, GDP, and monetary indicators.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit_delay: Optional[float] = None,
    ):
        """
        Initialize FRED fetcher.

        Args:
            api_key: FRED API key (default: from config)
            rate_limit_delay: Delay between requests in seconds (default: from config)
        """
        self.api_key = api_key if api_key is not None else config.fred_api_key
        self.rate_limit_delay = (
            rate_limit_delay
            if rate_limit_delay is not None
            else config.fred_rate_limit_seconds
        )

        if not self.api_key:
            logger.warning(
                "FRED API key not configured. "
                "Set FRED_API_KEY in .env file or disable FRED integration."
            )
            self.fred = None
        else:
            try:
                self.fred = Fred(api_key=self.api_key)
                logger.info("FRED API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize FRED API client: {str(e)}")
                self.fred = None

    def _check_api_available(self) -> None:
        """
        Check if FRED API is available.

        Raises:
            FREDFetcherError: If API key is missing or client not initialized
        """
        if not self.api_key:
            raise FREDFetcherError(
                "FRED API key not configured. "
                "Set FRED_API_KEY in .env file or disable FRED integration."
            )
        if self.fred is None:
            raise FREDFetcherError("FRED API client not initialized")

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting delay between requests."""
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)

    def fetch_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: Optional[str] = None,
        aggregation_method: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch a time series by series ID.

        Args:
            series_id: FRED series ID (e.g., 'GDP', 'UNRATE', 'FEDFUNDS')
            start_date: Start date (YYYY-MM-DD format, optional)
            end_date: End date (YYYY-MM-DD format, optional)
            frequency: Data frequency ('d'=daily, 'w'=weekly, 'm'=monthly,
                'q'=quarterly, 'a'=annual, optional)
            aggregation_method: Aggregation method ('avg', 'sum', 'eop', optional)

        Returns:
            Dictionary containing series data and metadata

        Raises:
            FREDFetcherError: If fetching fails
        """
        self._check_api_available()

        logger.info(f"Fetching FRED series: {series_id}")
        try:
            self._apply_rate_limit()

            # Fetch series data
            data = self.fred.get_series(
                series_id,
                start=start_date,
                end=end_date,
                frequency=frequency,
                aggregation_method=aggregation_method,
            )

            if data is None or data.empty:
                logger.warning(f"No data returned for series {series_id}")
                return {
                    "series_id": series_id,
                    "data": None,
                    "metadata": {},
                    "error": "No data available",
                }

            # Fetch series info for metadata
            self._apply_rate_limit()
            try:
                series_info = self.fred.get_series_info(series_id)
                metadata = {
                    "title": series_info.get("title", ""),
                    "units": series_info.get("units", ""),
                    "frequency": series_info.get("frequency", ""),
                    "seasonal_adjustment": series_info.get("seasonal_adjustment", ""),
                    "last_updated": series_info.get("last_updated", ""),
                    "observation_start": series_info.get("observation_start", ""),
                    "observation_end": series_info.get("observation_end", ""),
                    "notes": series_info.get("notes", ""),
                }
            except Exception as e:
                logger.warning(f"Failed to fetch series info for {series_id}: {str(e)}")
                metadata = {}

            logger.info(
                f"Successfully fetched {len(data)} observations for series {series_id}"
            )

            return {
                "series_id": series_id,
                "data": data,
                "metadata": metadata,
                "start_date": start_date,
                "end_date": end_date,
            }

        except Exception as e:
            logger.error(
                f"Error fetching FRED series {series_id}: {str(e)}", exc_info=True
            )
            raise FREDFetcherError(
                f"Error fetching FRED series {series_id}: {str(e)}"
            ) from e

    def fetch_multiple_series(
        self,
        series_ids: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch multiple time series.

        Args:
            series_ids: List of FRED series IDs
            start_date: Start date (YYYY-MM-DD format, optional)
            end_date: End date (YYYY-MM-DD format, optional)

        Returns:
            Dictionary mapping series_id to series data

        Raises:
            FREDFetcherError: If fetching fails
        """
        self._check_api_available()

        logger.info(f"Fetching {len(series_ids)} FRED series")
        results = {}

        for series_id in series_ids:
            try:
                result = self.fetch_series(
                    series_id, start_date=start_date, end_date=end_date
                )
                results[series_id] = result
            except FREDFetcherError as e:
                logger.warning(f"Failed to fetch series {series_id}: {str(e)}")
                results[series_id] = {
                    "series_id": series_id,
                    "data": None,
                    "metadata": {},
                    "error": str(e),
                }

        successful_count = len(
            [r for r in results.values() if r.get("data") is not None]
        )
        logger.info(
            f"Successfully fetched {successful_count} out of {len(series_ids)} series"
        )
        return results

    def search_series(self, search_text: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for FRED series by text.

        Args:
            search_text: Search query text
            limit: Maximum number of results to return (default: 20)

        Returns:
            List of series information dictionaries

        Raises:
            FREDFetcherError: If search fails
        """
        self._check_api_available()

        logger.info(f"Searching FRED series: '{search_text}'")
        try:
            self._apply_rate_limit()

            # Search for series
            search_results = self.fred.search(search_text)

            if search_results is None or search_results.empty:
                logger.info(f"No series found for search: '{search_text}'")
                return []

            # Convert to list of dictionaries
            results = []
            for _, row in search_results.head(limit).iterrows():
                results.append(
                    {
                        "series_id": row.get("id", ""),
                        "title": row.get("title", ""),
                        "units": row.get("units", ""),
                        "frequency": row.get("frequency", ""),
                        "seasonal_adjustment": row.get("seasonal_adjustment", ""),
                    }
                )

            logger.info(f"Found {len(results)} series matching '{search_text}'")
            return results

        except Exception as e:
            logger.error(f"Error searching FRED series: {str(e)}", exc_info=True)
            raise FREDFetcherError(f"Error searching FRED series: {str(e)}") from e

    def format_series_for_rag(self, series_data: Dict[str, Any]) -> str:
        """
        Format FRED time series data for RAG ingestion.

        Args:
            series_data: Series data dictionary from fetch_series()

        Returns:
            Formatted text string for RAG
        """
        series_id = series_data.get("series_id", "Unknown")
        metadata = series_data.get("metadata", {})
        data = series_data.get("data")

        if data is None or data.empty:
            return f"FRED Series: {series_id}\nNo data available"

        # Build formatted text
        text_parts = [
            f"FRED Economic Data Series: {series_id}",
            f"Title: {metadata.get('title', 'N/A')}",
            f"Units: {metadata.get('units', 'N/A')}",
            f"Frequency: {metadata.get('frequency', 'N/A')}",
            f"Seasonal Adjustment: {metadata.get('seasonal_adjustment', 'N/A')}",
            (
                f"Observation Period: {metadata.get('observation_start', 'N/A')} "
                f"to {metadata.get('observation_end', 'N/A')}"
            ),
            f"Last Updated: {metadata.get('last_updated', 'N/A')}",
        ]

        if metadata.get("notes"):
            text_parts.append(f"Notes: {metadata.get('notes', '')[:500]}")

        # Add recent data points (last 10 observations)
        text_parts.append("\nRecent Data Points:")
        recent_data = data.tail(10)
        for date, value in recent_data.items():
            text_parts.append(f"  {date.strftime('%Y-%m-%d')}: {value}")

        # Add summary statistics
        if len(data) > 0:
            text_parts.append("\nSummary Statistics:")
            text_parts.append(f"  Total Observations: {len(data)}")
            text_parts.append(f"  Latest Value: {data.iloc[-1]}")
            text_parts.append(f"  Mean: {data.mean():.2f}")
            text_parts.append(f"  Min: {data.min():.2f}")
            text_parts.append(f"  Max: {data.max():.2f}")

        return "\n".join(text_parts)

    def get_series_metadata(self, series_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from FRED series data.

        Args:
            series_data: Series data dictionary from fetch_series()

        Returns:
            Metadata dictionary for ChromaDB storage
        """
        series_id = series_data.get("series_id", "")
        metadata = series_data.get("metadata", {})
        data = series_data.get("data")

        return {
            "source": "fred",
            "series_id": series_id,
            "title": metadata.get("title", ""),
            "units": metadata.get("units", ""),
            "frequency": metadata.get("frequency", ""),
            "seasonal_adjustment": metadata.get("seasonal_adjustment", ""),
            "observation_start": metadata.get("observation_start", ""),
            "observation_end": metadata.get("observation_end", ""),
            "last_updated": metadata.get("last_updated", ""),
            "data_points": len(data) if data is not None and not data.empty else 0,
            "start_date": series_data.get("start_date", ""),
            "end_date": series_data.get("end_date", ""),
        }
