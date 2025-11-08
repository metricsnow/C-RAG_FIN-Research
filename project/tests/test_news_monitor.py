"""
Unit tests for news monitoring service.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.news_monitor import NewsMonitor, NewsMonitorError


class TestNewsMonitor:
    """Test cases for NewsMonitor class."""

    @pytest.fixture
    def mock_pipeline(self):
        """Create a mock ingestion pipeline."""
        pipeline = MagicMock()
        pipeline.news_fetcher = MagicMock()
        pipeline.process_news = MagicMock(return_value=["id1", "id2"])
        return pipeline

    @pytest.fixture
    def mock_chroma_store(self):
        """Create a mock ChromaDB store."""
        store = MagicMock()
        store.query_by_text = MagicMock(
            return_value={"ids": [], "metadatas": [], "documents": []}
        )
        return store

    @pytest.fixture
    def sample_feeds(self):
        """Sample RSS feed URLs."""
        return ["https://example.com/feed1", "https://example.com/feed2"]

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_init(self, mock_chroma_store_class, mock_pipeline_class, sample_feeds):
        """Test NewsMonitor initialization."""
        mock_pipeline_class.return_value = MagicMock()
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(
            feed_urls=sample_feeds,
            poll_interval_minutes=15,
            collection_name="test_collection",
        )

        assert monitor.feed_urls == sample_feeds
        assert monitor.poll_interval_minutes == 15
        assert monitor.collection_name == "test_collection"
        assert monitor.is_running is False
        assert monitor.is_paused is False
        assert len(monitor.processed_urls) == 0

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_init_with_filters(
        self, mock_chroma_store_class, mock_pipeline_class, sample_feeds
    ):
        """Test NewsMonitor initialization with filters."""
        mock_pipeline_class.return_value = MagicMock()
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(
            feed_urls=sample_feeds,
            filter_tickers=["AAPL", "MSFT"],
            filter_keywords=["earnings", "revenue"],
            filter_categories=["earnings"],
        )

        assert monitor.filter_tickers == ["AAPL", "MSFT"]
        assert monitor.filter_keywords == ["earnings", "revenue"]
        assert monitor.filter_categories == ["earnings"]

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_check_article_exists_found(
        self, mock_chroma_store_class, mock_pipeline_class, sample_feeds
    ):
        """Test checking article existence when article is found."""
        mock_pipeline_class.return_value = MagicMock()
        mock_store = MagicMock()
        mock_store.query_by_text.return_value = {
            "ids": ["id1"],
            "metadatas": [
                {"url": "https://example.com/article", "source_type": "news"}
            ],
            "documents": [],
        }
        mock_chroma_store_class.return_value = mock_store

        monitor = NewsMonitor(feed_urls=sample_feeds)
        result = monitor._check_article_exists("https://example.com/article")

        assert result is True

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_check_article_exists_not_found(
        self, mock_chroma_store_class, mock_pipeline_class, sample_feeds
    ):
        """Test checking article existence when article is not found."""
        mock_pipeline_class.return_value = MagicMock()
        mock_store = MagicMock()
        mock_store.query_by_text.return_value = {
            "ids": [],
            "metadatas": [],
            "documents": [],
        }
        mock_chroma_store_class.return_value = mock_store

        monitor = NewsMonitor(feed_urls=sample_feeds)
        result = monitor._check_article_exists("https://example.com/article")

        assert result is False

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_should_process_article_no_filters(
        self, mock_chroma_store_class, mock_pipeline_class, sample_feeds
    ):
        """Test article processing when no filters are set."""
        mock_pipeline_class.return_value = MagicMock()
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(feed_urls=sample_feeds)
        article = {"title": "Test Article", "content": "Content"}

        assert monitor._should_process_article(article) is True

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_should_process_article_ticker_filter_match(
        self, mock_chroma_store_class, mock_pipeline_class, sample_feeds
    ):
        """Test article processing with ticker filter that matches."""
        mock_pipeline_class.return_value = MagicMock()
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(feed_urls=sample_feeds, filter_tickers=["AAPL"])
        article = {"title": "AAPL Earnings", "tickers": ["AAPL", "MSFT"]}

        assert monitor._should_process_article(article) is True

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_should_process_article_ticker_filter_no_match(
        self, mock_chroma_store_class, mock_pipeline_class, sample_feeds
    ):
        """Test article processing with ticker filter that doesn't match."""
        mock_pipeline_class.return_value = MagicMock()
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(feed_urls=sample_feeds, filter_tickers=["AAPL"])
        article = {"title": "MSFT Earnings", "tickers": ["MSFT"]}

        assert monitor._should_process_article(article) is False

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_should_process_article_keyword_filter_match(
        self, mock_chroma_store_class, mock_pipeline_class, sample_feeds
    ):
        """Test article processing with keyword filter that matches."""
        mock_pipeline_class.return_value = MagicMock()
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(feed_urls=sample_feeds, filter_keywords=["earnings"])
        article = {"title": "Company Earnings Report", "content": "Revenue increased"}

        assert monitor._should_process_article(article) is True

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_should_process_article_keyword_filter_no_match(
        self, mock_chroma_store_class, mock_pipeline_class, sample_feeds
    ):
        """Test article processing with keyword filter that doesn't match."""
        mock_pipeline_class.return_value = MagicMock()
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(feed_urls=sample_feeds, filter_keywords=["earnings"])
        article = {"title": "Market Update", "content": "Stock prices rose"}

        assert monitor._should_process_article(article) is False

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_start_success(
        self, mock_chroma_store_class, mock_pipeline_class, sample_feeds
    ):
        """Test starting the monitoring service successfully."""
        mock_pipeline = MagicMock()
        mock_pipeline.news_fetcher = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(feed_urls=sample_feeds, poll_interval_minutes=1)

        with patch.object(monitor, "_poll_feeds"):
            monitor.start()

            assert monitor.is_running is True
            assert monitor.scheduler is not None
            assert monitor.stats["start_time"] is not None

            monitor.stop()

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_start_no_feeds(self, mock_chroma_store_class, mock_pipeline_class):
        """Test starting the monitoring service with no feeds."""
        mock_pipeline_class.return_value = MagicMock()
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(feed_urls=[])

        with pytest.raises(NewsMonitorError, match="No feed URLs configured"):
            monitor.start()

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_start_already_running(
        self, mock_chroma_store_class, mock_pipeline_class, sample_feeds
    ):
        """Test starting the monitoring service when already running."""
        mock_pipeline_class.return_value = MagicMock()
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(feed_urls=sample_feeds)
        monitor.is_running = True

        with pytest.raises(NewsMonitorError, match="already running"):
            monitor.start()

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_stop(self, mock_chroma_store_class, mock_pipeline_class, sample_feeds):
        """Test stopping the monitoring service."""
        mock_pipeline_class.return_value = MagicMock()
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(feed_urls=sample_feeds)
        monitor.is_running = True
        monitor.scheduler = MagicMock()

        monitor.stop()

        assert monitor.is_running is False

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_pause_resume(
        self, mock_chroma_store_class, mock_pipeline_class, sample_feeds
    ):
        """Test pausing and resuming the monitoring service."""
        mock_pipeline_class.return_value = MagicMock()
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(feed_urls=sample_feeds)
        monitor.is_running = True

        monitor.pause()
        assert monitor.is_paused is True

        monitor.resume()
        assert monitor.is_paused is False

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_get_stats(
        self, mock_chroma_store_class, mock_pipeline_class, sample_feeds
    ):
        """Test getting monitoring statistics."""
        mock_pipeline_class.return_value = MagicMock()
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(feed_urls=sample_feeds)
        monitor.stats["total_polls"] = 5
        monitor.stats["total_articles_processed"] = 10
        monitor.stats["start_time"] = datetime.now()

        stats = monitor.get_stats()

        assert stats["total_polls"] == 5
        assert stats["total_articles_processed"] == 10
        assert stats["feed_count"] == len(sample_feeds)
        assert "uptime_seconds" in stats

    @patch("app.services.news_monitor.IngestionPipeline")
    @patch("app.services.news_monitor.ChromaStore")
    def test_health_check(
        self, mock_chroma_store_class, mock_pipeline_class, sample_feeds
    ):
        """Test health check."""
        mock_pipeline_class.return_value = MagicMock()
        mock_chroma_store_class.return_value = MagicMock()

        monitor = NewsMonitor(feed_urls=sample_feeds)
        monitor.is_running = True
        monitor.scheduler = MagicMock()
        monitor.scheduler.running = True

        health = monitor.health_check()

        assert health["service_running"] is True
        assert health["scheduler_running"] is True
        assert health["pipeline_available"] is True
        assert health["feeds_configured"] is True
