"""
Unit tests for news fetcher module.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.ingestion.news_fetcher import NewsFetcher, NewsFetcherError


class TestNewsFetcher:
    """Test cases for NewsFetcher class."""

    def test_init(self):
        """Test NewsFetcher initialization."""
        fetcher = NewsFetcher(
            use_rss=True,
            use_scraping=True,
            rss_rate_limit=1.5,
            scraping_rate_limit=2.5,
            scrape_full_content=True,
        )
        assert fetcher.use_rss is True
        assert fetcher.use_scraping is True
        assert fetcher.scrape_full_content is True
        assert fetcher.rss_parser is not None
        assert fetcher.news_scraper is not None

    def test_init_disabled(self):
        """Test NewsFetcher initialization with features disabled."""
        fetcher = NewsFetcher(use_rss=False, use_scraping=False)
        assert fetcher.rss_parser is None
        assert fetcher.news_scraper is None

    @patch("app.ingestion.news_fetcher.RSSParser")
    def test_fetch_from_rss(self, mock_rss_parser_class):
        """Test fetching from RSS feeds."""
        mock_parser = MagicMock()
        mock_parser.parse_feeds.return_value = [
            {
                "title": "Test Article",
                "content": "Content about AAPL and MSFT",
                "url": "https://example.com/article",
                "source": "reuters",
                "author": "Author",
                "date": "2025-01-27",
            }
        ]
        mock_rss_parser_class.return_value = mock_parser

        fetcher = NewsFetcher(use_rss=True, use_scraping=False)
        articles = fetcher.fetch_from_rss(["https://example.com/feed"])

        assert len(articles) == 1
        assert "tickers" in articles[0]
        assert "category" in articles[0]

    def test_fetch_from_rss_disabled(self):
        """Test fetching from RSS when disabled."""
        fetcher = NewsFetcher(use_rss=False)
        with pytest.raises(NewsFetcherError):
            fetcher.fetch_from_rss(["https://example.com/feed"])

    def test_extract_tickers(self):
        """Test ticker extraction from article."""
        fetcher = NewsFetcher()
        article = {
            "title": "AAPL and MSFT stocks rise",
            "content": "Apple Inc (AAPL) and Microsoft (MSFT) saw gains today.",
        }
        tickers = fetcher._extract_tickers(article)
        assert "AAPL" in tickers
        assert "MSFT" in tickers

    def test_categorize_article(self):
        """Test article categorization."""
        fetcher = NewsFetcher()

        earnings_article = {
            "title": "Q1 Earnings Report",
            "content": "Quarterly earnings",
        }
        assert fetcher._categorize_article(earnings_article) == "earnings"

        market_article = {"title": "Stock Market Update", "content": "Trading activity"}
        assert fetcher._categorize_article(market_article) == "markets"

    def test_deduplicate_articles(self):
        """Test article deduplication."""
        fetcher = NewsFetcher()
        articles = [
            {"url": "https://example.com/article1", "title": "Article 1"},
            {"url": "https://example.com/article2", "title": "Article 2"},
            {"url": "https://example.com/article1", "title": "Duplicate"},
        ]
        unique = fetcher._deduplicate_articles(articles)
        assert len(unique) == 2

    def test_to_documents(self):
        """Test conversion to Document objects."""
        fetcher = NewsFetcher()
        articles = [
            {
                "title": "Test Article",
                "content": "Article content about AAPL",
                "url": "https://example.com/article",
                "source": "reuters",
                "author": "Author",
                "date": "2025-01-27",
                "tickers": ["AAPL"],
                "category": "markets",
            }
        ]
        documents = fetcher.to_documents(articles)
        assert len(documents) == 1
        assert documents[0].page_content.startswith("Test Article")
        assert documents[0].metadata["source"] == "reuters"
        assert documents[0].metadata["tickers"] == "AAPL"
