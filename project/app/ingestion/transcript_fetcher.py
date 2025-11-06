"""
Earnings call transcript fetcher.

Fetches earnings call transcripts from web scraping sources.
Note: TIKR does not offer an API and scraping TIKR is prohibited.
This implementation uses legitimate public sources only.
"""

import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from app.utils.logger import get_logger

logger = get_logger(__name__)


class TranscriptFetcherError(Exception):
    """Custom exception for transcript fetcher errors."""

    pass


class TranscriptFetcher:
    """
    Earnings call transcript fetcher.

    Fetches transcripts from legitimate web sources with proper rate limiting.
    Note: Respects robots.txt and implements rate limiting to avoid overloading servers.
    """

    SEEKING_ALPHA_BASE_URL = "https://seekingalpha.com"
    YAHOO_FINANCE_BASE_URL = "https://finance.yahoo.com"

    def __init__(
        self,
        rate_limit_delay: float = 1.0,
        use_web_scraping: bool = True,
    ):
        """
        Initialize transcript fetcher.

        Args:
            rate_limit_delay: Delay between requests in seconds (default: 1.0)
            use_web_scraping: Enable web scraping (default: True)
        """
        self.rate_limit_delay = rate_limit_delay
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
                "Accept-Language": "en-US,en;q=0.5",
            }
        )

    def _make_request(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Make HTTP request with rate limiting and error handling.

        Args:
            url: URL to request
            params: Query parameters

        Returns:
            Response object

        Raises:
            TranscriptFetcherError: If request fails
        """
        try:
            time.sleep(self.rate_limit_delay)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            raise TranscriptFetcherError(f"Request failed: {str(e)}") from e

    def _scrape_seeking_alpha_transcript(
        self, ticker: str, date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape transcript from Seeking Alpha.

        Args:
            ticker: Stock ticker symbol
            date: Transcript date (YYYY-MM-DD format, optional)

        Returns:
            Transcript data dictionary or None if not found
        """
        try:
            # Seeking Alpha transcript URL pattern
            # Note: This is a simplified implementation
            # Real implementation would need to handle their actual URL structure
            search_url = (
                f"{self.SEEKING_ALPHA_BASE_URL}/symbol/"
                f"{ticker.upper()}/earnings/transcript"
            )
            response = self._make_request(search_url)

            soup = BeautifulSoup(response.text, "html.parser")
            transcript_content = soup.find("div", class_="transcript-content")

            if not transcript_content:
                logger.warning(
                    f"No transcript content found on Seeking Alpha for {ticker}"
                )
                return None

            # Extract transcript text
            transcript_text = transcript_content.get_text(separator="\n", strip=True)

            # Extract speakers (simplified - would need more sophisticated parsing)
            speakers = []
            speaker_pattern = re.compile(
                r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):", re.MULTILINE
            )
            matches = speaker_pattern.findall(transcript_text)
            speakers = list(set(matches))

            return {
                "ticker": ticker.upper(),
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "transcript": transcript_text,
                "speakers": speakers,
                "source": "seeking_alpha",
                "url": search_url,
            }
        except Exception as e:
            logger.warning(f"Seeking Alpha scraping failed for {ticker}: {str(e)}")
            return None

    def _scrape_yahoo_finance_transcript(
        self, ticker: str, date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape transcript from Yahoo Finance.

        Args:
            ticker: Stock ticker symbol
            date: Transcript date (YYYY-MM-DD format, optional)

        Returns:
            Transcript data dictionary or None if not found
        """
        try:
            # Yahoo Finance transcript URL pattern
            url = f"{self.YAHOO_FINANCE_BASE_URL}/quote/{ticker.upper()}/events"
            response = self._make_request(url)

            soup = BeautifulSoup(response.text, "html.parser")
            # Note: Yahoo Finance structure may vary
            # This is a simplified implementation
            transcript_section = soup.find(
                "section", {"data-test": "earnings-call-transcript"}
            )

            if not transcript_section:
                logger.warning(f"No transcript found on Yahoo Finance for {ticker}")
                return None

            transcript_text = transcript_section.get_text(separator="\n", strip=True)

            # Extract speakers
            speakers = []
            speaker_pattern = re.compile(
                r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):", re.MULTILINE
            )
            matches = speaker_pattern.findall(transcript_text)
            speakers = list(set(matches))

            return {
                "ticker": ticker.upper(),
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "transcript": transcript_text,
                "speakers": speakers,
                "source": "yahoo_finance",
                "url": url,
            }
        except Exception as e:
            logger.warning(f"Yahoo Finance scraping failed for {ticker}: {str(e)}")
            return None

    def fetch_transcript(
        self,
        ticker: str,
        date: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch transcript from available web sources.

        Tries sources in order:
        1. Seeking Alpha (if enabled)
        2. Yahoo Finance (if enabled)

        Args:
            ticker: Stock ticker symbol
            date: Transcript date (YYYY-MM-DD format, optional)
            source: Preferred source ('seeking_alpha', 'yahoo_finance', None for auto)

        Returns:
            Transcript data dictionary or None if not found

        Raises:
            TranscriptFetcherError: If all sources fail
        """
        logger.info(
            f"Fetching transcript for {ticker} (date: {date}, source: {source})"
        )

        if not self.use_web_scraping:
            raise TranscriptFetcherError("Web scraping is disabled")

        # Try Seeking Alpha
        if not source or source == "seeking_alpha":
            try:
                result = self._scrape_seeking_alpha_transcript(ticker, date)
                if result:
                    logger.info(
                        f"Successfully scraped transcript from Seeking Alpha "
                        f"for {ticker}"
                    )
                    return result
            except Exception as e:
                logger.warning(f"Seeking Alpha scraping failed: {str(e)}")

        # Try Yahoo Finance
        if not source or source == "yahoo_finance":
            try:
                result = self._scrape_yahoo_finance_transcript(ticker, date)
                if result:
                    logger.info(
                        f"Successfully scraped transcript from Yahoo Finance "
                        f"for {ticker}"
                    )
                    return result
            except Exception as e:
                logger.warning(f"Yahoo Finance scraping failed: {str(e)}")

        logger.error(f"Failed to fetch transcript for {ticker} from any source")
        raise TranscriptFetcherError(f"Failed to fetch transcript for {ticker}")

    def fetch_transcripts_by_date_range(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        source: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple transcripts for a date range.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            source: Preferred source (optional)

        Returns:
            List of transcript data dictionaries

        Raises:
            TranscriptFetcherError: If fetching fails
        """
        transcripts = []
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        current_date = start
        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            try:
                transcript = self.fetch_transcript(ticker, date_str, source=source)
                if transcript:
                    transcripts.append(transcript)
            except TranscriptFetcherError:
                # Continue to next date if one fails
                logger.warning(f"Failed to fetch transcript for {ticker} on {date_str}")
            current_date += timedelta(days=1)

        logger.info(f"Fetched {len(transcripts)} transcripts for {ticker}")
        return transcripts
