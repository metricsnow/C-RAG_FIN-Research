"""
News processor for ingestion pipeline.

Handles processing of financial news articles.
"""

from typing import List, Optional

from app.alerts.news_alerts import NewsAlertSystem
from app.ingestion.news_fetcher import NewsFetcher, NewsFetcherError
from app.ingestion.processors.base_processor import BaseProcessor
from app.rag.embedding_factory import EmbeddingError
from app.utils.config import config
from app.utils.logger import get_logger
from app.utils.metrics import document_ingestion_total, track_error
from app.vector_db import ChromaStoreError

logger = get_logger(__name__)


class NewsProcessor(BaseProcessor):
    """
    Processor for financial news article ingestion.

    Handles fetching, chunking, embedding, and storage of news articles.
    """

    def __init__(
        self,
        document_loader,
        embedding_generator,
        chroma_store,
        news_fetcher: NewsFetcher,
        news_alert_system: Optional[NewsAlertSystem] = None,
        sentiment_analyzer=None,
    ):
        """
        Initialize news processor.

        Args:
            document_loader: DocumentLoader instance
            embedding_generator: EmbeddingGenerator instance
            chroma_store: ChromaStore instance
            news_fetcher: NewsFetcher instance
            news_alert_system: Optional NewsAlertSystem instance
            sentiment_analyzer: Optional SentimentAnalyzer instance
        """
        super().__init__(
            document_loader, embedding_generator, chroma_store, sentiment_analyzer
        )
        self.news_fetcher = news_fetcher
        self.news_alert_system = news_alert_system

    def process_news(
        self,
        feed_urls: Optional[List[str]] = None,
        article_urls: Optional[List[str]] = None,
        enhance_with_scraping: bool = True,
        store_embeddings: bool = True,
    ) -> List[str]:
        """
        Process financial news articles: fetch, parse, and store.

        Args:
            feed_urls: List of RSS feed URLs (optional)
            article_urls: List of article URLs to scrape (optional)
            enhance_with_scraping: Whether to scrape full content for RSS articles
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of document chunk IDs stored in ChromaDB

        Raises:
            IngestionPipelineError: If processing fails
        """
        from app.ingestion.pipeline import IngestionPipelineError

        if not config.news_enabled:
            raise IngestionPipelineError(
                "News integration is disabled in configuration"
            )

        if self.news_fetcher is None:
            raise IngestionPipelineError("News fetcher is not initialized")

        logger.info("Processing financial news articles")
        try:
            # Step 1: Fetch news articles
            logger.debug("Fetching news articles")
            articles = self.news_fetcher.fetch_news(
                feed_urls=feed_urls,
                article_urls=article_urls,
                enhance_with_scraping=enhance_with_scraping,
            )

            if not articles:
                logger.warning("No news articles fetched")
                return []

            # Step 1.5: Check articles against alert rules (if enabled)
            if self.news_alert_system and config.news_alerts_enabled:
                try:
                    logger.debug("Checking articles against alert rules")
                    alert_results = self.news_alert_system.check_articles(articles)
                    if alert_results:
                        logger.info(
                            f"Alert notifications sent for "
                            f"{len(alert_results)} articles"
                        )
                except Exception as e:
                    # Don't fail ingestion if alert checking fails
                    logger.warning(
                        f"Alert checking failed (continuing with ingestion): {str(e)}"
                    )

            # Step 2: Convert to Document objects
            logger.debug(f"Converting {len(articles)} articles to Document objects")
            documents = self.news_fetcher.to_documents(articles)

            if not documents:
                logger.warning("No documents generated from news articles")
                return []

            # Step 3: Process documents (chunk, embed, store)
            return self.process_documents_to_chunks(
                documents, store_embeddings=store_embeddings, source_name="news"
            )

        except NewsFetcherError as e:
            logger.error(f"News fetching failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(f"News fetching failed: {str(e)}") from e
        except EmbeddingError as e:
            logger.error(f"Embedding generation failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Embedding generation failed: {str(e)}"
            ) from e
        except ChromaStoreError as e:
            logger.error(f"ChromaDB storage failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(f"ChromaDB storage failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error processing news: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Unexpected error processing news: {str(e)}"
            ) from e
