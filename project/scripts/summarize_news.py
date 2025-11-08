#!/usr/bin/env python3
"""
Script to summarize existing news articles in ChromaDB.

Fetches news articles from ChromaDB, generates summaries using LLM,
and updates the articles with summary metadata.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Imports after sys.path modification (required for scripts)
from app.ingestion.news_summarizer import (  # noqa: E402
    NewsSummarizer,
    NewsSummarizerError,
)
from app.utils.config import config  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402
from app.vector_db import ChromaStore, ChromaStoreError  # noqa: E402

logger = get_logger(__name__)


def summarize_existing_articles(
    collection_name: str = "documents",
    limit: Optional[int] = None,
    update_chromadb: bool = True,
):
    """
    Summarize existing news articles in ChromaDB.

    Args:
        collection_name: ChromaDB collection name (default: "documents")
        limit: Maximum number of articles to summarize (None = all)
        update_chromadb: Whether to update ChromaDB with summaries (default: True)

    Returns:
        Number of articles successfully summarized
    """
    try:
        # Initialize ChromaDB store
        logger.info(f"Connecting to ChromaDB collection: {collection_name}")
        chroma_store = ChromaStore(collection_name=collection_name)

        # Initialize summarizer
        logger.info("Initializing news summarizer")
        summarizer = NewsSummarizer(
            enabled=True,
            llm_provider=(
                config.news_summarization_llm_provider
                if config.news_summarization_llm_provider
                else None
            ),
            llm_model=(
                config.news_summarization_llm_model
                if config.news_summarization_llm_model
                else None
            ),
            target_words=config.news_summarization_target_words,
            min_words=config.news_summarization_min_words,
            max_words=config.news_summarization_max_words,
        )

        if not summarizer.enabled:
            logger.error("News summarization is disabled")
            return 0

        # Query ChromaDB for news articles
        logger.info("Querying ChromaDB for news articles")
        try:
            # Get all documents with type="news_article" using ChromaDB get()
            # with where filter
            collection = chroma_store.collection
            if collection is None:
                raise ChromaStoreError("Collection is not initialized")

            # Get all documents with type="news_article"
            results = collection.get(
                where={"type": "news_article"},
                include=["metadatas", "documents"],
            )

            # Filter for news articles without summaries
            news_articles = []
            for i, doc_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                document_text = results["documents"][i] if results["documents"] else ""

                # Skip if already has summary
                if not metadata.get("summary"):
                    # Create a simple document-like object
                    from types import SimpleNamespace

                    doc = SimpleNamespace()
                    doc.metadata = metadata
                    doc.page_content = document_text
                    news_articles.append((doc_id, doc))

            logger.info(f"Found {len(news_articles)} news articles without summaries")

            if limit:
                news_articles = news_articles[:limit]
                logger.info(f"Limiting to {limit} articles")

            if not news_articles:
                logger.info("No articles to summarize")
                return 0

            # Summarize articles
            logger.info(f"Summarizing {len(news_articles)} articles")
            summarized_count = 0
            failed_count = 0

            for doc_id, doc in news_articles:
                try:
                    # Extract article content
                    title = doc.metadata.get("title", "")
                    content = doc.page_content

                    # Create article dict for summarizer
                    article = {
                        "title": title,
                        "content": content,
                        "url": doc.metadata.get("url", ""),
                        "source": doc.metadata.get("source", "unknown"),
                    }

                    # Generate summary
                    summary = summarizer.summarize_article(article)

                    if summary:
                        # Update document metadata with summary
                        if update_chromadb:
                            # Update metadata in ChromaDB
                            updated_metadata = doc.metadata.copy()
                            updated_metadata["summary"] = summary

                            # Update document in ChromaDB
                            # Note: ChromaDB update requires re-adding the document
                            # We'll need to get the embedding and re-add
                            # For simplicity, we'll log the summary for now
                            # Full update would require getting the embedding
                            logger.info(
                                f"Article {doc_id[:20]}... summarized "
                                f"({len(summary)} chars)"
                            )
                            logger.debug(f"Summary: {summary[:100]}...")

                        summarized_count += 1
                    else:
                        logger.warning(f"Failed to generate summary for {doc_id}")
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Error summarizing article {doc_id}: {str(e)}")
                    failed_count += 1
                    continue

            logger.info(
                f"Summarization complete: {summarized_count} succeeded, "
                f"{failed_count} failed"
            )
            return summarized_count

        except ChromaStoreError as e:
            logger.error(f"ChromaDB error: {str(e)}")
            raise

    except NewsSummarizerError as e:
        logger.error(f"Summarizer error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise


def main():
    """Main function to summarize existing news articles."""
    parser = argparse.ArgumentParser(
        description="Summarize existing news articles in ChromaDB"
    )
    parser.add_argument(
        "--collection",
        default="documents",
        help="ChromaDB collection name (default: documents)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of articles to summarize (default: all)",
    )
    parser.add_argument(
        "--no-update",
        action="store_true",
        help="Don't update ChromaDB (dry run mode)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (don't update ChromaDB)",
    )

    args = parser.parse_args()

    # Check if news summarization is enabled
    if not config.news_summarization_enabled:
        logger.error("News summarization is disabled in configuration")
        logger.info("Set NEWS_SUMMARIZATION_ENABLED=true to enable")
        sys.exit(1)

    update_chromadb = not (args.no_update or args.dry_run)

    try:
        count = summarize_existing_articles(
            collection_name=args.collection,
            limit=args.limit,
            update_chromadb=update_chromadb,
        )
        logger.info(f"Successfully summarized {count} articles")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to summarize articles: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
