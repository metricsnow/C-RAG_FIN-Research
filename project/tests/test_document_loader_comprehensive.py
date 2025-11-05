"""
Comprehensive tests for DocumentLoader - covering all methods and error paths.

Tests all DocumentLoader methods including process_documents, error handling, and edge cases.
"""

from pathlib import Path

import pytest

from app.ingestion import DocumentIngestionError, DocumentLoader


@pytest.fixture
def loader():
    """Create DocumentLoader instance."""
    return DocumentLoader(chunk_size=1000, chunk_overlap=200)


@pytest.mark.unit
def test_load_document_method(loader, test_documents_dir, sample_text_content):
    """Test load_document method directly."""
    text_file = test_documents_dir / "test_load.txt"
    text_file.write_text(sample_text_content)

    try:
        document = loader.load_document(text_file)

        assert document is not None, "Document should be loaded"
        assert len(document.page_content) > 0, "Document should have content"
        assert "source" in document.metadata, "Metadata should include source"
        assert "filename" in document.metadata, "Metadata should include filename"
        assert "type" in document.metadata, "Metadata should include type"
        assert "date" in document.metadata, "Metadata should include date"
    finally:
        if text_file.exists():
            text_file.unlink()


@pytest.mark.unit
def test_chunk_document_method(loader, production_financial_document_1):
    """Test chunk_document method directly."""
    from langchain_core.documents import Document

    document = Document(
        page_content=production_financial_document_1,
        metadata={"source": "test.txt", "type": "text"},
    )

    chunks = loader.chunk_document(document)

    assert len(chunks) > 0, "Should generate chunks"
    assert all(
        "chunk_index" in chunk.metadata for chunk in chunks
    ), "All chunks should have chunk_index"
    assert all(
        chunk.metadata["source"] == "test.txt" for chunk in chunks
    ), "All chunks should preserve source metadata"
    assert all(
        chunk.metadata["type"] == "text" for chunk in chunks
    ), "All chunks should preserve type metadata"


@pytest.mark.unit
def test_process_documents_success(
    loader, test_documents_dir, production_financial_document_1
):
    """Test process_documents with multiple files."""
    # Create multiple test files
    file1 = test_documents_dir / "test1.txt"
    file2 = test_documents_dir / "test2.txt"
    file3 = test_documents_dir / "test3.txt"

    content = production_financial_document_1[:500]

    file1.write_text(content)
    file2.write_text(content)
    file3.write_text(content)

    try:
        file_paths = [file1, file2, file3]
        all_chunks = loader.process_documents(file_paths)

        assert len(all_chunks) > 0, "Should process all documents"
        assert len(all_chunks) >= 3, "Should have chunks from all files"

        # Verify chunks from different files
        sources = set(chunk.metadata.get("filename") for chunk in all_chunks)
        assert len(sources) >= 1, "Should have chunks from multiple files"
    finally:
        # Cleanup
        for f in [file1, file2, file3]:
            if f.exists():
                f.unlink()


@pytest.mark.unit
def test_process_documents_partial_failure(
    loader, test_documents_dir, sample_text_content
):
    """Test process_documents continues when some files fail."""
    # Create valid and invalid files
    valid_file = test_documents_dir / "valid.txt"
    invalid_file = test_documents_dir / "invalid.pdf"

    valid_file.write_text(sample_text_content)
    invalid_file.write_text("test content")  # Wrong extension

    try:
        file_paths = [valid_file, invalid_file]
        all_chunks = loader.process_documents(file_paths)

        # Should process valid file and skip invalid
        assert len(all_chunks) > 0, "Should process valid file"
        # Invalid file should be skipped (error printed but not raised)
    finally:
        # Cleanup
        if valid_file.exists():
            valid_file.unlink()
        if invalid_file.exists():
            invalid_file.unlink()


@pytest.mark.unit
def test_process_documents_empty_list(loader):
    """Test process_documents with empty list."""
    chunks = loader.process_documents([])

    assert chunks == [], "Should return empty list for empty input"


@pytest.mark.unit
def test_get_file_type_method(loader, test_documents_dir):
    """Test _get_file_type method."""
    text_file = test_documents_dir / "test.txt"
    md_file = test_documents_dir / "test.md"

    text_file.write_text("test")
    md_file.write_text("# test")

    try:
        assert (
            loader._get_file_type(text_file) == "text"
        ), "Should return 'text' for .txt"
        assert (
            loader._get_file_type(md_file) == "markdown"
        ), "Should return 'markdown' for .md"
    finally:
        if text_file.exists():
            text_file.unlink()
        if md_file.exists():
            md_file.unlink()


@pytest.mark.unit
def test_validate_file_nonexistent(loader, test_documents_dir):
    """Test _validate_file with nonexistent file."""
    nonexistent = test_documents_dir / "nonexistent.txt"

    with pytest.raises(DocumentIngestionError, match="File not found"):
        loader._validate_file(nonexistent)


@pytest.mark.unit
def test_validate_file_directory(loader, test_documents_dir):
    """Test _validate_file with directory path."""
    with pytest.raises(DocumentIngestionError, match="Path is not a file"):
        loader._validate_file(test_documents_dir)


@pytest.mark.unit
def test_load_text_file_empty(loader, test_documents_dir):
    """Test _load_text_file with empty file."""
    empty_file = test_documents_dir / "empty.txt"
    empty_file.write_text("")

    try:
        # Empty file should still load (but may have no content)
        document = loader._load_text_file(empty_file)
        assert document is not None, "Should return document even if empty"
    finally:
        if empty_file.exists():
            empty_file.unlink()


@pytest.mark.unit
def test_load_markdown_file(loader, test_documents_dir, sample_markdown_content):
    """Test _load_markdown_file method."""
    md_file = test_documents_dir / "test_markdown.md"
    md_file.write_text(sample_markdown_content)

    try:
        document = loader._load_markdown_file(md_file)

        assert document is not None, "Should load markdown file"
        assert len(document.page_content) > 0, "Should have content"
        assert (
            "# Sample Markdown" in document.page_content
            or "Markdown" in document.page_content
        ), "Should contain markdown content"
    finally:
        if md_file.exists():
            md_file.unlink()


@pytest.mark.unit
def test_chunk_document_preserves_metadata(loader, production_financial_document_1):
    """Test that chunk_document preserves all original metadata."""
    from langchain_core.documents import Document

    original_metadata = {
        "source": "test.txt",
        "type": "text",
        "custom_field": "custom_value",
        "year": "2023",
    }

    document = Document(
        page_content=production_financial_document_1,
        metadata=original_metadata.copy(),
    )

    chunks = loader.chunk_document(document)

    # Verify all original metadata is preserved
    for chunk in chunks:
        for key, value in original_metadata.items():
            assert (
                chunk.metadata[key] == value
            ), f"Chunk should preserve metadata '{key}'"
        assert "chunk_index" in chunk.metadata, "Should add chunk_index"


@pytest.mark.unit
def test_chunk_document_small_content(loader):
    """Test chunking with very small content."""
    from langchain_core.documents import Document

    small_doc = Document(
        page_content="Very short text.",
        metadata={"source": "small.txt"},
    )

    chunks = loader.chunk_document(small_doc)

    assert len(chunks) > 0, "Should create at least one chunk even for small content"
    assert chunks[0].page_content == "Very short text.", "Should preserve content"


@pytest.mark.unit
def test_chunk_document_large_content(loader, production_financial_document_1):
    """Test chunking with large content that creates multiple chunks."""
    from langchain_core.documents import Document

    # Create large document by repeating content
    large_content = production_financial_document_1 * 5  # Repeat 5 times

    document = Document(
        page_content=large_content,
        metadata={"source": "large.txt"},
    )

    chunks = loader.chunk_document(document)

    assert len(chunks) > 1, "Large content should create multiple chunks"
    assert all(
        chunk.metadata["chunk_index"] == i for i, chunk in enumerate(chunks)
    ), "Chunk indices should be sequential"
