"""
Unit tests for central bank fetcher module.
"""

from unittest.mock import Mock, patch

import pytest
from bs4 import BeautifulSoup

from app.ingestion.central_bank_fetcher import (
    CentralBankFetcher,
    CentralBankFetcherError,
)


class TestCentralBankFetcher:
    """Test cases for CentralBankFetcher."""

    def test_init(self):
        """Test fetcher initialization."""
        fetcher = CentralBankFetcher(rate_limit_delay=1.0, use_web_scraping=True)
        assert fetcher.rate_limit_delay == 1.0
        assert fetcher.use_web_scraping is True
        assert fetcher.session is not None

    def test_init_with_defaults(self):
        """Test fetcher initialization with defaults."""
        with patch("app.ingestion.central_bank_fetcher.config") as mock_config:
            mock_config.central_bank_rate_limit_seconds = 2.0
            fetcher = CentralBankFetcher()
            assert fetcher.rate_limit_delay == 2.0

    def test_apply_rate_limit(self):
        """Test rate limiting."""
        fetcher = CentralBankFetcher(rate_limit_delay=0.01)
        import time

        start = time.time()
        fetcher._apply_rate_limit()
        elapsed = time.time() - start
        assert elapsed >= 0.01

    def test_make_request_success(self):
        """Test successful HTTP request."""
        fetcher = CentralBankFetcher(rate_limit_delay=0.0)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.text = "<html><body>Test</body></html>"

        with patch.object(fetcher.session, "get", return_value=mock_response):
            response = fetcher._make_request("https://example.com")
            assert response == mock_response

    def test_make_request_failure(self):
        """Test failed HTTP request."""
        fetcher = CentralBankFetcher(rate_limit_delay=0.0)
        import requests

        with patch.object(
            fetcher.session,
            "get",
            side_effect=requests.exceptions.RequestException("Error"),
        ):
            with pytest.raises(CentralBankFetcherError):
                fetcher._make_request("https://example.com")

    def test_parse_html(self):
        """Test HTML parsing."""
        fetcher = CentralBankFetcher()
        html = "<html><body><p>Test</p></body></html>"
        soup = fetcher._parse_html(html)
        assert isinstance(soup, BeautifulSoup)
        assert soup.find("p").text == "Test"

    def test_parse_html_invalid(self):
        """Test HTML parsing with invalid HTML."""
        fetcher = CentralBankFetcher()
        # BeautifulSoup handles invalid HTML gracefully
        html = "<html><body><p>Test</body></html>"
        soup = fetcher._parse_html(html)
        assert isinstance(soup, BeautifulSoup)

    def test_extract_forward_guidance(self):
        """Test forward guidance extraction."""
        fetcher = CentralBankFetcher()
        content = (
            "The Committee will continue to monitor economic developments. "
            "Our forward guidance indicates that policy will remain accommodative. "
            "The policy path forward depends on data."
        )
        guidance = fetcher.extract_forward_guidance(content)
        assert len(guidance) > 0
        assert any("forward guidance" in g.lower() for g in guidance)
        assert any("policy path" in g.lower() for g in guidance)

    def test_extract_forward_guidance_no_guidance(self):
        """Test forward guidance extraction with no guidance."""
        fetcher = CentralBankFetcher()
        content = "This is a regular statement without forward guidance."
        guidance = fetcher.extract_forward_guidance(content)
        assert len(guidance) == 0

    def test_format_for_rag(self):
        """Test RAG formatting."""
        fetcher = CentralBankFetcher()
        communication = {
            "type": "fomc_statement",
            "bank": "Federal Reserve",
            "date": "2025-01-27",
            "title": "FOMC Statement",
            "content": "The Committee decided to maintain the target range.",
        }
        formatted = fetcher.format_for_rag(communication)
        assert "FOMC STATEMENT" in formatted
        assert "Federal Reserve" in formatted
        assert "2025-01-27" in formatted
        assert "FOMC Statement" in formatted
        assert "The Committee decided" in formatted

    def test_get_metadata(self):
        """Test metadata extraction."""
        fetcher = CentralBankFetcher()
        communication = {
            "type": "fomc_statement",
            "bank": "Federal Reserve",
            "date": "2025-01-27",
            "url": "https://example.com/statement",
            "title": "FOMC Statement",
            "content": "The Committee will maintain accommodative policy.",
        }
        metadata = fetcher.get_metadata(communication)
        assert metadata["source"] == "central_bank"
        assert metadata["type"] == "fomc_statement"
        assert metadata["bank"] == "Federal Reserve"
        assert metadata["date"] == "2025-01-27"
        assert metadata["url"] == "https://example.com/statement"
        assert metadata["has_forward_guidance"] is True
        assert metadata["forward_guidance_count"] > 0

    def test_to_documents(self):
        """Test document conversion."""
        fetcher = CentralBankFetcher()
        communications = [
            {
                "type": "fomc_statement",
                "bank": "Federal Reserve",
                "date": "2025-01-27",
                "title": "FOMC Statement",
                "content": "Test content",
                "url": "https://example.com",
            }
        ]
        documents = fetcher.to_documents(communications)
        assert len(documents) == 1
        assert documents[0].page_content
        assert documents[0].metadata["type"] == "fomc_statement"

    def test_to_documents_empty(self):
        """Test document conversion with empty list."""
        fetcher = CentralBankFetcher()
        documents = fetcher.to_documents([])
        assert len(documents) == 0

    def test_fetch_fomc_statements_disabled(self):
        """Test FOMC statements fetching when web scraping is disabled."""
        fetcher = CentralBankFetcher(use_web_scraping=False)
        with pytest.raises(CentralBankFetcherError):
            fetcher.fetch_fomc_statements()

    @patch("app.ingestion.central_bank_fetcher.CentralBankFetcher._make_request")
    def test_fetch_fomc_statements_success(self, mock_request):
        """Test successful FOMC statements fetching."""
        fetcher = CentralBankFetcher(rate_limit_delay=0.0, use_web_scraping=True)

        # Mock HTML response
        html_content = """
        <html>
        <body>
            <a href="/monetarypolicy/fomcstatement20250127.htm">
                January 27, 2025 Statement
            </a>
            <a href="/monetarypolicy/fomcstatement20250115.htm">
                January 15, 2025 Statement
            </a>
        </body>
        </html>
        """
        mock_response = Mock()
        mock_response.text = html_content

        # Mock statement page
        statement_html = """
        <html>
        <body>
            <div class="col">
                <p>FOMC Statement Content</p>
            </div>
        </body>
        </html>
        """
        mock_statement_response = Mock()
        mock_statement_response.text = statement_html

        # Setup mocks
        mock_request.side_effect = [
            mock_response,
            mock_statement_response,
            mock_statement_response,
        ]

        statements = fetcher.fetch_fomc_statements(limit=2)
        assert len(statements) > 0
        assert all(s["type"] == "fomc_statement" for s in statements)

    def test_fetch_fomc_minutes_disabled(self):
        """Test FOMC minutes fetching when web scraping is disabled."""
        fetcher = CentralBankFetcher(use_web_scraping=False)
        with pytest.raises(CentralBankFetcherError):
            fetcher.fetch_fomc_minutes()

    def test_fetch_fomc_press_conferences_disabled(self):
        """Test FOMC press conferences fetching when web scraping is disabled."""
        fetcher = CentralBankFetcher(use_web_scraping=False)
        with pytest.raises(CentralBankFetcherError):
            fetcher.fetch_fomc_press_conferences()

    def test_get_metadata_no_forward_guidance(self):
        """Test metadata extraction without forward guidance."""
        fetcher = CentralBankFetcher()
        communication = {
            "type": "fomc_statement",
            "bank": "Federal Reserve",
            "date": "2025-01-27",
            "url": "https://example.com",
            "title": "FOMC Statement",
            "content": "Regular statement without forward guidance keywords.",
        }
        metadata = fetcher.get_metadata(communication)
        assert metadata["has_forward_guidance"] is False
        assert metadata["forward_guidance_count"] == 0
