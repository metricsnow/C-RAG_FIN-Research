"""
Alternative data fetcher for LinkedIn job postings, supply chain data, and IPO data.

Fetches alternative data sources that provide insights into company hiring,
supply chain activity, and IPO/secondary offering information.
"""

import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from langchain_core.documents import Document

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import EDGAR fetcher for Form S-1
try:
    from app.ingestion.edgar_fetcher import EdgarFetcher

    EDGAR_FETCHER_AVAILABLE = True
except ImportError:
    EDGAR_FETCHER_AVAILABLE = False
    logger.warning("EDGAR fetcher not available. Form S-1 fetching will be limited.")


class AlternativeDataFetcherError(Exception):
    """Custom exception for alternative data fetcher errors."""

    pass


class AlternativeDataFetcher:
    """
    Alternative data fetcher.

    Fetches alternative data sources including:
    - LinkedIn job postings (hiring signals)
    - Supply chain data (port activity, shipping)
    - IPO/secondary offering data (Form S-1)
    """

    # Ticker symbol pattern
    TICKER_PATTERN = re.compile(r"\b([A-Z]{1,5})\b")

    def __init__(
        self,
        linkedin_enabled: bool = False,
        supply_chain_enabled: bool = False,
        ipo_enabled: bool = True,
        rate_limit_delay: float = 1.0,
    ):
        """
        Initialize alternative data fetcher.

        Args:
            linkedin_enabled: Whether to enable LinkedIn job postings
                (requires API/scraping)
            supply_chain_enabled: Whether to enable supply chain data (requires API)
            ipo_enabled: Whether to enable IPO/Form S-1 data (default: True, uses EDGAR)
            rate_limit_delay: Delay between requests in seconds (default: 1.0)
        """
        self.linkedin_enabled = linkedin_enabled
        self.supply_chain_enabled = supply_chain_enabled
        self.ipo_enabled = ipo_enabled
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()

        # Initialize EDGAR fetcher for Form S-1 (if enabled)
        self.edgar_fetcher = None
        if self.ipo_enabled and EDGAR_FETCHER_AVAILABLE:
            try:
                self.edgar_fetcher = EdgarFetcher(rate_limit_delay=rate_limit_delay)
                logger.info("EDGAR fetcher initialized for Form S-1 data")
            except Exception as e:
                logger.warning(f"Failed to initialize EDGAR fetcher: {str(e)}")
                self.ipo_enabled = False

        # LinkedIn API credentials (if available)
        import os

        self.linkedin_api_key = os.getenv("LINKEDIN_API_KEY")
        self.linkedin_base_url = os.getenv(
            "LINKEDIN_BASE_URL", "https://api.linkedin.com/v2"
        )

        if self.linkedin_enabled and not self.linkedin_api_key:
            logger.warning("LinkedIn API key not found. LinkedIn fetching disabled.")
            self.linkedin_enabled = False

        # Supply chain API credentials (if available)
        self.supply_chain_api_key = os.getenv("SUPPLY_CHAIN_API_KEY")
        self.supply_chain_base_url = os.getenv(
            "SUPPLY_CHAIN_BASE_URL", "https://api.supplychain.com"
        )

        if self.supply_chain_enabled and not self.supply_chain_api_key:
            logger.warning(
                "Supply chain API key not found. Supply chain fetching disabled."
            )
            self.supply_chain_enabled = False

    def _make_request(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with rate limiting.

        Args:
            url: URL to request
            headers: Optional headers to include

        Returns:
            JSON response as dictionary

        Raises:
            AlternativeDataFetcherError: If request fails
        """
        try:
            logger.debug(f"Making request to alternative data API: {url}")
            time.sleep(self.rate_limit_delay)  # Rate limiting

            request_headers = {"Accept": "application/json"}
            if headers:
                request_headers.update(headers)

            response = self.session.get(url, headers=request_headers, timeout=30)
            response.raise_for_status()
            logger.debug(f"Successfully fetched from alternative data API: {url}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Failed to fetch from alternative data API {url}: {str(e)}",
                exc_info=True,
            )
            raise AlternativeDataFetcherError(
                f"Failed to fetch from alternative data API: {str(e)}"
            ) from e

    def _extract_tickers(self, text: str) -> List[str]:
        """
        Extract ticker symbols from text.

        Args:
            text: Text to extract tickers from

        Returns:
            List of unique ticker symbols found
        """
        if not text:
            return []

        matches = self.TICKER_PATTERN.findall(text.upper())
        # Filter out common words
        common_words = {"THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL"}
        tickers = [
            ticker
            for ticker in set(matches)
            if ticker not in common_words and len(ticker) >= 1
        ]
        return sorted(tickers)

    def fetch_linkedin_jobs(
        self,
        company: Optional[str] = None,
        ticker: Optional[str] = None,
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """
        Fetch LinkedIn job postings for a company.

        Args:
            company: Company name (e.g., "Apple Inc.")
            ticker: Stock ticker symbol (e.g., "AAPL")
            limit: Maximum number of jobs to fetch (default: 25)

        Returns:
            List of job posting dictionaries

        Raises:
            AlternativeDataFetcherError: If fetching fails
        """
        if not self.linkedin_enabled:
            logger.warning("LinkedIn job fetching is disabled")
            return []

        try:
            # Example API call - actual implementation depends on
            # LinkedIn API documentation. Note: LinkedIn API requires
            # special access and may have restrictions
            url = f"{self.linkedin_base_url}/jobSearch"
            params = {"limit": limit}
            if company:
                params["company"] = company
            if ticker:
                params["ticker"] = ticker

            headers = {"Authorization": f"Bearer {self.linkedin_api_key}"}

            data = self._make_request(url, headers=headers)
            jobs = data.get("elements", [])

            job_list = []
            for job in jobs:
                job_data = {
                    "id": job.get("id", ""),
                    "title": job.get("title", ""),
                    "company": job.get("company", {}).get("name", company or "Unknown"),
                    "location": job.get("location", {}).get("name", ""),
                    "description": job.get("description", ""),
                    "posted_date": job.get("postedDate", datetime.now().isoformat()),
                    "url": job.get("url", ""),
                    "source": "linkedin",
                    "type": "job_posting",
                }

                # Extract tickers from job description
                full_text = f"{job_data['title']} {job_data['description']}"
                job_data["tickers"] = self._extract_tickers(full_text)

                job_list.append(job_data)

            logger.info(f"Fetched {len(job_list)} LinkedIn job postings")
            return job_list

        except Exception as e:
            logger.error(f"Failed to fetch LinkedIn jobs: {str(e)}", exc_info=True)
            raise AlternativeDataFetcherError(
                f"Failed to fetch LinkedIn jobs: {str(e)}"
            ) from e

    def fetch_supply_chain_data(
        self, ticker: Optional[str] = None, port: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch supply chain data (port activity, shipping).

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            port: Port name or code (optional)

        Returns:
            List of supply chain data dictionaries

        Raises:
            AlternativeDataFetcherError: If fetching fails
        """
        if not self.supply_chain_enabled:
            logger.warning("Supply chain data fetching is disabled")
            return []

        try:
            # Example API call - actual implementation depends on
            # supply chain API documentation
            url = f"{self.supply_chain_base_url}/activity"
            params = {}
            if ticker:
                params["ticker"] = ticker
            if port:
                params["port"] = port

            headers = {"Authorization": f"Bearer {self.supply_chain_api_key}"}

            data = self._make_request(url, headers=headers)
            activities = data.get("activities", [])

            activity_list = []
            for activity in activities:
                activity_data = {
                    "id": activity.get("id", ""),
                    "port": activity.get("port", {}).get("name", port or "Unknown"),
                    "vessel": activity.get("vessel", {}).get("name", ""),
                    "cargo": activity.get("cargo", ""),
                    "date": activity.get("date", datetime.now().isoformat()),
                    "ticker": ticker or activity.get("ticker", ""),
                    "source": "supply_chain",
                    "type": "supply_chain_activity",
                }

                activity_list.append(activity_data)

            logger.info(f"Fetched {len(activity_list)} supply chain activities")
            return activity_list

        except Exception as e:
            logger.error(f"Failed to fetch supply chain data: {str(e)}", exc_info=True)
            raise AlternativeDataFetcherError(
                f"Failed to fetch supply chain data: {str(e)}"
            ) from e

    def fetch_form_s1_filings(
        self, ticker: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch Form S-1 filings (IPO/secondary offerings) from SEC EDGAR.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            limit: Maximum number of filings to fetch (default: 10)

        Returns:
            List of Form S-1 filing dictionaries

        Raises:
            AlternativeDataFetcherError: If fetching fails
        """
        if not self.ipo_enabled or not self.edgar_fetcher:
            logger.warning(
                "Form S-1 fetching is disabled or EDGAR fetcher not available"
            )
            return []

        try:
            # Use EDGAR fetcher to get Form S-1 filings
            # Form S-1 is used for IPOs and secondary offerings
            filings = []

            if ticker:
                # Get company CIK from ticker
                cik = self.edgar_fetcher.get_company_cik(ticker)
                if not cik:
                    logger.warning(f"Could not find CIK for ticker {ticker}")
                    return []

                # Fetch recent Form S-1 filings
                recent_filings = self.edgar_fetcher.get_company_filings(
                    cik=cik, form_type="S-1", limit=limit
                )

                for filing in recent_filings:
                    filing_data = {
                        "accession_number": filing.get("accessionNumber", ""),
                        "filing_date": filing.get("filingDate", ""),
                        "form_type": filing.get("form", ""),
                        "ticker": ticker,
                        "cik": cik,
                        "source": "edgar",
                        "type": "form_s1",
                    }

                    # Get filing content if available
                    try:
                        filing_content = self.edgar_fetcher.get_filing_content(
                            accession_number=filing_data["accession_number"],
                            form_type="S-1",
                        )
                        if filing_content:
                            filing_data["content"] = filing_content.get("content", "")
                            filing_data["url"] = filing_content.get("url", "")
                    except Exception as e:
                        logger.warning(
                            f"Failed to fetch content for filing "
                            f"{filing_data['accession_number']}: {str(e)}"
                        )

                    filings.append(filing_data)
            else:
                # Fetch recent Form S-1 filings across all companies
                # This is a simplified approach - in practice,
                # you'd want to search by date range
                logger.info("Fetching recent Form S-1 filings (all companies)")
                # Note: This would require a more sophisticated search mechanism
                # For now, we'll return empty list if no ticker is provided
                pass

            logger.info(f"Fetched {len(filings)} Form S-1 filings")
            return filings

        except Exception as e:
            logger.error(f"Failed to fetch Form S-1 filings: {str(e)}", exc_info=True)
            raise AlternativeDataFetcherError(
                f"Failed to fetch Form S-1 filings: {str(e)}"
            ) from e

    def to_documents(self, data: List[Dict[str, Any]]) -> List[Document]:
        """
        Convert alternative data to LangChain Document objects.

        Args:
            data: List of alternative data dictionaries

        Returns:
            List of Document objects
        """
        documents = []
        for item in data:
            # Create document content based on type
            if item["type"] == "job_posting":
                content = f"Job Title: {item.get('title', '')}\n"
                content += f"Company: {item.get('company', '')}\n"
                content += f"Location: {item.get('location', '')}\n"
                content += f"\n{item.get('description', '')}"
            elif item["type"] == "supply_chain_activity":
                content = f"Port: {item.get('port', '')}\n"
                content += f"Vessel: {item.get('vessel', '')}\n"
                content += f"Cargo: {item.get('cargo', '')}\n"
                content += f"Date: {item.get('date', '')}"
            elif item["type"] == "form_s1":
                content = f"Form Type: {item.get('form_type', '')}\n"
                content += f"Filing Date: {item.get('filing_date', '')}\n"
                content += f"Ticker: {item.get('ticker', '')}\n"
                if item.get("content"):
                    content += f"\n{item.get('content', '')}"

            # Create metadata
            metadata = {
                "source": item.get("source", ""),
                "type": item.get("type", ""),
                "date": item.get("date")
                or item.get("filing_date", datetime.now().isoformat()),
            }

            # Add type-specific metadata
            if item.get("ticker"):
                metadata["ticker"] = item["ticker"]
            if item.get("url"):
                metadata["url"] = item["url"]
            if item.get("company"):
                metadata["company"] = item["company"]
            if item.get("port"):
                metadata["port"] = item["port"]
            if item.get("accession_number"):
                metadata["accession_number"] = item["accession_number"]
            if item.get("cik"):
                metadata["cik"] = item["cik"]

            document = Document(page_content=content, metadata=metadata)
            documents.append(document)

        return documents
