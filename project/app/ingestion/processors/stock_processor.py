"""
Stock data processor for ingestion pipeline.

Handles processing of stock data from yfinance.
"""

from typing import List

from langchain_core.documents import Document

from app.ingestion.processors.base_processor import BaseProcessor
from app.ingestion.stock_data_normalizer import StockDataNormalizer
from app.ingestion.yfinance_fetcher import YFinanceFetcher, YFinanceFetcherError
from app.rag.embedding_factory import EmbeddingError
from app.utils.config import config
from app.utils.logger import get_logger
from app.utils.metrics import document_ingestion_total, track_error
from app.vector_db import ChromaStoreError

logger = get_logger(__name__)


class StockProcessor(BaseProcessor):
    """
    Processor for stock data ingestion.

    Handles fetching, normalizing, chunking, embedding, and storage of stock data.
    """

    def __init__(
        self,
        document_loader,
        embedding_generator,
        chroma_store,
        yfinance_fetcher: YFinanceFetcher,
        stock_normalizer: StockDataNormalizer,
        sentiment_analyzer=None,
    ):
        """
        Initialize stock processor.

        Args:
            document_loader: DocumentLoader instance
            embedding_generator: EmbeddingGenerator instance
            chroma_store: ChromaStore instance
            yfinance_fetcher: YFinanceFetcher instance
            stock_normalizer: StockDataNormalizer instance
            sentiment_analyzer: Optional SentimentAnalyzer instance
        """
        super().__init__(
            document_loader, embedding_generator, chroma_store, sentiment_analyzer
        )
        self.yfinance_fetcher = yfinance_fetcher
        self.stock_normalizer = stock_normalizer

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
        from app.ingestion.pipeline import IngestionPipelineError

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
            documents = [
                Document(page_content=doc["text"], metadata=doc["metadata"])
                for doc in normalized_docs
            ]

            # Step 4: Chunk documents and process
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

            # Step 5: Generate embeddings and store using utility
            from app.utils.document_processors import generate_and_store_embeddings

            return generate_and_store_embeddings(
                chunks=all_chunks,
                embedding_generator=self.embedding_generator,
                chroma_store=self.chroma_store,
                store_embeddings=store_embeddings,
                source_name=f"stock data ({ticker_symbol})",
            )

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
        from app.ingestion.pipeline import IngestionPipelineError

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
