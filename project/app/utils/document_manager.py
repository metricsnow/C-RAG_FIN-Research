"""
Document management utilities for ChromaDB operations.

Provides high-level functions for document listing, searching, filtering,
and statistics calculation for the document management UI.
"""

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.ingestion.pipeline import IngestionPipeline, IngestionPipelineError
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

    def __init__(
        self,
        chroma_store: Optional[ChromaStore] = None,
        ingestion_pipeline: Optional[IngestionPipeline] = None,
    ):
        """
        Initialize document manager.

        Args:
            chroma_store: Optional ChromaStore instance.
                If None, creates a new one.
            ingestion_pipeline: Optional IngestionPipeline instance.
                If None, creates a new one.
        """
        self.chroma_store = chroma_store or ChromaStore()
        # If ingestion pipeline is provided, use it;
        # otherwise create one that shares the same store
        if ingestion_pipeline is None:
            # Create pipeline with same collection name as chroma_store
            self.ingestion_pipeline = IngestionPipeline(
                collection_name=self.chroma_store.collection_name
            )
            # Replace the pipeline's chroma_store with our shared instance
            self.ingestion_pipeline.chroma_store = self.chroma_store
        else:
            self.ingestion_pipeline = ingestion_pipeline
            # Ensure pipeline uses the same chroma_store
            if (
                self.ingestion_pipeline.chroma_store.collection_name
                != self.chroma_store.collection_name
            ):
                self.ingestion_pipeline.chroma_store = self.chroma_store
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

    def get_document_chunks_by_source(self, source: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document by source filename.

        Args:
            source: Source filename or path

        Returns:
            List of document chunks for the source

        Raises:
            DocumentManagerError: If retrieval fails
        """
        try:
            all_documents = self.get_all_documents()
            source_chunks = []

            # Normalize source for comparison
            source_normalized = Path(source).name if "/" in source else source

            for doc in all_documents:
                metadata = doc.get("metadata", {})
                doc_source = metadata.get("source") or metadata.get("filename", "")
                doc_source_normalized = (
                    Path(doc_source).name
                    if doc_source and "/" in doc_source
                    else doc_source
                )

                if doc_source_normalized == source_normalized:
                    source_chunks.append(doc)

            logger.debug(f"Found {len(source_chunks)} chunks for source: {source}")
            return source_chunks
        except Exception as e:
            logger.error(
                f"Failed to get document chunks by source: {str(e)}", exc_info=True
            )
            raise DocumentManagerError(
                f"Failed to get document chunks by source: {str(e)}"
            ) from e

    def get_current_version(self, source: str) -> int:
        """
        Get the current version number for a document source.

        Args:
            source: Source filename or path

        Returns:
            Current version number (1 if no previous versions)

        Raises:
            DocumentManagerError: If retrieval fails
        """
        try:
            chunks = self.get_document_chunks_by_source(source)
            if not chunks:
                return 0

            # Get the highest version number from chunks
            max_version = 0
            for chunk in chunks:
                metadata = chunk.get("metadata", {})
                version = metadata.get("version", 0)
                if isinstance(version, (int, float)):
                    max_version = max(max_version, int(version))

            return max_version
        except Exception as e:
            logger.error(f"Failed to get current version: {str(e)}", exc_info=True)
            raise DocumentManagerError(
                f"Failed to get current version: {str(e)}"
            ) from e

    def reindex_document(
        self,
        file_path: Path,
        preserve_metadata: bool = True,
        increment_version: bool = True,
    ) -> Dict[str, Any]:
        """
        Re-index a document by deleting old chunks and creating new ones.

        Args:
            file_path: Path to the document file to re-index
            preserve_metadata: Whether to preserve original metadata
                (ticker, form_type, etc.)
            increment_version: Whether to increment version number

        Returns:
            Dictionary with:
            - old_chunks_deleted: Number of old chunks deleted
            - new_chunks_created: Number of new chunks created
            - new_chunk_ids: List of new chunk IDs
            - version: New version number

        Raises:
            DocumentManagerError: If re-indexing fails
        """
        try:
            if not file_path.exists():
                raise DocumentManagerError(f"File not found: {file_path}")

            source_name = file_path.name

            # Get existing chunks for this document
            existing_chunks = self.get_document_chunks_by_source(source_name)
            old_chunk_ids = [chunk["id"] for chunk in existing_chunks]

            # Get current version
            current_version = (
                self.get_current_version(source_name) if increment_version else 0
            )
            new_version = current_version + 1 if increment_version else current_version

            # Preserve metadata from existing chunks if requested
            preserved_metadata = {}
            if preserve_metadata and existing_chunks:
                # Get metadata from first chunk (should be consistent across chunks)
                first_chunk_metadata = existing_chunks[0].get("metadata", {})
                # Preserve important metadata fields
                for key in ["ticker", "form_type", "filing_date", "date", "source"]:
                    if key in first_chunk_metadata:
                        preserved_metadata[key] = first_chunk_metadata[key]

            # Delete old chunks
            old_chunks_deleted = 0
            if old_chunk_ids:
                logger.info(
                    f"Deleting {len(old_chunk_ids)} old chunks "
                    f"for re-indexing: {source_name}"
                )
                old_chunks_deleted = self.delete_documents(old_chunk_ids)

            # Re-process document through ingestion pipeline
            logger.info(f"Re-indexing document: {file_path} (version {new_version})")
            new_chunk_ids = self.ingestion_pipeline.process_document(
                file_path, store_embeddings=True
            )

            # Update metadata with version information
            if new_chunk_ids and increment_version:
                # Get the new chunks and update their metadata
                new_chunks_data = self.chroma_store.get_by_ids(new_chunk_ids)
                updated_metadatas = []

                for metadata in new_chunks_data.get("metadatas", []):
                    updated_metadata = dict(metadata) if metadata else {}
                    # Add version tracking
                    updated_metadata["version"] = new_version
                    updated_metadata["version_date"] = datetime.now(
                        timezone.utc
                    ).isoformat()
                    if old_chunk_ids:
                        updated_metadata["previous_version_ids"] = str(old_chunk_ids)
                    # Preserve original metadata
                    if preserved_metadata:
                        updated_metadata.update(preserved_metadata)
                    updated_metadatas.append(updated_metadata)

                # Update chunks with version metadata
                if updated_metadatas:
                    self.chroma_store.update_documents(
                        ids=new_chunk_ids,
                        metadatas=updated_metadatas,
                    )
                    logger.info(
                        f"Updated {len(new_chunk_ids)} chunks with version metadata"
                    )

            result = {
                "old_chunks_deleted": old_chunks_deleted,
                "new_chunks_created": len(new_chunk_ids),
                "new_chunk_ids": new_chunk_ids,
                "version": new_version,
            }

            logger.info(
                f"Re-indexing complete: {old_chunks_deleted} deleted, "
                f"{len(new_chunk_ids)} created, version {new_version}"
            )
            return result

        except IngestionPipelineError as e:
            logger.error(
                f"Re-indexing failed during ingestion: {str(e)}", exc_info=True
            )
            raise DocumentManagerError(
                f"Re-indexing failed during ingestion: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Re-indexing failed: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Re-indexing failed: {str(e)}") from e

    def reindex_documents_batch(
        self,
        file_paths: List[Path],
        preserve_metadata: bool = True,
        increment_version: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Re-index multiple documents in batch.

        Args:
            file_paths: List of paths to document files to re-index
            preserve_metadata: Whether to preserve original metadata
            increment_version: Whether to increment version numbers

        Returns:
            List of re-indexing results for each document

        Raises:
            DocumentManagerError: If batch re-indexing fails
        """
        results = []
        logger.info(f"Starting batch re-indexing of {len(file_paths)} documents")

        for idx, file_path in enumerate(file_paths, 1):
            try:
                logger.info(
                    f"Re-indexing document {idx}/{len(file_paths)}: {file_path}"
                )
                result = self.reindex_document(
                    file_path,
                    preserve_metadata=preserve_metadata,
                    increment_version=increment_version,
                )
                result["file_path"] = str(file_path)
                result["status"] = "success"
                results.append(result)
            except DocumentManagerError as e:
                logger.warning(f"Failed to re-index {file_path}: {str(e)}")
                results.append(
                    {
                        "file_path": str(file_path),
                        "status": "error",
                        "error": str(e),
                        "old_chunks_deleted": 0,
                        "new_chunks_created": 0,
                        "version": 0,
                    }
                )

        success_count = len([r for r in results if r["status"] == "success"])
        error_count = len([r for r in results if r["status"] == "error"])
        logger.info(
            f"Batch re-indexing complete: {success_count} "
            f"successful, {error_count} failed"
        )
        return results

    def get_version_history(self, source: str) -> List[Dict[str, Any]]:
        """
        Get version history for a document source.

        Args:
            source: Source filename or path

        Returns:
            List of version information dictionaries

        Raises:
            DocumentManagerError: If retrieval fails
        """
        try:
            chunks = self.get_document_chunks_by_source(source)
            if not chunks:
                return []

            # Group chunks by version
            versions: Dict[int, Dict[str, Any]] = {}
            for chunk in chunks:
                metadata = chunk.get("metadata", {})
                version = metadata.get("version", 0)
                if isinstance(version, (int, float)):
                    version = int(version)
                else:
                    version = 0

                if version not in versions:
                    versions[version] = {
                        "version": version,
                        "version_date": metadata.get("version_date", "unknown"),
                        "chunk_count": 0,
                        "chunk_ids": [],
                        "metadata": metadata,
                    }

                versions[version]["chunk_count"] += 1
                versions[version]["chunk_ids"].append(chunk["id"])

            # Sort by version number
            version_list = sorted(versions.values(), key=lambda x: x["version"])
            logger.debug(f"Found {len(version_list)} versions for source: {source}")
            return version_list

        except Exception as e:
            logger.error(f"Failed to get version history: {str(e)}", exc_info=True)
            raise DocumentManagerError(
                f"Failed to get version history: {str(e)}"
            ) from e

    def compare_versions(
        self, source: str, version1: int, version2: int
    ) -> Dict[str, Any]:
        """
        Compare two versions of a document.

        Args:
            source: Source filename or path
            version1: First version number to compare
            version2: Second version number to compare

        Returns:
            Dictionary with comparison results:
            - version1_info: Information about version 1
            - version2_info: Information about version 2
            - differences: List of differences

        Raises:
            DocumentManagerError: If comparison fails
        """
        try:
            history = self.get_version_history(source)
            version1_info = next((v for v in history if v["version"] == version1), None)
            version2_info = next((v for v in history if v["version"] == version2), None)

            if not version1_info:
                raise DocumentManagerError(f"Version {version1} not found")
            if not version2_info:
                raise DocumentManagerError(f"Version {version2} not found")

            differences = []
            # Compare chunk counts
            if version1_info["chunk_count"] != version2_info["chunk_count"]:
                differences.append(
                    {
                        "field": "chunk_count",
                        "version1": version1_info["chunk_count"],
                        "version2": version2_info["chunk_count"],
                    }
                )

            # Compare metadata
            metadata1 = version1_info.get("metadata", {})
            metadata2 = version2_info.get("metadata", {})
            for key in set(list(metadata1.keys()) + list(metadata2.keys())):
                if key not in ["version", "version_date", "previous_version_ids"]:
                    val1 = metadata1.get(key)
                    val2 = metadata2.get(key)
                    if val1 != val2:
                        differences.append(
                            {
                                "field": key,
                                "version1": val1,
                                "version2": val2,
                            }
                        )

            return {
                "version1_info": version1_info,
                "version2_info": version2_info,
                "differences": differences,
            }

        except Exception as e:
            logger.error(f"Failed to compare versions: {str(e)}", exc_info=True)
            raise DocumentManagerError(f"Failed to compare versions: {str(e)}") from e
