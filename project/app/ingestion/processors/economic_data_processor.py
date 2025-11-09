"""
Economic data processor for ingestion pipeline.

Handles processing of economic data from multiple sources:
- Economic Calendar
- FRED (Federal Reserve Economic Data)
- World Bank
- IMF (International Monetary Fund)
- Central Bank communications
"""

from typing import List, Optional

from langchain_core.documents import Document

from app.ingestion.central_bank_fetcher import (
    CentralBankFetcher,
    CentralBankFetcherError,
)
from app.ingestion.economic_calendar_fetcher import (
    EconomicCalendarFetcher,
    EconomicCalendarFetcherError,
)
from app.ingestion.fred_fetcher import FREDFetcher, FREDFetcherError
from app.ingestion.imf_fetcher import IMFFetcher, IMFFetcherError
from app.ingestion.processors.base_processor import BaseProcessor
from app.ingestion.world_bank_fetcher import (
    WorldBankFetcher,
    WorldBankFetcherError,
)
from app.rag.embedding_factory import EmbeddingError
from app.utils.config import config
from app.utils.logger import get_logger
from app.utils.metrics import document_ingestion_total, track_error
from app.vector_db import ChromaStoreError

logger = get_logger(__name__)


class EconomicDataProcessor(BaseProcessor):
    """
    Processor for economic data ingestion.

    Handles fetching, formatting, chunking, embedding, and storage of economic data
    from multiple sources.
    """

    def __init__(
        self,
        document_loader,
        embedding_generator,
        chroma_store,
        economic_calendar_fetcher: Optional[EconomicCalendarFetcher] = None,
        fred_fetcher: Optional[FREDFetcher] = None,
        world_bank_fetcher: Optional[WorldBankFetcher] = None,
        imf_fetcher: Optional[IMFFetcher] = None,
        central_bank_fetcher: Optional[CentralBankFetcher] = None,
        sentiment_analyzer=None,
    ):
        """
        Initialize economic data processor.

        Args:
            document_loader: DocumentLoader instance
            embedding_generator: EmbeddingGenerator instance
            chroma_store: ChromaStore instance
            economic_calendar_fetcher: Optional EconomicCalendarFetcher instance
            fred_fetcher: Optional FREDFetcher instance
            world_bank_fetcher: Optional WorldBankFetcher instance
            imf_fetcher: Optional IMFFetcher instance
            central_bank_fetcher: Optional CentralBankFetcher instance
            sentiment_analyzer: Optional SentimentAnalyzer instance
        """
        super().__init__(
            document_loader, embedding_generator, chroma_store, sentiment_analyzer
        )
        self.economic_calendar_fetcher = economic_calendar_fetcher
        self.fred_fetcher = fred_fetcher
        self.world_bank_fetcher = world_bank_fetcher
        self.imf_fetcher = imf_fetcher
        self.central_bank_fetcher = central_bank_fetcher

    def _process_fetched_documents(
        self, documents: List[Document], source_name: str, store_embeddings: bool
    ) -> List[str]:
        """
        Common method to process fetched documents: chunk, embed, store.

        Args:
            documents: List of Document objects
            source_name: Name of data source for logging
            store_embeddings: Whether to store embeddings

        Returns:
            List of chunk IDs
        """
        if not documents:
            logger.warning(f"No documents generated from {source_name}")
            return []

        # Chunk documents
        all_chunks = []
        for doc in documents:
            chunks = self.document_loader.chunk_document(doc)
            all_chunks.extend(chunks)

        if not all_chunks:
            logger.warning(f"No chunks generated from {source_name}")
            return []

        logger.info(f"Generated {len(all_chunks)} chunks from {source_name}")

        # Generate embeddings and store using utility
        from app.utils.document_processors import generate_and_store_embeddings

        return generate_and_store_embeddings(
            chunks=all_chunks,
            embedding_generator=self.embedding_generator,
            chroma_store=self.chroma_store,
            store_embeddings=store_embeddings,
            source_name=source_name,
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
        from app.ingestion.pipeline import IngestionPipelineError

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

            # Step 3: Process documents
            return self._process_fetched_documents(
                documents, "economic calendar events", store_embeddings
            )

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
        from app.ingestion.pipeline import IngestionPipelineError

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

            # Step 3: Process documents
            return self._process_fetched_documents(
                documents, "FRED series", store_embeddings
            )

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
        from app.ingestion.pipeline import IngestionPipelineError

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

            # Step 3: Process documents
            return self._process_fetched_documents(
                documents, "World Bank indicators", store_embeddings
            )

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
        from app.ingestion.pipeline import IngestionPipelineError

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

            # Step 3: Process documents
            return self._process_fetched_documents(
                documents, "IMF indicators", store_embeddings
            )

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
        from app.ingestion.pipeline import IngestionPipelineError

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

            # Step 3: Process documents
            return self._process_fetched_documents(
                documents, "central bank communications", store_embeddings
            )

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
