"""
Economic calendar fetcher.

Fetches economic calendar data from Trading Economics API or alternative sources
to provide macroeconomic indicators and events for financial analysis.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EconomicCalendarFetcherError(Exception):
    """Custom exception for economic calendar fetcher errors."""

    pass


class EconomicCalendarFetcher:
    """
    Economic calendar fetcher.

    Fetches economic indicators and events from Trading Economics API
    or alternative sources with proper rate limiting and error handling.
    """

    # Trading Economics API endpoint
    TRADING_ECONOMICS_BASE_URL = "https://api.tradingeconomics.com/calendar"

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit_delay: Optional[float] = None,
        use_trading_economics: Optional[bool] = None,
    ):
        """
        Initialize economic calendar fetcher.

        Args:
            api_key: Trading Economics API key (default: from config)
            rate_limit_delay: Delay between requests in seconds (default: from config)
            use_trading_economics: Use Trading Economics API (default: from config)
        """
        self.api_key = (
            api_key if api_key is not None else config.trading_economics_api_key
        )
        self.rate_limit_delay = (
            rate_limit_delay
            if rate_limit_delay is not None
            else config.economic_calendar_rate_limit_seconds
        )
        self.use_trading_economics = (
            use_trading_economics
            if use_trading_economics is not None
            else config.economic_calendar_use_trading_economics
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

    def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """
        Make HTTP request with rate limiting and error handling.

        Args:
            url: URL to request
            params: Query parameters
            headers: Optional headers to add to request

        Returns:
            Response object

        Raises:
            EconomicCalendarFetcherError: If request fails
        """
        try:
            time.sleep(self.rate_limit_delay)
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)
            response = self.session.get(
                url, params=params, headers=request_headers, timeout=30
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            raise EconomicCalendarFetcherError(f"Request failed: {str(e)}") from e

    def _fetch_trading_economics_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
        importance: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch economic calendar from Trading Economics API.

        Args:
            start_date: Start date (YYYY-MM-DD format, optional)
            end_date: End date (YYYY-MM-DD format, optional)
            country: Country code (e.g., 'united states', optional)
            importance: Importance filter ('High', 'Medium', 'Low', optional)

        Returns:
            List of economic calendar events

        Raises:
            EconomicCalendarFetcherError: If API key is missing or request fails
        """
        if not self.api_key:
            logger.warning(
                "Trading Economics API key not configured. "
                "Set TRADING_ECONOMICS_API_KEY in .env file or "
                "disable Trading Economics."
            )
            return []

        try:
            params: Dict[str, Any] = {"c": self.api_key}
            if start_date:
                params["d1"] = start_date
            if end_date:
                params["d2"] = end_date
            if country:
                params["countries"] = country
            if importance:
                params["importance"] = importance

            response = self._make_request(
                self.TRADING_ECONOMICS_BASE_URL, params=params
            )
            data = response.json()

            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "error" in data:
                logger.error(f"Trading Economics API error: {data['error']}")
                return []
            else:
                logger.warning("Unexpected response format from Trading Economics API")
                return []

        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            raise EconomicCalendarFetcherError(
                f"Failed to parse API response: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Error fetching from Trading Economics API: {str(e)}")
            raise EconomicCalendarFetcherError(
                f"Error fetching calendar data: {str(e)}"
            ) from e

    def fetch_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
        importance: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch economic calendar events.

        Args:
            start_date: Start date (YYYY-MM-DD format, optional)
            end_date: End date (YYYY-MM-DD format, optional)
            country: Country code (e.g., 'united states', optional)
            importance: Importance filter ('High', 'Medium', 'Low', optional)

        Returns:
            List of economic calendar events with metadata

        Raises:
            EconomicCalendarFetcherError: If fetching fails
        """
        if not start_date:
            # Default to today
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            # Default to 30 days from start
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = start_dt + timedelta(days=30)
            end_date = end_dt.strftime("%Y-%m-%d")

        logger.info(
            f"Fetching economic calendar from {start_date} to {end_date}"
            + (f" for {country}" if country else "")
        )

        events = []

        # Try Trading Economics API if enabled
        if self.use_trading_economics:
            try:
                events = self._fetch_trading_economics_calendar(
                    start_date=start_date,
                    end_date=end_date,
                    country=country,
                    importance=importance,
                )
                if events:
                    logger.info(f"Fetched {len(events)} events from Trading Economics")
                    return events
            except EconomicCalendarFetcherError as e:
                logger.warning(
                    f"Trading Economics API failed: {str(e)}. "
                    "Consider using alternative sources or checking API key."
                )

        if not events:
            logger.warning("No economic calendar events fetched from any source")
            return []

        return events

    def fetch_calendar_by_date_range(
        self,
        start_date: str,
        end_date: str,
        country: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch economic calendar events for a date range.

        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            country: Country code (optional)

        Returns:
            List of economic calendar events
        """
        return self.fetch_calendar(
            start_date=start_date, end_date=end_date, country=country
        )

    def format_event_for_rag(self, event: Dict[str, Any]) -> str:
        """
        Format economic calendar event for RAG ingestion.

        Args:
            event: Economic calendar event dictionary

        Returns:
            Formatted text string for RAG
        """
        # Extract key fields from Trading Economics format
        event_name = event.get("Event", event.get("event", "Unknown Event"))
        country = event.get("Country", event.get("country", "Unknown"))
        date = event.get("Date", event.get("date", ""))
        time = event.get("Time", event.get("time", ""))
        actual = event.get("Actual", event.get("actual", ""))
        forecast = event.get("Forecast", event.get("forecast", ""))
        previous = event.get("Previous", event.get("previous", ""))
        importance = event.get("Importance", event.get("importance", ""))
        category = event.get("Category", event.get("category", ""))

        # Build formatted text
        text_parts = [
            f"Economic Event: {event_name}",
            f"Country: {country}",
            f"Date: {date}",
        ]
        if time:
            text_parts.append(f"Time: {time}")
        if category:
            text_parts.append(f"Category: {category}")
        if importance:
            text_parts.append(f"Importance: {importance}")
        if actual:
            text_parts.append(f"Actual: {actual}")
        if forecast:
            text_parts.append(f"Forecast: {forecast}")
        if previous:
            text_parts.append(f"Previous: {previous}")

        return "\n".join(text_parts)

    def get_event_metadata(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from economic calendar event.

        Args:
            event: Economic calendar event dictionary

        Returns:
            Metadata dictionary for ChromaDB storage
        """
        return {
            "source": "economic_calendar",
            "event_name": event.get("Event", event.get("event", "")),
            "country": event.get("Country", event.get("country", "")),
            "date": event.get("Date", event.get("date", "")),
            "time": event.get("Time", event.get("time", "")),
            "category": event.get("Category", event.get("category", "")),
            "importance": event.get("Importance", event.get("importance", "")),
            "actual": event.get("Actual", event.get("actual", "")),
            "forecast": event.get("Forecast", event.get("forecast", "")),
            "previous": event.get("Previous", event.get("previous", "")),
            "api_source": (
                "trading_economics" if self.use_trading_economics else "unknown"
            ),
        }
