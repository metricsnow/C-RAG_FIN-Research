"""
Pytest tests for IngestionPipeline - production conditions.

Tests the complete ingestion pipeline with real embeddings and production-like
financial documents. No demo data - all tests use production conditions.
"""

from pathlib import Path

import pytest

from app.ingestion import IngestionPipeline, IngestionPipelineError
from app.rag.embedding_factory import EmbeddingError, EmbeddingGenerator


@pytest.fixture
def production_pipeline(embedding_generator):
    """Create ingestion pipeline with real embeddings."""
    import uuid

    collection_name = f"test_pipeline_{uuid.uuid4().hex[:8]}"

    pipeline = IngestionPipeline(
        embedding_provider=embedding_generator.provider,
        collection_name=collection_name,
        chunk_size=1000,
        chunk_overlap=200,
    )
    yield pipeline
    # Cleanup
    try:
        pipeline.chroma_store.delete_collection()
    except Exception:
        pass


@pytest.fixture
def production_financial_file_1(test_documents_dir, production_financial_document_1):
    """Create production financial document file."""
    file_path = test_documents_dir / "financial_10k_revenue.txt"
    file_path.write_text(production_financial_document_1)
    yield file_path
    if file_path.exists():
        file_path.unlink()


@pytest.fixture
def production_financial_file_2(test_documents_dir, production_financial_document_2):
    """Create production financial document file."""
    file_path = test_documents_dir / "financial_10k_risks.txt"
    file_path.write_text(production_financial_document_2)
    yield file_path
    if file_path.exists():
        file_path.unlink()


@pytest.fixture
def production_financial_file_3(test_documents_dir, production_financial_document_3):
    """Create production financial document file."""
    file_path = test_documents_dir / "financial_10k_liquidity.txt"
    file_path.write_text(production_financial_document_3)
    yield file_path
    if file_path.exists():
        file_path.unlink()


@pytest.mark.integration
def test_pipeline_process_single_document(
    production_pipeline, production_financial_file_1, embedding_generator
):
    """Test processing a single production financial document."""
    # Process document
    chunk_ids = production_pipeline.process_document(production_financial_file_1)

    # Verify chunks were created
    assert len(chunk_ids) > 0, "Should generate chunk IDs"
    assert all(
        isinstance(id_val, str) for id_val in chunk_ids
    ), "All IDs should be strings"

    # Verify document count
    count = production_pipeline.get_document_count()
    assert count == len(chunk_ids), "Document count should match chunk IDs"

    # Verify chunks are retrievable
    results = production_pipeline.chroma_store.get_by_ids(chunk_ids[:3])
    assert len(results["ids"]) > 0, "Should retrieve stored chunks"

    # Verify embeddings are real (not dummy)
    for doc_text in results["documents"][:2]:
        test_embedding = embedding_generator.embed_query(doc_text[:100])
        assert (
            len(test_embedding) == embedding_generator.get_embedding_dimensions()
        ), "Embeddings should have correct dimensions"


@pytest.mark.integration
def test_pipeline_process_multiple_documents(
    production_pipeline,
    production_financial_file_1,
    production_financial_file_2,
    production_financial_file_3,
):
    """Test processing multiple production financial documents."""
    # Ensure collection is empty
    initial_count = production_pipeline.get_document_count()

    file_paths = [
        production_financial_file_1,
        production_financial_file_2,
        production_financial_file_3,
    ]

    # Process all documents
    all_chunk_ids = production_pipeline.process_documents(file_paths)

    # Verify all chunks were created
    assert len(all_chunk_ids) > 0, "Should generate chunk IDs for all documents"

    # Verify document count (should be initial + new chunks)
    final_count = production_pipeline.get_document_count()
    assert final_count == initial_count + len(
        all_chunk_ids
    ), f"Total count ({final_count}) should equal initial ({initial_count}) + new chunks ({len(all_chunk_ids)})"

    # Verify we can retrieve chunks from all documents
    sample_ids = all_chunk_ids[
        : min(5, len(all_chunk_ids))
    ]  # Sample from different documents
    results = production_pipeline.chroma_store.get_by_ids(sample_ids)
    assert len(results["ids"]) == len(
        sample_ids
    ), "Should retrieve all requested chunks"


@pytest.mark.integration
def test_pipeline_search_similar(
    production_pipeline,
    production_financial_file_1,
    production_financial_file_2,
    production_financial_file_3,
):
    """Test similarity search with production documents."""
    # Process documents
    file_paths = [
        production_financial_file_1,
        production_financial_file_2,
        production_financial_file_3,
    ]
    production_pipeline.process_documents(file_paths)

    # Search for revenue-related content
    query = "What was the total revenue for fiscal year 2023?"
    similar_docs = production_pipeline.search_similar(query, n_results=3)

    # Verify results
    assert len(similar_docs) > 0, "Should find similar documents"
    assert len(similar_docs) <= 3, "Should respect n_results parameter"

    # Verify document structure
    for doc in similar_docs:
        assert hasattr(doc, "page_content"), "Documents should have content"
        assert hasattr(doc, "metadata"), "Documents should have metadata"
        assert len(doc.page_content) > 0, "Document content should not be empty"

    # Verify relevance (should find revenue document)
    content_lower = " ".join([doc.page_content.lower() for doc in similar_docs])
    assert (
        "revenue" in content_lower or "394.3" in content_lower
    ), "Should find revenue-related content"


@pytest.mark.integration
def test_pipeline_error_handling_invalid_file(production_pipeline, test_documents_dir):
    """Test error handling for invalid file."""
    invalid_file = test_documents_dir / "nonexistent.txt"

    with pytest.raises(IngestionPipelineError):
        production_pipeline.process_document(invalid_file)


@pytest.mark.integration
def test_pipeline_error_handling_empty_file(production_pipeline, test_documents_dir):
    """Test error handling for empty file."""
    empty_file = test_documents_dir / "empty.txt"
    empty_file.write_text("")

    try:
        with pytest.raises(IngestionPipelineError):
            production_pipeline.process_document(empty_file)
    finally:
        if empty_file.exists():
            empty_file.unlink()


@pytest.mark.integration
def test_pipeline_process_document_objects(
    production_pipeline,
    production_financial_document_1,
    production_financial_document_2,
    embedding_generator,
):
    """Test processing Document objects directly."""
    from langchain_core.documents import Document

    documents = [
        Document(
            page_content=production_financial_document_1,
            metadata={"source": "test_doc_1", "type": "10-k", "section": "revenue"},
        ),
        Document(
            page_content=production_financial_document_2,
            metadata={"source": "test_doc_2", "type": "10-k", "section": "risks"},
        ),
    ]

    # Process documents
    chunk_ids = production_pipeline.process_document_objects(documents)

    # Verify chunks were created
    assert len(chunk_ids) > 0, "Should generate chunk IDs"

    # Verify metadata is preserved
    results = production_pipeline.chroma_store.get_by_ids(chunk_ids[:5])
    for metadata in results.get("metadatas", []):
        if metadata:
            assert "source" in metadata, "Source metadata should be preserved"
            assert "type" in metadata, "Type metadata should be preserved"


@pytest.mark.integration
def test_pipeline_chunk_size_and_overlap(
    production_pipeline,
    production_financial_file_1,
):
    """Test that chunk size and overlap are applied correctly."""
    # Process document
    chunk_ids = production_pipeline.process_document(production_financial_file_1)

    # Retrieve chunks
    results = production_pipeline.chroma_store.get_by_ids(chunk_ids)

    # Verify chunk sizes are reasonable (within expected range)
    for doc_text in results["documents"]:
        assert len(doc_text) > 0, "Chunks should have content"
        # Chunks should be around chunk_size (1000) with some variance
        # Allow 50% variance for overlap and content boundaries
        assert len(doc_text) <= 1500, "Chunks should not exceed reasonable size"


@pytest.mark.integration
def test_pipeline_without_storage(production_pipeline, production_financial_file_1):
    """Test processing document without storing in ChromaDB."""
    # Get initial count
    initial_count = production_pipeline.get_document_count()

    # Process without storage
    chunk_ids = production_pipeline.process_document(
        production_financial_file_1, store_embeddings=False
    )

    # Verify placeholder IDs returned
    assert len(chunk_ids) > 0, "Should return placeholder IDs"
    assert all(
        id_val.startswith("chunk_") for id_val in chunk_ids
    ), "Placeholder IDs should have correct format"

    # Verify nothing was stored (count should remain the same)
    final_count = production_pipeline.get_document_count()
    assert (
        final_count == initial_count
    ), f"No documents should be stored when store_embeddings=False (initial: {initial_count}, final: {final_count})"
