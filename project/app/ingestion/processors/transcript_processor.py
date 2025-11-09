"""
Transcript processor for ingestion pipeline.

Handles processing of earnings call transcripts.
"""

from typing import List, Optional

from langchain_core.documents import Document

from app.ingestion.processors.base_processor import BaseProcessor
from app.ingestion.transcript_fetcher import TranscriptFetcher, TranscriptFetcherError
from app.ingestion.transcript_parser import TranscriptParser, TranscriptParserError
from app.rag.embedding_factory import EmbeddingError
from app.utils.config import config
from app.utils.logger import get_logger
from app.utils.metrics import document_ingestion_total, track_error
from app.vector_db import ChromaStoreError

logger = get_logger(__name__)


class TranscriptProcessor(BaseProcessor):
    """
    Processor for earnings call transcript ingestion.

    Handles fetching, parsing, chunking, embedding, and storage of transcripts.
    """

    def __init__(
        self,
        document_loader,
        embedding_generator,
        chroma_store,
        transcript_fetcher: TranscriptFetcher,
        transcript_parser: TranscriptParser,
        sentiment_analyzer=None,
    ):
        """
        Initialize transcript processor.

        Args:
            document_loader: DocumentLoader instance
            embedding_generator: EmbeddingGenerator instance
            chroma_store: ChromaStore instance
            transcript_fetcher: TranscriptFetcher instance
            transcript_parser: TranscriptParser instance
            sentiment_analyzer: Optional SentimentAnalyzer instance
        """
        super().__init__(
            document_loader, embedding_generator, chroma_store, sentiment_analyzer
        )
        self.transcript_fetcher = transcript_fetcher
        self.transcript_parser = transcript_parser

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
        from app.ingestion.pipeline import IngestionPipelineError

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

            # Step 5: Chunk document and process
            chunks = self.document_loader.chunk_document(document)

            if not chunks:
                logger.warning(f"No chunks generated from transcript for {ticker}")
                return []

            logger.info(f"Generated {len(chunks)} chunks from transcript for {ticker}")

            # Step 6: Generate embeddings and store using utility
            from app.utils.document_processors import generate_and_store_embeddings

            return generate_and_store_embeddings(
                chunks=chunks,
                embedding_generator=self.embedding_generator,
                chroma_store=self.chroma_store,
                store_embeddings=store_embeddings,
                source_name=f"transcript ({ticker})",
            )

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
        from app.ingestion.pipeline import IngestionPipelineError

        all_ids = []

        logger.info(f"Processing transcripts for {len(ticker_symbols)} tickers")
        for idx, ticker in enumerate(ticker_symbols, 1):
            try:
                logger.info(
                    f"Processing transcript {idx}/{len(ticker_symbols)}: {ticker}"
                )
                ids = self.process_transcript(
                    ticker, date=date, source=source, store_embeddings=store_embeddings
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
