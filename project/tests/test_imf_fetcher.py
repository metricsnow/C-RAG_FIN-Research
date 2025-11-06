"""
Unit tests for IMF fetcher module.
"""

from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests

from app.ingestion.imf_fetcher import IMFFetcher, IMFFetcherError


class TestIMFFetcher:
    """Test cases for IMFFetcher."""

    def test_init(self):
        """Test fetcher initialization."""
        fetcher = IMFFetcher(rate_limit_delay=1.0)
        assert fetcher.rate_limit_delay == 1.0
        assert fetcher.session is not None

    @patch("app.ingestion.imf_fetcher.requests.Session")
    def test_fetch_indicator_success(self, mock_session_class):
        """Test successful indicator fetching."""
        # Mock session and response
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "values": {
                "US": {"2020": 100.0, "2021": 102.0},
                "CN": {"2020": 50.0, "2021": 52.0},
            },
            "metadata": {
                "name": "GDP Growth",
                "description": "Real GDP growth rate",
                "unit": "Percent",
            },
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        fetcher = IMFFetcher(rate_limit_delay=0.0)
        result = fetcher.fetch_indicator("NGDP_RPCH")

        assert result["indicator_code"] == "NGDP_RPCH"
        assert result["data"] is not None
        assert isinstance(result["data"], pd.DataFrame)
        assert "metadata" in result

    @patch("app.ingestion.imf_fetcher.requests.Session")
    def test_fetch_indicator_no_data(self, mock_session_class):
        """Test indicator fetching with no data."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        fetcher = IMFFetcher(rate_limit_delay=0.0)
        result = fetcher.fetch_indicator("INVALID")

        assert result["indicator_code"] == "INVALID"
        assert result["data"] is None
        assert "error" in result

    @patch("app.ingestion.imf_fetcher.requests.Session")
    def test_fetch_multiple_indicators(self, mock_session_class):
        """Test fetching multiple indicators."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "values": {"US": {"2020": 100.0}},
            "metadata": {"name": "Test Indicator", "unit": "Percent"},
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        fetcher = IMFFetcher(rate_limit_delay=0.0)
        results = fetcher.fetch_multiple_indicators(["NGDP_RPCH", "LUR"])

        assert len(results) == 2
        assert "NGDP_RPCH" in results
        assert "LUR" in results

    @patch("app.ingestion.imf_fetcher.requests.Session")
    def test_get_available_indicators(self, mock_session_class):
        """Test getting available indicators."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "NGDP_RPCH": {
                "name": "GDP Growth",
                "description": "Real GDP growth rate",
                "unit": "Percent",
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        fetcher = IMFFetcher(rate_limit_delay=0.0)
        indicators = fetcher.get_available_indicators()

        assert len(indicators) > 0
        assert indicators[0]["indicator_code"] == "NGDP_RPCH"

    @patch("app.ingestion.imf_fetcher.requests.Session")
    def test_get_countries(self, mock_session_class):
        """Test getting countries list."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "US": {"name": "United States", "region": "North America"}
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        fetcher = IMFFetcher(rate_limit_delay=0.0)
        countries = fetcher.get_countries()

        assert len(countries) > 0
        assert countries[0]["country_code"] == "US"

    def test_format_indicator_for_rag(self):
        """Test formatting indicator data for RAG."""
        indicator_data = {
            "indicator_code": "NGDP_RPCH",
            "metadata": {
                "name": "GDP Growth",
                "description": "Real GDP growth rate",
                "unit": "Percent",
            },
            "data": pd.DataFrame({"US": [2.0, 2.5]}, index=[2020, 2021]),
        }

        fetcher = IMFFetcher(rate_limit_delay=0.0)
        formatted = fetcher.format_indicator_for_rag(indicator_data)

        assert "NGDP_RPCH" in formatted
        assert "GDP Growth" in formatted
        assert "US" in formatted

    def test_get_indicator_metadata(self):
        """Test extracting indicator metadata."""
        indicator_data = {
            "indicator_code": "NGDP_RPCH",
            "metadata": {
                "name": "GDP Growth",
                "description": "Real GDP growth rate",
                "unit": "Percent",
            },
            "data": pd.DataFrame({"US": [2.0]}, index=[2020]),
            "country_codes": ["US"],
            "start_year": 2020,
            "end_year": 2021,
        }

        fetcher = IMFFetcher(rate_limit_delay=0.0)
        metadata = fetcher.get_indicator_metadata(indicator_data)

        assert metadata["source"] == "imf"
        assert metadata["indicator_code"] == "NGDP_RPCH"
        assert metadata["name"] == "GDP Growth"
        assert metadata["data_points"] > 0

    @patch("app.ingestion.imf_fetcher.requests.Session")
    def test_request_error_handling(self, mock_session_class):
        """Test error handling for API requests."""
        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.RequestException("API Error")
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        fetcher = IMFFetcher(rate_limit_delay=0.0)

        with pytest.raises(IMFFetcherError):
            fetcher.fetch_indicator("NGDP_RPCH")
