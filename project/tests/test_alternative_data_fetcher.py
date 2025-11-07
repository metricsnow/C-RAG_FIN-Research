"""
Tests for alternative data fetcher.

Tests LinkedIn jobs, supply chain data, and Form S-1 fetching.
"""

from app.ingestion.alternative_data_fetcher import AlternativeDataFetcher


class TestAlternativeDataFetcher:
    """Test suite for AlternativeDataFetcher."""

    def test_init_without_credentials(self):
        """Test initialization without API credentials."""
        fetcher = AlternativeDataFetcher(
            linkedin_enabled=False, supply_chain_enabled=False, ipo_enabled=True
        )
        assert not fetcher.linkedin_enabled
        assert not fetcher.supply_chain_enabled
        assert fetcher.ipo_enabled  # IPO uses EDGAR, no API key needed

    def test_extract_tickers(self):
        """Test ticker extraction from text."""
        fetcher = AlternativeDataFetcher(
            linkedin_enabled=False, supply_chain_enabled=False, ipo_enabled=False
        )
        text = "Looking for opportunities at AAPL and MSFT"
        tickers = fetcher._extract_tickers(text)
        assert "AAPL" in tickers
        assert "MSFT" in tickers

    def test_fetch_linkedin_jobs_disabled(self):
        """Test LinkedIn job fetching when disabled."""
        fetcher = AlternativeDataFetcher(linkedin_enabled=False)
        jobs = fetcher.fetch_linkedin_jobs(company="Apple Inc.")
        assert jobs == []

    def test_fetch_supply_chain_data_disabled(self):
        """Test supply chain data fetching when disabled."""
        fetcher = AlternativeDataFetcher(supply_chain_enabled=False)
        data = fetcher.fetch_supply_chain_data(ticker="AAPL")
        assert data == []

    def test_fetch_form_s1_filings_disabled(self):
        """Test Form S-1 fetching when disabled."""
        fetcher = AlternativeDataFetcher(ipo_enabled=False)
        filings = fetcher.fetch_form_s1_filings(ticker="AAPL")
        assert filings == []

    def test_to_documents_job_posting(self):
        """Test conversion of job postings to documents."""
        fetcher = AlternativeDataFetcher(
            linkedin_enabled=False, supply_chain_enabled=False, ipo_enabled=False
        )
        jobs = [
            {
                "id": "job123",
                "title": "Software Engineer",
                "company": "Apple Inc.",
                "location": "Cupertino, CA",
                "description": "Join our team at AAPL",
                "posted_date": "2025-01-27T12:00:00",
                "url": "https://linkedin.com/jobs/123",
                "source": "linkedin",
                "type": "job_posting",
                "tickers": ["AAPL"],
            }
        ]
        documents = fetcher.to_documents(jobs)
        assert len(documents) == 1
        assert "Apple Inc." in documents[0].page_content
        assert documents[0].metadata["type"] == "job_posting"
        assert documents[0].metadata["company"] == "Apple Inc."

    def test_to_documents_supply_chain(self):
        """Test conversion of supply chain data to documents."""
        fetcher = AlternativeDataFetcher(
            linkedin_enabled=False, supply_chain_enabled=False, ipo_enabled=False
        )
        activities = [
            {
                "id": "activity123",
                "port": "Los Angeles",
                "vessel": "Ship Name",
                "cargo": "Electronics",
                "date": "2025-01-27T12:00:00",
                "ticker": "AAPL",
                "source": "supply_chain",
                "type": "supply_chain_activity",
            }
        ]
        documents = fetcher.to_documents(activities)
        assert len(documents) == 1
        assert "Los Angeles" in documents[0].page_content
        assert documents[0].metadata["type"] == "supply_chain_activity"
        assert documents[0].metadata["ticker"] == "AAPL"

    def test_to_documents_form_s1(self):
        """Test conversion of Form S-1 filings to documents."""
        fetcher = AlternativeDataFetcher(
            linkedin_enabled=False, supply_chain_enabled=False, ipo_enabled=False
        )
        filings = [
            {
                "accession_number": "0001234567-25-000001",
                "filing_date": "2025-01-27",
                "form_type": "S-1",
                "ticker": "AAPL",
                "cik": "0000320193",
                "source": "edgar",
                "type": "form_s1",
                "content": "IPO filing content",
                "url": "https://sec.gov/Archives/edgar/data/320193/000123456725000001/",
            }
        ]
        documents = fetcher.to_documents(filings)
        assert len(documents) == 1
        assert "S-1" in documents[0].page_content
        assert documents[0].metadata["type"] == "form_s1"
        assert documents[0].metadata["ticker"] == "AAPL"
        assert documents[0].metadata["accession_number"] == "0001234567-25-000001"
