"""
Document ingestion pipeline with embedding generation and ChromaDB storage.

Integrates document loading, chunking, embedding generation, and vector storage.
"""

from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document

from app.ingestion.central_bank_fetcher import (
    CentralBankFetcher,
    CentralBankFetcherError,
)
from app.ingestion.document_loader import DocumentIngestionError, DocumentLoader
from app.ingestion.economic_calendar_fetcher import (
    EconomicCalendarFetcher,
    EconomicCalendarFetcherError,
)
from app.ingestion.fred_fetcher import FREDFetcher, FREDFetcherError
from app.ingestion.imf_fetcher import IMFFetcher, IMFFetcherError
from app.ingestion.news_fetcher import NewsFetcher, NewsFetcherError
from app.ingestion.stock_data_normalizer import StockDataNormalizer
from app.ingestion.transcript_fetcher import TranscriptFetcher, TranscriptFetcherError
from app.ingestion.transcript_parser import TranscriptParser, TranscriptParserError
from app.ingestion.world_bank_fetcher import (
    WorldBankFetcher,
    WorldBankFetcherError,
)
from app.ingestion.yfinance_fetcher import YFinanceFetcher, YFinanceFetcherError
from app.rag.embedding_factory import EmbeddingError, EmbeddingGenerator
from app.utils.config import config
from app.utils.logger import get_logger
from app.utils.metrics import (
    document_chunks_created,
    document_ingestion_duration_seconds,
    document_ingestion_total,
    document_size_bytes,
    track_duration,
    track_error,
    track_success,
)
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
        self.news_fetcher = (
            NewsFetcher(
                use_rss=config.news_use_rss,
                use_scraping=config.news_use_scraping,
                rss_rate_limit=config.news_rss_rate_limit_seconds,
                scraping_rate_limit=config.news_scraping_rate_limit_seconds,
                scrape_full_content=config.news_scrape_full_content,
            )
            if config.news_enabled
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
        logger.info(f"Processing document: {file_path}")
        try:
            # Track document size
            file_size = file_path.stat().st_size if file_path.exists() else 0
            document_size_bytes.observe(file_size)

            # Track ingestion duration
            with track_duration(document_ingestion_duration_seconds):
                # Step 1: Load and chunk document
                logger.debug(f"Loading and chunking document: {file_path}")
                chunks = self.document_loader.process_document(file_path)

                if not chunks:
                    logger.error(f"No chunks generated from {file_path}")
                    raise IngestionPipelineError(
                        f"No chunks generated from {file_path}"
                    )

                logger.info(f"Generated {len(chunks)} chunks from document")

                # Step 2: Generate embeddings
                logger.debug(f"Generating embeddings for {len(chunks)} chunks")
                texts = [chunk.page_content for chunk in chunks]
                embeddings = self.embedding_generator.embed_documents(texts)

                if len(embeddings) != len(chunks):
                    logger.error(
                        f"Embedding count ({len(embeddings)}) does not match "
                        f"chunk count ({len(chunks)})"
                    )
                    raise IngestionPipelineError(
                        f"Embedding count ({len(embeddings)}) does not match "
                        f"chunk count ({len(chunks)})"
                    )

                logger.debug(f"Generated {len(embeddings)} embeddings")

                # Track chunks created
                document_chunks_created.observe(len(chunks))

                # Step 3: Store in ChromaDB (if requested)
                if store_embeddings:
                    logger.debug(f"Storing {len(chunks)} chunks in ChromaDB")
                    ids = self.chroma_store.add_documents(chunks, embeddings)
                    logger.info(f"Successfully stored {len(ids)} chunks in ChromaDB")
                    track_success(document_ingestion_total)
                    return ids
                else:
                    # Return placeholder IDs if not storing
                    logger.debug("Skipping ChromaDB storage (store_embeddings=False)")
                    track_success(document_ingestion_total)
                    return [f"chunk_{i}" for i in range(len(chunks))]

        except DocumentIngestionError as e:
            logger.error(f"Document ingestion failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(f"Document ingestion failed: {str(e)}") from e
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
            logger.error(f"Unexpected error in pipeline: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Unexpected error in pipeline: {str(e)}"
            ) from e

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
        all_ids = []

        logger.info(f"Processing {len(file_paths)} documents")
        for idx, file_path in enumerate(file_paths, 1):
            try:
                logger.info(f"Processing document {idx}/{len(file_paths)}: {file_path}")
                ids = self.process_document(
                    file_path, store_embeddings=store_embeddings
                )
                all_ids.extend(ids)
            except IngestionPipelineError as e:
                # Log error but continue processing other files
                logger.warning(f"Failed to process {file_path}: {str(e)}")
                continue
        logger.info(
            f"Completed processing {len(file_paths)} documents, "
            f"stored {len(all_ids)} chunks"
        )

        return all_ids

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
        logger.info(f"Processing {len(documents)} document objects")
        all_ids = []

        for idx, doc in enumerate(documents, 1):
            try:
                logger.debug(f"Processing document {idx}/{len(documents)}")
                # Chunk the document
                chunks = self.document_loader.chunk_document(doc)

                if not chunks:
                    logger.error("No chunks generated from document")
                    raise IngestionPipelineError("No chunks generated from document")

                # Generate embeddings
                texts = [chunk.page_content for chunk in chunks]
                embeddings = self.embedding_generator.embed_documents(texts)

                if len(embeddings) != len(chunks):
                    logger.error(
                        f"Embedding count ({len(embeddings)}) does not match "
                        f"chunk count ({len(chunks)})"
                    )
                    raise IngestionPipelineError(
                        f"Embedding count ({len(embeddings)}) does not match "
                        f"chunk count ({len(chunks)})"
                    )

                # Store in ChromaDB (if requested)
                if store_embeddings:
                    ids = self.chroma_store.add_documents(chunks, embeddings)
                    all_ids.extend(ids)
                else:
                    # Return placeholder IDs if not storing
                    all_ids.extend([f"chunk_{i}" for i in range(len(chunks))])

            except DocumentIngestionError as e:
                logger.error(f"Document ingestion failed: {str(e)}", exc_info=True)
                raise IngestionPipelineError(
                    f"Document ingestion failed: {str(e)}"
                ) from e
            except EmbeddingError as e:
                logger.error(f"Embedding generation failed: {str(e)}", exc_info=True)
                raise IngestionPipelineError(
                    f"Embedding generation failed: {str(e)}"
                ) from e
            except ChromaStoreError as e:
                logger.error(f"ChromaDB storage failed: {str(e)}", exc_info=True)
                raise IngestionPipelineError(
                    f"ChromaDB storage failed: {str(e)}"
                ) from e
            except Exception as e:
                logger.warning(f"Failed to process document: {str(e)}", exc_info=True)
                continue
        logger.info(
            f"Completed processing {len(documents)} document objects, "
            f"stored {len(all_ids)} chunks"
        )

        return all_ids

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
        if not config.yfinance_enabled:
            raise IngestionPipelineError(
                "yfinance integration is disabled in configuration"
            )

        if self.yfinance_fetcher is None:
            raise IngestionPipelineError("yfinance fetcher is not initialized")

        logger.info(f"Processing stock data for {ticker_symbol}")
        try:
            # Step 1: Fetch stock data
            logger.debug(f"Fetching stock data for {ticker_symbol}")
            stock_data = self.yfinance_fetcher.fetch_all_data(
                ticker_symbol, include_history=include_history
            )

            # Step 2: Normalize data to text documents
            logger.debug(f"Normalizing stock data for {ticker_symbol}")
            normalized_docs = self.stock_normalizer.normalize_all_data(
                stock_data, ticker_symbol
            )

            if not normalized_docs:
                logger.warning(
                    f"No documents generated from stock data for {ticker_symbol}"
                )
                return []

            # Step 3: Convert to LangChain Document objects
            from langchain_core.documents import Document

            documents = [
                Document(page_content=doc["text"], metadata=doc["metadata"])
                for doc in normalized_docs
            ]

            # Step 4: Chunk documents (if needed)
            all_chunks = []
            for doc in documents:
                chunks = self.document_loader.chunk_document(doc)
                all_chunks.extend(chunks)

            if not all_chunks:
                logger.warning(
                    f"No chunks generated from stock data for {ticker_symbol}"
                )
                return []

            logger.info(
                f"Generated {len(all_chunks)} chunks from stock data "
                f"for {ticker_symbol}"
            )

            # Step 5: Generate embeddings
            logger.debug(f"Generating embeddings for {len(all_chunks)} chunks")
            texts = [chunk.page_content for chunk in all_chunks]
            embeddings = self.embedding_generator.embed_documents(texts)

            if len(embeddings) != len(all_chunks):
                logger.error(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )
                raise IngestionPipelineError(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )

            # Step 6: Store in ChromaDB (if requested)
            if store_embeddings:
                logger.debug(f"Storing {len(all_chunks)} chunks in ChromaDB")
                ids = self.chroma_store.add_documents(all_chunks, embeddings)
                logger.info(
                    f"Successfully stored {len(ids)} stock data chunks "
                    f"in ChromaDB for {ticker_symbol}"
                )
                track_success(document_ingestion_total)
                return ids
            else:
                logger.debug("Skipping ChromaDB storage (store_embeddings=False)")
                track_success(document_ingestion_total)
                return [f"chunk_{i}" for i in range(len(all_chunks))]

        except YFinanceFetcherError as e:
            logger.error(f"yfinance fetching failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(f"yfinance fetching failed: {str(e)}") from e
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
            logger.error(
                f"Unexpected error processing stock data: {str(e)}", exc_info=True
            )
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Unexpected error processing stock data: {str(e)}"
            ) from e

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
        all_ids = []

        logger.info(f"Processing stock data for {len(ticker_symbols)} tickers")
        for idx, ticker in enumerate(ticker_symbols, 1):
            try:
                logger.info(f"Processing ticker {idx}/{len(ticker_symbols)}: {ticker}")
                ids = self.process_stock_data(
                    ticker,
                    include_history=include_history,
                    store_embeddings=store_embeddings,
                )
                all_ids.extend(ids)
            except IngestionPipelineError as e:
                # Log error but continue processing other tickers
                logger.warning(f"Failed to process {ticker}: {str(e)}")
                continue

        logger.info(
            f"Completed processing {len(ticker_symbols)} tickers, "
            f"stored {len(all_ids)} chunks"
        )
        return all_ids

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
        if not config.transcript_enabled:
            raise IngestionPipelineError(
                "Transcript integration is disabled in configuration"
            )

        if self.transcript_fetcher is None or self.transcript_parser is None:
            raise IngestionPipelineError(
                "Transcript fetcher or parser is not initialized"
            )

        logger.info(f"Processing transcript for {ticker} (date: {date})")
        try:
            # Step 1: Fetch transcript
            logger.debug(f"Fetching transcript for {ticker}")
            transcript_data = self.transcript_fetcher.fetch_transcript(
                ticker, date=date, source=source
            )

            if not transcript_data:
                logger.warning(f"No transcript found for {ticker} on {date}")
                return []

            # Step 2: Parse transcript
            logger.debug(f"Parsing transcript for {ticker}")
            parsed_transcript = self.transcript_parser.parse_transcript(transcript_data)

            # Step 3: Format for RAG ingestion
            formatted_text = self.transcript_parser.format_transcript_for_rag(
                parsed_transcript
            )

            # Step 4: Create Document object with metadata
            metadata = {
                "ticker": parsed_transcript["ticker"],
                "date": parsed_transcript.get("date", ""),
                "quarter": parsed_transcript.get("quarter", ""),
                "fiscal_year": parsed_transcript.get("fiscal_year", ""),
                "source": parsed_transcript.get("source", ""),
                "url": parsed_transcript.get("url", ""),
                "transcript_type": "earnings_call",
                "speakers": ", ".join(
                    [s["name"] for s in parsed_transcript.get("speakers", [])]
                ),
                "management_speakers": len(
                    [
                        s
                        for s in parsed_transcript.get("speakers", [])
                        if s["role"] == "management"
                    ]
                ),
                "analyst_speakers": len(
                    [
                        s
                        for s in parsed_transcript.get("speakers", [])
                        if s["role"] == "analyst"
                    ]
                ),
                "qa_count": len(parsed_transcript.get("qa_sections", [])),
                "guidance_count": len(parsed_transcript.get("forward_guidance", [])),
            }

            document = Document(page_content=formatted_text, metadata=metadata)

            # Step 5: Chunk document
            chunks = self.document_loader.chunk_document(document)

            if not chunks:
                logger.warning(f"No chunks generated from transcript for {ticker}")
                return []

            logger.info(f"Generated {len(chunks)} chunks from transcript for {ticker}")

            # Step 6: Generate embeddings
            logger.debug(f"Generating embeddings for {len(chunks)} chunks")
            texts = [chunk.page_content for chunk in chunks]
            embeddings = self.embedding_generator.embed_documents(texts)

            if len(embeddings) != len(chunks):
                logger.error(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(chunks)})"
                )
                raise IngestionPipelineError(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(chunks)})"
                )

            # Step 7: Store in ChromaDB (if requested)
            if store_embeddings:
                logger.debug(f"Storing {len(chunks)} chunks in ChromaDB")
                ids = self.chroma_store.add_documents(chunks, embeddings)
                logger.info(
                    f"Successfully stored {len(ids)} transcript chunks "
                    f"in ChromaDB for {ticker}"
                )
                track_success(document_ingestion_total)
                return ids
            else:
                logger.debug("Skipping ChromaDB storage (store_embeddings=False)")
                track_success(document_ingestion_total)
                return [f"chunk_{i}" for i in range(len(chunks))]

        except TranscriptFetcherError as e:
            logger.error(f"Transcript fetching failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(f"Transcript fetching failed: {str(e)}") from e
        except TranscriptParserError as e:
            logger.error(f"Transcript parsing failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(f"Transcript parsing failed: {str(e)}") from e
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
            logger.error(
                f"Unexpected error processing transcript: {str(e)}", exc_info=True
            )
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Unexpected error processing transcript: {str(e)}"
            ) from e

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
        all_ids = []

        logger.info(f"Processing transcripts for {len(ticker_symbols)} tickers")
        for idx, ticker in enumerate(ticker_symbols, 1):
            try:
                logger.info(
                    f"Processing transcript {idx}/{len(ticker_symbols)}: {ticker}"
                )
                ids = self.process_transcript(
                    ticker,
                    date=date,
                    source=source,
                    store_embeddings=store_embeddings,
                )
                all_ids.extend(ids)
            except IngestionPipelineError as e:
                # Log error but continue processing other tickers
                logger.warning(f"Failed to process transcript for {ticker}: {str(e)}")
                continue

        logger.info(
            f"Completed processing {len(ticker_symbols)} transcripts, "
            f"stored {len(all_ids)} chunks"
        )
        return all_ids

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

            # Step 2: Convert to Document objects
            logger.debug(f"Converting {len(articles)} articles to Document objects")
            documents = self.news_fetcher.to_documents(articles)

            if not documents:
                logger.warning("No documents generated from news articles")
                return []

            # Step 3: Chunk documents
            all_chunks = []
            for doc in documents:
                chunks = self.document_loader.chunk_document(doc)
                all_chunks.extend(chunks)

            if not all_chunks:
                logger.warning("No chunks generated from news articles")
                return []

            logger.info(f"Generated {len(all_chunks)} chunks from news articles")

            # Step 4: Generate embeddings
            logger.debug(f"Generating embeddings for {len(all_chunks)} chunks")
            texts = [chunk.page_content for chunk in all_chunks]
            embeddings = self.embedding_generator.embed_documents(texts)

            if len(embeddings) != len(all_chunks):
                logger.error(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )
                raise IngestionPipelineError(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )

            # Step 5: Store in ChromaDB (if requested)
            if store_embeddings:
                logger.debug(f"Storing {len(all_chunks)} chunks in ChromaDB")
                ids = self.chroma_store.add_documents(all_chunks, embeddings)
                logger.info(
                    f"Successfully stored {len(ids)} news article chunks in ChromaDB"
                )
                track_success(document_ingestion_total)
                return ids
            else:
                logger.debug("Skipping ChromaDB storage (store_embeddings=False)")
                track_success(document_ingestion_total)
                return [f"chunk_{i}" for i in range(len(all_chunks))]

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
        if not config.economic_calendar_enabled:
            raise IngestionPipelineError(
                "Economic calendar integration is disabled in configuration"
            )

        if self.economic_calendar_fetcher is None:
            raise IngestionPipelineError("Economic calendar fetcher is not initialized")

        logger.info("Processing economic calendar events")
        try:
            # Step 1: Fetch economic calendar events
            logger.debug("Fetching economic calendar events")
            events = self.economic_calendar_fetcher.fetch_calendar(
                start_date=start_date,
                end_date=end_date,
                country=country,
                importance=importance,
            )

            if not events:
                logger.warning("No economic calendar events fetched")
                return []

            # Step 2: Convert to Document objects
            logger.debug(f"Converting {len(events)} events to Document objects")
            documents = []
            for event in events:
                formatted_text = self.economic_calendar_fetcher.format_event_for_rag(
                    event
                )
                metadata = self.economic_calendar_fetcher.get_event_metadata(event)
                document = Document(page_content=formatted_text, metadata=metadata)
                documents.append(document)

            if not documents:
                logger.warning("No documents generated from economic calendar events")
                return []

            # Step 3: Chunk documents
            all_chunks = []
            for doc in documents:
                chunks = self.document_loader.chunk_document(doc)
                all_chunks.extend(chunks)

            if not all_chunks:
                logger.warning("No chunks generated from economic calendar events")
                return []

            logger.info(
                f"Generated {len(all_chunks)} chunks from economic calendar events"
            )

            # Step 4: Generate embeddings
            logger.debug(f"Generating embeddings for {len(all_chunks)} chunks")
            texts = [chunk.page_content for chunk in all_chunks]
            embeddings = self.embedding_generator.embed_documents(texts)

            if len(embeddings) != len(all_chunks):
                logger.error(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )
                raise IngestionPipelineError(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )

            # Step 5: Store in ChromaDB (if requested)
            if store_embeddings:
                logger.debug(f"Storing {len(all_chunks)} chunks in ChromaDB")
                ids = self.chroma_store.add_documents(all_chunks, embeddings)
                logger.info(
                    f"Successfully stored {len(ids)} economic calendar "
                    f"chunks in ChromaDB"
                )
                track_success(document_ingestion_total)
                return ids
            else:
                logger.debug("Skipping ChromaDB storage (store_embeddings=False)")
                track_success(document_ingestion_total)
                return [f"chunk_{i}" for i in range(len(all_chunks))]

        except EconomicCalendarFetcherError as e:
            logger.error(f"Economic calendar fetching failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Economic calendar fetching failed: {str(e)}"
            ) from e
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
            logger.error(
                f"Unexpected error processing economic calendar: {str(e)}",
                exc_info=True,
            )
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Unexpected error processing economic calendar: {str(e)}"
            ) from e

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
        if not config.fred_enabled:
            raise IngestionPipelineError(
                "FRED integration is disabled in configuration"
            )

        if self.fred_fetcher is None:
            raise IngestionPipelineError("FRED fetcher is not initialized")

        logger.info(f"Processing {len(series_ids)} FRED series")
        try:
            # Step 1: Fetch FRED series data
            logger.debug(f"Fetching FRED series: {series_ids}")
            series_data = self.fred_fetcher.fetch_multiple_series(
                series_ids, start_date=start_date, end_date=end_date
            )

            if not series_data:
                logger.warning("No FRED series data fetched")
                return []

            # Step 2: Convert to Document objects
            logger.debug(f"Converting {len(series_data)} series to Document objects")
            documents = []
            for series_id, data in series_data.items():
                if data.get("data") is None:
                    logger.warning(f"Skipping series {series_id}: no data available")
                    continue

                formatted_text = self.fred_fetcher.format_series_for_rag(data)
                metadata = self.fred_fetcher.get_series_metadata(data)
                document = Document(page_content=formatted_text, metadata=metadata)
                documents.append(document)

            if not documents:
                logger.warning("No documents generated from FRED series")
                return []

            # Step 3: Chunk documents
            all_chunks = []
            for doc in documents:
                chunks = self.document_loader.chunk_document(doc)
                all_chunks.extend(chunks)

            if not all_chunks:
                logger.warning("No chunks generated from FRED series")
                return []

            logger.info(f"Generated {len(all_chunks)} chunks from FRED series")

            # Step 4: Generate embeddings
            logger.debug(f"Generating embeddings for {len(all_chunks)} chunks")
            texts = [chunk.page_content for chunk in all_chunks]
            embeddings = self.embedding_generator.embed_documents(texts)

            if len(embeddings) != len(all_chunks):
                logger.error(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )
                raise IngestionPipelineError(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )

            # Step 5: Store in ChromaDB (if requested)
            if store_embeddings:
                logger.debug(f"Storing {len(all_chunks)} chunks in ChromaDB")
                ids = self.chroma_store.add_documents(all_chunks, embeddings)
                logger.info(
                    f"Successfully stored {len(ids)} FRED series chunks in ChromaDB"
                )
                track_success(document_ingestion_total)
                return ids
            else:
                logger.debug("Skipping ChromaDB storage (store_embeddings=False)")
                track_success(document_ingestion_total)
                return [f"chunk_{i}" for i in range(len(all_chunks))]

        except FREDFetcherError as e:
            logger.error(f"FRED fetching failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(f"FRED fetching failed: {str(e)}") from e
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
            logger.error(
                f"Unexpected error processing FRED series: {str(e)}", exc_info=True
            )
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Unexpected error processing FRED series: {str(e)}"
            ) from e

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
        if not self.world_bank_fetcher:
            raise IngestionPipelineError(
                "World Bank integration is disabled. "
                "Set WORLD_BANK_ENABLED=true in .env file."
            )

        logger.info(f"Processing {len(indicator_codes)} World Bank indicators")
        try:
            # Step 1: Fetch World Bank indicator data
            logger.debug(f"Fetching World Bank indicators: {indicator_codes}")
            indicator_data = self.world_bank_fetcher.fetch_multiple_indicators(
                indicator_codes,
                country_codes=country_codes,
                start_year=start_year,
                end_year=end_year,
            )

            if not indicator_data:
                logger.warning("No World Bank indicator data fetched")
                return []

            # Step 2: Convert to Document objects
            logger.debug(
                f"Converting {len(indicator_data)} indicators to Document objects"
            )
            documents = []
            for indicator_code, data in indicator_data.items():
                if data.get("data") is None:
                    logger.warning(
                        f"Skipping indicator {indicator_code}: no data available"
                    )
                    continue

                formatted_text = self.world_bank_fetcher.format_indicator_for_rag(data)
                metadata = self.world_bank_fetcher.get_indicator_metadata(data)
                document = Document(page_content=formatted_text, metadata=metadata)
                documents.append(document)

            if not documents:
                logger.warning("No documents generated from World Bank indicators")
                return []

            # Step 3: Chunk documents
            all_chunks = []
            for doc in documents:
                chunks = self.document_loader.chunk_document(doc)
                all_chunks.extend(chunks)

            if not all_chunks:
                logger.warning("No chunks generated from World Bank indicators")
                return []

            logger.info(
                f"Generated {len(all_chunks)} chunks from World Bank indicators"
            )

            # Step 4: Generate embeddings
            logger.debug(f"Generating embeddings for {len(all_chunks)} chunks")
            texts = [chunk.page_content for chunk in all_chunks]
            embeddings = self.embedding_generator.embed_documents(texts)

            if len(embeddings) != len(all_chunks):
                logger.error(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )
                raise IngestionPipelineError(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )

            logger.debug(f"Generated {len(embeddings)} embeddings")

            # Track chunks created
            document_chunks_created.observe(len(all_chunks))

            # Step 5: Store in ChromaDB (if requested)
            if store_embeddings:
                logger.debug(f"Storing {len(all_chunks)} chunks in ChromaDB")
                ids = self.chroma_store.add_documents(all_chunks, embeddings)
                logger.info(
                    f"Successfully stored {len(ids)} chunks from World Bank indicators"
                )
                track_success(document_ingestion_total)
                return ids
            else:
                logger.debug("Skipping ChromaDB storage (store_embeddings=False)")
                track_success(document_ingestion_total)
                return [f"chunk_{i}" for i in range(len(all_chunks))]

        except WorldBankFetcherError as e:
            logger.error(f"World Bank fetching failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(f"World Bank fetching failed: {str(e)}") from e
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
            logger.error(
                f"Unexpected error processing World Bank indicators: {str(e)}",
                exc_info=True,
            )
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Unexpected error processing World Bank indicators: {str(e)}"
            ) from e

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
        if not self.imf_fetcher:
            raise IngestionPipelineError(
                "IMF integration is disabled. Set IMF_ENABLED=true in .env file."
            )

        logger.info(f"Processing {len(indicator_codes)} IMF indicators")
        try:
            # Step 1: Fetch IMF indicator data
            logger.debug(f"Fetching IMF indicators: {indicator_codes}")
            indicator_data = self.imf_fetcher.fetch_multiple_indicators(
                indicator_codes,
                country_codes=country_codes,
                start_year=start_year,
                end_year=end_year,
            )

            if not indicator_data:
                logger.warning("No IMF indicator data fetched")
                return []

            # Step 2: Convert to Document objects
            logger.debug(
                f"Converting {len(indicator_data)} indicators to Document objects"
            )
            documents = []
            for indicator_code, data in indicator_data.items():
                if data.get("data") is None:
                    logger.warning(
                        f"Skipping indicator {indicator_code}: no data available"
                    )
                    continue

                formatted_text = self.imf_fetcher.format_indicator_for_rag(data)
                metadata = self.imf_fetcher.get_indicator_metadata(data)
                document = Document(page_content=formatted_text, metadata=metadata)
                documents.append(document)

            if not documents:
                logger.warning("No documents generated from IMF indicators")
                return []

            # Step 3: Chunk documents
            all_chunks = []
            for doc in documents:
                chunks = self.document_loader.chunk_document(doc)
                all_chunks.extend(chunks)

            if not all_chunks:
                logger.warning("No chunks generated from IMF indicators")
                return []

            logger.info(f"Generated {len(all_chunks)} chunks from IMF indicators")

            # Step 4: Generate embeddings
            logger.debug(f"Generating embeddings for {len(all_chunks)} chunks")
            texts = [chunk.page_content for chunk in all_chunks]
            embeddings = self.embedding_generator.embed_documents(texts)

            if len(embeddings) != len(all_chunks):
                logger.error(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )
                raise IngestionPipelineError(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )

            logger.debug(f"Generated {len(embeddings)} embeddings")

            # Track chunks created
            document_chunks_created.observe(len(all_chunks))

            # Step 5: Store in ChromaDB (if requested)
            if store_embeddings:
                logger.debug(f"Storing {len(all_chunks)} chunks in ChromaDB")
                ids = self.chroma_store.add_documents(all_chunks, embeddings)
                logger.info(
                    f"Successfully stored {len(ids)} chunks from IMF indicators"
                )
                track_success(document_ingestion_total)
                return ids
            else:
                logger.debug("Skipping ChromaDB storage (store_embeddings=False)")
                track_success(document_ingestion_total)
                return [f"chunk_{i}" for i in range(len(all_chunks))]

        except IMFFetcherError as e:
            logger.error(f"IMF fetching failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(f"IMF fetching failed: {str(e)}") from e
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
            logger.error(
                f"Unexpected error processing IMF indicators: {str(e)}", exc_info=True
            )
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Unexpected error processing IMF indicators: {str(e)}"
            ) from e

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
        if not config.central_bank_enabled:
            raise IngestionPipelineError(
                "Central bank integration is disabled. "
                "Set CENTRAL_BANK_ENABLED=true in .env file."
            )

        if self.central_bank_fetcher is None:
            raise IngestionPipelineError("Central bank fetcher is not initialized")

        # Default to all communication types if not specified
        if comm_types is None:
            comm_types = ["fomc_statement", "fomc_minutes", "fomc_press_conference"]

        logger.info(f"Processing central bank communications: {comm_types}")
        try:
            # Step 1: Fetch central bank communications
            all_communications = []
            for comm_type in comm_types:
                logger.debug(f"Fetching {comm_type}")
                try:
                    if comm_type == "fomc_statement":
                        communications = (
                            self.central_bank_fetcher.fetch_fomc_statements(
                                start_date=start_date,
                                end_date=end_date,
                                limit=limit,
                            )
                        )
                    elif comm_type == "fomc_minutes":
                        communications = self.central_bank_fetcher.fetch_fomc_minutes(
                            start_date=start_date,
                            end_date=end_date,
                            limit=limit,
                        )
                    elif comm_type == "fomc_press_conference":
                        communications = (
                            self.central_bank_fetcher.fetch_fomc_press_conferences(
                                start_date=start_date,
                                end_date=end_date,
                                limit=limit,
                            )
                        )
                    else:
                        logger.warning(f"Unknown communication type: {comm_type}")
                        continue

                    all_communications.extend(communications)
                except CentralBankFetcherError as e:
                    logger.warning(f"Failed to fetch {comm_type}: {str(e)}")
                    continue

            if not all_communications:
                logger.warning("No central bank communications fetched")
                return []

            logger.info(
                f"Fetched {len(all_communications)} central bank communications"
            )

            # Step 2: Convert to Document objects
            logger.debug(
                f"Converting {len(all_communications)} communications "
                f"to Document objects"
            )
            documents = self.central_bank_fetcher.to_documents(all_communications)

            if not documents:
                logger.warning(
                    "No documents generated from central bank communications"
                )
                return []

            # Step 3: Chunk documents
            all_chunks = []
            for doc in documents:
                chunks = self.document_loader.chunk_document(doc)
                all_chunks.extend(chunks)

            if not all_chunks:
                logger.warning("No chunks generated from central bank communications")
                return []

            logger.info(
                f"Generated {len(all_chunks)} chunks from central bank communications"
            )

            # Step 4: Generate embeddings
            logger.debug(f"Generating embeddings for {len(all_chunks)} chunks")
            texts = [chunk.page_content for chunk in all_chunks]
            embeddings = self.embedding_generator.embed_documents(texts)

            if len(embeddings) != len(all_chunks):
                logger.error(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )
                raise IngestionPipelineError(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(all_chunks)})"
                )

            logger.debug(f"Generated {len(embeddings)} embeddings")

            # Track chunks created
            document_chunks_created.observe(len(all_chunks))

            # Step 5: Store in ChromaDB (if requested)
            if store_embeddings:
                logger.debug(f"Storing {len(all_chunks)} chunks in ChromaDB")
                ids = self.chroma_store.add_documents(all_chunks, embeddings)
                logger.info(
                    f"Successfully stored {len(ids)} chunks "
                    f"from central bank communications"
                )
                track_success(document_ingestion_total)
                return ids
            else:
                logger.debug("Skipping ChromaDB storage (store_embeddings=False)")
                track_success(document_ingestion_total)
                return [f"chunk_{i}" for i in range(len(all_chunks))]

        except CentralBankFetcherError as e:
            logger.error(f"Central bank fetching failed: {str(e)}", exc_info=True)
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Central bank fetching failed: {str(e)}"
            ) from e
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
            logger.error(
                f"Unexpected error processing central bank communications: {str(e)}",
                exc_info=True,
            )
            track_error(document_ingestion_total)
            raise IngestionPipelineError(
                f"Unexpected error processing central bank communications: {str(e)}"
            ) from e


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
