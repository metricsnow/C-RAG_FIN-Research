"""
ChromaDB vector store implementation.

Handles ChromaDB setup, document storage, and similarity search operations.
"""

import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any

import chromadb
from chromadb import Collection
from chromadb.config import Settings
from langchain_core.documents import Document

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChromaStoreError(Exception):
    """Custom exception for ChromaDB operations."""

    pass


class ChromaStore:
    """
    ChromaDB vector store for document embeddings.

    Supports persistent storage and similarity search operations.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: Optional[Path] = None,
    ):
        """
        Initialize ChromaDB vector store.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory for persistent storage.
                If None, uses config.CHROMA_DB_DIR
        """
        self.collection_name = collection_name

        # Use configured directory or provided path
        if persist_directory is None:
            persist_directory = config.CHROMA_DB_DIR

        # Ensure directory exists
        persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize persistent client
        logger.info(f"Initializing ChromaDB client: persist_directory={persist_directory}")
        try:
            self.client = chromadb.PersistentClient(
                path=str(persist_directory),
            )
            logger.debug("ChromaDB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {str(e)}", exc_info=True)
            raise ChromaStoreError(
                f"Failed to initialize ChromaDB client: {str(e)}"
            ) from e

        # Get or create collection
        self.collection: Optional[Collection] = None
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Ensure collection exists, create if it doesn't."""
        logger.debug(f"Ensuring collection exists: {self.collection_name}")
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Document embeddings for RAG system"},
            )
            if self.collection is None:
                logger.error(f"Failed to get or create collection '{self.collection_name}'")
                raise ChromaStoreError(
                    f"Failed to get or create collection '{self.collection_name}'"
                )
            logger.info(f"Collection '{self.collection_name}' ready (count: {self.collection.count()})")
        except Exception as e:
            logger.error(
                f"Failed to get or create collection '{self.collection_name}': {str(e)}",
                exc_info=True
            )
            raise ChromaStoreError(
                f"Failed to get or create collection '{self.collection_name}': {str(e)}"
            ) from e

    def add_documents(
        self,
        documents: List[Document],
        embeddings: List[List[float]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Add documents with embeddings to ChromaDB.

        Args:
            documents: List of LangChain Document objects
            embeddings: List of embedding vectors for each document
            ids: Optional list of unique IDs. If None, generates UUIDs

        Returns:
            List of document IDs that were added

        Raises:
            ChromaStoreError: If adding documents fails
        """
        logger.info(f"Adding {len(documents)} documents to ChromaDB")
        if not documents:
            logger.error("Cannot add empty list of documents")
            raise ChromaStoreError("Cannot add empty list of documents")

        if len(documents) != len(embeddings):
            logger.error(
                f"Documents count ({len(documents)}) does not match "
                f"embeddings count ({len(embeddings)})"
            )
            raise ChromaStoreError(
                f"Documents count ({len(documents)}) does not match "
                f"embeddings count ({len(embeddings)})"
            )

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        if len(ids) != len(documents):
            raise ChromaStoreError(
                f"IDs count ({len(ids)}) does not match documents count ({len(documents)})"
            )

        if self.collection is None:
            raise ChromaStoreError("Collection is not initialized")

        try:
            # Extract texts and metadata
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]

            # Add to collection
            logger.debug(f"Adding documents to collection '{self.collection_name}'")
            # Type ignore for ChromaDB API compatibility
            self.collection.add(
                ids=ids,
                embeddings=embeddings,  # type: ignore[arg-type]
                documents=texts,
                metadatas=metadatas,  # type: ignore[arg-type]
            )

            logger.info(f"Successfully added {len(ids)} documents to ChromaDB")
            return ids
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {str(e)}", exc_info=True)
            raise ChromaStoreError(f"Failed to add documents to ChromaDB: {str(e)}") from e

    def query_by_embedding(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query collection by embedding vector.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return (default: 5)
            where: Optional metadata filter dictionary
            where_document: Optional document content filter

        Returns:
            Dictionary with keys: ids, distances, metadatas, documents

        Raises:
            ChromaStoreError: If query fails
        """
        if self.collection is None:
            raise ChromaStoreError("Collection is not initialized")

        logger.debug(f"Querying ChromaDB: n_results={n_results}")
        try:
            # Type ignore for ChromaDB API compatibility
            results = self.collection.query(
                query_embeddings=[query_embedding],  # type: ignore[arg-type]
                n_results=n_results,
                where=where,
                where_document=where_document,  # type: ignore[arg-type]
                include=["metadatas", "documents", "distances"],
            )
            logger.debug(f"Query returned {len(results.get('ids', [])[0] if results.get('ids') else [])} results")

            # Convert to simpler format (single query result)
            return {
                "ids": results["ids"][0] if results["ids"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "documents": results["documents"][0] if results["documents"] else [],
            }
        except Exception as e:
            logger.error(f"Failed to query ChromaDB: {str(e)}", exc_info=True)
            raise ChromaStoreError(f"Failed to query ChromaDB: {str(e)}") from e

    def query_by_text(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query collection by text (requires embedding function in collection).

        Args:
            query_text: Query text string
            n_results: Number of results to return (default: 5)
            where: Optional metadata filter dictionary
            where_document: Optional document content filter

        Returns:
            Dictionary with keys: ids, distances, metadatas, documents

        Raises:
            ChromaStoreError: If query fails
        """
        if self.collection is None:
            raise ChromaStoreError("Collection is not initialized")

        logger.debug(f"Querying ChromaDB by text: n_results={n_results}, query='{query_text[:50]}...'")
        try:
            # Type ignore for ChromaDB API compatibility
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
                where_document=where_document,  # type: ignore[arg-type]
                include=["metadatas", "documents", "distances"],
            )
            logger.debug(f"Query returned {len(results.get('ids', [])[0] if results.get('ids') else [])} results")

            # Convert to simpler format (single query result)
            return {
                "ids": results["ids"][0] if results["ids"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "documents": results["documents"][0] if results["documents"] else [],
            }
        except Exception as e:
            logger.error(f"Failed to query ChromaDB by text: {str(e)}", exc_info=True)
            raise ChromaStoreError(f"Failed to query ChromaDB by text: {str(e)}") from e

    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        """
        Retrieve documents by their IDs.

        Args:
            ids: List of document IDs to retrieve

        Returns:
            Dictionary with keys: ids, metadatas, documents

        Raises:
            ChromaStoreError: If retrieval fails
        """
        if self.collection is None:
            raise ChromaStoreError("Collection is not initialized")

        logger.debug(f"Getting documents by IDs: count={len(ids)}")
        try:
            results = self.collection.get(
                ids=ids,
                include=["metadatas", "documents"],
            )

            logger.debug(f"Retrieved {len(results.get('ids', []))} documents")
            return {
                "ids": results["ids"],
                "metadatas": results["metadatas"],
                "documents": results["documents"],
            }
        except Exception as e:
            logger.error(f"Failed to get documents by IDs: {str(e)}", exc_info=True)
            raise ChromaStoreError(f"Failed to get documents by IDs: {str(e)}") from e

    def get_all(self) -> Dict[str, Any]:
        """
        Retrieve all documents from the collection.

        Returns:
            Dictionary with keys: ids, metadatas, documents

        Raises:
            ChromaStoreError: If retrieval fails
        """
        if self.collection is None:
            raise ChromaStoreError("Collection is not initialized")

        logger.debug("Getting all documents from collection")
        try:
            # Get all documents (ChromaDB doesn't have a direct "get all" method)
            # We query with a large n_results or use get() with empty where clause
            results = self.collection.get(
                include=["metadatas", "documents"],
            )

            count = len(results.get("ids", []))
            logger.debug(f"Retrieved {count} documents from collection")
            return {
                "ids": results["ids"],
                "metadatas": results["metadatas"],
                "documents": results["documents"],
            }
        except Exception as e:
            logger.error(f"Failed to get all documents: {str(e)}", exc_info=True)
            raise ChromaStoreError(f"Failed to get all documents: {str(e)}") from e

    def count(self) -> int:
        """
        Get the number of documents in the collection.

        Returns:
            Number of documents in the collection

        Raises:
            ChromaStoreError: If count fails
        """
        if self.collection is None:
            raise ChromaStoreError("Collection is not initialized")

        try:
            count = self.collection.count()
            logger.debug(f"Collection '{self.collection_name}' contains {count} documents")
            return count
        except Exception as e:
            logger.error(f"Failed to count documents: {str(e)}", exc_info=True)
            raise ChromaStoreError(f"Failed to count documents: {str(e)}") from e

    def delete_collection(self) -> None:
        """
        Delete the collection from ChromaDB.

        Raises:
            ChromaStoreError: If deletion fails
        """
        logger.info(f"Deleting collection '{self.collection_name}'")
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = None
            logger.info(f"Successfully deleted collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Failed to delete collection '{self.collection_name}': {str(e)}", exc_info=True)
            raise ChromaStoreError(
                f"Failed to delete collection '{self.collection_name}': {str(e)}"
            ) from e

    def reset(self) -> None:
        """
        Reset the collection (delete all documents).

        Note: This deletes and recreates the collection.
        """
        logger.info(f"Resetting collection '{self.collection_name}'")
        try:
            self.delete_collection()
            self._ensure_collection()
            logger.info(f"Successfully reset collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Failed to reset collection: {str(e)}", exc_info=True)
            raise ChromaStoreError(f"Failed to reset collection: {str(e)}") from e

