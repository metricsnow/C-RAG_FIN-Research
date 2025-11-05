"""
Pytest tests for ChromaDB integration - production conditions.

Tests ChromaDB setup, document storage, and similarity search operations
using real embeddings from production embedding generator.
No demo or dummy data - all tests use production conditions.
"""

from langchain_core.documents import Document

import pytest

from app.vector_db import ChromaStore, ChromaStoreError
from app.utils.config import config


@pytest.fixture
def test_store():
    """Create a ChromaDB store for testing."""
    store = ChromaStore(collection_name="test_chromadb")
    yield store
    # Cleanup: Delete test collection
    try:
        store.delete_collection()
    except Exception:
        pass  # Collection may already be deleted


@pytest.fixture
def production_financial_documents(
    production_financial_document_1,
    production_financial_document_2,
    production_financial_document_3,
):
    """Create production financial documents for testing."""
    return [
        Document(
            page_content=production_financial_document_1,
            metadata={
                "source": "10-K_2023_revenue.txt",
                "type": "10-K",
                "section": "revenue",
                "year": "2023",
                "company": "test_company",
            },
        ),
        Document(
            page_content=production_financial_document_2,
            metadata={
                "source": "10-K_2023_risks.txt",
                "type": "10-K",
                "section": "risks",
                "year": "2023",
                "company": "test_company",
            },
        ),
        Document(
            page_content=production_financial_document_3,
            metadata={
                "source": "10-K_2023_liquidity.txt",
                "type": "10-K",
                "section": "liquidity",
                "year": "2023",
                "company": "test_company",
            },
        ),
    ]


@pytest.mark.integration
@pytest.mark.chromadb
def test_chromadb_connection(test_store):
    """Test ChromaDB client connection."""
    assert test_store is not None, "Store should be created"
    assert test_store.collection_name == "test_chromadb", "Collection name should match"


@pytest.mark.integration
@pytest.mark.chromadb
def test_add_documents(test_store, production_financial_documents, embedding_generator):
    """Test adding production financial documents to ChromaDB with real embeddings."""
    # Generate real embeddings
    texts = [doc.page_content for doc in production_financial_documents]
    embeddings = embedding_generator.embed_documents(texts)
    
    # Verify embeddings are real
    assert len(embeddings) == len(production_financial_documents), "Should generate embeddings for all documents"
    assert all(len(emb) == embedding_generator.get_embedding_dimensions() for emb in embeddings), \
        "All embeddings should have correct dimensions"
    
    # Add to ChromaDB
    ids = test_store.add_documents(production_financial_documents, embeddings)
    
    assert len(ids) == len(production_financial_documents), "Should return ID for each document"
    assert all(isinstance(id_val, str) for id_val in ids), "All IDs should be strings"


@pytest.mark.integration
@pytest.mark.chromadb
def test_count(test_store, production_financial_documents, embedding_generator):
    """Test document count with production documents."""
    texts = [doc.page_content for doc in production_financial_documents]
    embeddings = embedding_generator.embed_documents(texts)
    test_store.add_documents(production_financial_documents, embeddings)
    
    count = test_store.count()
    assert count == len(production_financial_documents), "Count should match number of documents added"


@pytest.mark.integration
@pytest.mark.chromadb
def test_query_by_embedding(test_store, production_financial_documents, embedding_generator):
    """Test similarity search with real embeddings on production financial documents."""
    texts = [doc.page_content for doc in production_financial_documents]
    embeddings = embedding_generator.embed_documents(texts)
    test_store.add_documents(production_financial_documents, embeddings)
    
    # Create real query embedding for financial query
    query_text = "What was the total revenue for fiscal year 2023?"
    query_embedding = embedding_generator.embed_query(query_text)
    
    # Verify query embedding is real
    assert len(query_embedding) == embedding_generator.get_embedding_dimensions(), \
        "Query embedding should have correct dimensions"
    
    results = test_store.query_by_embedding(query_embedding, n_results=2)
    
    assert "ids" in results, "Results should contain ids"
    assert "documents" in results, "Results should contain documents"
    assert len(results["ids"]) > 0, "Should find at least one result"
    assert len(results["ids"]) <= 2, "Should respect n_results parameter"
    
    # Verify results are relevant (should find revenue document)
    if results["documents"]:
        content_lower = " ".join([doc.lower() for doc in results["documents"]]).lower()
        # Should find revenue-related content
        assert "revenue" in content_lower or "394.3" in content_lower, \
            "Results should be relevant to revenue query"


@pytest.mark.integration
@pytest.mark.chromadb
def test_get_by_ids(test_store, production_financial_documents, embedding_generator):
    """Test retrieving production documents by IDs."""
    texts = [doc.page_content for doc in production_financial_documents]
    embeddings = embedding_generator.embed_documents(texts)
    ids = test_store.add_documents(production_financial_documents, embeddings)
    
    # Get first document
    results = test_store.get_by_ids([ids[0]])
    
    assert "ids" in results, "Results should contain ids"
    assert len(results["ids"]) > 0, "Should retrieve document"
    assert results["ids"][0] == ids[0], "Retrieved ID should match"
    
    # Verify content matches
    if results["documents"]:
        assert results["documents"][0] == production_financial_documents[0].page_content, \
            "Retrieved content should match original"


@pytest.mark.integration
@pytest.mark.chromadb
def test_get_all(test_store, production_financial_documents, embedding_generator):
    """Test retrieving all production documents."""
    texts = [doc.page_content for doc in production_financial_documents]
    embeddings = embedding_generator.embed_documents(texts)
    test_store.add_documents(production_financial_documents, embeddings)
    
    results = test_store.get_all()
    
    assert "ids" in results, "Results should contain ids"
    assert len(results["ids"]) == len(production_financial_documents), "Should retrieve all documents"
    
    # Verify all documents are present
    retrieved_content = " ".join(results["documents"]).lower()
    assert "revenue" in retrieved_content, "Should contain revenue document"
    assert "risk" in retrieved_content, "Should contain risk document"
    assert "liquidity" in retrieved_content, "Should contain liquidity document"


@pytest.mark.integration
@pytest.mark.chromadb
def test_metadata_filtering(test_store, production_financial_documents, embedding_generator):
    """Test metadata filtering with production documents and real embeddings."""
    texts = [doc.page_content for doc in production_financial_documents]
    embeddings = embedding_generator.embed_documents(texts)
    test_store.add_documents(production_financial_documents, embeddings)
    
    # Create real query embedding
    query_text = "financial information and business operations"
    query_embedding = embedding_generator.embed_query(query_text)
    
    # Query with metadata filter for 10-K documents
    results = test_store.query_by_embedding(
        query_embedding,
        n_results=5,
        where={"type": "10-K"},
    )
    
    assert "ids" in results, "Results should contain ids"
    # Verify all results match the filter
    if results["ids"] and "metadatas" in results:
        for metadata in results["metadatas"]:
            if metadata:
                assert metadata.get("type") == "10-K", "Results should match type filter"
                assert metadata.get("company") == "test_company", "Results should match company filter"

