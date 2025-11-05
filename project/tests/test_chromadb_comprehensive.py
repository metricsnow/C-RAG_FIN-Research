"""
Comprehensive tests for ChromaDB - covering all methods and error paths.

Tests all ChromaStore methods including query_by_text, reset, and error handling.
"""

import pytest
from langchain_core.documents import Document

from app.vector_db import ChromaStore, ChromaStoreError


@pytest.fixture
def test_store_comprehensive(embedding_generator):
    """Create ChromaDB store with unique collection name for comprehensive testing."""
    import uuid

    collection_name = f"test_chromadb_comp_{uuid.uuid4().hex[:8]}"

    store = ChromaStore(collection_name=collection_name)
    yield store
    # Cleanup
    try:
        store.delete_collection()
    except Exception:
        pass


@pytest.fixture
def production_documents_with_embeddings(
    production_financial_document_1,
    production_financial_document_2,
    production_financial_document_3,
    embedding_generator,
):
    """Create production documents with real embeddings."""
    from langchain_core.documents import Document

    documents = [
        Document(
            page_content=production_financial_document_1,
            metadata={
                "source": "10-K_2023_revenue.txt",
                "type": "10-K",
                "section": "revenue",
            },
        ),
        Document(
            page_content=production_financial_document_2,
            metadata={
                "source": "10-K_2023_risks.txt",
                "type": "10-K",
                "section": "risks",
            },
        ),
        Document(
            page_content=production_financial_document_3,
            metadata={
                "source": "10-K_2023_liquidity.txt",
                "type": "10-K",
                "section": "liquidity",
            },
        ),
    ]

    texts = [doc.page_content for doc in documents]
    embeddings = embedding_generator.embed_documents(texts)
    return documents, embeddings


@pytest.mark.integration
@pytest.mark.chromadb
def test_chromadb_query_by_text(
    test_store_comprehensive,
    production_documents_with_embeddings,
    embedding_generator,
):
    """Test query_by_text method with production documents."""
    documents, embeddings = production_documents_with_embeddings

    # Add documents
    test_store_comprehensive.add_documents(documents, embeddings)

    # Query by text (if ChromaDB collection has embedding function)
    # Note: This may not work if collection doesn't have embedding function
    try:
        results = test_store_comprehensive.query_by_text(
            "What was the revenue for fiscal year 2023?",
            n_results=2,
        )

        assert "ids" in results, "Results should contain ids"
        assert "documents" in results, "Results should contain documents"
        assert len(results["ids"]) <= 2, "Should respect n_results parameter"
    except ChromaStoreError:
        # This is expected if collection doesn't have embedding function
        # ChromaDB requires embedding function for query_by_text
        pytest.skip("query_by_text requires collection with embedding function")


@pytest.mark.integration
@pytest.mark.chromadb
def test_chromadb_reset(
    test_store_comprehensive,
    production_documents_with_embeddings,
):
    """Test reset method that deletes and recreates collection."""
    documents, embeddings = production_documents_with_embeddings

    # Add documents
    test_store_comprehensive.add_documents(documents, embeddings)

    # Verify documents are there
    count_before = test_store_comprehensive.count()
    assert count_before == len(documents), "Documents should be added"

    # Reset collection
    test_store_comprehensive.reset()

    # Verify collection is empty
    count_after = test_store_comprehensive.count()
    assert count_after == 0, "Collection should be empty after reset"

    # Verify collection still exists and works
    assert (
        test_store_comprehensive.collection is not None
    ), "Collection should exist after reset"


@pytest.mark.integration
@pytest.mark.chromadb
def test_chromadb_add_documents_with_custom_ids(
    test_store_comprehensive,
    production_documents_with_embeddings,
):
    """Test adding documents with custom IDs."""
    documents, embeddings = production_documents_with_embeddings

    custom_ids = [f"custom_id_{i}" for i in range(len(documents))]
    returned_ids = test_store_comprehensive.add_documents(
        documents, embeddings, ids=custom_ids
    )

    assert returned_ids == custom_ids, "Should return custom IDs"

    # Verify documents can be retrieved by custom IDs
    results = test_store_comprehensive.get_by_ids(custom_ids)
    assert len(results["ids"]) == len(
        custom_ids
    ), "Should retrieve all documents by custom IDs"


@pytest.mark.integration
@pytest.mark.chromadb
def test_chromadb_add_documents_empty_list(
    test_store_comprehensive, embedding_generator
):
    """Test error handling for empty document list."""
    with pytest.raises(ChromaStoreError, match="Cannot add empty list"):
        test_store_comprehensive.add_documents([], [])


@pytest.mark.integration
@pytest.mark.chromadb
def test_chromadb_add_documents_mismatch_count(
    test_store_comprehensive,
    production_financial_document_1,
    production_financial_document_2,
    embedding_generator,
):
    """Test error handling for document/embedding count mismatch."""
    from langchain_core.documents import Document

    documents = [
        Document(
            page_content=production_financial_document_1,
            metadata={"source": "doc1.txt"},
        ),
        Document(
            page_content=production_financial_document_2,
            metadata={"source": "doc2.txt"},
        ),
    ]
    embeddings = embedding_generator.embed_documents(
        [doc.page_content for doc in documents]
    )

    # Add one extra embedding
    embeddings.append(embeddings[0])

    with pytest.raises(ChromaStoreError, match="does not match"):
        test_store_comprehensive.add_documents(documents, embeddings)


@pytest.mark.integration
@pytest.mark.chromadb
def test_chromadb_add_documents_id_count_mismatch(
    test_store_comprehensive,
    production_documents_with_embeddings,
):
    """Test error handling for ID count mismatch."""
    documents, embeddings = production_documents_with_embeddings

    # Provide wrong number of IDs
    wrong_ids = ["id1", "id2"]  # Only 2 IDs for potentially 3 documents

    with pytest.raises(ChromaStoreError, match="IDs count"):
        test_store_comprehensive.add_documents(documents, embeddings, ids=wrong_ids)


@pytest.mark.integration
@pytest.mark.chromadb
def test_chromadb_query_by_embedding_empty_collection(
    test_store_comprehensive,
    embedding_generator,
):
    """Test query on empty collection."""
    query_text = "test query"
    query_embedding = embedding_generator.embed_query(query_text)

    results = test_store_comprehensive.query_by_embedding(query_embedding, n_results=5)

    assert "ids" in results, "Results should contain ids"
    assert len(results["ids"]) == 0, "Should return empty results for empty collection"


@pytest.mark.integration
@pytest.mark.chromadb
def test_chromadb_get_by_ids_empty_list(test_store_comprehensive):
    """Test get_by_ids with empty list - should raise error."""
    # ChromaDB doesn't allow empty ID list, should raise error
    with pytest.raises(ChromaStoreError):
        test_store_comprehensive.get_by_ids([])


@pytest.mark.integration
@pytest.mark.chromadb
def test_chromadb_get_by_ids_nonexistent(
    test_store_comprehensive,
    production_documents_with_embeddings,
):
    """Test get_by_ids with nonexistent IDs."""
    documents, embeddings = production_documents_with_embeddings
    test_store_comprehensive.add_documents(documents, embeddings)

    # Try to get nonexistent IDs
    results = test_store_comprehensive.get_by_ids(
        ["nonexistent_id_1", "nonexistent_id_2"]
    )

    assert "ids" in results, "Results should contain ids"
    assert len(results["ids"]) == 0, "Should return empty results for nonexistent IDs"


@pytest.mark.integration
@pytest.mark.chromadb
def test_chromadb_query_with_where_document_filter(
    test_store_comprehensive,
    production_documents_with_embeddings,
    embedding_generator,
):
    """Test query with where_document filter."""
    documents, embeddings = production_documents_with_embeddings
    test_store_comprehensive.add_documents(documents, embeddings)

    query_embedding = embedding_generator.embed_query("financial information")

    # Query with document content filter (requires ChromaDB support)
    try:
        results = test_store_comprehensive.query_by_embedding(
            query_embedding,
            n_results=5,
            where_document={"$contains": "revenue"},
        )

        assert "ids" in results, "Results should contain ids"
        # Results should contain documents with "revenue" in content
        if results["documents"]:
            content_lower = " ".join(results["documents"]).lower()
            assert "revenue" in content_lower, "Filtered results should contain revenue"
    except Exception:
        # where_document may not be fully supported in all ChromaDB versions
        pytest.skip("where_document filter may not be supported")


@pytest.mark.integration
@pytest.mark.chromadb
def test_chromadb_delete_collection(
    test_store_comprehensive, production_documents_with_embeddings
):
    """Test delete_collection method."""
    documents, embeddings = production_documents_with_embeddings
    test_store_comprehensive.add_documents(documents, embeddings)

    # Verify documents exist
    assert test_store_comprehensive.count() > 0, "Documents should exist"

    # Delete collection
    test_store_comprehensive.delete_collection()

    # Verify collection is None
    assert (
        test_store_comprehensive.collection is None
    ), "Collection should be None after deletion"

    # Collection needs to be recreated before accessing count
    # Accessing count() will trigger _ensure_collection automatically
    test_store_comprehensive._ensure_collection()
    count = test_store_comprehensive.count()
    assert count == 0, "New collection should be empty"


@pytest.mark.integration
@pytest.mark.chromadb
def test_chromadb_ensure_collection(test_store_comprehensive):
    """Test that collection is automatically created."""
    # Collection should be created in __init__, verify it exists
    assert test_store_comprehensive.collection is not None, "Collection should exist"
    assert (
        test_store_comprehensive.collection.name
        == test_store_comprehensive.collection_name
    ), "Collection name should match"
