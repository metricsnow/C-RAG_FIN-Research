"""
Unit tests for news scraper module.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.ingestion.news_scraper import NewsScraper, NewsScraperError


class TestNewsScraper:
    """Test cases for NewsScraper class."""

    def test_init(self):
        """Test NewsScraper initialization."""
        scraper = NewsScraper(
            rate_limit_seconds=3.0, timeout=60, max_retries=5, respect_robots_txt=False
        )
        assert scraper.rate_limit_seconds == 3.0
        assert scraper.timeout == 60
        assert scraper.max_retries == 5
        assert scraper.respect_robots_txt is False
        assert scraper.last_request_time is None

    @patch("app.ingestion.news_scraper.BeautifulSoup")
    @patch("app.ingestion.news_scraper.requests.Session")
    def test_scrape_article_success(self, mock_session_class, mock_bs4):
        """Test successful article scraping."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.content = (
            b"<html><body><h1>Test Article</h1><p>Content</p></body></html>"
        )
        mock_response.raise_for_status = MagicMock()

        # Mock session instance
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        mock_session.mount = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock BeautifulSoup
        mock_soup = MagicMock()
        mock_title = MagicMock()
        mock_title.get_text.return_value = "Test Article"
        mock_soup.select_one.return_value = mock_title
        mock_soup.select.return_value = [
            MagicMock(get_text=lambda strip=True: "Content")
        ]
        mock_soup.find.return_value = None
        mock_bs4.return_value = mock_soup

        scraper = NewsScraper()
        article = scraper.scrape_article("https://example.com/article")

        assert article is not None
        assert article["title"] == "Test Article"
        assert article["url"] == "https://example.com/article"

    @patch("app.ingestion.news_scraper.requests.Session")
    def test_scrape_article_http_error(self, mock_session_class):
        """Test article scraping with HTTP error."""
        # Mock session instance
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Connection error")
        mock_session.headers = {}
        mock_session.mount = MagicMock()
        mock_session_class.return_value = mock_session

        scraper = NewsScraper()
        with pytest.raises(NewsScraperError):
            scraper.scrape_article("https://example.com/article")

    def test_determine_source(self):
        """Test source determination from URL."""
        scraper = NewsScraper()

        assert scraper._determine_source("https://www.reuters.com/article") == "reuters"
        assert (
            scraper._determine_source("https://www.bloomberg.com/article")
            == "bloomberg"
        )
        assert scraper._determine_source("https://www.cnbc.com/article") == "cnbc"
        assert (
            scraper._determine_source("https://www.ft.com/article") == "financial_times"
        )
