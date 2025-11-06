"""
Unit tests for FRED fetcher module.
"""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from app.ingestion.fred_fetcher import FREDFetcher, FREDFetcherError


class TestFREDFetcher:
    """Test cases for FREDFetcher."""

    def test_init(self):
        """Test fetcher initialization."""
        fetcher = FREDFetcher(api_key="test-key-123")
        assert fetcher.api_key == "test-key-123"
        assert fetcher.rate_limit_delay == 0.2

    def test_init_without_api_key(self):
        """Test fetcher initialization without API key."""
        fetcher = FREDFetcher(api_key="")
        assert fetcher.api_key == ""
        assert fetcher.fred is None

    def test_init_with_custom_rate_limit(self):
        """Test fetcher initialization with custom rate limit."""
        fetcher = FREDFetcher(api_key="test-key", rate_limit_delay=1.0)
        assert fetcher.rate_limit_delay == 1.0

    @patch("app.ingestion.fred_fetcher.Fred")
    def test_fetch_series_success(self, mock_fred_class):
        """Test successful series fetching."""
        # Mock FRED client
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred

        # Mock series data
        dates = pd.date_range("2020-01-01", "2024-12-31", freq="Q")
        values = [100.0, 102.0, 104.0, 106.0, 108.0] * 4
        mock_series_data = pd.Series(values, index=dates[: len(values)])

        # Mock series info
        mock_series_info = {
            "title": "Gross Domestic Product",
            "units": "Billions of Dollars",
            "frequency": "Quarterly",
            "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
            "last_updated": "2024-12-31 12:00:00",
            "observation_start": "2020-01-01",
            "observation_end": "2024-12-31",
            "notes": "GDP data",
        }

        mock_fred.get_series.return_value = mock_series_data
        mock_fred.get_series_info.return_value = mock_series_info

        fetcher = FREDFetcher(api_key="test-key")
        fetcher.fred = mock_fred

        result = fetcher.fetch_series(
            "GDP", start_date="2020-01-01", end_date="2024-12-31"
        )

        assert result is not None
        assert result["series_id"] == "GDP"
        assert result["data"] is not None
        assert len(result["data"]) > 0
        assert result["metadata"]["title"] == "Gross Domestic Product"
        assert result["metadata"]["units"] == "Billions of Dollars"

    @patch("app.ingestion.fred_fetcher.Fred")
    def test_fetch_series_no_data(self, mock_fred_class):
        """Test series fetching with no data."""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred
        mock_fred.get_series.return_value = pd.Series(dtype=float)

        fetcher = FREDFetcher(api_key="test-key")
        fetcher.fred = mock_fred

        result = fetcher.fetch_series("INVALID")

        assert result is not None
        assert result["series_id"] == "INVALID"
        assert result["data"] is None
        assert "error" in result

    @patch("app.ingestion.fred_fetcher.Fred")
    def test_fetch_series_no_api_key(self, mock_fred_class):
        """Test series fetching without API key."""
        fetcher = FREDFetcher(api_key="")

        with pytest.raises(FREDFetcherError, match="FRED API key not configured"):
            fetcher.fetch_series("GDP")

    @patch("app.ingestion.fred_fetcher.Fred")
    def test_fetch_multiple_series_success(self, mock_fred_class):
        """Test fetching multiple series."""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred

        # Mock series data
        dates = pd.date_range("2020-01-01", "2024-12-31", freq="M")
        mock_series_data = pd.Series([5.0] * len(dates), index=dates)

        mock_fred.get_series.return_value = mock_series_data
        mock_fred.get_series_info.return_value = {"title": "Test Series"}

        fetcher = FREDFetcher(api_key="test-key")
        fetcher.fred = mock_fred

        result = fetcher.fetch_multiple_series(
            ["GDP", "UNRATE"], start_date="2020-01-01", end_date="2024-12-31"
        )

        assert result is not None
        assert "GDP" in result
        assert "UNRATE" in result
        assert result["GDP"]["data"] is not None
        assert result["UNRATE"]["data"] is not None

    @patch("app.ingestion.fred_fetcher.Fred")
    def test_search_series_success(self, mock_fred_class):
        """Test series search."""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred

        # Mock search results
        mock_search_results = pd.DataFrame(
            {
                "id": ["UNRATE", "U6RATE"],
                "title": ["Unemployment Rate", "U-6 Unemployment Rate"],
                "units": ["Percent", "Percent"],
                "frequency": ["Monthly", "Monthly"],
                "seasonal_adjustment": ["Seasonally Adjusted", "Seasonally Adjusted"],
            }
        )

        mock_fred.search.return_value = mock_search_results

        fetcher = FREDFetcher(api_key="test-key")
        fetcher.fred = mock_fred

        result = fetcher.search_series("unemployment", limit=10)

        assert result is not None
        assert len(result) == 2
        assert result[0]["series_id"] == "UNRATE"
        assert result[0]["title"] == "Unemployment Rate"
        assert result[1]["series_id"] == "U6RATE"

    @patch("app.ingestion.fred_fetcher.Fred")
    def test_search_series_no_results(self, mock_fred_class):
        """Test series search with no results."""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred
        mock_fred.search.return_value = pd.DataFrame()

        fetcher = FREDFetcher(api_key="test-key")
        fetcher.fred = mock_fred

        result = fetcher.search_series("nonexistent")

        assert result == []

    def test_format_series_for_rag(self):
        """Test formatting series data for RAG."""
        dates = pd.date_range("2024-01-01", "2024-12-31", freq="M")
        data = pd.Series([5.0, 5.1, 5.2, 5.3] * 3, index=dates[:12])

        series_data = {
            "series_id": "UNRATE",
            "data": data,
            "metadata": {
                "title": "Unemployment Rate",
                "units": "Percent",
                "frequency": "Monthly",
                "seasonal_adjustment": "Seasonally Adjusted",
                "observation_start": "2024-01-01",
                "observation_end": "2024-12-31",
                "last_updated": "2024-12-31",
                "notes": "Unemployment rate data",
            },
        }

        fetcher = FREDFetcher(api_key="test-key")
        formatted = fetcher.format_series_for_rag(series_data)

        assert "FRED Economic Data Series: UNRATE" in formatted
        assert "Unemployment Rate" in formatted
        assert "Percent" in formatted
        assert "Monthly" in formatted
        assert "Recent Data Points" in formatted
        assert "Summary Statistics" in formatted

    def test_format_series_for_rag_no_data(self):
        """Test formatting series with no data."""
        series_data = {
            "series_id": "INVALID",
            "data": None,
            "metadata": {},
        }

        fetcher = FREDFetcher(api_key="test-key")
        formatted = fetcher.format_series_for_rag(series_data)

        assert "FRED Series: INVALID" in formatted
        assert "No data available" in formatted

    def test_get_series_metadata(self):
        """Test extracting series metadata."""
        dates = pd.date_range("2024-01-01", "2024-12-31", freq="M")
        data = pd.Series([5.0] * 12, index=dates)

        series_data = {
            "series_id": "UNRATE",
            "data": data,
            "metadata": {
                "title": "Unemployment Rate",
                "units": "Percent",
                "frequency": "Monthly",
                "seasonal_adjustment": "Seasonally Adjusted",
                "observation_start": "2024-01-01",
                "observation_end": "2024-12-31",
                "last_updated": "2024-12-31",
            },
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        }

        fetcher = FREDFetcher(api_key="test-key")
        metadata = fetcher.get_series_metadata(series_data)

        assert metadata["source"] == "fred"
        assert metadata["series_id"] == "UNRATE"
        assert metadata["title"] == "Unemployment Rate"
        assert metadata["units"] == "Percent"
        assert metadata["data_points"] == 12

    @patch("app.ingestion.fred_fetcher.Fred")
    def test_fetch_series_error_handling(self, mock_fred_class):
        """Test error handling in series fetching."""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred
        mock_fred.get_series.side_effect = Exception("API Error")

        fetcher = FREDFetcher(api_key="test-key")
        fetcher.fred = mock_fred

        with pytest.raises(FREDFetcherError, match="Error fetching FRED series"):
            fetcher.fetch_series("GDP")

    @patch("app.ingestion.fred_fetcher.Fred")
    def test_search_series_error_handling(self, mock_fred_class):
        """Test error handling in series search."""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred
        mock_fred.search.side_effect = Exception("API Error")

        fetcher = FREDFetcher(api_key="test-key")
        fetcher.fred = mock_fred

        with pytest.raises(FREDFetcherError, match="Error searching FRED series"):
            fetcher.search_series("unemployment")
