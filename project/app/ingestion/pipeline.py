"""
Document ingestion pipeline with embedding generation and ChromaDB storage.

Integrates document loading, chunking, embedding generation, and vector storage.
"""

from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document

from app.ingestion.document_loader import DocumentIngestionError, DocumentLoader
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
                    logger.debug(f"Skipping ChromaDB storage (store_embeddings=False)")
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
            f"Completed processing {len(file_paths)} documents, stored {len(all_ids)} chunks"
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
                    raise IngestionPipelineError(f"No chunks generated from document")

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
            f"Completed processing {len(documents)} document objects, stored {len(all_ids)} chunks"
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
            f"Searching for similar documents: query='{query_text[:50]}...', n_results={n_results}"
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
            for i, (doc_id, doc_text, metadata) in enumerate(
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
