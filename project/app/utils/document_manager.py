"""
Document management utilities for ChromaDB operations.

Provides high-level functions for document listing, searching, filtering,
and statistics calculation for the document management UI.
"""

from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger
from app.vector_db.chroma_store import ChromaStore, ChromaStoreError

logger = get_logger(__name__)


class DocumentManagerError(Exception):
    """Custom exception for document management operations."""

    pass


class DocumentManager:
    """
    Document management utility for ChromaDB operations.

    Provides methods for listing, searching, filtering, and managing documents.
    """

    def __init__(self, chroma_store: Optional[ChromaStore] = None):
        """
        Initialize document manager.

        Args:
            chroma_store: Optional ChromaStore instance. If None, creates a new one.
        """
        self.chroma_store = chroma_store or ChromaStore()
        logger.debug("DocumentManager initialized")

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Get all documents with their metadata.

        Returns:
            List of document dictionaries with id, metadata, and content

        Raises:
            DocumentManagerError: If retrieval fails
        """
        try:
            all_data = self.chroma_store.get_all()
            documents = []

            for doc_id, metadata, content in zip(
                all_data.get("ids", []),
                all_data.get("metadatas", []),
                all_data.get("documents", []),
            ):
                documents.append(
                    {
                        "id": doc_id,
                        "metadata": metadata or {},
                        "content": content,
                    }
                )

            logger.debug(f"Retrieved {len(documents)} documents")
            return documents
        except ChromaStoreError as e:
            logger.error(f"Failed to get all documents: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to get all documents: {str(e)}") from e

    def get_documents_by_metadata(
        self,
        ticker: Optional[str] = None,
        form_type: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get documents filtered by metadata.

        Args:
            ticker: Optional ticker symbol filter
            form_type: Optional form type filter (e.g., '10-K', '10-Q', '8-K')
            filename: Optional filename filter (partial match)

        Returns:
            List of filtered document dictionaries

        Raises:
            DocumentManagerError: If retrieval fails
        """
        try:
            all_documents = self.get_all_documents()
            filtered = []

            for doc in all_documents:
                metadata = doc.get("metadata", {})
                match = True

                if ticker and metadata.get("ticker") != ticker:
                    match = False
                if form_type and metadata.get("form_type") != form_type:
                    match = False
                if filename:
                    doc_filename = metadata.get("filename", "") or metadata.get(
                        "source", ""
                    )
                    if filename.lower() not in doc_filename.lower():
                        match = False

                if match:
                    filtered.append(doc)

            logger.debug(
                f"Filtered documents: ticker={ticker}, form_type={form_type}, "
                f"filename={filename}, count={len(filtered)}"
            )
            return filtered
        except Exception as e:
            logger.error(f"Failed to filter documents: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to filter documents: {str(e)}") from e

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single document by its ID.

        Args:
            doc_id: Document ID

        Returns:
            Document dictionary or None if not found

        Raises:
            DocumentManagerError: If retrieval fails
        """
        try:
            result = self.chroma_store.get_by_ids([doc_id])
            if result.get("ids"):
                return {
                    "id": result["ids"][0],
                    "metadata": result["metadatas"][0] if result["metadatas"] else {},
                    "content": result["documents"][0] if result["documents"] else "",
                }
            return None
        except ChromaStoreError as e:
            logger.error(f"Failed to get document by ID: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to get document by ID: {str(e)}") from e

    def delete_documents(self, doc_ids: List[str]) -> int:
        """
        Delete documents by their IDs.

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            Number of documents deleted

        Raises:
            DocumentManagerError: If deletion fails
        """
        if not doc_ids:
            return 0

        try:
            deleted_count = self.chroma_store.delete_documents(ids=doc_ids)
            logger.info(f"Deleted {deleted_count} documents: {doc_ids}")
            return deleted_count
        except ChromaStoreError as e:
            logger.error(f"Failed to delete documents: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to delete documents: {str(e)}") from e

    def delete_documents_by_metadata(
        self,
        ticker: Optional[str] = None,
        form_type: Optional[str] = None,
    ) -> int:
        """
        Delete documents by metadata filter.

        Args:
            ticker: Optional ticker symbol filter
            form_type: Optional form type filter

        Returns:
            Number of documents deleted

        Raises:
            DocumentManagerError: If deletion fails
        """
        try:
            where: Dict[str, Any] = {}
            if ticker:
                where["ticker"] = ticker
            if form_type:
                where["form_type"] = form_type

            if not where:
                raise ValueError("Either ticker or form_type must be provided")

            deleted_count = self.chroma_store.delete_documents(where=where)
            logger.info(
                f"Deleted {deleted_count} documents by metadata: ticker={ticker}, "
                f"form_type={form_type}"
            )
            return deleted_count
        except (ChromaStoreError, ValueError) as e:
            logger.error(
                f"Failed to delete documents by metadata: {str(e)}", exc_info=True
            )
            raise DocumentManagerError(
                f"Failed to delete documents by metadata: {str(e)}"
            ) from e

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get document statistics.

        Returns:
            Dictionary with statistics:
            - total_documents: Total number of documents
            - total_chunks: Total number of chunks (same as documents in our case)
            - documents_by_ticker: Count of documents per ticker
            - documents_by_form_type: Count of documents per form type
            - unique_tickers: Number of unique tickers
            - unique_form_types: Number of unique form types

        Raises:
            DocumentManagerError: If statistics calculation fails
        """
        try:
            all_documents = self.get_all_documents()
            total_documents = len(all_documents)

            tickers = []
            form_types = []

            for doc in all_documents:
                metadata = doc.get("metadata", {})
                ticker = metadata.get("ticker")
                form_type = metadata.get("form_type")

                if ticker:
                    tickers.append(ticker)
                if form_type:
                    form_types.append(form_type)

            ticker_counts = Counter(tickers)
            form_type_counts = Counter(form_types)

            stats = {
                "total_documents": total_documents,
                # In our case, each chunk is a document
                "total_chunks": total_documents,
                "documents_by_ticker": dict(ticker_counts),
                "documents_by_form_type": dict(form_type_counts),
                "unique_tickers": len(ticker_counts),
                "unique_form_types": len(form_type_counts),
            }

            logger.debug(f"Calculated statistics: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {str(e)}", exc_info=True)
            raise DocumentManagerError(
                f"Failed to calculate statistics: {str(e)}"
            ) from e

    def group_documents_by_source(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group documents by their source filename.

        Returns:
            Dictionary mapping source filenames to lists of document chunks

        Raises:
            DocumentManagerError: If grouping fails
        """
        try:
            all_documents = self.get_all_documents()
            grouped: Dict[str, List[Dict[str, Any]]] = {}

            for doc in all_documents:
                metadata = doc.get("metadata", {})
                source = metadata.get("source") or metadata.get("filename", "unknown")
                # Extract just the filename if it's a path
                if isinstance(source, str) and "/" in source:
                    source = Path(source).name

                if source not in grouped:
                    grouped[source] = []
                grouped[source].append(doc)

            logger.debug(f"Grouped documents into {len(grouped)} sources")
            return grouped
        except Exception as e:
            logger.error(f"Failed to group documents: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to group documents: {str(e)}") from e
