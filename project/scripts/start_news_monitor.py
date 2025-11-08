#!/usr/bin/env python3
"""
Script to start the automated news monitoring service.

Starts a background service that continuously monitors RSS feeds
and automatically ingests new articles.
"""

import argparse
import signal
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Imports after sys.path modification (required for scripts)
from app.services.news_monitor import NewsMonitor, NewsMonitorError  # noqa: E402
from app.utils.config import config  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

# Global monitor instance for signal handling
monitor: NewsMonitor = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    if monitor:
        try:
            monitor.stop()
        except Exception as e:
            logger.error(f"Error stopping monitor: {str(e)}")
    sys.exit(0)


def main():
    """Main function to start news monitoring service."""
    parser = argparse.ArgumentParser(
        description="Start automated news monitoring service"
    )
    parser.add_argument(
        "--feeds",
        nargs="+",
        help="RSS feed URLs to monitor (overrides config)",
        default=None,
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Polling interval in minutes (overrides config)",
        default=None,
    )
    parser.add_argument(
        "--collection",
        default="documents",
        help="ChromaDB collection name (default: documents)",
    )
    parser.add_argument(
        "--no-scraping",
        action="store_true",
        help="Disable full content scraping",
    )
    parser.add_argument(
        "--filter-tickers",
        nargs="+",
        help="Ticker symbols to filter (e.g., AAPL MSFT)",
        default=None,
    )
    parser.add_argument(
        "--filter-keywords",
        nargs="+",
        help="Keywords to filter (e.g., earnings revenue)",
        default=None,
    )
    parser.add_argument(
        "--filter-categories",
        nargs="+",
        help="Categories to filter (e.g., earnings markets)",
        default=None,
    )

    args = parser.parse_args()

    # Check if news monitoring is enabled
    if not config.news_monitor_enabled and not args.feeds:
        logger.error("News monitoring is disabled in configuration")
        logger.info("Set NEWS_MONITOR_ENABLED=true in .env or use --feeds argument")
        sys.exit(1)

    # Check if news is enabled
    if not config.news_enabled:
        logger.error("News integration is disabled in configuration")
        sys.exit(1)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Create monitor instance
        logger.info("Initializing news monitoring service")
        global monitor
        monitor = NewsMonitor(
            feed_urls=args.feeds,
            poll_interval_minutes=args.interval
            or config.news_monitor_poll_interval_minutes,
            collection_name=args.collection,
            enable_scraping=not args.no_scraping,
            filter_tickers=args.filter_tickers,
            filter_keywords=args.filter_keywords,
            filter_categories=args.filter_categories,
        )

        # Start monitoring service
        logger.info("Starting news monitoring service")
        monitor.start()

        # Print status
        logger.info("News monitoring service is running")
        logger.info(f"Monitoring {len(monitor.feed_urls)} feeds")
        logger.info(f"Polling interval: {monitor.poll_interval_minutes} minutes")
        logger.info("Press Ctrl+C to stop")

        # Keep service running
        try:
            while monitor.is_running:
                import time

                time.sleep(1)

                # Print stats periodically (every 5 minutes)
                stats = monitor.get_stats()
                if stats["total_polls"] > 0 and stats["total_polls"] % 5 == 0:
                    logger.info(
                        f"Stats: polls={stats['total_polls']}, "
                        f"processed={stats['total_articles_processed']}, "
                        f"ingested={stats['total_articles_ingested']}, "
                        f"errors={stats['total_errors']}"
                    )

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        finally:
            monitor.stop()
            logger.info("News monitoring service stopped")

    except NewsMonitorError as e:
        logger.error(f"News monitor error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
