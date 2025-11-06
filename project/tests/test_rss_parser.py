"""
Unit tests for RSS parser module.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.ingestion.rss_parser import RSSParser, RSSParserError


class TestRSSParser:
    """Test cases for RSSParser class."""

    def test_init(self):
        """Test RSSParser initialization."""
        parser = RSSParser(rate_limit_seconds=2.0, timeout=60, max_retries=5)
        assert parser.rate_limit_seconds == 2.0
        assert parser.timeout == 60
        assert parser.max_retries == 5
        assert parser.last_request_time is None

    @patch("app.ingestion.rss_parser.feedparser")
    def test_parse_feed_success(self, mock_feedparser):
        """Test successful RSS feed parsing."""
        # Mock feedparser response
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.feed = {
            "title": "Test Feed",
            "link": "https://example.com/feed",
        }
        mock_entry = MagicMock()
        mock_entry.get.side_effect = lambda key, default="": {
            "title": "Test Article",
            "link": "https://example.com/article",
            "summary": "Test content",
        }.get(key, default)
        mock_entry.published_parsed = (2025, 1, 27, 12, 0, 0, 0, 0, 0)
        mock_entry.author = "Test Author"
        mock_feed.entries = [mock_entry]
        mock_feedparser.parse.return_value = mock_feed

        parser = RSSParser()
        articles = parser.parse_feed("https://example.com/feed")

        assert len(articles) == 1
        assert articles[0]["title"] == "Test Article"
        assert articles[0]["url"] == "https://example.com/article"
        assert articles[0]["source"] == "example"

    @patch("app.ingestion.rss_parser.feedparser")
    def test_parse_feed_error(self, mock_feedparser):
        """Test RSS feed parsing with error."""
        mock_feedparser.parse.side_effect = Exception("Network error")

        parser = RSSParser()
        with pytest.raises(RSSParserError):
            parser.parse_feed("https://example.com/feed")

    def test_determine_source(self):
        """Test source determination from URL."""
        parser = RSSParser()

        assert parser._determine_source("https://www.reuters.com/feed", "") == "reuters"
        assert parser._determine_source("https://www.cnbc.com/feed", "") == "cnbc"
        assert (
            parser._determine_source("https://www.marketwatch.com/feed", "")
            == "marketwatch"
        )
        assert (
            parser._determine_source("https://www.ft.com/feed", "") == "financial_times"
        )

    @patch("app.ingestion.rss_parser.feedparser")
    def test_parse_feeds_multiple(self, mock_feedparser):
        """Test parsing multiple feeds."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.feed = {"title": "Test Feed", "link": "https://example.com"}
        mock_feed.entries = []
        mock_feedparser.parse.return_value = mock_feed

        parser = RSSParser()
        articles = parser.parse_feeds(
            ["https://example.com/feed1", "https://example.com/feed2"]
        )

        assert mock_feedparser.parse.call_count == 2
        assert isinstance(articles, list)
