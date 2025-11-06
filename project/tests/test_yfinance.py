"""
Unit tests for yfinance stock data integration (TASK-030).

Tests yfinance fetcher, stock data normalizer, and pipeline integration.
"""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from app.ingestion.stock_data_normalizer import StockDataNormalizer
from app.ingestion.yfinance_fetcher import (
    YFinanceFetcher,
    YFinanceFetcherError,
)


class TestYFinanceFetcher:
    """Tests for YFinanceFetcher class."""

    @pytest.fixture
    def fetcher(self):
        """Create YFinanceFetcher instance with fast rate limiting for tests."""
        return YFinanceFetcher(rate_limit_seconds=0.1)

    @patch("app.ingestion.yfinance_fetcher.yf")
    def test_fetch_ticker_info_success(self, mock_yf, fetcher):
        """Test successful ticker info fetching."""
        # Mock ticker info
        mock_info = {
            "longName": "Apple Inc.",
            "sector": "Technology",
            "marketCap": 3000000000000,
            "currentPrice": 150.0,
        }
        mock_ticker = Mock()
        mock_ticker.info = mock_info
        mock_yf.Ticker.return_value = mock_ticker

        result = fetcher.fetch_ticker_info("AAPL")

        assert result == mock_info
        mock_yf.Ticker.assert_called_once_with("AAPL")

    @patch("app.ingestion.yfinance_fetcher.yf")
    def test_fetch_ticker_info_empty(self, mock_yf, fetcher):
        """Test ticker info fetching with empty result."""
        mock_ticker = Mock()
        mock_ticker.info = {}
        mock_yf.Ticker.return_value = mock_ticker

        with pytest.raises(YFinanceFetcherError, match="No information available"):
            fetcher.fetch_ticker_info("INVALID")

    @patch("app.ingestion.yfinance_fetcher.yf")
    def test_fetch_historical_prices_success(self, mock_yf, fetcher):
        """Test successful historical price fetching."""
        # Create mock DataFrame
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        mock_history = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "High": [101.0, 102.0, 103.0, 104.0, 105.0],
                "Low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "Close": [100.5, 101.5, 102.5, 103.5, 104.5],
                "Volume": [1000000, 1100000, 1200000, 1300000, 1400000],
            },
            index=dates,
        )

        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_history
        mock_yf.Ticker.return_value = mock_ticker

        result = fetcher.fetch_historical_prices("AAPL", period="1mo")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        mock_ticker.history.assert_called_once()

    @patch("app.ingestion.yfinance_fetcher.yf")
    def test_fetch_historical_prices_empty(self, mock_yf, fetcher):
        """Test historical price fetching with empty result."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_yf.Ticker.return_value = mock_ticker

        with pytest.raises(YFinanceFetcherError, match="No historical data available"):
            fetcher.fetch_historical_prices("INVALID")

    @patch("app.ingestion.yfinance_fetcher.yf")
    def test_fetch_dividends_success(self, mock_yf, fetcher):
        """Test successful dividend fetching."""
        dates = pd.date_range("2024-01-01", periods=3, freq="Q")
        mock_dividends = pd.Series([0.25, 0.25, 0.25], index=dates)

        mock_ticker = Mock()
        mock_ticker.dividends = mock_dividends
        mock_yf.Ticker.return_value = mock_ticker

        result = fetcher.fetch_dividends("AAPL")

        assert isinstance(result, pd.Series)
        assert len(result) == 3

    @patch("app.ingestion.yfinance_fetcher.yf")
    def test_fetch_dividends_empty(self, mock_yf, fetcher):
        """Test dividend fetching with empty result."""
        mock_ticker = Mock()
        mock_ticker.dividends = pd.Series(dtype=float)
        mock_yf.Ticker.return_value = mock_ticker

        result = fetcher.fetch_dividends("AAPL")

        assert isinstance(result, pd.Series)
        assert result.empty

    @patch("app.ingestion.yfinance_fetcher.yf")
    def test_fetch_earnings_success(self, mock_yf, fetcher):
        """Test successful earnings fetching."""
        dates = pd.date_range("2024-01-01", periods=4, freq="Q")
        mock_earnings = pd.DataFrame(
            {"Revenue": [1000000000, 1100000000, 1200000000, 1300000000]},
            index=dates,
        )

        mock_ticker = Mock()
        mock_ticker.earnings = mock_earnings
        mock_yf.Ticker.return_value = mock_ticker

        result = fetcher.fetch_earnings("AAPL")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4

    @patch("app.ingestion.yfinance_fetcher.yf")
    def test_fetch_recommendations_success(self, mock_yf, fetcher):
        """Test successful recommendations fetching."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        mock_recommendations = pd.DataFrame(
            {
                "Firm": ["Firm A", "Firm B", "Firm C"],
                "To Grade": ["Buy", "Hold", "Buy"],
                "From Grade": ["Hold", "Hold", "Hold"],
                "Action": ["upgrade", "main", "upgrade"],
            },
            index=dates,
        )

        mock_ticker = Mock()
        mock_ticker.recommendations = mock_recommendations
        mock_yf.Ticker.return_value = mock_ticker

        result = fetcher.fetch_recommendations("AAPL")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    @patch("app.ingestion.yfinance_fetcher.yf")
    def test_fetch_all_data_success(self, mock_yf, fetcher):
        """Test fetching all data for a ticker."""
        # Mock all data sources
        mock_info = {"longName": "Apple Inc.", "currentPrice": 150.0}
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        mock_history = pd.DataFrame(
            {"Close": [150.0, 151.0, 152.0, 153.0, 154.0]}, index=dates
        )
        mock_dividends = pd.Series([0.25], index=[dates[0]])
        mock_earnings = pd.DataFrame({"Revenue": [1000000000]}, index=[dates[0]])
        mock_recommendations = pd.DataFrame(
            {"Firm": ["Firm A"], "To Grade": ["Buy"]}, index=[dates[0]]
        )

        mock_ticker = Mock()
        mock_ticker.info = mock_info
        mock_ticker.history.return_value = mock_history
        mock_ticker.dividends = mock_dividends
        mock_ticker.earnings = mock_earnings
        mock_ticker.recommendations = mock_recommendations
        mock_yf.Ticker.return_value = mock_ticker

        result = fetcher.fetch_all_data("AAPL", include_history=True)

        assert "info" in result
        assert "history" in result
        assert "dividends" in result
        assert "earnings" in result
        assert "recommendations" in result

    def test_rate_limiting(self, fetcher):
        """Test rate limiting between requests."""
        import time

        start_time = time.time()
        fetcher._apply_rate_limit()
        fetcher._apply_rate_limit()
        elapsed = time.time() - start_time

        # Should have waited at least rate_limit_seconds
        assert elapsed >= fetcher.rate_limit_seconds


class TestStockDataNormalizer:
    """Tests for StockDataNormalizer class."""

    def test_normalize_ticker_info(self):
        """Test ticker info normalization."""
        info = {
            "longName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "marketCap": 3000000000000,
            "currentPrice": 150.0,
            "trailingPE": 30.0,
            "dividendYield": 0.005,
        }

        result = StockDataNormalizer.normalize_ticker_info(info, "AAPL")

        assert isinstance(result, str)
        assert "AAPL" in result
        assert "Apple Inc." in result
        assert "Technology" in result
        assert "$150.00" in result or "150.0" in result

    def test_normalize_historical_prices(self):
        """Test historical price normalization."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        history = pd.DataFrame(
            {
                "Open": [100.0] * 10,
                "High": [105.0] * 10,
                "Low": [95.0] * 10,
                "Close": [102.0] * 10,
                "Volume": [1000000] * 10,
            },
            index=dates,
        )

        result = StockDataNormalizer.normalize_historical_prices(history, "AAPL")

        assert isinstance(result, str)
        assert "AAPL" in result
        assert "Historical Price Data" in result
        assert "10" in result  # Should mention 10 trading days

    def test_normalize_dividends(self):
        """Test dividend normalization."""
        dates = pd.date_range("2024-01-01", periods=4, freq="Q")
        dividends = pd.Series([0.25, 0.25, 0.25, 0.25], index=dates)

        result = StockDataNormalizer.normalize_dividends(dividends, "AAPL")

        assert isinstance(result, str)
        assert "AAPL" in result
        assert "Dividend History" in result
        assert "4" in result  # Should mention 4 payments

    def test_normalize_earnings(self):
        """Test earnings normalization."""
        dates = pd.date_range("2024-01-01", periods=4, freq="Q")
        earnings = pd.DataFrame(
            {"Revenue": [1000000000, 1100000000, 1200000000, 1300000000]},
            index=dates,
        )

        result = StockDataNormalizer.normalize_earnings(earnings, "AAPL")

        assert isinstance(result, str)
        assert "AAPL" in result
        assert "Earnings Data" in result

    def test_normalize_recommendations(self):
        """Test recommendations normalization."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        recommendations = pd.DataFrame(
            {
                "Firm": ["Firm A", "Firm B", "Firm C"],
                "To Grade": ["Buy", "Hold", "Buy"],
                "From Grade": ["Hold", "Hold", "Hold"],
                "Action": ["upgrade", "main", "upgrade"],
            },
            index=dates,
        )

        result = StockDataNormalizer.normalize_recommendations(recommendations, "AAPL")

        assert isinstance(result, str)
        assert "AAPL" in result
        assert "Recommendations" in result

    def test_normalize_all_data(self):
        """Test normalization of all data types."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        data = {
            "info": {
                "longName": "Apple Inc.",
                "currentPrice": 150.0,
                "marketCap": 3000000000000,
            },
            "history": pd.DataFrame(
                {"Close": [150.0, 151.0, 152.0, 153.0, 154.0]}, index=dates
            ),
            "dividends": pd.Series([0.25], index=[dates[0]]),
            "earnings": pd.DataFrame({"Revenue": [1000000000]}, index=[dates[0]]),
            "recommendations": pd.DataFrame(
                {"Firm": ["Firm A"], "To Grade": ["Buy"]}, index=[dates[0]]
            ),
        }

        result = StockDataNormalizer.normalize_all_data(data, "AAPL")

        assert isinstance(result, list)
        assert len(result) > 0
        for doc in result:
            assert "text" in doc
            assert "metadata" in doc
            assert doc["metadata"]["ticker"] == "AAPL"
            assert doc["metadata"]["source"] == "yfinance"
            assert "data_type" in doc["metadata"]


class TestPipelineIntegration:
    """Tests for pipeline integration with yfinance."""

    @pytest.fixture
    def mock_pipeline(self, monkeypatch):
        """Create a mock pipeline with yfinance enabled."""
        from app.ingestion.pipeline import IngestionPipeline

        # Mock config to enable yfinance
        monkeypatch.setattr("app.utils.config.config.yfinance_enabled", True)

        pipeline = IngestionPipeline()
        return pipeline

    @patch("app.ingestion.pipeline.YFinanceFetcher")
    def test_process_stock_data_disabled(self, mock_fetcher_class, monkeypatch):
        """Test that process_stock_data fails when yfinance is disabled."""
        from app.ingestion.pipeline import IngestionPipeline

        monkeypatch.setattr("app.utils.config.config.yfinance_enabled", False)

        pipeline = IngestionPipeline()

        with pytest.raises(Exception, match="yfinance integration is disabled"):
            pipeline.process_stock_data("AAPL")

    @patch("app.ingestion.pipeline.YFinanceFetcher")
    def test_process_stock_data_success(self, mock_fetcher_class, monkeypatch):
        """Test successful stock data processing."""
        from app.ingestion.pipeline import IngestionPipeline

        monkeypatch.setattr("app.utils.config.config.yfinance_enabled", True)

        # Mock fetcher
        mock_fetcher = Mock()
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        mock_fetcher.fetch_all_data.return_value = {
            "info": {"longName": "Apple Inc.", "currentPrice": 150.0},
            "history": pd.DataFrame(
                {"Close": [150.0, 151.0, 152.0, 153.0, 154.0]}, index=dates
            ),
            "dividends": pd.Series(dtype=float),
            "earnings": pd.DataFrame(),
            "recommendations": pd.DataFrame(),
        }
        mock_fetcher_class.return_value = mock_fetcher

        pipeline = IngestionPipeline()

        # Mock embedding and storage to avoid actual API calls
        # Need to return embeddings for each chunk (will be 2 chunks from 2 documents)
        with (
            patch.object(
                pipeline.embedding_generator,
                "embed_documents",
                return_value=[
                    [0.1] * 384,
                    [0.2] * 384,
                ],  # Return 2 embeddings for 2 chunks
            ),
            patch.object(
                pipeline.chroma_store, "add_documents", return_value=["id1", "id2"]
            ),
        ):
            result = pipeline.process_stock_data("AAPL", store_embeddings=True)

            assert isinstance(result, list)
            assert len(result) > 0
