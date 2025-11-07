"""
Tests for ESG data fetcher.

Tests ESG data fetching from MSCI, Sustainalytics, and CDP.
"""

from app.ingestion.esg_fetcher import ESGFetcher


class TestESGFetcher:
    """Test suite for ESGFetcher."""

    def test_init_without_credentials(self):
        """Test initialization without API credentials."""
        fetcher = ESGFetcher(
            msci_enabled=False, sustainalytics_enabled=False, cdp_enabled=False
        )
        assert not fetcher.msci_enabled
        assert not fetcher.sustainalytics_enabled
        assert not fetcher.cdp_enabled

    def test_fetch_msci_esg_rating_disabled(self):
        """Test MSCI ESG fetching when disabled."""
        fetcher = ESGFetcher(msci_enabled=False)
        rating = fetcher.fetch_msci_esg_rating("AAPL")
        assert rating is None

    def test_fetch_sustainalytics_rating_disabled(self):
        """Test Sustainalytics fetching when disabled."""
        fetcher = ESGFetcher(sustainalytics_enabled=False)
        rating = fetcher.fetch_sustainalytics_rating("AAPL")
        assert rating is None

    def test_fetch_cdp_data_disabled(self):
        """Test CDP fetching when disabled."""
        fetcher = ESGFetcher(cdp_enabled=False)
        data = fetcher.fetch_cdp_data("AAPL")
        assert data is None

    def test_fetch_esg_data_no_providers(self):
        """Test ESG data fetching with no providers enabled."""
        fetcher = ESGFetcher(
            msci_enabled=False, sustainalytics_enabled=False, cdp_enabled=False
        )
        data = fetcher.fetch_esg_data(tickers=["AAPL"])
        assert data == []

    def test_to_documents(self):
        """Test conversion of ESG data to documents."""
        fetcher = ESGFetcher(
            msci_enabled=False, sustainalytics_enabled=False, cdp_enabled=False
        )
        esg_data = [
            {
                "provider": "MSCI",
                "ticker": "AAPL",
                "rating": "AAA",
                "score": 85,
                "category": "Technology",
                "last_updated": "2025-01-27T12:00:00",
                "source": "msci_esg",
                "type": "esg_rating",
            }
        ]
        documents = fetcher.to_documents(esg_data)
        assert len(documents) == 1
        assert "AAPL" in documents[0].page_content
        assert documents[0].metadata["provider"] == "MSCI"
        assert documents[0].metadata["ticker"] == "AAPL"
        assert documents[0].metadata["rating"] == "AAA"

    def test_to_documents_multiple_providers(self):
        """Test document conversion with multiple providers."""
        fetcher = ESGFetcher(
            msci_enabled=False, sustainalytics_enabled=False, cdp_enabled=False
        )
        esg_data = [
            {
                "provider": "MSCI",
                "ticker": "AAPL",
                "rating": "AAA",
                "score": 85,
                "source": "msci_esg",
                "type": "esg_rating",
                "last_updated": "2025-01-27T12:00:00",
            },
            {
                "provider": "Sustainalytics",
                "ticker": "AAPL",
                "rating": "Low Risk",
                "score": 20,
                "risk_level": "Low",
                "source": "sustainalytics_esg",
                "type": "esg_rating",
                "last_updated": "2025-01-27T12:00:00",
            },
        ]
        documents = fetcher.to_documents(esg_data)
        assert len(documents) == 2
        assert all(doc.metadata["ticker"] == "AAPL" for doc in documents)
