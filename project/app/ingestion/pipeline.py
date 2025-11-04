"""
Document ingestion pipeline with embedding generation and ChromaDB storage.

Integrates document loading, chunking, embedding generation, and vector storage.
"""

from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document

from app.ingestion.document_loader import DocumentLoader, DocumentIngestionError
from app.rag.embedding_factory import EmbeddingGenerator, EmbeddingError
from app.vector_db import ChromaStore, ChromaStoreError
from app.utils.config import config


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
        try:
            # Step 1: Load and chunk document
            chunks = self.document_loader.process_document(file_path)

            if not chunks:
                raise IngestionPipelineError(f"No chunks generated from {file_path}")

            # Step 2: Generate embeddings
            texts = [chunk.page_content for chunk in chunks]
            embeddings = self.embedding_generator.embed_documents(texts)

            if len(embeddings) != len(chunks):
                raise IngestionPipelineError(
                    f"Embedding count ({len(embeddings)}) does not match "
                    f"chunk count ({len(chunks)})"
                )

            # Step 3: Store in ChromaDB (if requested)
            if store_embeddings:
                ids = self.chroma_store.add_documents(chunks, embeddings)
                return ids
            else:
                # Return placeholder IDs if not storing
                return [f"chunk_{i}" for i in range(len(chunks))]

        except DocumentIngestionError as e:
            raise IngestionPipelineError(f"Document ingestion failed: {str(e)}") from e
        except EmbeddingError as e:
            raise IngestionPipelineError(f"Embedding generation failed: {str(e)}") from e
        except ChromaStoreError as e:
            raise IngestionPipelineError(f"ChromaDB storage failed: {str(e)}") from e
        except Exception as e:
            raise IngestionPipelineError(f"Unexpected error in pipeline: {str(e)}") from e

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

        for file_path in file_paths:
            try:
                ids = self.process_document(file_path, store_embeddings=store_embeddings)
                all_ids.extend(ids)
            except IngestionPipelineError as e:
                # Log error but continue processing other files
                print(f"Warning: Failed to process {file_path}: {str(e)}")
                continue

        return all_ids

    def get_document_count(self) -> int:
        """
        Get the number of documents stored in ChromaDB.

        Returns:
            Number of documents in the collection
        """
        return self.chroma_store.count()

    def search_similar(
        self, query_text: str, n_results: int = 5
    ) -> List[Document]:
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
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.embed_query(query_text)

            # Search ChromaDB
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

            return documents

        except EmbeddingError as e:
            raise IngestionPipelineError(f"Query embedding failed: {str(e)}") from e
        except ChromaStoreError as e:
            raise IngestionPipelineError(f"ChromaDB search failed: {str(e)}") from e
        except Exception as e:
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

