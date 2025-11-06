"""
News fetcher for financial news aggregation.

Combines RSS feed parsing and web scraping to collect financial news
articles from multiple sources with metadata extraction and ticker detection.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Set

from langchain_core.documents import Document

from app.ingestion.news_scraper import NewsScraper, NewsScraperError
from app.ingestion.rss_parser import RSSParser, RSSParserError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NewsFetcherError(Exception):
    """Custom exception for news fetcher errors."""

    pass


class NewsFetcher:
    """
    News fetcher combining RSS feeds and web scraping.

    Fetches financial news from RSS feeds and optionally scrapes
    full article content, extracts metadata, and detects ticker symbols.
    """

    # Common ticker symbol pattern (1-5 uppercase letters)
    TICKER_PATTERN = re.compile(r"\b([A-Z]{1,5})\b")

    # Common financial tickers to filter (avoid false positives)
    COMMON_WORDS = {
        "THE",
        "AND",
        "FOR",
        "ARE",
        "BUT",
        "NOT",
        "YOU",
        "ALL",
        "CAN",
        "HER",
        "WAS",
        "ONE",
        "OUR",
        "OUT",
        "DAY",
        "GET",
        "HAS",
        "HIM",
        "HIS",
        "HOW",
        "ITS",
        "MAY",
        "NEW",
        "NOW",
        "OLD",
        "SEE",
        "TWO",
        "WHO",
        "WAY",
        "USE",
    }

    def __init__(
        self,
        use_rss: bool = True,
        use_scraping: bool = True,
        rss_rate_limit: float = 1.0,
        scraping_rate_limit: float = 2.0,
        scrape_full_content: bool = True,
    ):
        """
        Initialize news fetcher.

        Args:
            use_rss: Whether to use RSS feeds (default: True)
            use_scraping: Whether to use web scraping (default: True)
            rss_rate_limit: Rate limit for RSS feed requests (seconds)
            scraping_rate_limit: Rate limit for web scraping (seconds)
            scrape_full_content: Whether to scrape full article content (default: True)
        """
        self.use_rss = use_rss
        self.use_scraping = use_scraping
        self.scrape_full_content = scrape_full_content

        # Initialize RSS parser
        self.rss_parser = (
            RSSParser(rate_limit_seconds=rss_rate_limit) if use_rss else None
        )

        # Initialize news scraper
        self.news_scraper = (
            NewsScraper(rate_limit_seconds=scraping_rate_limit)
            if use_scraping
            else None
        )

    def fetch_from_rss(self, feed_urls: List[str]) -> List[Dict]:
        """
        Fetch news articles from RSS feeds.

        Args:
            feed_urls: List of RSS feed URLs

        Returns:
            List of article dictionaries

        Raises:
            NewsFetcherError: If fetching fails
        """
        if not self.use_rss or self.rss_parser is None:
            raise NewsFetcherError("RSS parsing is disabled")

        logger.info(f"Fetching news from {len(feed_urls)} RSS feeds")
        try:
            articles = self.rss_parser.parse_feeds(feed_urls)

            # Enhance articles with ticker detection and metadata
            for article in articles:
                article["tickers"] = self._extract_tickers(article)
                article["category"] = self._categorize_article(article)

            return articles

        except RSSParserError as e:
            logger.error(f"RSS parsing failed: {str(e)}")
            raise NewsFetcherError(f"RSS parsing failed: {str(e)}") from e

    def fetch_from_urls(self, article_urls: List[str]) -> List[Dict]:
        """
        Fetch news articles by scraping URLs.

        Args:
            article_urls: List of article URLs to scrape

        Returns:
            List of article dictionaries

        Raises:
            NewsFetcherError: If fetching fails
        """
        if not self.use_scraping or self.news_scraper is None:
            raise NewsFetcherError("Web scraping is disabled")

        logger.info(f"Scraping {len(article_urls)} articles")
        try:
            articles = self.news_scraper.scrape_articles(article_urls)

            # Enhance articles with ticker detection and metadata
            for article in articles:
                article["tickers"] = self._extract_tickers(article)
                article["category"] = self._categorize_article(article)

            return articles

        except NewsScraperError as e:
            logger.error(f"Web scraping failed: {str(e)}")
            raise NewsFetcherError(f"Web scraping failed: {str(e)}") from e

    def fetch_news(
        self,
        feed_urls: Optional[List[str]] = None,
        article_urls: Optional[List[str]] = None,
        enhance_with_scraping: bool = True,
    ) -> List[Dict]:
        """
        Fetch news articles from RSS feeds and/or URLs.

        Args:
            feed_urls: List of RSS feed URLs (optional)
            article_urls: List of article URLs to scrape (optional)
            enhance_with_scraping: Whether to scrape full content for RSS articles

        Returns:
            List of article dictionaries

        Raises:
            NewsFetcherError: If fetching fails
        """
        all_articles = []

        # Fetch from RSS feeds
        if feed_urls and self.use_rss:
            try:
                rss_articles = self.fetch_from_rss(feed_urls)
                all_articles.extend(rss_articles)

                # Optionally scrape full content for RSS articles
                if (
                    enhance_with_scraping
                    and self.scrape_full_content
                    and self.use_scraping
                ):
                    logger.info("Enhancing RSS articles with full content scraping")
                    for article in rss_articles:
                        if article.get("url"):
                            try:
                                scraped = self.news_scraper.scrape_article(
                                    article["url"]
                                )
                                if scraped and scraped.get("content"):
                                    # Merge scraped content
                                    article["content"] = scraped["content"]
                                    if scraped.get("author"):
                                        article["author"] = scraped["author"]
                                    if scraped.get("date"):
                                        article["date"] = scraped["date"]
                            except Exception as e:
                                logger.debug(
                                    f"Failed to enhance article "
                                    f"{article['url']}: {str(e)}"
                                )
                                continue

            except NewsFetcherError as e:
                logger.warning(f"RSS fetching failed: {str(e)}")

        # Fetch from direct URLs
        if article_urls and self.use_scraping:
            try:
                scraped_articles = self.fetch_from_urls(article_urls)
                all_articles.extend(scraped_articles)
            except NewsFetcherError as e:
                logger.warning(f"URL scraping failed: {str(e)}")

        # Remove duplicates based on URL
        unique_articles = self._deduplicate_articles(all_articles)

        logger.info(f"Total unique articles fetched: {len(unique_articles)}")
        return unique_articles

    def _extract_tickers(self, article: Dict) -> List[str]:
        """
        Extract ticker symbols mentioned in article.

        Args:
            article: Article dictionary

        Returns:
            List of ticker symbols found
        """
        text = f"{article.get('title', '')} {article.get('content', '')}"
        text = text.upper()

        # Find potential tickers
        potential_tickers = set(self.TICKER_PATTERN.findall(text))

        # Filter out common words and validate
        tickers = []
        for ticker in potential_tickers:
            if (
                len(ticker) >= 1
                and len(ticker) <= 5
                and ticker not in self.COMMON_WORDS
                and ticker.isalpha()
            ):
                tickers.append(ticker)

        return sorted(set(tickers))

    def _categorize_article(self, article: Dict) -> str:
        """
        Categorize article based on content.

        Args:
            article: Article dictionary

        Returns:
            Article category (earnings, markets, analysis, etc.)
        """
        text = f"{article.get('title', '')} {article.get('content', '')}".lower()

        if any(
            word in text for word in ["earnings", "quarterly", "q1", "q2", "q3", "q4"]
        ):
            return "earnings"
        elif any(word in text for word in ["market", "trading", "stock", "shares"]):
            return "markets"
        elif any(
            word in text for word in ["analysis", "forecast", "outlook", "prediction"]
        ):
            return "analysis"
        elif any(
            word in text for word in ["merger", "acquisition", "deal", "takeover"]
        ):
            return "m&a"
        elif any(
            word in text for word in ["ipo", "initial public offering", "listing"]
        ):
            return "ipo"
        else:
            return "general"

    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Remove duplicate articles based on URL.

        Args:
            articles: List of article dictionaries

        Returns:
            Deduplicated list of articles
        """
        seen_urls: Set[str] = set()
        unique_articles = []

        for article in articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)

        return unique_articles

    def to_documents(self, articles: List[Dict]) -> List[Document]:
        """
        Convert article dictionaries to LangChain Document objects.

        Args:
            articles: List of article dictionaries

        Returns:
            List of Document objects with metadata
        """
        documents = []

        for article in articles:
            # Combine title and content
            content = f"{article.get('title', '')}\n\n{article.get('content', '')}"
            content = content.strip()

            if not content:
                continue

            # Create metadata
            metadata = {
                "source": article.get("source", "unknown"),
                "url": article.get("url", ""),
                "date": article.get("date", datetime.now().isoformat()),
                "author": article.get("author", ""),
                "tickers": ", ".join(article.get("tickers", [])),
                "category": article.get("category", "general"),
                "type": "news_article",
                "feed_title": article.get("feed_title", ""),
            }

            # Create Document
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)

        logger.info(f"Converted {len(documents)} articles to Document objects")
        return documents
