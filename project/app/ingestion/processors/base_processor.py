"""
Base processor class for ingestion pipeline.

Provides common functionality for all data source processors.
"""

from typing import List, Optional

from langchain_core.documents import Document

from app.ingestion.document_loader import DocumentLoader
from app.ingestion.sentiment_analyzer import SentimentAnalyzer
from app.rag.embedding_factory import EmbeddingGenerator
from app.utils.document_processors import generate_and_store_embeddings
from app.utils.logger import get_logger
from app.vector_db import ChromaStore

logger = get_logger(__name__)


class BaseProcessor:
    """
    Base class for data source processors.

    Provides common functionality for chunking, embedding generation,
    and storage that is shared across all data source types.
    """

    def __init__(
        self,
        document_loader: DocumentLoader,
        embedding_generator: EmbeddingGenerator,
        chroma_store: ChromaStore,
        sentiment_analyzer: Optional[SentimentAnalyzer] = None,
    ):
        """
        Initialize base processor.

        Args:
            document_loader: DocumentLoader instance for chunking
            embedding_generator: EmbeddingGenerator instance for embeddings
            chroma_store: ChromaStore instance for storage
            sentiment_analyzer: Optional SentimentAnalyzer for enrichment
        """
        self.document_loader = document_loader
        self.embedding_generator = embedding_generator
        self.chroma_store = chroma_store
        self.sentiment_analyzer = sentiment_analyzer

    def enrich_with_sentiment(self, document: Document) -> Document:
        """
        Enrich document metadata with sentiment analysis.

        Args:
            document: Document to enrich

        Returns:
            Document with enriched metadata
        """
        if self.sentiment_analyzer is None:
            return document

        try:
            from app.utils.config import config

            text = document.page_content
            if not text or not text.strip():
                return document

            # Perform comprehensive sentiment analysis
            analysis = self.sentiment_analyzer.analyze_document(
                text,
                extract_guidance=config.sentiment_extract_guidance,
                extract_risks=config.sentiment_extract_risks,
            )

            # Add sentiment metadata
            overall = analysis["sentiment"]
            sentiment_metadata = {
                "sentiment": overall["overall_sentiment"],
                "sentiment_score": overall["overall_score"],
                "sentiment_model": overall.get("model", "unknown"),
            }

            # Add model-specific scores if available
            if analysis["sentiment"].get("finbert"):
                finbert = analysis["sentiment"]["finbert"]
                sentiment_metadata["sentiment_finbert"] = finbert["sentiment"]
                sentiment_metadata["sentiment_finbert_score"] = finbert["score"]
                sentiment_metadata["sentiment_finbert_confidence"] = finbert.get(
                    "confidence", 0.0
                )

            if analysis["sentiment"].get("vader"):
                vader = analysis["sentiment"]["vader"]
                sentiment_metadata["sentiment_vader"] = vader["sentiment"]
                sentiment_metadata["sentiment_vader_score"] = vader["score"]

            if analysis["sentiment"].get("textblob"):
                textblob = analysis["sentiment"]["textblob"]
                sentiment_metadata["sentiment_textblob"] = textblob["sentiment"]
                sentiment_metadata["sentiment_textblob_score"] = textblob["score"]

            # Add forward guidance metadata
            if config.sentiment_extract_guidance:
                sentiment_metadata["forward_guidance_count"] = analysis.get(
                    "forward_guidance_count", 0
                )
                sentiment_metadata["has_forward_guidance"] = (
                    analysis.get("forward_guidance_count", 0) > 0
                )

            # Add risk factors metadata
            if config.sentiment_extract_risks:
                sentiment_metadata["risk_factors_count"] = analysis.get(
                    "risk_factors_count", 0
                )
                sentiment_metadata["has_risk_factors"] = (
                    analysis.get("risk_factors_count", 0) > 0
                )

            # Merge with existing metadata
            enriched_metadata = {**document.metadata, **sentiment_metadata}

            # Create new document with enriched metadata
            return Document(
                page_content=document.page_content, metadata=enriched_metadata
            )

        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {str(e)}")
            return document

    def process_documents_to_chunks(
        self,
        documents: List[Document],
        store_embeddings: bool = True,
        source_name: str = "documents",
    ) -> List[str]:
        """
        Process documents: chunk, embed, and store.

        Common pattern used across all processors.

        Args:
            documents: List of Document objects to process
            store_embeddings: Whether to store embeddings in ChromaDB
            source_name: Name of data source for logging

        Returns:
            List of document chunk IDs stored in ChromaDB
        """
        logger.info(f"Processing {len(documents)} {source_name} document objects")
        all_chunks = []

        for idx, doc in enumerate(documents, 1):
            try:
                logger.debug(
                    f"Processing {source_name} document {idx}/{len(documents)}"
                )
                # Enrich document with sentiment analysis if enabled
                if self.sentiment_analyzer is not None:
                    doc = self.enrich_with_sentiment(doc)
                # Chunk the document
                chunks = self.document_loader.chunk_document(doc)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.warning(
                    f"Failed to process {source_name} document {idx}: {str(e)}",
                    exc_info=True,
                )
                continue

        if not all_chunks:
            logger.warning(f"No chunks generated from {source_name} documents")
            return []

        logger.info(
            f"Generated {len(all_chunks)} chunks from {len(documents)} "
            f"{source_name} documents"
        )

        # Generate embeddings and store using utility function
        return generate_and_store_embeddings(
            chunks=all_chunks,
            embedding_generator=self.embedding_generator,
            chroma_store=self.chroma_store,
            store_embeddings=store_embeddings,
            source_name=source_name,
        )
