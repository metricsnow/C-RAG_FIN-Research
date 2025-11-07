"""
ESG (Environmental, Social, Governance) data fetcher.

Fetches ESG ratings and data from various providers including
MSCI, Sustainalytics, and CDP (Carbon Disclosure Project).
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from langchain_core.documents import Document

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ESGFetcherError(Exception):
    """Custom exception for ESG fetcher errors."""

    pass


class ESGFetcher:
    """
    ESG data fetcher.

    Fetches ESG ratings and data from various providers.
    Note: Most ESG data providers require API keys or subscriptions.
    This implementation provides a framework for integration.
    """

    def __init__(
        self,
        msci_enabled: bool = False,
        sustainalytics_enabled: bool = False,
        cdp_enabled: bool = False,
        rate_limit_delay: float = 1.0,
    ):
        """
        Initialize ESG fetcher.

        Args:
            msci_enabled: Whether to enable MSCI ESG data
                (requires API key)
            sustainalytics_enabled: Whether to enable Sustainalytics data
                (requires API key)
            cdp_enabled: Whether to enable CDP data (requires API key)
            rate_limit_delay: Delay between requests in seconds (default: 1.0)
        """
        self.msci_enabled = msci_enabled
        self.sustainalytics_enabled = sustainalytics_enabled
        self.cdp_enabled = cdp_enabled
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()

        # Initialize API clients if credentials are available
        import os

        # MSCI ESG API (example - actual implementation depends on API documentation)
        self.msci_api_key = os.getenv("MSCI_ESG_API_KEY")
        self.msci_base_url = os.getenv("MSCI_ESG_BASE_URL", "https://api.msci.com")

        # Sustainalytics API (example - actual implementation
        # depends on API documentation)
        self.sustainalytics_api_key = os.getenv("SUSTAINALYTICS_API_KEY")
        self.sustainalytics_base_url = os.getenv(
            "SUSTAINALYTICS_BASE_URL", "https://api.sustainalytics.com"
        )

        # CDP API (example - actual implementation depends on API documentation)
        self.cdp_api_key = os.getenv("CDP_API_KEY")
        self.cdp_base_url = os.getenv("CDP_BASE_URL", "https://api.cdp.net")

        if self.msci_enabled and not self.msci_api_key:
            logger.warning("MSCI ESG API key not found. MSCI fetching disabled.")
            self.msci_enabled = False

        if self.sustainalytics_enabled and not self.sustainalytics_api_key:
            logger.warning(
                "Sustainalytics API key not found. Sustainalytics fetching disabled."
            )
            self.sustainalytics_enabled = False

        if self.cdp_enabled and not self.cdp_api_key:
            logger.warning("CDP API key not found. CDP fetching disabled.")
            self.cdp_enabled = False

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
            ESGFetcherError: If request fails
        """
        try:
            logger.debug(f"Making request to ESG API: {url}")
            time.sleep(self.rate_limit_delay)  # Rate limiting

            request_headers = {"Accept": "application/json"}
            if headers:
                request_headers.update(headers)

            response = self.session.get(url, headers=request_headers, timeout=30)
            response.raise_for_status()
            logger.debug(f"Successfully fetched from ESG API: {url}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch from ESG API {url}: {str(e)}", exc_info=True)
            raise ESGFetcherError(f"Failed to fetch from ESG API: {str(e)}") from e

    def fetch_msci_esg_rating(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch MSCI ESG rating for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")

        Returns:
            ESG rating data or None if not available

        Raises:
            ESGFetcherError: If fetching fails
        """
        if not self.msci_enabled:
            logger.warning("MSCI ESG fetching is disabled")
            return None

        try:
            # Example API call - actual implementation depends on MSCI API documentation
            url = f"{self.msci_base_url}/esg/ratings/{ticker}"
            headers = {"Authorization": f"Bearer {self.msci_api_key}"}

            data = self._make_request(url, headers=headers)

            return {
                "provider": "MSCI",
                "ticker": ticker,
                "rating": data.get("rating", ""),
                "score": data.get("score", 0),
                "category": data.get("category", ""),
                "last_updated": data.get("last_updated", datetime.now().isoformat()),
                "source": "msci_esg",
                "type": "esg_rating",
            }
        except Exception as e:
            logger.error(f"Failed to fetch MSCI ESG rating for {ticker}: {str(e)}")
            raise ESGFetcherError(f"Failed to fetch MSCI ESG rating: {str(e)}") from e

    def fetch_sustainalytics_rating(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch Sustainalytics ESG rating for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")

        Returns:
            ESG rating data or None if not available

        Raises:
            ESGFetcherError: If fetching fails
        """
        if not self.sustainalytics_enabled:
            logger.warning("Sustainalytics ESG fetching is disabled")
            return None

        try:
            # Example API call - actual implementation depends on
            # Sustainalytics API documentation
            url = f"{self.sustainalytics_base_url}/esg/ratings/{ticker}"
            headers = {"Authorization": f"Bearer {self.sustainalytics_api_key}"}

            data = self._make_request(url, headers=headers)

            return {
                "provider": "Sustainalytics",
                "ticker": ticker,
                "rating": data.get("rating", ""),
                "score": data.get("score", 0),
                "risk_level": data.get("risk_level", ""),
                "last_updated": data.get("last_updated", datetime.now().isoformat()),
                "source": "sustainalytics_esg",
                "type": "esg_rating",
            }
        except Exception as e:
            logger.error(
                f"Failed to fetch Sustainalytics ESG rating for {ticker}: {str(e)}"
            )
            raise ESGFetcherError(
                f"Failed to fetch Sustainalytics ESG rating: {str(e)}"
            ) from e

    def fetch_cdp_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch CDP (Carbon Disclosure Project) data for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")

        Returns:
            CDP data or None if not available

        Raises:
            ESGFetcherError: If fetching fails
        """
        if not self.cdp_enabled:
            logger.warning("CDP fetching is disabled")
            return None

        try:
            # Example API call - actual implementation depends on CDP API documentation
            url = f"{self.cdp_base_url}/companies/{ticker}"
            headers = {"Authorization": f"Bearer {self.cdp_api_key}"}

            data = self._make_request(url, headers=headers)

            return {
                "provider": "CDP",
                "ticker": ticker,
                "disclosure_score": data.get("disclosure_score", 0),
                "performance_score": data.get("performance_score", 0),
                "leadership_level": data.get("leadership_level", ""),
                "last_updated": data.get("last_updated", datetime.now().isoformat()),
                "source": "cdp_climate",
                "type": "esg_rating",
            }
        except Exception as e:
            logger.error(f"Failed to fetch CDP data for {ticker}: {str(e)}")
            raise ESGFetcherError(f"Failed to fetch CDP data: {str(e)}") from e

    def fetch_esg_data(
        self, tickers: List[str], providers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch ESG data for multiple tickers from specified providers.

        Args:
            tickers: List of ticker symbols
            providers: List of providers to use (["msci", "sustainalytics", "cdp"])
                If None, uses all enabled providers

        Returns:
            List of ESG data dictionaries

        Raises:
            ESGFetcherError: If fetching fails
        """
        if providers is None:
            providers = []
            if self.msci_enabled:
                providers.append("msci")
            if self.sustainalytics_enabled:
                providers.append("sustainalytics")
            if self.cdp_enabled:
                providers.append("cdp")

        if not providers:
            logger.warning("No ESG providers enabled")
            return []

        all_data = []
        for ticker in tickers:
            try:
                if "msci" in providers:
                    msci_data = self.fetch_msci_esg_rating(ticker)
                    if msci_data:
                        all_data.append(msci_data)

                if "sustainalytics" in providers:
                    sustainalytics_data = self.fetch_sustainalytics_rating(ticker)
                    if sustainalytics_data:
                        all_data.append(sustainalytics_data)

                if "cdp" in providers:
                    cdp_data = self.fetch_cdp_data(ticker)
                    if cdp_data:
                        all_data.append(cdp_data)

            except Exception as e:
                logger.warning(f"Failed to fetch ESG data for {ticker}: {str(e)}")
                continue

        logger.info(
            f"Fetched ESG data for {len(all_data)} ticker-provider combinations"
        )
        return all_data

    def to_documents(self, esg_data: List[Dict[str, Any]]) -> List[Document]:
        """
        Convert ESG data to LangChain Document objects.

        Args:
            esg_data: List of ESG data dictionaries

        Returns:
            List of Document objects
        """
        documents = []
        for data in esg_data:
            # Create document content
            content_parts = [
                f"Provider: {data.get('provider', 'Unknown')}",
                f"Ticker: {data.get('ticker', 'Unknown')}",
            ]

            if data.get("rating"):
                content_parts.append(f"Rating: {data.get('rating')}")
            if data.get("score"):
                content_parts.append(f"Score: {data.get('score')}")
            if data.get("risk_level"):
                content_parts.append(f"Risk Level: {data.get('risk_level')}")
            if data.get("category"):
                content_parts.append(f"Category: {data.get('category')}")
            if data.get("disclosure_score"):
                content_parts.append(
                    f"Disclosure Score: {data.get('disclosure_score')}"
                )
            if data.get("performance_score"):
                content_parts.append(
                    f"Performance Score: {data.get('performance_score')}"
                )
            if data.get("leadership_level"):
                content_parts.append(
                    f"Leadership Level: {data.get('leadership_level')}"
                )

            content = "\n".join(content_parts)

            # Create metadata
            metadata = {
                "source": data.get("source", ""),
                "type": data.get("type", "esg_rating"),
                "provider": data.get("provider", ""),
                "ticker": data.get("ticker", ""),
                "last_updated": data.get("last_updated", datetime.now().isoformat()),
            }

            # Add rating-specific metadata
            if data.get("rating"):
                metadata["rating"] = str(data["rating"])
            if data.get("score"):
                metadata["score"] = str(data["score"])
            if data.get("risk_level"):
                metadata["risk_level"] = str(data["risk_level"])
            if data.get("category"):
                metadata["category"] = str(data["category"])

            document = Document(page_content=content, metadata=metadata)
            documents.append(document)

        return documents
