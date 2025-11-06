"""
Unit tests for World Bank fetcher module.
"""

from unittest.mock import patch

import pandas as pd

from app.ingestion.world_bank_fetcher import WorldBankFetcher


class TestWorldBankFetcher:
    """Test cases for WorldBankFetcher."""

    def test_init(self):
        """Test fetcher initialization."""
        fetcher = WorldBankFetcher(rate_limit_delay=1.0)
        assert fetcher.rate_limit_delay == 1.0

    @patch("app.ingestion.world_bank_fetcher.wb")
    def test_fetch_indicator_success(self, mock_wb):
        """Test successful indicator fetching."""
        # Mock indicator data
        mock_data = pd.DataFrame(
            {
                "USA": [100.0, 102.0, 104.0],
                "CHN": [50.0, 52.0, 54.0],
            },
            index=[2020, 2021, 2022],
        )

        # Mock indicator info
        mock_indicators = pd.DataFrame(
            [
                {
                    "id": "NY.GDP.MKTP.CD",
                    "name": "GDP (current US$)",
                    "source": "World Bank",
                    "topic": "Economic Policy & Debt",
                    "unit": "US$",
                    "note": "GDP data",
                }
            ]
        )

        mock_wb.get_series.return_value = mock_data
        mock_wb.get_indicators.return_value = mock_indicators

        fetcher = WorldBankFetcher(rate_limit_delay=0.0)
        result = fetcher.fetch_indicator("NY.GDP.MKTP.CD")

        assert result["indicator_code"] == "NY.GDP.MKTP.CD"
        assert result["data"] is not None
        assert "metadata" in result

    @patch("app.ingestion.world_bank_fetcher.wb")
    def test_fetch_indicator_no_data(self, mock_wb):
        """Test indicator fetching with no data."""
        mock_wb.get_series.return_value = pd.DataFrame()

        fetcher = WorldBankFetcher(rate_limit_delay=0.0)
        result = fetcher.fetch_indicator("INVALID.INDICATOR")

        assert result["indicator_code"] == "INVALID.INDICATOR"
        assert result["data"] is None
        assert "error" in result

    @patch("app.ingestion.world_bank_fetcher.wb")
    def test_fetch_multiple_indicators(self, mock_wb):
        """Test fetching multiple indicators."""
        mock_data = pd.DataFrame({"USA": [100.0]}, index=[2020])
        mock_indicators = pd.DataFrame(
            [
                {
                    "id": "NY.GDP.MKTP.CD",
                    "name": "GDP",
                    "source": "WB",
                    "topic": "Econ",
                    "unit": "$",
                    "note": "",
                }
            ]
        )

        mock_wb.get_series.return_value = mock_data
        mock_wb.get_indicators.return_value = mock_indicators

        fetcher = WorldBankFetcher(rate_limit_delay=0.0)
        results = fetcher.fetch_multiple_indicators(["NY.GDP.MKTP.CD", "SP.POP.TOTL"])

        assert len(results) == 2
        assert "NY.GDP.MKTP.CD" in results
        assert "SP.POP.TOTL" in results

    @patch("app.ingestion.world_bank_fetcher.wb")
    def test_search_indicators(self, mock_wb):
        """Test searching for indicators."""
        mock_results = pd.DataFrame(
            [
                {
                    "id": "NY.GDP.MKTP.CD",
                    "name": "GDP (current US$)",
                    "source": "World Bank",
                    "topic": "Economic Policy & Debt",
                }
            ]
        )

        mock_wb.search_indicators.return_value = mock_results

        fetcher = WorldBankFetcher(rate_limit_delay=0.0)
        results = fetcher.search_indicators("gdp")

        assert len(results) > 0
        assert results[0]["indicator_code"] == "NY.GDP.MKTP.CD"

    @patch("app.ingestion.world_bank_fetcher.wb")
    def test_get_countries(self, mock_wb):
        """Test getting countries list."""
        mock_countries = pd.DataFrame(
            [
                {
                    "id": "USA",
                    "name": "United States",
                    "region": "North America",
                    "incomeLevel": "High income",
                }
            ]
        )

        mock_wb.get_countries.return_value = mock_countries

        fetcher = WorldBankFetcher(rate_limit_delay=0.0)
        countries = fetcher.get_countries()

        assert len(countries) > 0
        assert countries[0]["country_code"] == "USA"

    def test_format_indicator_for_rag(self):
        """Test formatting indicator data for RAG."""
        indicator_data = {
            "indicator_code": "NY.GDP.MKTP.CD",
            "metadata": {
                "name": "GDP (current US$)",
                "source": "World Bank",
                "topic": "Economic Policy & Debt",
                "unit": "US$",
            },
            "data": pd.DataFrame({"USA": [100.0, 102.0]}, index=[2020, 2021]),
        }

        fetcher = WorldBankFetcher(rate_limit_delay=0.0)
        formatted = fetcher.format_indicator_for_rag(indicator_data)

        assert "NY.GDP.MKTP.CD" in formatted
        assert "GDP (current US$)" in formatted
        assert "USA" in formatted

    def test_get_indicator_metadata(self):
        """Test extracting indicator metadata."""
        indicator_data = {
            "indicator_code": "NY.GDP.MKTP.CD",
            "metadata": {
                "name": "GDP (current US$)",
                "source": "World Bank",
                "topic": "Economic Policy & Debt",
                "unit": "US$",
            },
            "data": pd.DataFrame({"USA": [100.0]}, index=[2020]),
            "country_codes": ["USA"],
            "start_year": 2020,
            "end_year": 2021,
        }

        fetcher = WorldBankFetcher(rate_limit_delay=0.0)
        metadata = fetcher.get_indicator_metadata(indicator_data)

        assert metadata["source"] == "world_bank"
        assert metadata["indicator_code"] == "NY.GDP.MKTP.CD"
        assert metadata["name"] == "GDP (current US$)"
        assert metadata["data_points"] > 0
