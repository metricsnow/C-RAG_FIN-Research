"""
RSS feed parser for financial news aggregation.

Handles parsing of RSS feeds from financial news sources including
Reuters, Bloomberg, CNBC, Financial Times, and MarketWatch.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import feedparser

from app.utils.logger import get_logger

logger = get_logger(__name__)


class RSSParserError(Exception):
    """Custom exception for RSS parser errors."""

    pass


class RSSParser:
    """
    RSS feed parser for financial news sources.

    Supports parsing RSS feeds from multiple financial news sources
    with rate limiting and error handling.
    """

    # Default RSS feed URLs for financial news sources
    DEFAULT_FEEDS = {
        "reuters": "https://www.reuters.com/finance",
        "cnbc": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "marketwatch": "https://www.marketwatch.com/rss/topstories",
        "financial_times": "https://www.ft.com/?format=rss",
    }

    def __init__(
        self,
        rate_limit_seconds: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize RSS parser.

        Args:
            rate_limit_seconds: Minimum seconds between feed requests
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.rate_limit_seconds = rate_limit_seconds
        self.timeout = timeout
        self.max_retries = max_retries
        self.last_request_time: Optional[float] = None

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit_seconds:
                sleep_time = self.rate_limit_seconds - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        self.last_request_time = time.time()

    def parse_feed(self, feed_url: str) -> List[Dict]:
        """
        Parse RSS feed from URL.

        Args:
            feed_url: URL of the RSS feed

        Returns:
            List of article dictionaries with title, content, date, etc.

        Raises:
            RSSParserError: If parsing fails
        """
        self._rate_limit()

        logger.info(f"Parsing RSS feed: {feed_url}")

        try:
            # Parse feed using feedparser
            feed = feedparser.parse(feed_url)

            # Check for parsing errors
            if feed.bozo and feed.bozo_exception:
                logger.warning(
                    f"Feed parsing warning for {feed_url}: {feed.bozo_exception}"
                )

            # Extract feed metadata
            feed_title = feed.feed.get("title", "Unknown Feed")
            feed_link = feed.feed.get("link", feed_url)

            logger.debug(f"Feed '{feed_title}' contains {len(feed.entries)} entries")

            # Parse entries
            articles = []
            for entry in feed.entries:
                try:
                    article = self._parse_entry(entry, feed_title, feed_link)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse entry: {str(e)}")
                    continue

            logger.info(f"Successfully parsed {len(articles)} articles from {feed_url}")
            return articles

        except Exception as e:
            logger.error(
                f"Failed to parse RSS feed {feed_url}: {str(e)}", exc_info=True
            )
            raise RSSParserError(f"Failed to parse RSS feed: {str(e)}") from e

    def _parse_entry(self, entry, feed_title: str, feed_link: str) -> Optional[Dict]:
        """
        Parse a single RSS entry into article dictionary.

        Args:
            entry: feedparser entry object
            feed_title: Title of the feed
            feed_link: Link to the feed source

        Returns:
            Article dictionary or None if parsing fails
        """
        try:
            # Extract title
            title = entry.get("title", "").strip()
            if not title:
                logger.debug("Skipping entry with no title")
                return None

            # Extract link
            link = entry.get("link", "").strip()
            if not link:
                logger.debug(f"Skipping entry '{title}' with no link")
                return None

            # Extract description/content
            content = ""
            if hasattr(entry, "content") and entry.content:
                # Try to get full content
                content = entry.content[0].get("value", "")
            elif hasattr(entry, "summary"):
                content = entry.summary
            elif hasattr(entry, "description"):
                content = entry.description

            # Extract publication date
            published_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published_date = datetime(*entry.published_parsed[:6]).isoformat()
                except (ValueError, TypeError):
                    pass
            elif hasattr(entry, "published"):
                try:
                    # Try to parse published string
                    published_date = entry.published
                except Exception:
                    pass

            # Extract author
            author = ""
            if hasattr(entry, "author"):
                author = entry.author
            elif hasattr(entry, "author_detail") and entry.author_detail:
                author = entry.author_detail.get("name", "")

            # Determine source from feed URL or feed title
            source = self._determine_source(feed_link, feed_title)

            article = {
                "title": title,
                "content": content,
                "url": link,
                "source": source,
                "author": author,
                "date": published_date or datetime.now().isoformat(),
                "feed_title": feed_title,
                "feed_url": feed_link,
            }

            return article

        except Exception as e:
            logger.warning(f"Error parsing entry: {str(e)}")
            return None

    def _determine_source(self, feed_url: str, feed_title: str) -> str:
        """
        Determine news source from feed URL or title.

        Args:
            feed_url: Feed URL
            feed_title: Feed title

        Returns:
            Source name (reuters, cnbc, marketwatch, etc.)
        """
        url_lower = feed_url.lower()
        title_lower = feed_title.lower()

        if "reuters" in url_lower or "reuters" in title_lower:
            return "reuters"
        elif "cnbc" in url_lower or "cnbc" in title_lower:
            return "cnbc"
        elif "marketwatch" in url_lower or "marketwatch" in title_lower:
            return "marketwatch"
        elif "ft.com" in url_lower or "financial times" in title_lower:
            return "financial_times"
        elif "bloomberg" in url_lower or "bloomberg" in title_lower:
            return "bloomberg"
        else:
            # Extract domain name as fallback
            try:
                domain = urlparse(feed_url).netloc
                return domain.replace("www.", "").split(".")[0]
            except Exception:
                return "unknown"

    def parse_feeds(self, feed_urls: List[str]) -> List[Dict]:
        """
        Parse multiple RSS feeds.

        Args:
            feed_urls: List of RSS feed URLs

        Returns:
            Combined list of articles from all feeds
        """
        all_articles = []

        logger.info(f"Parsing {len(feed_urls)} RSS feeds")
        for idx, feed_url in enumerate(feed_urls, 1):
            try:
                logger.info(f"Processing feed {idx}/{len(feed_urls)}: {feed_url}")
                articles = self.parse_feed(feed_url)
                all_articles.extend(articles)
            except RSSParserError as e:
                logger.warning(f"Failed to parse feed {feed_url}: {str(e)}")
                continue

        logger.info(f"Total articles parsed: {len(all_articles)}")
        return all_articles

    def get_default_feeds(self) -> List[str]:
        """
        Get list of default RSS feed URLs.

        Returns:
            List of default RSS feed URLs
        """
        # Note: These are example URLs - actual RSS feed URLs may vary
        # Users should verify and update these URLs
        return list(self.DEFAULT_FEEDS.values())
