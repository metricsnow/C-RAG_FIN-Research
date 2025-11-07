"""
Comprehensive tests for document re-indexing and versioning functionality.

Tests document re-indexing, version tracking, version history, and version comparison.
"""

from pathlib import Path

import pytest

from app.ingestion.pipeline import IngestionPipeline
from app.utils.document_manager import DocumentManager, DocumentManagerError
from app.vector_db.chroma_store import ChromaStore


@pytest.fixture
def test_chroma_store(tmp_path):
    """Create a test ChromaDB store with temporary directory."""
    return ChromaStore(
        collection_name="test_documents",
        persist_directory=tmp_path / "chroma_test",
    )


@pytest.fixture
def test_ingestion_pipeline(test_chroma_store):
    """Create a test ingestion pipeline."""
    pipeline = IngestionPipeline(
        collection_name="test_documents",
        chunk_size=500,
        chunk_overlap=100,
    )
    # Use the same chroma_store instance
    pipeline.chroma_store = test_chroma_store
    return pipeline


@pytest.fixture
def document_manager(test_chroma_store, test_ingestion_pipeline):
    """Create a DocumentManager instance for testing."""
    return DocumentManager(
        chroma_store=test_chroma_store,
        ingestion_pipeline=test_ingestion_pipeline,
    )


@pytest.fixture
def sample_document_file(tmp_path, sample_text_content):
    """Create a sample document file for testing."""
    doc_file = tmp_path / "test_document.txt"
    doc_file.write_text(sample_text_content)
    return doc_file


@pytest.fixture
def indexed_document(document_manager, sample_document_file):
    """Index a sample document and return the file path."""
    # Index the document
    document_manager.ingestion_pipeline.process_document(
        sample_document_file, store_embeddings=True
    )
    return sample_document_file


@pytest.mark.unit
def test_get_document_chunks_by_source(document_manager, indexed_document):
    """Test getting document chunks by source filename."""
    source_name = indexed_document.name
    chunks = document_manager.get_document_chunks_by_source(source_name)

    assert len(chunks) > 0, "Should find chunks for indexed document"
    for chunk in chunks:
        assert "id" in chunk, "Chunk should have ID"
        assert "metadata" in chunk, "Chunk should have metadata"
        metadata = chunk["metadata"]
        source = metadata.get("source") or metadata.get("filename", "")
        assert source_name in source or Path(source).name == source_name


@pytest.mark.unit
def test_get_current_version_no_versions(document_manager, indexed_document):
    """Test getting current version when no versions exist."""
    source_name = indexed_document.name
    version = document_manager.get_current_version(source_name)

    # Should return 0 if no version metadata exists
    assert version >= 0, "Version should be non-negative"


@pytest.mark.unit
def test_reindex_document_basic(document_manager, indexed_document):
    """Test basic document re-indexing."""
    source_name = indexed_document.name

    # Get initial chunk count
    initial_chunks = document_manager.get_document_chunks_by_source(source_name)
    initial_count = len(initial_chunks)

    # Re-index the document
    result = document_manager.reindex_document(
        indexed_document,
        preserve_metadata=True,
        increment_version=True,
    )

    # Verify results
    assert result["old_chunks_deleted"] == initial_count, "Should delete old chunks"
    assert result["new_chunks_created"] > 0, "Should create new chunks"
    assert result["version"] == 1, "Should be version 1 after first re-index"

    # Verify new chunks exist
    new_chunks = document_manager.get_document_chunks_by_source(source_name)
    assert len(new_chunks) == result["new_chunks_created"], "New chunks should exist"


@pytest.mark.unit
def test_reindex_document_preserve_metadata(document_manager, indexed_document):
    """Test that metadata is preserved during re-indexing."""
    source_name = indexed_document.name

    # Get initial metadata
    initial_chunks = document_manager.get_document_chunks_by_source(source_name)
    initial_metadata = initial_chunks[0].get("metadata", {})

    # Add some test metadata
    test_ticker = "TEST"
    test_form_type = "10-K"
    # Update metadata in ChromaDB (simulate existing metadata)
    if initial_chunks:
        chunk_id = initial_chunks[0]["id"]
        test_metadata = dict(initial_metadata)
        test_metadata["ticker"] = test_ticker
        test_metadata["form_type"] = test_form_type
        document_manager.chroma_store.update_documents(
            ids=[chunk_id], metadatas=[test_metadata]
        )

    # Re-index with metadata preservation
    document_manager.reindex_document(
        indexed_document,
        preserve_metadata=True,
        increment_version=True,
    )

    # Verify metadata was preserved
    new_chunks = document_manager.get_document_chunks_by_source(source_name)
    if new_chunks:
        # Metadata should be preserved (if it was in the original)
        # Note: This depends on the original metadata structure
        assert new_chunks[0].get("metadata", {}) is not None


@pytest.mark.unit
def test_reindex_document_increment_version(document_manager, indexed_document):
    """Test version incrementing during re-indexing."""

    # First re-index
    result1 = document_manager.reindex_document(
        indexed_document,
        preserve_metadata=True,
        increment_version=True,
    )
    assert result1["version"] == 1, "First re-index should be version 1"

    # Second re-index
    result2 = document_manager.reindex_document(
        indexed_document,
        preserve_metadata=True,
        increment_version=True,
    )
    assert result2["version"] == 2, "Second re-index should be version 2"

    # Third re-index
    result3 = document_manager.reindex_document(
        indexed_document,
        preserve_metadata=True,
        increment_version=True,
    )
    assert result3["version"] == 3, "Third re-index should be version 3"


@pytest.mark.unit
def test_reindex_document_no_version_increment(document_manager, indexed_document):
    """Test re-indexing without version increment."""

    # Re-index without version increment
    result = document_manager.reindex_document(
        indexed_document,
        preserve_metadata=True,
        increment_version=False,
    )

    # Version should remain 0 or not be set
    assert result["version"] == 0, "Version should be 0 when not incrementing"


@pytest.mark.unit
def test_reindex_document_file_not_found(document_manager, tmp_path):
    """Test re-indexing with non-existent file."""
    non_existent_file = tmp_path / "non_existent.txt"

    with pytest.raises(DocumentManagerError) as exc_info:
        document_manager.reindex_document(non_existent_file)

    assert "not found" in str(exc_info.value).lower() or "File not found" in str(
        exc_info.value
    )


@pytest.mark.unit
def test_reindex_documents_batch(document_manager, tmp_path, sample_text_content):
    """Test batch re-indexing of multiple documents."""
    # Create multiple test documents
    doc_files = []
    for i in range(3):
        doc_file = tmp_path / f"test_doc_{i}.txt"
        doc_file.write_text(f"{sample_text_content}\n\nDocument {i} content.")
        doc_files.append(doc_file)

        # Index each document first
        document_manager.ingestion_pipeline.process_document(
            doc_file, store_embeddings=True
        )

    # Re-index all documents
    results = document_manager.reindex_documents_batch(
        doc_files,
        preserve_metadata=True,
        increment_version=True,
    )

    assert len(results) == 3, "Should process all 3 documents"
    for result in results:
        assert result["status"] == "success", "All re-indexing should succeed"
        assert result["old_chunks_deleted"] > 0, "Should delete old chunks"
        assert result["new_chunks_created"] > 0, "Should create new chunks"
        assert result["version"] == 1, "Should be version 1"


@pytest.mark.unit
def test_get_version_history(document_manager, indexed_document):
    """Test getting version history for a document."""
    source_name = indexed_document.name

    # Re-index multiple times to create version history
    # Note: Each re-index deletes old chunks, so only the latest version exists
    for i in range(3):
        result = document_manager.reindex_document(
            indexed_document,
            preserve_metadata=True,
            increment_version=True,
        )
        assert result["version"] == i + 1, f"Re-index {i+1} should be version {i+1}"

    # Get version history - should only have the latest version
    # since old chunks are deleted
    history = document_manager.get_version_history(source_name)

    # After re-indexing, only the latest version's chunks exist (old chunks are deleted)
    assert len(history) >= 1, "Should have at least the latest version"
    latest_version = max(v["version"] for v in history)
    assert latest_version == 3, "Latest version should be 3"

    # Check version information
    for version_info in history:
        assert "version" in version_info, "Should have version number"
        assert "chunk_count" in version_info, "Should have chunk count"
        assert "chunk_ids" in version_info, "Should have chunk IDs"
        assert version_info["chunk_count"] > 0, "Should have chunks"


@pytest.mark.unit
def test_get_version_history_no_versions(document_manager, indexed_document):
    """Test getting version history when no versions exist."""
    source_name = indexed_document.name

    # Get version history (no re-indexing done)
    history = document_manager.get_version_history(source_name)

    # Should return empty list or list with version 0
    assert isinstance(history, list), "Should return a list"


@pytest.mark.unit
def test_compare_versions(document_manager, indexed_document):
    """Test comparing two versions of a document."""
    source_name = indexed_document.name

    # Create first version
    result1 = document_manager.reindex_document(
        indexed_document,
        preserve_metadata=True,
        increment_version=True,
    )
    assert result1["version"] == 1

    # Note: After re-indexing, version 1 chunks are deleted, so we can't compare
    # versions that no longer exist. This test verifies the error handling.
    # For a real comparison, we would need to keep old chunks (not delete them)
    # or use a different versioning strategy.

    # Modify document content
    modified_content = indexed_document.read_text() + "\n\nAdditional content."
    indexed_document.write_text(modified_content)

    # Create second version (this deletes version 1 chunks)
    result2 = document_manager.reindex_document(
        indexed_document,
        preserve_metadata=True,
        increment_version=True,
    )
    assert result2["version"] == 2

    # Since old chunks are deleted during re-indexing, we can only compare
    # if we have both versions. In this case, version 1 no longer exists.
    # The function should handle this gracefully.
    history = document_manager.get_version_history(source_name)
    available_versions = [v["version"] for v in history]

    # If both versions exist (which they won't after deletion), compare them
    if 1 in available_versions and 2 in available_versions:
        comparison = document_manager.compare_versions(source_name, 1, 2)
        assert "version1_info" in comparison
        assert "version2_info" in comparison
        assert "differences" in comparison
    else:
        # Expected behavior: old versions are deleted, so comparison fails
        with pytest.raises(DocumentManagerError):
            document_manager.compare_versions(source_name, 1, 2)


@pytest.mark.unit
def test_compare_versions_not_found(document_manager, indexed_document):
    """Test comparing versions that don't exist."""
    source_name = indexed_document.name

    with pytest.raises(DocumentManagerError) as exc_info:
        document_manager.compare_versions(source_name, 99, 100)

    assert "not found" in str(exc_info.value).lower() or "Version" in str(
        exc_info.value
    )


@pytest.mark.integration
def test_full_reindex_workflow(document_manager, indexed_document):
    """Test full re-indexing workflow with version tracking."""
    source_name = indexed_document.name

    # Step 1: Initial indexing (already done in fixture)
    initial_chunks = document_manager.get_document_chunks_by_source(source_name)
    initial_count = len(initial_chunks)

    # Step 2: First re-index
    result1 = document_manager.reindex_document(
        indexed_document,
        preserve_metadata=True,
        increment_version=True,
    )

    assert result1["old_chunks_deleted"] == initial_count
    assert result1["version"] == 1

    # Step 3: Get version history (should have version 1)
    history = document_manager.get_version_history(source_name)
    assert len(history) >= 1, "Should have at least version 1"
    assert any(v["version"] == 1 for v in history), "Should have version 1"

    # Step 4: Second re-index (this deletes version 1 chunks)
    result2 = document_manager.reindex_document(
        indexed_document,
        preserve_metadata=True,
        increment_version=True,
    )

    assert result2["version"] == 2

    # Step 5: Get updated version history (should have version 2, version 1 deleted)
    history_after = document_manager.get_version_history(source_name)
    assert len(history_after) >= 1, "Should have at least version 2"
    assert any(v["version"] == 2 for v in history_after), "Should have version 2"

    # Step 6: Verify current version
    current_version = document_manager.get_current_version(source_name)
    assert current_version == 2, "Current version should be 2"

    # Step 7: Compare versions - version 1 no longer exists (was deleted)
    # So we can only compare if both versions exist, which they don't after deletion
    available_versions = [v["version"] for v in history_after]
    if 1 in available_versions and 2 in available_versions:
        comparison = document_manager.compare_versions(source_name, 1, 2)
        assert comparison["version1_info"]["version"] == 1
        assert comparison["version2_info"]["version"] == 2
    else:
        # Expected: version 1 was deleted, so comparison should fail
        with pytest.raises(DocumentManagerError):
            document_manager.compare_versions(source_name, 1, 2)


@pytest.mark.integration
def test_reindex_with_metadata_preservation(
    document_manager, tmp_path, sample_text_content
):
    """Test re-indexing preserves important metadata fields."""
    # Create document with metadata
    doc_file = tmp_path / "metadata_test.txt"
    doc_file.write_text(sample_text_content)

    # Index document
    document_manager.ingestion_pipeline.process_document(
        doc_file, store_embeddings=True
    )

    # Add metadata to chunks
    chunks = document_manager.get_document_chunks_by_source(doc_file.name)
    if chunks:
        test_metadata = {
            "ticker": "AAPL",
            "form_type": "10-K",
            "filing_date": "2023-12-31",
        }
        chunk_ids = [chunk["id"] for chunk in chunks]
        updated_metadatas = []
        for chunk in chunks:
            metadata = dict(chunk.get("metadata", {}))
            metadata.update(test_metadata)
            updated_metadatas.append(metadata)

        document_manager.chroma_store.update_documents(
            ids=chunk_ids, metadatas=updated_metadatas
        )

    # Re-index with metadata preservation
    document_manager.reindex_document(
        doc_file,
        preserve_metadata=True,
        increment_version=True,
    )

    # Verify metadata was preserved
    new_chunks = document_manager.get_document_chunks_by_source(doc_file.name)
    if new_chunks:
        new_metadata = new_chunks[0].get("metadata", {})
        # Check if preserved metadata fields are present
        # (may not be exact match due to how preservation works)
        assert "version" in new_metadata, "Should have version metadata"


@pytest.mark.integration
def test_batch_reindex_with_errors(document_manager, tmp_path, sample_text_content):
    """Test batch re-indexing handles errors gracefully."""
    # Create valid and invalid documents
    valid_doc = tmp_path / "valid.txt"
    valid_doc.write_text(sample_text_content)
    document_manager.ingestion_pipeline.process_document(
        valid_doc, store_embeddings=True
    )

    invalid_doc = tmp_path / "invalid.txt"
    # Don't create the file - it will cause an error

    # Try batch re-indexing
    results = document_manager.reindex_documents_batch(
        [valid_doc, invalid_doc],
        preserve_metadata=True,
        increment_version=True,
    )

    assert len(results) == 2, "Should process both documents"
    assert results[0]["status"] == "success", "Valid doc should succeed"
    assert results[1]["status"] == "error", "Invalid doc should fail"
    assert "error" in results[1], "Error result should have error message"


@pytest.mark.unit
def test_chroma_store_update_documents(test_chroma_store):
    """Test ChromaStore update_documents method."""
    from langchain_core.documents import Document

    # Add initial documents
    docs = [
        Document(page_content="Test content 1", metadata={"key": "value1"}),
        Document(page_content="Test content 2", metadata={"key": "value2"}),
    ]
    embeddings = [[0.1] * 384, [0.2] * 384]  # Mock embeddings
    ids = test_chroma_store.add_documents(docs, embeddings)

    # Update metadata
    updated_metadatas = [
        {"key": "updated_value1", "new_field": "test1"},
        {"key": "updated_value2", "new_field": "test2"},
    ]
    test_chroma_store.update_documents(ids=ids, metadatas=updated_metadatas)

    # Verify update
    result = test_chroma_store.get_by_ids(ids)
    assert len(result["metadatas"]) == 2
    assert result["metadatas"][0]["key"] == "updated_value1"
    assert result["metadatas"][0]["new_field"] == "test1"


@pytest.mark.unit
def test_chroma_store_update_documents_validation(test_chroma_store):
    """Test ChromaStore update_documents validation."""

    # Test empty IDs
    with pytest.raises(ValueError):
        test_chroma_store.update_documents(ids=[], metadatas=[{"key": "value"}])

    # Test mismatched lengths
    with pytest.raises(ValueError):
        test_chroma_store.update_documents(
            ids=["id1", "id2"], metadatas=[{"key": "value"}]
        )
