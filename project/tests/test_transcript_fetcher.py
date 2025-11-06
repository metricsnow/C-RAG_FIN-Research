"""
Unit tests for transcript fetcher module.
"""

from unittest.mock import Mock, patch

import pytest

from app.ingestion.transcript_fetcher import TranscriptFetcher, TranscriptFetcherError


class TestTranscriptFetcher:
    """Test cases for TranscriptFetcher."""

    def test_init(self):
        """Test fetcher initialization."""
        fetcher = TranscriptFetcher(use_web_scraping=False)
        assert fetcher.use_web_scraping is False
        assert fetcher.rate_limit_delay == 1.0

    def test_init_with_custom_rate_limit(self):
        """Test fetcher initialization with custom rate limit."""
        fetcher = TranscriptFetcher(rate_limit_delay=2.0, use_web_scraping=True)
        assert fetcher.rate_limit_delay == 2.0
        assert fetcher.use_web_scraping is True

    @patch("app.ingestion.transcript_fetcher.requests.Session")
    @patch("app.ingestion.transcript_fetcher.BeautifulSoup")
    def test_scrape_seeking_alpha_success(self, mock_soup, mock_session):
        """Test successful Seeking Alpha scraping."""
        # Mock HTML response
        mock_response = Mock()
        mock_response.text = (
            "<html><body><div class='transcript-content'>"
            "Test transcript</div></body></html>"
        )
        mock_response.raise_for_status = Mock()

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session_instance.headers = {}
        mock_session.return_value = mock_session_instance

        # Mock BeautifulSoup
        mock_soup_instance = Mock()
        mock_div = Mock()
        mock_div.get_text.return_value = "Speaker: Test content"
        mock_soup_instance.find.return_value = mock_div
        mock_soup.return_value = mock_soup_instance

        fetcher = TranscriptFetcher(use_web_scraping=True)
        fetcher.session = mock_session_instance

        result = fetcher._scrape_seeking_alpha_transcript("AAPL", "2025-01-15")

        assert result is not None
        assert result["ticker"] == "AAPL"
        assert result["source"] == "seeking_alpha"

    @patch("app.ingestion.transcript_fetcher.requests.Session")
    @patch("app.ingestion.transcript_fetcher.BeautifulSoup")
    def test_scrape_seeking_alpha_not_found(self, mock_soup, mock_session):
        """Test Seeking Alpha scraping when transcript not found."""
        mock_response = Mock()
        mock_response.text = "<html><body></body></html>"
        mock_response.raise_for_status = Mock()

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session_instance.headers = {}
        mock_session.return_value = mock_session_instance

        mock_soup_instance = Mock()
        mock_soup_instance.find.return_value = None
        mock_soup.return_value = mock_soup_instance

        fetcher = TranscriptFetcher(use_web_scraping=True)
        fetcher.session = mock_session_instance

        result = fetcher._scrape_seeking_alpha_transcript("AAPL")
        assert result is None

    @patch(
        "app.ingestion.transcript_fetcher."
        "TranscriptFetcher._scrape_seeking_alpha_transcript"
    )
    def test_fetch_transcript_seeking_alpha_success(self, mock_sa):
        """Test fetch_transcript with Seeking Alpha success."""
        mock_sa.return_value = {
            "ticker": "AAPL",
            "date": "2025-01-15",
            "transcript": "Test",
            "source": "seeking_alpha",
        }

        fetcher = TranscriptFetcher(use_web_scraping=True)
        result = fetcher.fetch_transcript("AAPL", "2025-01-15", source="seeking_alpha")

        assert result is not None
        assert result["ticker"] == "AAPL"
        assert result["source"] == "seeking_alpha"
        mock_sa.assert_called_once()

    @patch(
        "app.ingestion.transcript_fetcher."
        "TranscriptFetcher._scrape_seeking_alpha_transcript"
    )
    @patch(
        "app.ingestion.transcript_fetcher."
        "TranscriptFetcher._scrape_yahoo_finance_transcript"
    )
    def test_fetch_transcript_fallback(self, mock_yahoo, mock_sa):
        """Test fetch_transcript with fallback between sources."""
        mock_sa.return_value = None
        mock_yahoo.return_value = {
            "ticker": "AAPL",
            "date": "2025-01-15",
            "transcript": "Test",
            "source": "yahoo_finance",
        }

        fetcher = TranscriptFetcher(use_web_scraping=True)
        result = fetcher.fetch_transcript("AAPL", "2025-01-15")

        assert result is not None
        assert result["source"] == "yahoo_finance"

    @patch(
        "app.ingestion.transcript_fetcher."
        "TranscriptFetcher._scrape_seeking_alpha_transcript"
    )
    @patch(
        "app.ingestion.transcript_fetcher."
        "TranscriptFetcher._scrape_yahoo_finance_transcript"
    )
    def test_fetch_transcript_all_sources_fail(self, mock_yahoo, mock_sa):
        """Test fetch_transcript when all sources fail."""
        mock_sa.return_value = None
        mock_yahoo.return_value = None

        fetcher = TranscriptFetcher(use_web_scraping=True)

        with pytest.raises(TranscriptFetcherError):
            fetcher.fetch_transcript("AAPL", "2025-01-15")

    def test_fetch_transcript_web_scraping_disabled(self):
        """Test fetch_transcript when web scraping is disabled."""
        fetcher = TranscriptFetcher(use_web_scraping=False)

        with pytest.raises(TranscriptFetcherError, match="Web scraping is disabled"):
            fetcher.fetch_transcript("AAPL", "2025-01-15")

    def test_fetch_transcripts_by_date_range(self):
        """Test fetching transcripts for date range."""
        with patch.object(TranscriptFetcher, "fetch_transcript") as mock_fetch:
            mock_fetch.side_effect = [
                {"ticker": "AAPL", "date": "2025-01-15", "transcript": "Test1"},
                None,  # One date fails
                {"ticker": "AAPL", "date": "2025-01-17", "transcript": "Test2"},
            ]

            fetcher = TranscriptFetcher(use_web_scraping=False)
            results = fetcher.fetch_transcripts_by_date_range(
                "AAPL", "2025-01-15", "2025-01-17"
            )

            assert len(results) == 2
            assert results[0]["date"] == "2025-01-15"
            assert results[1]["date"] == "2025-01-17"
