"""
Unit tests for economic calendar fetcher module.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.ingestion.economic_calendar_fetcher import (
    EconomicCalendarFetcher,
    EconomicCalendarFetcherError,
)


class TestEconomicCalendarFetcher:
    """Test cases for EconomicCalendarFetcher."""

    def test_init(self):
        """Test fetcher initialization."""
        fetcher = EconomicCalendarFetcher(use_trading_economics=False)
        assert fetcher.use_trading_economics is False
        assert fetcher.rate_limit_delay == 1.0

    def test_init_with_custom_rate_limit(self):
        """Test fetcher initialization with custom rate limit."""
        fetcher = EconomicCalendarFetcher(
            rate_limit_delay=2.0, use_trading_economics=True
        )
        assert fetcher.rate_limit_delay == 2.0
        assert fetcher.use_trading_economics is True

    def test_init_with_api_key(self):
        """Test fetcher initialization with API key."""
        fetcher = EconomicCalendarFetcher(api_key="test-key-123")
        assert fetcher.api_key == "test-key-123"
        assert fetcher.use_trading_economics is True  # Default from config

    @patch("app.ingestion.economic_calendar_fetcher.requests.Session")
    def test_fetch_trading_economics_success(self, mock_session):
        """Test successful Trading Economics fetching."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "Event": "GDP Growth Rate",
                "Country": "United States",
                "Date": "2025-01-27T10:00:00",
                "Time": "10:00",
                "Actual": "2.5%",
                "Forecast": "2.3%",
                "Previous": "2.1%",
                "Importance": "High",
                "Category": "GDP",
            }
        ]
        mock_response.raise_for_status = Mock()

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session_instance.headers = {}
        mock_session.return_value = mock_session_instance

        fetcher = EconomicCalendarFetcher(
            use_trading_economics=True, api_key="test-key"
        )
        fetcher.session = mock_session_instance

        result = fetcher._fetch_trading_economics_calendar(
            start_date="2025-01-27", end_date="2025-01-28"
        )

        assert result is not None
        assert len(result) == 1
        assert result[0]["Event"] == "GDP Growth Rate"
        assert result[0]["Country"] == "United States"

    @patch("app.ingestion.economic_calendar_fetcher.requests.Session")
    def test_fetch_trading_economics_no_api_key(self, mock_session):
        """Test Trading Economics fetching without API key."""
        fetcher = EconomicCalendarFetcher(use_trading_economics=True, api_key="")

        result = fetcher._fetch_trading_economics_calendar()

        assert result == []

    @patch("app.ingestion.economic_calendar_fetcher.requests.Session")
    def test_fetch_trading_economics_empty_response(self, mock_session):
        """Test Trading Economics fetching with empty response."""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = Mock()

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session_instance.headers = {}
        mock_session.return_value = mock_session_instance

        fetcher = EconomicCalendarFetcher(
            use_trading_economics=True, api_key="test-key"
        )
        fetcher.session = mock_session_instance

        result = fetcher._fetch_trading_economics_calendar()

        assert result == []

    @patch("app.ingestion.economic_calendar_fetcher.requests.Session")
    def test_fetch_trading_economics_error_response(self, mock_session):
        """Test Trading Economics fetching with error response."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid API key"}
        mock_response.raise_for_status = Mock()

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session_instance.headers = {}
        mock_session.return_value = mock_session_instance

        fetcher = EconomicCalendarFetcher(
            use_trading_economics=True, api_key="test-key"
        )
        fetcher.session = mock_session_instance

        result = fetcher._fetch_trading_economics_calendar()

        assert result == []

    @patch("app.ingestion.economic_calendar_fetcher.requests.Session")
    def test_fetch_calendar_with_defaults(self, mock_session):
        """Test fetch_calendar with default date range."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "Event": "GDP Growth Rate",
                "Country": "United States",
                "Date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "Time": "10:00",
                "Actual": "2.5%",
                "Forecast": "2.3%",
                "Previous": "2.1%",
                "Importance": "High",
                "Category": "GDP",
            }
        ]
        mock_response.raise_for_status = Mock()

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session_instance.headers = {}
        mock_session.return_value = mock_session_instance

        fetcher = EconomicCalendarFetcher(
            use_trading_economics=True, api_key="test-key"
        )
        fetcher.session = mock_session_instance

        result = fetcher.fetch_calendar()

        assert result is not None
        assert len(result) == 1

    @patch("app.ingestion.economic_calendar_fetcher.requests.Session")
    def test_fetch_calendar_with_country(self, mock_session):
        """Test fetch_calendar with country filter."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "Event": "GDP Growth Rate",
                "Country": "United States",
                "Date": "2025-01-27T10:00:00",
                "Time": "10:00",
                "Actual": "2.5%",
                "Forecast": "2.3%",
                "Previous": "2.1%",
                "Importance": "High",
                "Category": "GDP",
            }
        ]
        mock_response.raise_for_status = Mock()

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session_instance.headers = {}
        mock_session.return_value = mock_session_instance

        fetcher = EconomicCalendarFetcher(
            use_trading_economics=True, api_key="test-key"
        )
        fetcher.session = mock_session_instance

        result = fetcher.fetch_calendar(
            start_date="2025-01-27",
            end_date="2025-01-28",
            country="united states",
        )

        assert result is not None
        assert len(result) == 1

    @patch("app.ingestion.economic_calendar_fetcher.requests.Session")
    def test_fetch_calendar_with_importance(self, mock_session):
        """Test fetch_calendar with importance filter."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "Event": "GDP Growth Rate",
                "Country": "United States",
                "Date": "2025-01-27T10:00:00",
                "Time": "10:00",
                "Actual": "2.5%",
                "Forecast": "2.3%",
                "Previous": "2.1%",
                "Importance": "High",
                "Category": "GDP",
            }
        ]
        mock_response.raise_for_status = Mock()

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session_instance.headers = {}
        mock_session.return_value = mock_session_instance

        fetcher = EconomicCalendarFetcher(
            use_trading_economics=True, api_key="test-key"
        )
        fetcher.session = mock_session_instance

        result = fetcher.fetch_calendar(
            start_date="2025-01-27",
            end_date="2025-01-28",
            importance="High",
        )

        assert result is not None
        assert len(result) == 1

    def test_format_event_for_rag(self):
        """Test formatting event for RAG."""
        fetcher = EconomicCalendarFetcher()
        event = {
            "Event": "GDP Growth Rate",
            "Country": "United States",
            "Date": "2025-01-27T10:00:00",
            "Time": "10:00",
            "Actual": "2.5%",
            "Forecast": "2.3%",
            "Previous": "2.1%",
            "Importance": "High",
            "Category": "GDP",
        }

        formatted = fetcher.format_event_for_rag(event)

        assert "Economic Event: GDP Growth Rate" in formatted
        assert "Country: United States" in formatted
        assert "Date: 2025-01-27T10:00:00" in formatted
        assert "Actual: 2.5%" in formatted
        assert "Forecast: 2.3%" in formatted
        assert "Previous: 2.1%" in formatted

    def test_get_event_metadata(self):
        """Test extracting event metadata."""
        fetcher = EconomicCalendarFetcher()
        event = {
            "Event": "GDP Growth Rate",
            "Country": "United States",
            "Date": "2025-01-27T10:00:00",
            "Time": "10:00",
            "Actual": "2.5%",
            "Forecast": "2.3%",
            "Previous": "2.1%",
            "Importance": "High",
            "Category": "GDP",
        }

        metadata = fetcher.get_event_metadata(event)

        assert metadata["source"] == "economic_calendar"
        assert metadata["event_name"] == "GDP Growth Rate"
        assert metadata["country"] == "United States"
        assert metadata["date"] == "2025-01-27T10:00:00"
        assert metadata["importance"] == "High"
        assert metadata["category"] == "GDP"

    @patch("app.ingestion.economic_calendar_fetcher.requests.Session")
    def test_fetch_calendar_by_date_range(self, mock_session):
        """Test fetch_calendar_by_date_range method."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "Event": "GDP Growth Rate",
                "Country": "United States",
                "Date": "2025-01-27T10:00:00",
                "Time": "10:00",
                "Actual": "2.5%",
                "Forecast": "2.3%",
                "Previous": "2.1%",
                "Importance": "High",
                "Category": "GDP",
            }
        ]
        mock_response.raise_for_status = Mock()

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session_instance.headers = {}
        mock_session.return_value = mock_session_instance

        fetcher = EconomicCalendarFetcher(
            use_trading_economics=True, api_key="test-key"
        )
        fetcher.session = mock_session_instance

        result = fetcher.fetch_calendar_by_date_range(
            start_date="2025-01-27", end_date="2025-01-28"
        )

        assert result is not None
        assert len(result) == 1

    @patch("app.ingestion.economic_calendar_fetcher.requests.Session")
    def test_request_error_handling(self, mock_session):
        """Test error handling for request failures."""
        mock_session_instance = Mock()
        mock_session_instance.get.side_effect = Exception("Network error")
        mock_session_instance.headers = {}
        mock_session.return_value = mock_session_instance

        fetcher = EconomicCalendarFetcher(
            use_trading_economics=True, api_key="test-key"
        )
        fetcher.session = mock_session_instance

        with pytest.raises(EconomicCalendarFetcherError):
            fetcher._fetch_trading_economics_calendar()

    @patch("app.ingestion.economic_calendar_fetcher.requests.Session")
    def test_json_decode_error(self, mock_session):
        """Test handling of JSON decode errors."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session_instance.headers = {}
        mock_session.return_value = mock_session_instance

        fetcher = EconomicCalendarFetcher(
            use_trading_economics=True, api_key="test-key"
        )
        fetcher.session = mock_session_instance

        with pytest.raises(EconomicCalendarFetcherError):
            fetcher._fetch_trading_economics_calendar()
