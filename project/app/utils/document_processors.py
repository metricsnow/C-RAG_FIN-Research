"""
Document processing utilities for ingestion pipeline.

Provides common functions for chunking, embedding generation, and storage
that are used across multiple data source processors.
"""

from typing import List

from langchain_core.documents import Document

from app.rag.embedding_factory import EmbeddingError, EmbeddingGenerator
from app.utils.logger import get_logger
from app.utils.metrics import (
    document_chunks_created,
    track_error,
    track_success,
)
from app.vector_db import ChromaStore, ChromaStoreError

logger = get_logger(__name__)


def generate_and_store_embeddings(
    chunks: List[Document],
    embedding_generator: EmbeddingGenerator,
    chroma_store: ChromaStore,
    store_embeddings: bool = True,
    source_name: str = "documents",
) -> List[str]:
    """
    Generate embeddings for chunks and store them in ChromaDB.

    This is a common pattern used across all data source processors:
    - Generate embeddings for chunks
    - Validate embedding count matches chunk count
    - Store in ChromaDB (if requested)
    - Track metrics

    Args:
        chunks: List of Document chunks to process
        embedding_generator: EmbeddingGenerator instance
        chroma_store: ChromaStore instance
        store_embeddings: Whether to store embeddings in ChromaDB (default: True)
        source_name: Name of data source for logging (default: "documents")

    Returns:
        List of document chunk IDs stored in ChromaDB

    Raises:
        ValueError: If embedding count doesn't match chunk count
        EmbeddingError: If embedding generation fails
        ChromaStoreError: If storage fails
    """
    if not chunks:
        logger.warning(f"No chunks provided for {source_name}")
        return []

    logger.debug(f"Generating embeddings for {len(chunks)} {source_name} chunks")
    texts = [chunk.page_content for chunk in chunks]
    embeddings = embedding_generator.embed_documents(texts)

    if len(embeddings) != len(chunks):
        error_msg = (
            f"Embedding count ({len(embeddings)}) does not match "
            f"chunk count ({len(chunks)}) for {source_name}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.debug(f"Generated {len(embeddings)} embeddings for {source_name}")

    # Track chunks created
    document_chunks_created.observe(len(chunks))

    # Store in ChromaDB (if requested)
    if store_embeddings:
        logger.debug(f"Storing {len(chunks)} {source_name} chunks in ChromaDB")
        try:
            ids = chroma_store.add_documents(chunks, embeddings)
            logger.info(
                f"Successfully stored {len(ids)} {source_name} chunks in ChromaDB"
            )
            track_success(document_chunks_created)
            return ids
        except ChromaStoreError as e:
            logger.error(f"ChromaDB storage failed for {source_name}: {str(e)}")
            track_error(document_chunks_created)
            raise
    else:
        logger.debug(f"Skipping ChromaDB storage for {source_name} (store_embeddings=False)")
        track_success(document_chunks_created)
        return [f"chunk_{i}" for i in range(len(chunks))]

