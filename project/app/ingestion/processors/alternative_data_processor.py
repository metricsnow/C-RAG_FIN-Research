"""
Alternative data processor for ingestion pipeline.

Handles processing of alternative data sources:
- Social Media (Reddit, Twitter/X)
- ESG (Environmental, Social, Governance) data
- Alternative data (LinkedIn jobs, supply chain, Form S-1)
"""

from typing import List, Optional

from app.ingestion.alternative_data_fetcher import (
    AlternativeDataFetcher,
    AlternativeDataFetcherError,
)
from app.ingestion.esg_fetcher import ESGFetcher, ESGFetcherError
from app.ingestion.processors.base_processor import BaseProcessor
from app.ingestion.social_media_fetcher import (
    SocialMediaFetcher,
    SocialMediaFetcherError,
)
from app.utils.logger import get_logger
from app.utils.metrics import document_ingestion_total, track_error

logger = get_logger(__name__)


class AlternativeDataProcessor(BaseProcessor):
    """
    Processor for alternative data ingestion.

    Handles fetching, chunking, embedding, and storage of alternative data
    from multiple sources.
    """

    def __init__(
        self,
        document_loader,
        embedding_generator,
        chroma_store,
        social_media_fetcher: Optional[SocialMediaFetcher] = None,
        esg_fetcher: Optional[ESGFetcher] = None,
        alternative_data_fetcher: Optional[AlternativeDataFetcher] = None,
        sentiment_analyzer=None,
    ):
        """
        Initialize alternative data processor.

        Args:
            document_loader: DocumentLoader instance
            embedding_generator: EmbeddingGenerator instance
            chroma_store: ChromaStore instance
            social_media_fetcher: Optional SocialMediaFetcher instance
            esg_fetcher: Optional ESGFetcher instance
            alternative_data_fetcher: Optional AlternativeDataFetcher instance
            sentiment_analyzer: Optional SentimentAnalyzer instance
        """
        super().__init__(
            document_loader, embedding_generator, chroma_store, sentiment_analyzer
        )
        self.social_media_fetcher = social_media_fetcher
        self.esg_fetcher = esg_fetcher
        self.alternative_data_fetcher = alternative_data_fetcher

    def process_social_media(
        self,
        subreddits: Optional[List[str]] = None,
        twitter_query: Optional[str] = None,
        limit: int = 25,
        store_embeddings: bool = True,
    ) -> List[str]:
        """
        Process social media posts (Reddit and Twitter/X).

        Args:
            subreddits: List of Reddit subreddits to fetch from
            twitter_query: Twitter/X search query
            limit: Maximum number of posts per source (default: 25)
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of chunk IDs

        Raises:
            IngestionPipelineError: If processing fails
        """
        from app.ingestion.pipeline import IngestionPipelineError

        if not self.social_media_fetcher:
            raise IngestionPipelineError("Social media fetcher is not enabled")

        logger.info("Processing social media posts")
        try:
            # Step 1: Fetch social media posts
            all_posts = []

            # Fetch Reddit posts if enabled
            if self.social_media_fetcher.reddit_enabled:
                logger.debug("Fetching Reddit posts")
                reddit_posts = self.social_media_fetcher.fetch_reddit_posts(
                    subreddits=subreddits, limit=limit
                )
                all_posts.extend(reddit_posts)

            # Fetch Twitter tweets if enabled
            if self.social_media_fetcher.twitter_enabled and twitter_query:
                logger.debug(f"Fetching Twitter tweets for query: {twitter_query}")
                twitter_tweets = self.social_media_fetcher.fetch_twitter_tweets(
                    query=twitter_query, max_results=limit
                )
                all_posts.extend(twitter_tweets)

            if not all_posts:
                logger.warning("No social media posts fetched")
                return []

            # Step 2: Convert to Document objects
            logger.debug(f"Converting {len(all_posts)} posts to Document objects")
            documents = self.social_media_fetcher.to_documents(all_posts)

            if not documents:
                logger.warning("No documents generated from social media posts")
                return []

            # Step 3: Process documents
            return self.process_documents_to_chunks(
                documents, store_embeddings=store_embeddings, source_name="social media"
            )

        except SocialMediaFetcherError as e:
            logger.error(f"Social media fetching failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Social media fetching failed: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(
                f"Unexpected error processing social media posts: {str(e)}",
                exc_info=True,
            )
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Unexpected error processing social media posts: {str(e)}"
            ) from e

    def process_esg_data(
        self,
        tickers: List[str],
        providers: Optional[List[str]] = None,
        store_embeddings: bool = True,
    ) -> List[str]:
        """
        Process ESG data for multiple tickers.

        Args:
            tickers: List of ticker symbols
            providers: List of ESG providers (["msci", "sustainalytics", "cdp"])
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of chunk IDs

        Raises:
            IngestionPipelineError: If processing fails
        """
        from app.ingestion.pipeline import IngestionPipelineError

        if not self.esg_fetcher:
            raise IngestionPipelineError("ESG fetcher is not enabled")

        logger.info(f"Processing ESG data for {len(tickers)} tickers")
        try:
            # Step 1: Fetch ESG data
            logger.debug("Fetching ESG data")
            esg_data = self.esg_fetcher.fetch_esg_data(
                tickers=tickers, providers=providers
            )

            if not esg_data:
                logger.warning("No ESG data fetched")
                return []

            # Step 2: Convert to Document objects
            logger.debug(f"Converting {len(esg_data)} ESG records to Document objects")
            documents = self.esg_fetcher.to_documents(esg_data)

            if not documents:
                logger.warning("No documents generated from ESG data")
                return []

            # Step 3: Process documents
            return self.process_documents_to_chunks(
                documents, store_embeddings=store_embeddings, source_name="ESG data"
            )

        except ESGFetcherError as e:
            logger.error(f"ESG fetching failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(f"ESG fetching failed: {str(e)}") from e
        except Exception as e:
            logger.error(
                f"Unexpected error processing ESG data: {str(e)}", exc_info=True
            )
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Unexpected error processing ESG data: {str(e)}"
            ) from e

    def process_alternative_data(
        self,
        tickers: Optional[List[str]] = None,
        linkedin_company: Optional[str] = None,
        form_s1_limit: int = 10,
        store_embeddings: bool = True,
    ) -> List[str]:
        """
        Process alternative data (LinkedIn jobs, supply chain, Form S-1).

        Args:
            tickers: List of ticker symbols for Form S-1 and supply chain
            linkedin_company: Company name for LinkedIn job search
            form_s1_limit: Maximum number of Form S-1 filings to fetch (default: 10)
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of chunk IDs

        Raises:
            IngestionPipelineError: If processing fails
        """
        from app.ingestion.pipeline import IngestionPipelineError

        if not self.alternative_data_fetcher:
            raise IngestionPipelineError("Alternative data fetcher is not enabled")

        logger.info("Processing alternative data")
        try:
            # Step 1: Fetch alternative data
            all_data = []

            # Fetch LinkedIn jobs if enabled
            if self.alternative_data_fetcher.linkedin_enabled and linkedin_company:
                logger.debug(f"Fetching LinkedIn jobs for {linkedin_company}")
                linkedin_jobs = self.alternative_data_fetcher.fetch_linkedin_jobs(
                    company=linkedin_company, ticker=tickers[0] if tickers else None
                )
                all_data.extend(linkedin_jobs)

            # Fetch supply chain data if enabled
            if self.alternative_data_fetcher.supply_chain_enabled and tickers:
                logger.debug(f"Fetching supply chain data for {tickers}")
                for ticker in tickers:
                    supply_chain_data = (
                        self.alternative_data_fetcher.fetch_supply_chain_data(
                            ticker=ticker
                        )
                    )
                    all_data.extend(supply_chain_data)

            # Fetch Form S-1 filings if enabled
            if self.alternative_data_fetcher.ipo_enabled:
                logger.debug("Fetching Form S-1 filings")
                if tickers:
                    for ticker in tickers:
                        form_s1_filings = (
                            self.alternative_data_fetcher.fetch_form_s1_filings(
                                ticker=ticker, limit=form_s1_limit
                            )
                        )
                        all_data.extend(form_s1_filings)
                else:
                    form_s1_filings = (
                        self.alternative_data_fetcher.fetch_form_s1_filings(
                            limit=form_s1_limit
                        )
                    )
                    all_data.extend(form_s1_filings)

            if not all_data:
                logger.warning("No alternative data fetched")
                return []

            # Step 2: Convert to Document objects
            logger.debug(f"Converting {len(all_data)} records to Document objects")
            documents = self.alternative_data_fetcher.to_documents(all_data)

            if not documents:
                logger.warning("No documents generated from alternative data")
                return []

            # Step 3: Process documents
            return self.process_documents_to_chunks(
                documents,
                store_embeddings=store_embeddings,
                source_name="alternative data",
            )

        except AlternativeDataFetcherError as e:
            logger.error(f"Alternative data fetching failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Alternative data fetching failed: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(
                f"Unexpected error processing alternative data: {str(e)}", exc_info=True
            )
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Unexpected error processing alternative data: {str(e)}"
            ) from e
