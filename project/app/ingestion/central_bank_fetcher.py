"""
Central Bank Data Fetcher.

Fetches central bank communications including FOMC statements, meeting minutes,
press conference transcripts, interest rate decisions, and forward guidance
through web scraping and API access.
"""

import re
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CentralBankFetcherError(Exception):
    """Custom exception for central bank fetcher errors."""

    pass


class CentralBankFetcher:
    """
    Central Bank Data Fetcher.

    Fetches central bank communications from Federal Reserve (FOMC) and other
    central banks with proper rate limiting and error handling.
    """

    # Federal Reserve FOMC base URLs
    FOMC_BASE_URL = "https://www.federalreserve.gov"
    FOMC_STATEMENTS_URL = (
        "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    )
    FOMC_MINUTES_URL = (
        "https://www.federalreserve.gov/monetarypolicy/fomc_historical.htm"
    )
    FOMC_PRESS_CONFERENCES_URL = (
        "https://www.federalreserve.gov/monetarypolicy/fomcpresconf.htm"
    )

    # Forward guidance keywords
    FORWARD_GUIDANCE_KEYWORDS = [
        "forward guidance",
        "policy path",
        "future policy",
        "policy outlook",
        "monetary policy stance",
        "accommodative",
        "restrictive",
        "neutral",
        "policy normalization",
        "policy tightening",
        "policy easing",
    ]

    def __init__(
        self,
        rate_limit_delay: Optional[float] = None,
        use_web_scraping: bool = True,
    ):
        """
        Initialize central bank fetcher.

        Args:
            rate_limit_delay: Delay between requests in seconds (default: from config)
            use_web_scraping: Whether to use web scraping (default: True)
        """
        self.rate_limit_delay = (
            rate_limit_delay
            if rate_limit_delay is not None
            else config.central_bank_rate_limit_seconds
        )
        self.use_web_scraping = use_web_scraping
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                ),
            }
        )

        logger.info("Central Bank API client initialized")

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting delay between requests."""
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)

    def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """
        Make HTTP request with error handling.

        Args:
            url: URL to request
            params: Query parameters

        Returns:
            Response object

        Raises:
            CentralBankFetcherError: If request fails
        """
        try:
            self._apply_rate_limit()
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Central bank request failed: {str(e)}")
            raise CentralBankFetcherError(f"Request failed: {str(e)}") from e

    def _parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content with BeautifulSoup.

        Args:
            html_content: HTML content string

        Returns:
            BeautifulSoup object
        """
        try:
            return BeautifulSoup(html_content, "html.parser")
        except Exception as e:
            logger.error(f"HTML parsing failed: {str(e)}")
            raise CentralBankFetcherError(f"HTML parsing failed: {str(e)}") from e

    def fetch_fomc_statements(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch FOMC statements.

        Args:
            start_date: Start date (YYYY-MM-DD format, optional)
            end_date: End date (YYYY-MM-DD format, optional)
            limit: Maximum number of statements to fetch (optional)

        Returns:
            List of statement dictionaries

        Raises:
            CentralBankFetcherError: If fetching fails
        """
        if not self.use_web_scraping:
            raise CentralBankFetcherError("Web scraping is disabled")

        logger.info("Fetching FOMC statements")
        try:
            # Fetch the FOMC calendar page
            response = self._make_request(self.FOMC_STATEMENTS_URL)
            soup = self._parse_html(response.text)

            statements = []
            # Find statement links (simplified example - structure may vary)
            # FOMC website structure may change, so this needs to be adapted
            statement_links = soup.find_all(
                "a", href=re.compile(r"/monetarypolicy/fomc.*\.htm")
            )

            for link in statement_links[:limit] if limit else statement_links:
                try:
                    href = link.get("href", "")
                    if not href.startswith("http"):
                        href = f"{self.FOMC_BASE_URL}{href}"

                    # Fetch individual statement
                    statement_response = self._make_request(href)
                    statement_soup = self._parse_html(statement_response.text)

                    # Extract statement content
                    content_div = statement_soup.find(
                        "div", class_=re.compile(r"col|content|statement")
                    )
                    if not content_div:
                        content_div = statement_soup.find(
                            "div", id=re.compile(r"content|main")
                        )

                    content = (
                        content_div.get_text(separator="\n", strip=True)
                        if content_div
                        else ""
                    )

                    # Extract date from link text or page
                    date_text = link.get_text(strip=True)
                    date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", date_text)
                    if not date_match:
                        # Try to find date in the page
                        date_elem = statement_soup.find("time") or statement_soup.find(
                            "span", class_=re.compile(r"date")
                        )
                        if date_elem:
                            date_text = date_elem.get_text(strip=True)
                            date_match = re.search(
                                r"(\d{1,2}/\d{1,2}/\d{4})", date_text
                            )

                    statement_date = date_match.group(1) if date_match else None

                    if content:
                        statements.append(
                            {
                                "type": "fomc_statement",
                                "bank": "Federal Reserve",
                                "date": statement_date,
                                "url": href,
                                "content": content,
                                "title": link.get_text(strip=True),
                            }
                        )
                except Exception as e:
                    logger.warning(f"Failed to fetch statement from {href}: {str(e)}")
                    continue

            logger.info(f"Successfully fetched {len(statements)} FOMC statements")
            return statements

        except Exception as e:
            logger.error(f"Error fetching FOMC statements: {str(e)}", exc_info=True)
            raise CentralBankFetcherError(
                f"Error fetching FOMC statements: {str(e)}"
            ) from e

    def fetch_fomc_minutes(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch FOMC meeting minutes.

        Args:
            start_date: Start date (YYYY-MM-DD format, optional)
            end_date: End date (YYYY-MM-DD format, optional)
            limit: Maximum number of minutes to fetch (optional)

        Returns:
            List of minutes dictionaries

        Raises:
            CentralBankFetcherError: If fetching fails
        """
        if not self.use_web_scraping:
            raise CentralBankFetcherError("Web scraping is disabled")

        logger.info("Fetching FOMC meeting minutes")
        try:
            # Fetch the FOMC historical page
            response = self._make_request(self.FOMC_MINUTES_URL)
            soup = self._parse_html(response.text)

            minutes = []
            # Find minutes links
            minutes_links = soup.find_all(
                "a", href=re.compile(r"/monetarypolicy/fomcminutes.*\.htm")
            )

            for link in minutes_links[:limit] if limit else minutes_links:
                try:
                    href = link.get("href", "")
                    if not href.startswith("http"):
                        href = f"{self.FOMC_BASE_URL}{href}"

                    # Fetch individual minutes
                    minutes_response = self._make_request(href)
                    minutes_soup = self._parse_html(minutes_response.text)

                    # Extract minutes content
                    content_div = minutes_soup.find(
                        "div", class_=re.compile(r"col|content|minutes")
                    )
                    if not content_div:
                        content_div = minutes_soup.find(
                            "div", id=re.compile(r"content|main")
                        )

                    content = (
                        content_div.get_text(separator="\n", strip=True)
                        if content_div
                        else ""
                    )

                    # Extract date
                    date_text = link.get_text(strip=True)
                    date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", date_text)

                    minutes_date = date_match.group(1) if date_match else None

                    if content:
                        minutes.append(
                            {
                                "type": "fomc_minutes",
                                "bank": "Federal Reserve",
                                "date": minutes_date,
                                "url": href,
                                "content": content,
                                "title": link.get_text(strip=True),
                            }
                        )
                except Exception as e:
                    logger.warning(f"Failed to fetch minutes from {href}: {str(e)}")
                    continue

            logger.info(f"Successfully fetched {len(minutes)} FOMC meeting minutes")
            return minutes

        except Exception as e:
            logger.error(f"Error fetching FOMC minutes: {str(e)}", exc_info=True)
            raise CentralBankFetcherError(
                f"Error fetching FOMC minutes: {str(e)}"
            ) from e

    def fetch_fomc_press_conferences(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch FOMC press conference transcripts.

        Args:
            start_date: Start date (YYYY-MM-DD format, optional)
            end_date: End date (YYYY-MM-DD format, optional)
            limit: Maximum number of transcripts to fetch (optional)

        Returns:
            List of press conference dictionaries

        Raises:
            CentralBankFetcherError: If fetching fails
        """
        if not self.use_web_scraping:
            raise CentralBankFetcherError("Web scraping is disabled")

        logger.info("Fetching FOMC press conference transcripts")
        try:
            # Fetch the FOMC press conferences page
            response = self._make_request(self.FOMC_PRESS_CONFERENCES_URL)
            soup = self._parse_html(response.text)

            transcripts = []
            # Find transcript links
            transcript_links = soup.find_all(
                "a", href=re.compile(r"/monetarypolicy/fomcpresconf.*\.htm")
            )

            for link in transcript_links[:limit] if limit else transcript_links:
                try:
                    href = link.get("href", "")
                    if not href.startswith("http"):
                        href = f"{self.FOMC_BASE_URL}{href}"

                    # Fetch individual transcript
                    transcript_response = self._make_request(href)
                    transcript_soup = self._parse_html(transcript_response.text)

                    # Extract transcript content
                    content_div = transcript_soup.find(
                        "div", class_=re.compile(r"col|content|transcript")
                    )
                    if not content_div:
                        content_div = transcript_soup.find(
                            "div", id=re.compile(r"content|main")
                        )

                    content = (
                        content_div.get_text(separator="\n", strip=True)
                        if content_div
                        else ""
                    )

                    # Extract date
                    date_text = link.get_text(strip=True)
                    date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", date_text)

                    transcript_date = date_match.group(1) if date_match else None

                    if content:
                        transcripts.append(
                            {
                                "type": "fomc_press_conference",
                                "bank": "Federal Reserve",
                                "date": transcript_date,
                                "url": href,
                                "content": content,
                                "title": link.get_text(strip=True),
                            }
                        )
                except Exception as e:
                    logger.warning(f"Failed to fetch transcript from {href}: {str(e)}")
                    continue

            logger.info(
                f"Successfully fetched {len(transcripts)} "
                f"FOMC press conference transcripts"
            )
            return transcripts

        except Exception as e:
            logger.error(
                f"Error fetching FOMC press conferences: {str(e)}", exc_info=True
            )
            raise CentralBankFetcherError(
                f"Error fetching FOMC press conferences: {str(e)}"
            ) from e

    def extract_forward_guidance(self, content: str) -> List[str]:
        """
        Extract forward guidance statements from content.

        Args:
            content: Document content text

        Returns:
            List of forward guidance statements
        """
        guidance_statements = []

        # Find sentences containing forward guidance keywords
        sentences = re.split(r"[.!?]\s+", content)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for keyword in self.FORWARD_GUIDANCE_KEYWORDS:
                if keyword.lower() in sentence_lower:
                    guidance_statements.append(sentence.strip())
                    break

        return guidance_statements

    def format_for_rag(self, communication: Dict[str, Any]) -> str:
        """
        Format central bank communication for RAG ingestion.

        Args:
            communication: Communication dictionary from fetch methods

        Returns:
            Formatted text string for RAG
        """
        comm_type = communication.get("type", "unknown")
        bank = communication.get("bank", "Unknown")
        date = communication.get("date", "Unknown")
        title = communication.get("title", "")
        content = communication.get("content", "")

        # Extract forward guidance if available
        forward_guidance = self.extract_forward_guidance(content)
        guidance_text = (
            "\n".join([f"- {g}" for g in forward_guidance])
            if forward_guidance
            else "None identified"
        )

        # Build formatted text
        text_parts = [
            f"Central Bank Communication: {comm_type.upper()}",
            f"Bank: {bank}",
            f"Date: {date}",
            f"Title: {title}",
            "",
            "Forward Guidance Statements:",
            guidance_text,
            "",
            "Full Content:",
            content,
        ]

        return "\n".join(text_parts)

    def get_metadata(self, communication: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from central bank communication.

        Args:
            communication: Communication dictionary from fetch methods

        Returns:
            Metadata dictionary for ChromaDB storage
        """
        content = communication.get("content", "")
        forward_guidance = self.extract_forward_guidance(content)

        return {
            "source": "central_bank",
            "type": communication.get("type", ""),
            "bank": communication.get("bank", ""),
            "date": communication.get("date", ""),
            "url": communication.get("url", ""),
            "title": communication.get("title", ""),
            "has_forward_guidance": len(forward_guidance) > 0,
            "forward_guidance_count": len(forward_guidance),
        }

    def to_documents(self, communications: List[Dict[str, Any]]) -> List[Document]:
        """
        Convert communication dictionaries to LangChain Document objects.

        Args:
            communications: List of communication dictionaries

        Returns:
            List of Document objects with metadata
        """
        documents = []

        for comm in communications:
            # Format for RAG
            formatted_text = self.format_for_rag(comm)

            if not formatted_text.strip():
                continue

            # Get metadata
            metadata = self.get_metadata(comm)

            # Create Document
            doc = Document(page_content=formatted_text, metadata=metadata)
            documents.append(doc)

        logger.info(f"Converted {len(documents)} communications to Document objects")
        return documents
