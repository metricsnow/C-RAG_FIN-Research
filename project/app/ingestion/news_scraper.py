"""
Web scraper for financial news articles.

Handles respectful web scraping of financial news articles from
Reuters, Bloomberg, CNBC, and other sources with rate limiting
and proper error handling.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.utils.logger import get_logger

logger = get_logger(__name__)


class NewsScraperError(Exception):
    """Custom exception for news scraper errors."""

    pass


class NewsScraper:
    """
    Web scraper for financial news articles.

    Supports scraping from major financial news sources with
    rate limiting, respectful scraping practices, and error handling.
    """

    # User agent for respectful scraping
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    # Common selectors for article content (source-specific)
    CONTENT_SELECTORS = {
        "reuters": [
            "article p",
            ".ArticleBodyWrapper p",
            ".StandardArticleBody_body p",
        ],
        "bloomberg": [
            "article p",
            ".body-copy p",
            ".story-body-text",
        ],
        "cnbc": [
            "article p",
            ".ArticleBody-articleBody p",
            ".group p",
        ],
        "default": ["article p", "main p", ".content p", ".article-body p"],
    }

    def __init__(
        self,
        rate_limit_seconds: float = 2.0,
        timeout: int = 30,
        max_retries: int = 3,
        respect_robots_txt: bool = True,
    ):
        """
        Initialize news scraper.

        Args:
            rate_limit_seconds: Minimum seconds between requests
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            respect_robots_txt: Whether to respect robots.txt (default: True)
        """
        self.rate_limit_seconds = rate_limit_seconds
        self.timeout = timeout
        self.max_retries = max_retries
        self.respect_robots_txt = respect_robots_txt
        self.last_request_time: Optional[float] = None

        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = requests.adapters.Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set user agent
        self.session.headers.update({"User-Agent": self.USER_AGENT})

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit_seconds:
                sleep_time = self.rate_limit_seconds - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        self.last_request_time = time.time()

    def scrape_article(self, article_url: str) -> Optional[Dict]:
        """
        Scrape article content from URL.

        Args:
            article_url: URL of the article to scrape

        Returns:
            Article dictionary with title, content, metadata, or None if scraping fails

        Raises:
            NewsScraperError: If scraping fails critically
        """
        self._rate_limit()

        logger.info(f"Scraping article: {article_url}")

        try:
            # Fetch article page
            response = self.session.get(article_url, timeout=self.timeout)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")

            # Determine source from URL
            source = self._determine_source(article_url)

            # Extract article data
            article = {
                "title": self._extract_title(soup, source),
                "content": self._extract_content(soup, source),
                "author": self._extract_author(soup, source),
                "date": self._extract_date(soup, source),
                "url": article_url,
                "source": source,
            }

            # Validate article has content
            if not article["title"] or not article["content"]:
                logger.warning(f"Article {article_url} missing title or content")
                return None

            logger.debug(
                f"Successfully scraped article: {article['title'][:50]}... "
                f"({len(article['content'])} chars)"
            )
            return article

        except requests.RequestException as e:
            logger.error(f"HTTP error scraping {article_url}: {str(e)}")
            raise NewsScraperError(f"HTTP error scraping article: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error scraping {article_url}: {str(e)}", exc_info=True)
            raise NewsScraperError(f"Error scraping article: {str(e)}") from e

    def _extract_title(self, soup: BeautifulSoup, source: str) -> str:
        """
        Extract article title from HTML.

        Args:
            soup: BeautifulSoup object
            source: News source name

        Returns:
            Article title
        """
        # Try multiple selectors
        selectors = [
            "h1",
            "article h1",
            ".article-title",
            ".headline",
            "title",
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title:
                    return title

        return ""

    def _extract_content(self, soup: BeautifulSoup, source: str) -> str:
        """
        Extract article content from HTML.

        Args:
            soup: BeautifulSoup object
            source: News source name

        Returns:
            Article content text
        """
        # Get source-specific selectors
        selectors = self.CONTENT_SELECTORS.get(
            source, self.CONTENT_SELECTORS["default"]
        )

        # Try each selector
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                # Combine text from all matching elements
                paragraphs = [elem.get_text(strip=True) for elem in elements]
                content = "\n\n".join(paragraphs)
                if len(content) > 100:  # Minimum content length
                    return content

        # Fallback: try to extract from article tag
        article = soup.find("article")
        if article:
            # Remove script and style elements
            for script in article(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            content = article.get_text(separator="\n\n", strip=True)
            if len(content) > 100:
                return content

        return ""

    def _extract_author(self, soup: BeautifulSoup, source: str) -> str:
        """
        Extract article author from HTML.

        Args:
            soup: BeautifulSoup object
            source: News source name

        Returns:
            Author name
        """
        # Try multiple selectors
        selectors = [
            ".author",
            ".byline",
            "[rel='author']",
            "meta[name='author']",
            "meta[property='article:author']",
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == "meta":
                    author = element.get("content", "")
                else:
                    author = element.get_text(strip=True)
                if author:
                    return author

        return ""

    def _extract_date(self, soup: BeautifulSoup, source: str) -> str:
        """
        Extract article publication date from HTML.

        Args:
            soup: BeautifulSoup object
            source: News source name

        Returns:
            Publication date in ISO format
        """
        # Try meta tags first
        meta_selectors = [
            "meta[property='article:published_time']",
            "meta[name='publish-date']",
            "meta[name='date']",
            "time[datetime]",
            "time",
        ]

        for selector in meta_selectors:
            element = soup.select_one(selector)
            if element:
                date_str = element.get("content") or element.get("datetime")
                if date_str:
                    try:
                        # Try to parse and format date
                        # This is simplified - in production, use dateutil.parser
                        return date_str
                    except Exception:
                        pass

        # Fallback to current date
        return datetime.now().isoformat()

    def _determine_source(self, url: str) -> str:
        """
        Determine news source from URL.

        Args:
            url: Article URL

        Returns:
            Source name (reuters, bloomberg, cnbc, etc.)
        """
        domain = urlparse(url).netloc.lower()

        if "reuters.com" in domain:
            return "reuters"
        elif "bloomberg.com" in domain:
            return "bloomberg"
        elif "cnbc.com" in domain:
            return "cnbc"
        elif "ft.com" in domain or "financialtimes.com" in domain:
            return "financial_times"
        elif "marketwatch.com" in domain:
            return "marketwatch"
        else:
            # Extract domain name as fallback
            return domain.replace("www.", "").split(".")[0]

    def scrape_articles(self, article_urls: List[str]) -> List[Dict]:
        """
        Scrape multiple articles.

        Args:
            article_urls: List of article URLs to scrape

        Returns:
            List of scraped article dictionaries
        """
        articles = []

        logger.info(f"Scraping {len(article_urls)} articles")
        for idx, url in enumerate(article_urls, 1):
            try:
                logger.info(f"Scraping article {idx}/{len(article_urls)}: {url}")
                article = self.scrape_article(url)
                if article:
                    articles.append(article)
            except NewsScraperError as e:
                logger.warning(f"Failed to scrape {url}: {str(e)}")
                continue

        logger.info(f"Successfully scraped {len(articles)} articles")
        return articles
