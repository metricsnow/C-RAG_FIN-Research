"""
Document ingestion pipeline with embedding generation and ChromaDB storage.

Integrates document loading, chunking, embedding generation, and vector storage.
"""

from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document

from app.alerts.news_alerts import NewsAlertSystem
from app.ingestion.alternative_data_fetcher import AlternativeDataFetcher
from app.ingestion.central_bank_fetcher import CentralBankFetcher
from app.ingestion.document_loader import DocumentLoader
from app.ingestion.economic_calendar_fetcher import EconomicCalendarFetcher
from app.ingestion.esg_fetcher import ESGFetcher
from app.ingestion.fred_fetcher import FREDFetcher
from app.ingestion.imf_fetcher import IMFFetcher
from app.ingestion.news_fetcher import NewsFetcher
from app.ingestion.news_summarizer import NewsSummarizer
from app.ingestion.processors.alternative_data_processor import (
    AlternativeDataProcessor,
)
from app.ingestion.processors.document_processor import DocumentProcessor
from app.ingestion.processors.economic_data_processor import EconomicDataProcessor
from app.ingestion.processors.news_processor import NewsProcessor
from app.ingestion.processors.stock_processor import StockProcessor
from app.ingestion.processors.transcript_processor import TranscriptProcessor
from app.ingestion.sentiment_analyzer import SentimentAnalyzer
from app.ingestion.social_media_fetcher import SocialMediaFetcher
from app.ingestion.stock_data_normalizer import StockDataNormalizer
from app.ingestion.transcript_fetcher import TranscriptFetcher
from app.ingestion.transcript_parser import TranscriptParser
from app.ingestion.world_bank_fetcher import WorldBankFetcher
from app.ingestion.yfinance_fetcher import YFinanceFetcher
from app.rag.embedding_factory import EmbeddingError, EmbeddingGenerator
from app.utils.config import config
from app.utils.logger import get_logger
from app.vector_db import ChromaStore, ChromaStoreError

logger = get_logger(__name__)


class IngestionPipelineError(Exception):
    """Custom exception for ingestion pipeline errors."""

    pass


class IngestionPipeline:
    """
    Complete document ingestion pipeline.

    Handles document loading, chunking, embedding generation,
    and storage in ChromaDB.
    """

    def __init__(
        self,
        embedding_provider: Optional[str] = None,
        collection_name: str = "documents",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize ingestion pipeline.

        Args:
            embedding_provider: Embedding provider ('openai' or 'ollama').
                If None, uses config.EMBEDDING_PROVIDER
            collection_name: ChromaDB collection name
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.document_loader = DocumentLoader(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.embedding_generator = EmbeddingGenerator(provider=embedding_provider)
        self.chroma_store = ChromaStore(collection_name=collection_name)

        # Initialize document processor
        self.document_processor = DocumentProcessor(
            document_loader=self.document_loader,
            embedding_generator=self.embedding_generator,
            chroma_store=self.chroma_store,
            sentiment_analyzer=None,  # Set after sentiment_analyzer init
        )

        self.yfinance_fetcher = YFinanceFetcher() if config.yfinance_enabled else None
        self.stock_normalizer = StockDataNormalizer()
        self.transcript_fetcher = (
            TranscriptFetcher(
                rate_limit_delay=config.transcript_rate_limit_seconds,
                use_web_scraping=config.transcript_use_web_scraping,
            )
            if config.transcript_enabled
            else None
        )
        self.transcript_parser = (
            TranscriptParser() if config.transcript_enabled else None
        )
        # Initialize news summarizer if enabled
        self.news_summarizer = (
            NewsSummarizer(
                enabled=config.news_summarization_enabled,
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
            if config.news_enabled and config.news_summarization_enabled
            else None
        )
        self.news_fetcher = (
            NewsFetcher(
                use_rss=config.news_use_rss,
                use_scraping=config.news_use_scraping,
                rss_rate_limit=config.news_rss_rate_limit_seconds,
                scraping_rate_limit=config.news_scraping_rate_limit_seconds,
                scrape_full_content=config.news_scrape_full_content,
                summarizer=self.news_summarizer,
            )
            if config.news_enabled
            else None
        )
        # Initialize news alert system if enabled
        self.news_alert_system = (
            NewsAlertSystem()
            if config.news_enabled and config.news_alerts_enabled
            else None
        )
        self.sentiment_analyzer = (
            SentimentAnalyzer(
                use_finbert=config.sentiment_use_finbert,
                use_textblob=config.sentiment_use_textblob,
                use_vader=config.sentiment_use_vader,
            )
            if config.sentiment_enabled
            else None
        )
        # Update document processor with sentiment analyzer
        if self.document_processor:
            self.document_processor.sentiment_analyzer = self.sentiment_analyzer

        # Initialize stock processor
        self.stock_processor = (
            StockProcessor(
                document_loader=self.document_loader,
                embedding_generator=self.embedding_generator,
                chroma_store=self.chroma_store,
                yfinance_fetcher=self.yfinance_fetcher,
                stock_normalizer=self.stock_normalizer,
                sentiment_analyzer=self.sentiment_analyzer,
            )
            if config.yfinance_enabled and self.yfinance_fetcher
            else None
        )

        # Initialize transcript processor
        self.transcript_processor = (
            TranscriptProcessor(
                document_loader=self.document_loader,
                embedding_generator=self.embedding_generator,
                chroma_store=self.chroma_store,
                transcript_fetcher=self.transcript_fetcher,
                transcript_parser=self.transcript_parser,
                sentiment_analyzer=self.sentiment_analyzer,
            )
            if config.transcript_enabled
            and self.transcript_fetcher
            and self.transcript_parser
            else None
        )

        # Initialize news processor
        self.news_processor = (
            NewsProcessor(
                document_loader=self.document_loader,
                embedding_generator=self.embedding_generator,
                chroma_store=self.chroma_store,
                news_fetcher=self.news_fetcher,
                news_alert_system=self.news_alert_system,
                sentiment_analyzer=self.sentiment_analyzer,
            )
            if config.news_enabled and self.news_fetcher
            else None
        )

        self.economic_calendar_fetcher = (
            EconomicCalendarFetcher(
                rate_limit_delay=config.economic_calendar_rate_limit_seconds,
            )
            if config.economic_calendar_enabled
            else None
        )
        self.fred_fetcher = (
            FREDFetcher(
                rate_limit_delay=config.fred_rate_limit_seconds,
            )
            if config.fred_enabled
            else None
        )
        self.world_bank_fetcher = (
            WorldBankFetcher(
                rate_limit_delay=config.world_bank_rate_limit_seconds,
            )
            if config.world_bank_enabled
            else None
        )
        self.imf_fetcher = (
            IMFFetcher(
                rate_limit_delay=config.imf_rate_limit_seconds,
            )
            if config.imf_enabled
            else None
        )
        self.central_bank_fetcher = (
            CentralBankFetcher(
                rate_limit_delay=config.central_bank_rate_limit_seconds,
                use_web_scraping=config.central_bank_use_web_scraping,
            )
            if config.central_bank_enabled
            else None
        )
        # Alternative Data Sources (TASK-044)
        self.social_media_fetcher = (
            SocialMediaFetcher(
                reddit_enabled=config.social_media_reddit_enabled,
                twitter_enabled=config.social_media_twitter_enabled,
                sentiment_enabled=config.social_media_sentiment_enabled,
                rate_limit_delay=config.social_media_rate_limit,
            )
            if config.social_media_enabled
            else None
        )
        self.esg_fetcher = (
            ESGFetcher(
                msci_enabled=config.esg_msci_enabled,
                sustainalytics_enabled=config.esg_sustainalytics_enabled,
                cdp_enabled=config.esg_cdp_enabled,
                rate_limit_delay=config.esg_rate_limit,
            )
            if config.esg_enabled
            else None
        )
        self.alternative_data_fetcher = (
            AlternativeDataFetcher(
                linkedin_enabled=config.alternative_data_linkedin_enabled,
                supply_chain_enabled=config.alternative_data_supply_chain_enabled,
                ipo_enabled=config.alternative_data_ipo_enabled,
                rate_limit_delay=config.alternative_data_rate_limit,
            )
            if config.alternative_data_enabled
            else None
        )

        # Initialize economic data processor
        self.economic_data_processor = EconomicDataProcessor(
            document_loader=self.document_loader,
            embedding_generator=self.embedding_generator,
            chroma_store=self.chroma_store,
            economic_calendar_fetcher=self.economic_calendar_fetcher,
            fred_fetcher=self.fred_fetcher,
            world_bank_fetcher=self.world_bank_fetcher,
            imf_fetcher=self.imf_fetcher,
            central_bank_fetcher=self.central_bank_fetcher,
            sentiment_analyzer=self.sentiment_analyzer,
        )

        # Initialize alternative data processor
        self.alternative_data_processor = (
            AlternativeDataProcessor(
                document_loader=self.document_loader,
                embedding_generator=self.embedding_generator,
                chroma_store=self.chroma_store,
                social_media_fetcher=self.social_media_fetcher,
                esg_fetcher=self.esg_fetcher,
                alternative_data_fetcher=self.alternative_data_fetcher,
                sentiment_analyzer=self.sentiment_analyzer,
            )
            if (
                config.social_media_enabled
                or config.esg_enabled
                or config.alternative_data_enabled
            )
            else None
        )

    def process_document(
        self, file_path: Path, store_embeddings: bool = True
    ) -> List[str]:
        """
        Process a single document: load, chunk, embed, and store.

        Args:
            file_path: Path to the document file
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of document chunk IDs stored in ChromaDB

        Raises:
            IngestionPipelineError: If processing fails
        """
        return self.document_processor.process_document(
            file_path, store_embeddings=store_embeddings
        )

    def process_documents(
        self, file_paths: List[Path], store_embeddings: bool = True
    ) -> List[str]:
        """
        Process multiple documents sequentially.

        Args:
            file_paths: List of paths to document files
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of all document chunk IDs stored in ChromaDB

        Raises:
            IngestionPipelineError: If processing fails
        """
        return self.document_processor.process_documents(
            file_paths, store_embeddings=store_embeddings
        )

    def process_document_objects(
        self, documents: List[Document], store_embeddings: bool = True
    ) -> List[str]:
        """
        Process Document objects directly (without file paths).

        Args:
            documents: List of Document objects to process
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of all document chunk IDs stored in ChromaDB

        Raises:
            IngestionPipelineError: If processing fails
        """
        return self.document_processor.process_documents_to_chunks(
            documents, store_embeddings=store_embeddings, source_name="document objects"
        )

    def _enrich_with_sentiment(self, document: Document) -> Document:
        """
        Enrich document metadata with sentiment analysis.

        Args:
            document: Document to enrich

        Returns:
            Document with enriched metadata
        """
        return self.document_processor.enrich_with_sentiment(document)

    def get_document_count(self) -> int:
        """
        Get the number of documents stored in ChromaDB.

        Returns:
            Number of documents in the collection
        """
        count = self.chroma_store.count()
        logger.debug(f"Document count in ChromaDB: {count}")
        return count

    def search_similar(self, query_text: str, n_results: int = 5) -> List[Document]:
        """
        Search for similar documents using query text.

        Args:
            query_text: Query text string
            n_results: Number of results to return

        Returns:
            List of similar Document objects with metadata

        Raises:
            IngestionPipelineError: If search fails
        """
        logger.info(
            f"Searching for similar documents: query='{query_text[:50]}...', "
            f"n_results={n_results}"
        )
        try:
            # Generate query embedding
            logger.debug("Generating query embedding")
            query_embedding = self.embedding_generator.embed_query(query_text)

            # Search ChromaDB
            logger.debug(f"Searching ChromaDB with n_results={n_results}")
            results = self.chroma_store.query_by_embedding(
                query_embedding, n_results=n_results
            )

            # Convert to Document objects
            documents = []
            for _, (_, doc_text, metadata) in enumerate(
                zip(results["ids"], results["documents"], results["metadatas"])
            ):
                doc = Document(page_content=doc_text, metadata=metadata)
                documents.append(doc)

            logger.info(f"Found {len(documents)} similar documents")
            return documents

        except EmbeddingError as e:
            logger.error(f"Query embedding failed: {str(e)}", exc_info=True)
            raise IngestionPipelineError(f"Query embedding failed: {str(e)}") from e
        except ChromaStoreError as e:
            logger.error(f"ChromaDB search failed: {str(e)}", exc_info=True)
            raise IngestionPipelineError(f"ChromaDB search failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in search: {str(e)}", exc_info=True)
            raise IngestionPipelineError(f"Unexpected error in search: {str(e)}") from e

    def process_stock_data(
        self,
        ticker_symbol: str,
        include_history: bool = True,
        store_embeddings: bool = True,
    ) -> List[str]:
        """
        Process stock data for a ticker symbol: fetch, normalize, and store.

        Args:
            ticker_symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            include_history: Whether to include historical price data (default: True)
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of document chunk IDs stored in ChromaDB

        Raises:
            IngestionPipelineError: If processing fails
        """
        if self.stock_processor is None:
            raise IngestionPipelineError("Stock processor is not initialized")
        return self.stock_processor.process_stock_data(
            ticker_symbol,
            include_history=include_history,
            store_embeddings=store_embeddings,
        )

    def process_stock_tickers(
        self,
        ticker_symbols: List[str],
        include_history: bool = True,
        store_embeddings: bool = True,
    ) -> List[str]:
        """
        Process stock data for multiple ticker symbols.

        Args:
            ticker_symbols: List of stock ticker symbols
            include_history: Whether to include historical price data (default: True)
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of all document chunk IDs stored in ChromaDB

        Raises:
            IngestionPipelineError: If processing fails
        """
        if self.stock_processor is None:
            raise IngestionPipelineError("Stock processor is not initialized")
        return self.stock_processor.process_stock_tickers(
            ticker_symbols,
            include_history=include_history,
            store_embeddings=store_embeddings,
        )

    def process_transcript(
        self,
        ticker: str,
        date: Optional[str] = None,
        source: Optional[str] = None,
        store_embeddings: bool = True,
    ) -> List[str]:
        """
        Process earnings call transcript: fetch, parse, and store.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            date: Transcript date (YYYY-MM-DD format, optional)
            source: Preferred source ('seeking_alpha', 'yahoo_finance', None for auto)
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of document chunk IDs stored in ChromaDB

        Raises:
            IngestionPipelineError: If processing fails
        """
        if self.transcript_processor is None:
            raise IngestionPipelineError("Transcript processor is not initialized")
        return self.transcript_processor.process_transcript(
            ticker, date=date, source=source, store_embeddings=store_embeddings
        )

    def process_transcripts(
        self,
        ticker_symbols: List[str],
        date: Optional[str] = None,
        source: Optional[str] = None,
        store_embeddings: bool = True,
    ) -> List[str]:
        """
        Process transcripts for multiple ticker symbols.

        Args:
            ticker_symbols: List of stock ticker symbols
            date: Transcript date (YYYY-MM-DD format, optional)
            source: Preferred source (optional)
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of all document chunk IDs stored in ChromaDB

        Raises:
            IngestionPipelineError: If processing fails
        """
        if self.transcript_processor is None:
            raise IngestionPipelineError("Transcript processor is not initialized")
        return self.transcript_processor.process_transcripts(
            ticker_symbols, date=date, source=source, store_embeddings=store_embeddings
        )

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
        if self.news_processor is None:
            raise IngestionPipelineError("News processor is not initialized")
        return self.news_processor.process_news(
            feed_urls=feed_urls,
            article_urls=article_urls,
            enhance_with_scraping=enhance_with_scraping,
            store_embeddings=store_embeddings,
        )

    def process_economic_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
        importance: Optional[str] = None,
        store_embeddings: bool = True,
    ) -> List[str]:
        """
        Process economic calendar events: fetch, parse, and store.

        Args:
            start_date: Start date (YYYY-MM-DD format, optional)
            end_date: End date (YYYY-MM-DD format, optional)
            country: Country code (e.g., 'united states', optional)
            importance: Importance filter ('High', 'Medium', 'Low', optional)
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of document chunk IDs stored in ChromaDB

        Raises:
            IngestionPipelineError: If processing fails
        """
        return self.economic_data_processor.process_economic_calendar(
            start_date=start_date,
            end_date=end_date,
            country=country,
            importance=importance,
            store_embeddings=store_embeddings,
        )

    def process_fred_series(
        self,
        series_ids: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        store_embeddings: bool = True,
    ) -> List[str]:
        """
        Process FRED time series: fetch, format, and store.

        Args:
            series_ids: List of FRED series IDs (e.g., ['GDP', 'UNRATE', 'FEDFUNDS'])
            start_date: Start date (YYYY-MM-DD format, optional)
            end_date: End date (YYYY-MM-DD format, optional)
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of document chunk IDs stored in ChromaDB

        Raises:
            IngestionPipelineError: If processing fails
        """
        return self.economic_data_processor.process_fred_series(
            series_ids=series_ids,
            start_date=start_date,
            end_date=end_date,
            store_embeddings=store_embeddings,
        )

    def process_world_bank_indicators(
        self,
        indicator_codes: List[str],
        country_codes: Optional[List[str]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        store_embeddings: bool = True,
    ) -> List[str]:
        """
        Process World Bank indicators through the ingestion pipeline.

        Args:
            indicator_codes: List of World Bank indicator codes
            country_codes: List of country ISO codes (optional)
            start_year: Start year (optional)
            end_year: End year (optional)
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of document chunk IDs stored in ChromaDB

        Raises:
            IngestionPipelineError: If processing fails
        """
        return self.economic_data_processor.process_world_bank_indicators(
            indicator_codes=indicator_codes,
            country_codes=country_codes,
            start_year=start_year,
            end_year=end_year,
            store_embeddings=store_embeddings,
        )

    def process_imf_indicators(
        self,
        indicator_codes: List[str],
        country_codes: Optional[List[str]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        store_embeddings: bool = True,
    ) -> List[str]:
        """
        Process IMF indicators through the ingestion pipeline.

        Args:
            indicator_codes: List of IMF indicator codes
            country_codes: List of country ISO codes (optional)
            start_year: Start year (optional)
            end_year: End year (optional)
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of document chunk IDs stored in ChromaDB

        Raises:
            IngestionPipelineError: If processing fails
        """
        return self.economic_data_processor.process_imf_indicators(
            indicator_codes=indicator_codes,
            country_codes=country_codes,
            start_year=start_year,
            end_year=end_year,
            store_embeddings=store_embeddings,
        )

    def process_central_bank(
        self,
        comm_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
        store_embeddings: bool = True,
    ) -> List[str]:
        """
        Process central bank communications through the ingestion pipeline.

        Args:
            comm_types: List of communication types to fetch
                ('fomc_statement', 'fomc_minutes', 'fomc_press_conference',
                or None for all)
            start_date: Start date (YYYY-MM-DD format, optional)
            end_date: End date (YYYY-MM-DD format, optional)
            limit: Maximum number of communications per type (optional)
            store_embeddings: Whether to store embeddings in ChromaDB (default: True)

        Returns:
            List of document chunk IDs stored in ChromaDB

        Raises:
            IngestionPipelineError: If processing fails
        """
        return self.economic_data_processor.process_central_bank(
            comm_types=comm_types,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            store_embeddings=store_embeddings,
        )

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
        if self.alternative_data_processor is None:
            raise IngestionPipelineError(
                "Alternative data processor is not initialized"
            )
        return self.alternative_data_processor.process_social_media(
            subreddits=subreddits,
            twitter_query=twitter_query,
            limit=limit,
            store_embeddings=store_embeddings,
        )

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
        if self.alternative_data_processor is None:
            raise IngestionPipelineError(
                "Alternative data processor is not initialized"
            )
        return self.alternative_data_processor.process_esg_data(
            tickers=tickers, providers=providers, store_embeddings=store_embeddings
        )

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
        if self.alternative_data_processor is None:
            raise IngestionPipelineError(
                "Alternative data processor is not initialized"
            )
        return self.alternative_data_processor.process_alternative_data(
            tickers=tickers,
            linkedin_company=linkedin_company,
            form_s1_limit=form_s1_limit,
            store_embeddings=store_embeddings,
        )


def create_pipeline(
    embedding_provider: Optional[str] = None,
    collection_name: str = "documents",
) -> IngestionPipeline:
    """
    Create an ingestion pipeline instance.

    Args:
        embedding_provider: Embedding provider ('openai' or 'ollama').
            If None, uses config.EMBEDDING_PROVIDER
        collection_name: ChromaDB collection name

    Returns:
        IngestionPipeline instance
    """
    return IngestionPipeline(
        embedding_provider=embedding_provider,
        collection_name=collection_name,
    )
