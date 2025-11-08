"""
Automated news monitoring service.

Continuously monitors RSS feeds and news sources, automatically ingesting
new articles and detecting relevant content based on configurable criteria.
"""

import threading
from datetime import datetime
from typing import Dict, List, Optional, Set

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.ingestion.pipeline import IngestionPipeline, IngestionPipelineError
from app.utils.config import config
from app.utils.logger import get_logger
from app.vector_db.chroma_store import ChromaStore

logger = get_logger(__name__)


class NewsMonitorError(Exception):
    """Custom exception for news monitor errors."""

    pass


class NewsMonitor:
    """
    Automated news monitoring service.

    Continuously monitors RSS feeds and automatically ingests new articles
    using a background scheduler. Supports configurable intervals, feed sources,
    and filtering criteria.
    """

    def __init__(
        self,
        feed_urls: Optional[List[str]] = None,
        poll_interval_minutes: int = 30,
        collection_name: str = "documents",
        enable_scraping: bool = True,
        filter_tickers: Optional[List[str]] = None,
        filter_keywords: Optional[List[str]] = None,
        filter_categories: Optional[List[str]] = None,
    ):
        """
        Initialize news monitoring service.

        Args:
            feed_urls: List of RSS feed URLs to monitor (default: from config)
            poll_interval_minutes: Polling interval in minutes (default: 30)
            collection_name: ChromaDB collection name (default: "documents")
            enable_scraping: Whether to scrape full article content (default: True)
            filter_tickers: Optional list of ticker symbols to filter (default: None)
            filter_keywords: Optional list of keywords to filter (default: None)
            filter_categories: Optional list of categories to filter (default: None)
        """
        # Configuration - parse feed URLs from config if string
        config_feeds = config.news_monitor_feeds
        if isinstance(config_feeds, str):
            config_feeds = [f.strip() for f in config_feeds.split(",") if f.strip()]
        elif config_feeds is None:
            config_feeds = []

        self.feed_urls = feed_urls or config_feeds
        if not self.feed_urls:
            logger.warning("No feed URLs configured for news monitoring")
            self.feed_urls = []

        self.poll_interval_minutes = poll_interval_minutes
        self.collection_name = collection_name
        self.enable_scraping = enable_scraping
        self.filter_tickers = filter_tickers or []
        self.filter_keywords = filter_keywords or []
        self.filter_categories = filter_categories or []

        # Service state
        self.scheduler: Optional[BackgroundScheduler] = None
        self.is_running = False
        self.is_paused = False
        self._shutdown_event = threading.Event()

        # Statistics
        self.stats = {
            "total_polls": 0,
            "total_articles_processed": 0,
            "total_articles_ingested": 0,
            "total_errors": 0,
            "last_poll_time": None,
            "last_poll_success": False,
            "start_time": None,
        }

        # Deduplication tracking
        self.processed_urls: Set[str] = set()
        self.feed_last_processed: Dict[str, datetime] = {}

        # Initialize pipeline
        try:
            logger.info("Initializing ingestion pipeline for news monitoring")
            self.pipeline = IngestionPipeline(collection_name=collection_name)
        except Exception as e:
            logger.error(f"Failed to initialize ingestion pipeline: {str(e)}")
            raise NewsMonitorError(
                f"Failed to initialize ingestion pipeline: {str(e)}"
            ) from e

        # Initialize ChromaDB store for deduplication
        try:
            logger.info("Initializing ChromaDB store for deduplication")
            self.chroma_store = ChromaStore(collection_name=collection_name)
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB store: {str(e)}")
            raise NewsMonitorError(
                f"Failed to initialize ChromaDB store: {str(e)}"
            ) from e

        logger.info(
            f"News monitor initialized: {len(self.feed_urls)} feeds, "
            f"interval={poll_interval_minutes} minutes"
        )

    def _check_article_exists(self, url: str) -> bool:
        """
        Check if article URL already exists in ChromaDB.

        Args:
            url: Article URL to check

        Returns:
            True if article exists, False otherwise
        """
        try:
            # Query ChromaDB for articles with this URL using metadata filter
            results = self.chroma_store.query_by_text(
                query_text=url[:50],  # Use first 50 chars as query
                n_results=10,  # Get more results to check
                where={"source_type": "news"},
            )

            # Check if any results have matching URL in metadata
            if results.get("metadatas"):
                for metadata in results["metadatas"]:
                    if metadata.get("url") == url:
                        return True

            return False
        except Exception as e:
            logger.warning(f"Error checking article existence: {str(e)}")
            # On error, assume article doesn't exist to avoid missing new articles
            return False

    def _should_process_article(self, article: Dict) -> bool:
        """
        Check if article should be processed based on filter criteria.

        Args:
            article: Article dictionary with metadata

        Returns:
            True if article should be processed, False otherwise
        """
        # If no filters, process all articles
        if (
            not self.filter_tickers
            and not self.filter_keywords
            and not self.filter_categories
        ):
            return True

        # Check ticker filter
        if self.filter_tickers:
            article_tickers = article.get("tickers", [])
            if isinstance(article_tickers, str):
                article_tickers = [t.strip() for t in article_tickers.split(",")]
            if not any(ticker in article_tickers for ticker in self.filter_tickers):
                return False

        # Check keyword filter
        if self.filter_keywords:
            title = article.get("title", "").lower()
            content = article.get("content", "").lower()
            text = f"{title} {content}"
            if not any(keyword.lower() in text for keyword in self.filter_keywords):
                return False

        # Check category filter
        if self.filter_categories:
            article_category = article.get("category", "").lower()
            if article_category not in [c.lower() for c in self.filter_categories]:
                return False

        return True

    def _poll_feeds(self) -> None:
        """
        Poll RSS feeds and ingest new articles.

        This method is called periodically by the scheduler.
        """
        if self.is_paused:
            logger.debug("News monitor is paused, skipping poll")
            return

        logger.info(f"Polling {len(self.feed_urls)} RSS feeds for new articles")
        self.stats["total_polls"] += 1
        self.stats["last_poll_time"] = datetime.now()

        try:
            # Process each feed
            total_processed = 0
            total_ingested = 0

            for feed_url in self.feed_urls:
                try:
                    logger.debug(f"Processing feed: {feed_url}")

                    # Fetch news from this feed
                    articles = self.pipeline.news_fetcher.fetch_from_rss([feed_url])

                    if not articles:
                        logger.debug(f"No articles found in feed: {feed_url}")
                        continue

                    # Filter and deduplicate articles
                    new_articles = []
                    for article in articles:
                        article_url = article.get("url", "")
                        if not article_url:
                            continue

                        # Check deduplication - first check in-memory cache
                        if article_url in self.processed_urls:
                            logger.debug(f"Article already processed: {article_url}")
                            continue

                        # Check if article exists in ChromaDB
                        if self._check_article_exists(article_url):
                            logger.debug(f"Article already in ChromaDB: {article_url}")
                            self.processed_urls.add(article_url)
                            continue

                        # Check filters
                        if not self._should_process_article(article):
                            title = article.get("title", "Unknown")
                            logger.debug(f"Article filtered out: {title}")
                            # Still mark as processed to avoid re-checking
                            self.processed_urls.add(article_url)
                            continue

                        new_articles.append(article)
                        self.processed_urls.add(article_url)

                    if not new_articles:
                        logger.debug(
                            f"No new articles to process from feed: {feed_url}"
                        )
                        continue

                    # Ingest new articles by URL
                    article_count = len(new_articles)
                    logger.info(
                        f"Ingesting {article_count} new articles from feed: {feed_url}"
                    )
                    try:
                        # Extract URLs from new articles
                        new_article_urls = [
                            article.get("url") for article in new_articles
                        ]
                        new_article_urls = [url for url in new_article_urls if url]

                        if new_article_urls:
                            ids = self.pipeline.process_news(
                                article_urls=new_article_urls,
                                enhance_with_scraping=self.enable_scraping,
                                store_embeddings=True,
                            )
                            ingested_count = len(ids)
                            total_ingested += ingested_count
                            total_processed += len(new_articles)

                            logger.info(
                                f"Successfully ingested {ingested_count} articles "
                                f"from feed: {feed_url}"
                            )
                        else:
                            logger.warning(
                                f"No valid URLs found in {article_count} new articles"
                            )
                    except IngestionPipelineError as e:
                        error_msg = str(e)
                        logger.error(
                            f"Failed to ingest articles from feed "
                            f"{feed_url}: {error_msg}"
                        )
                        self.stats["total_errors"] += 1
                        continue

                    # Update last processed time for this feed
                    self.feed_last_processed[feed_url] = datetime.now()

                except Exception as e:
                    logger.error(
                        f"Error processing feed {feed_url}: {str(e)}", exc_info=True
                    )
                    self.stats["total_errors"] += 1
                    continue

            # Update statistics
            self.stats["total_articles_processed"] += total_processed
            self.stats["total_articles_ingested"] += total_ingested
            self.stats["last_poll_success"] = True

            logger.info(
                f"Poll completed: processed={total_processed}, "
                f"ingested={total_ingested}, errors={self.stats['total_errors']}"
            )

        except Exception as e:
            logger.error(f"Error in feed polling: {str(e)}", exc_info=True)
            self.stats["total_errors"] += 1
            self.stats["last_poll_success"] = False

    def start(self) -> None:
        """
        Start the news monitoring service.

        Raises:
            NewsMonitorError: If service is already running or fails to start
        """
        if self.is_running:
            raise NewsMonitorError("News monitor is already running")

        if not self.feed_urls:
            raise NewsMonitorError("No feed URLs configured for monitoring")

        logger.info("Starting news monitoring service")
        try:
            # Create scheduler
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_job(
                func=self._poll_feeds,
                trigger=IntervalTrigger(minutes=self.poll_interval_minutes),
                id="news_monitor_poll",
                name="News Feed Polling",
                replace_existing=True,
            )

            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            self.stats["start_time"] = datetime.now()

            logger.info(
                f"News monitoring service started: "
                f"polling every {self.poll_interval_minutes} minutes"
            )

            # Perform initial poll
            logger.info("Performing initial feed poll")
            self._poll_feeds()

        except Exception as e:
            logger.error(f"Failed to start news monitoring service: {str(e)}")
            self.is_running = False
            raise NewsMonitorError(
                f"Failed to start news monitoring service: {str(e)}"
            ) from e

    def stop(self) -> None:
        """Stop the news monitoring service."""
        if not self.is_running:
            logger.warning("News monitor is not running")
            return

        logger.info("Stopping news monitoring service")
        try:
            if self.scheduler:
                self.scheduler.shutdown(wait=True)
            self.is_running = False
            self._shutdown_event.set()
            logger.info("News monitoring service stopped")
        except Exception as e:
            logger.error(f"Error stopping news monitoring service: {str(e)}")
            raise NewsMonitorError(
                f"Error stopping news monitoring service: {str(e)}"
            ) from e

    def pause(self) -> None:
        """Pause monitoring (scheduler continues but polls are skipped)."""
        if not self.is_running:
            raise NewsMonitorError("News monitor is not running")

        logger.info("Pausing news monitoring service")
        self.is_paused = True

    def resume(self) -> None:
        """Resume the news monitoring service."""
        if not self.is_running:
            raise NewsMonitorError("News monitor is not running")

        logger.info("Resuming news monitoring service")
        self.is_paused = False

    def get_stats(self) -> Dict:
        """
        Get monitoring service statistics.

        Returns:
            Dictionary with monitoring statistics
        """
        stats = self.stats.copy()
        if self.stats["start_time"]:
            uptime = datetime.now() - self.stats["start_time"]
            stats["uptime_seconds"] = uptime.total_seconds()
        else:
            stats["uptime_seconds"] = 0

        stats["is_running"] = self.is_running
        stats["is_paused"] = self.is_paused
        stats["feed_count"] = len(self.feed_urls)
        stats["processed_urls_count"] = len(self.processed_urls)

        return stats

    def health_check(self) -> Dict[str, bool]:
        """
        Perform health check on the monitoring service.

        Returns:
            Dictionary with health check results
        """
        health = {
            "service_running": self.is_running,
            "scheduler_running": (
                self.scheduler is not None and self.scheduler.running
            ),
            "pipeline_available": self.pipeline is not None,
            "chroma_store_available": self.chroma_store is not None,
            "feeds_configured": len(self.feed_urls) > 0,
        }

        return health
