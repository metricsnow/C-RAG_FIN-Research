"""
Integration tests for news monitoring service.

Tests the full workflow of automated news monitoring including
feed polling, article detection, deduplication, and ingestion.
"""

import time
from unittest.mock import patch

import pytest

from app.services.news_monitor import NewsMonitor


@pytest.mark.integration
class TestNewsMonitorIntegration:
    """Integration tests for NewsMonitor service."""

    @pytest.fixture
    def sample_articles(self):
        """Sample article data for testing."""
        return [
            {
                "title": "AAPL Earnings Beat Expectations",
                "content": "Apple reported strong earnings...",
                "url": "https://example.com/article1",
                "source": "reuters",
                "author": "Author 1",
                "date": "2025-01-27",
                "tickers": ["AAPL"],
                "category": "earnings",
            },
            {
                "title": "MSFT Revenue Growth",
                "content": "Microsoft revenue increased...",
                "url": "https://example.com/article2",
                "source": "cnbc",
                "author": "Author 2",
                "date": "2025-01-27",
                "tickers": ["MSFT"],
                "category": "markets",
            },
        ]

    @pytest.fixture
    def sample_feeds(self):
        """Sample RSS feed URLs."""
        return ["https://example.com/feed1"]

    @pytest.mark.slow
    def test_full_monitoring_workflow(self, sample_feeds, sample_articles, tmp_path):
        """Test full monitoring workflow with real components."""
        # This test requires actual pipeline and ChromaDB setup
        # Skip if not available
        pytest.importorskip("chromadb")

        # Use temporary directory for ChromaDB
        import os

        original_chroma_path = os.environ.get("CHROMA_DB_PATH")
        try:
            os.environ["CHROMA_DB_PATH"] = str(tmp_path / "chroma_db")

            # Create monitor with short polling interval for testing
            monitor = NewsMonitor(
                feed_urls=sample_feeds,
                poll_interval_minutes=1,  # Short interval for testing
                collection_name="test_monitor",
            )

            # Mock the news fetcher to return sample articles
            with patch.object(
                monitor.pipeline.news_fetcher,
                "fetch_from_rss",
                return_value=sample_articles,
            ):
                # Start monitoring
                monitor.start()

                # Wait a bit for initial poll
                time.sleep(2)

                # Check stats
                stats = monitor.get_stats()
                assert stats["total_polls"] >= 1

                # Stop monitoring
                monitor.stop()

                # Verify service stopped
                assert monitor.is_running is False

        finally:
            if original_chroma_path:
                os.environ["CHROMA_DB_PATH"] = original_chroma_path
            else:
                os.environ.pop("CHROMA_DB_PATH", None)

    def test_deduplication_workflow(self, sample_feeds, sample_articles):
        """Test article deduplication during monitoring."""
        monitor = NewsMonitor(feed_urls=sample_feeds, poll_interval_minutes=1)

        # Mock ChromaDB to return existing article
        with patch.object(
            monitor.chroma_store,
            "query_by_text",
            return_value={
                "ids": ["id1"],
                "metadatas": [
                    {"url": sample_articles[0]["url"], "source_type": "news"}
                ],
                "documents": [],
            },
        ):
            # Check that article is detected as existing
            exists = monitor._check_article_exists(sample_articles[0]["url"])
            assert exists is True

            # Check that new article is not detected as existing
            exists = monitor._check_article_exists("https://example.com/new_article")
            assert exists is False

    def test_filtering_workflow(self, sample_feeds, sample_articles):
        """Test article filtering during monitoring."""
        monitor = NewsMonitor(
            feed_urls=sample_feeds,
            filter_tickers=["AAPL"],
            filter_keywords=["earnings"],
            filter_categories=["earnings"],
        )

        # Test ticker filter
        article_with_aapl = sample_articles[0]
        assert monitor._should_process_article(article_with_aapl) is True

        article_with_msft = sample_articles[1]
        assert monitor._should_process_article(article_with_msft) is False

        # Test keyword filter
        monitor.filter_tickers = []
        monitor.filter_keywords = ["earnings"]
        assert monitor._should_process_article(article_with_aapl) is True
        assert monitor._should_process_article(article_with_msft) is False

        # Test category filter
        monitor.filter_keywords = []
        monitor.filter_categories = ["earnings"]
        assert monitor._should_process_article(article_with_aapl) is True
        assert monitor._should_process_article(article_with_msft) is False

    def test_service_lifecycle(self, sample_feeds):
        """Test service start/stop/pause/resume lifecycle."""
        monitor = NewsMonitor(feed_urls=sample_feeds, poll_interval_minutes=1)

        # Test start
        with patch.object(monitor, "_poll_feeds"):
            monitor.start()
            assert monitor.is_running is True

            # Test pause
            monitor.pause()
            assert monitor.is_paused is True

            # Test resume
            monitor.resume()
            assert monitor.is_paused is False

            # Test stop
            monitor.stop()
            assert monitor.is_running is False

    def test_error_handling(self, sample_feeds):
        """Test error handling during monitoring."""
        monitor = NewsMonitor(feed_urls=sample_feeds, poll_interval_minutes=1)

        # Mock pipeline to raise error
        with patch.object(
            monitor.pipeline.news_fetcher,
            "fetch_from_rss",
            side_effect=Exception("Network error"),
        ):
            # Poll should handle error gracefully
            monitor._poll_feeds()

            # Check that error was recorded
            stats = monitor.get_stats()
            assert stats["total_errors"] > 0
            # Note: last_poll_success may be True if errors are caught per-feed
            # The important thing is that errors are tracked and service continues
            assert stats["total_polls"] == 1

    def test_statistics_tracking(self, sample_feeds, sample_articles):
        """Test statistics tracking during monitoring."""
        monitor = NewsMonitor(feed_urls=sample_feeds, poll_interval_minutes=1)

        # Mock successful poll
        with (
            patch.object(
                monitor.pipeline.news_fetcher,
                "fetch_from_rss",
                return_value=sample_articles,
            ),
            patch.object(monitor.pipeline, "process_news", return_value=["id1", "id2"]),
            patch.object(monitor, "_check_article_exists", return_value=False),
        ):
            monitor._poll_feeds()

            stats = monitor.get_stats()
            assert stats["total_polls"] == 1
            assert stats["total_articles_processed"] > 0
            assert stats["last_poll_success"] is True
