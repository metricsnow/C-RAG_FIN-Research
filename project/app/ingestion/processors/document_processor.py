"""
Document processor for file-based document ingestion.

Handles processing of documents from file paths.
"""

from pathlib import Path
from typing import List

from app.ingestion.document_loader import DocumentIngestionError
from app.ingestion.processors.base_processor import BaseProcessor
from app.rag.embedding_factory import EmbeddingError
from app.utils.logger import get_logger
from app.utils.metrics import (
    document_ingestion_duration_seconds,
    document_ingestion_total,
    document_size_bytes,
    track_duration,
    track_error,
)
from app.vector_db import ChromaStoreError

logger = get_logger(__name__)


class DocumentProcessor(BaseProcessor):
    """
    Processor for file-based document ingestion.

    Handles loading, chunking, embedding, and storage of documents from file paths.
    """

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
        from app.ingestion.pipeline import IngestionPipelineError

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

                # Step 2: Generate embeddings and store (chunks are already created)
                from app.utils.document_processors import generate_and_store_embeddings

                return generate_and_store_embeddings(
                    chunks=chunks,
                    embedding_generator=self.embedding_generator,
                    chroma_store=self.chroma_store,
                    store_embeddings=store_embeddings,
                    source_name="document",
                )

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
        from app.ingestion.pipeline import IngestionPipelineError

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
