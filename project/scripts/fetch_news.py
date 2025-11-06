#!/usr/bin/env python3
"""
Script to fetch and ingest financial news articles.

Fetches news from RSS feeds and/or scrapes articles from URLs,
then ingests them into the ChromaDB vector database.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Imports after sys.path modification (required for scripts)
from app.ingestion.pipeline import (  # noqa: E402
    IngestionPipeline,
    IngestionPipelineError,
)
from app.utils.config import config  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def main():
    """Main function to fetch and ingest news articles."""
    parser = argparse.ArgumentParser(
        description="Fetch and ingest financial news articles"
    )
    parser.add_argument(
        "--feeds",
        nargs="+",
        help="RSS feed URLs to parse",
        default=None,
    )
    parser.add_argument(
        "--urls",
        nargs="+",
        help="Article URLs to scrape",
        default=None,
    )
    parser.add_argument(
        "--no-scraping",
        action="store_true",
        help="Disable full content scraping for RSS articles",
    )
    parser.add_argument(
        "--no-store",
        action="store_true",
        help="Don't store embeddings in ChromaDB (for testing)",
    )
    parser.add_argument(
        "--collection",
        default="documents",
        help="ChromaDB collection name (default: documents)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.feeds and not args.urls:
        logger.error("Must provide at least --feeds or --urls")
        parser.print_help()
        sys.exit(1)

    # Check if news is enabled
    if not config.news_enabled:
        logger.error("News integration is disabled in configuration")
        sys.exit(1)

    try:
        # Create pipeline
        logger.info("Initializing ingestion pipeline")
        pipeline = IngestionPipeline(collection_name=args.collection)

        # Fetch and process news
        logger.info("Fetching and processing news articles")
        ids = pipeline.process_news(
            feed_urls=args.feeds,
            article_urls=args.urls,
            enhance_with_scraping=not args.no_scraping,
            store_embeddings=not args.no_store,
        )

        logger.info(f"Successfully processed {len(ids)} news article chunks")
        print(f"Processed {len(ids)} chunks from news articles")

    except IngestionPipelineError as e:
        logger.error(f"Pipeline error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
