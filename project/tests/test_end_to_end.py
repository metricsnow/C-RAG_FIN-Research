"""
Pytest tests for end-to-end workflow - production conditions.

Tests the complete workflow from document ingestion to RAG querying
with real embeddings, production financial documents, and full system integration.
No demo data - all tests use production conditions.
"""

import pytest

from app.ingestion import IngestionPipeline
from app.rag.chain import create_rag_system


@pytest.fixture
def end_to_end_system(embedding_generator):
    """Create complete end-to-end system for testing."""
    collection_name = "test_e2e_production"
    
    # Create pipeline
    pipeline = IngestionPipeline(
        embedding_provider=embedding_generator.provider,
        collection_name=collection_name,
    )
    
    # Create RAG system
    rag_system = create_rag_system(
        collection_name=collection_name,
        top_k=5,
        embedding_provider=embedding_generator.provider,
    )
    
    return {
        "pipeline": pipeline,
        "rag_system": rag_system,
        "collection_name": collection_name,
    }


@pytest.fixture
def populated_e2e_system(
    end_to_end_system,
    production_financial_document_1,
    production_financial_document_2,
    production_financial_document_3,
    production_financial_document_4,
    production_financial_document_5,
):
    """Create end-to-end system with production documents indexed."""
    from langchain_core.documents import Document
    
    documents = [
        Document(
            page_content=production_financial_document_1,
            metadata={"source": "10-K_2023_revenue.txt", "type": "10-K", "section": "revenue"},
        ),
        Document(
            page_content=production_financial_document_2,
            metadata={"source": "10-K_2023_risks.txt", "type": "10-K", "section": "risks"},
        ),
        Document(
            page_content=production_financial_document_3,
            metadata={"source": "10-K_2023_liquidity.txt", "type": "10-K", "section": "liquidity"},
        ),
        Document(
            page_content=production_financial_document_4,
            metadata={"source": "investment_report.txt", "type": "report"},
        ),
        Document(
            page_content=production_financial_document_5,
            metadata={"source": "market_analysis.txt", "type": "analysis"},
        ),
    ]
    
    # Index all documents
    end_to_end_system["pipeline"].process_document_objects(documents)
    
    return end_to_end_system


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_end_to_end_workflow(populated_e2e_system):
    """Test complete end-to-end workflow: ingestion -> indexing -> querying."""
    pipeline = populated_e2e_system["pipeline"]
    rag_system = populated_e2e_system["rag_system"]
    
    # Verify documents are indexed
    doc_count = pipeline.get_document_count()
    assert doc_count > 0, "Documents should be indexed"
    
    # Test query
    query = "What was the total revenue for fiscal year 2023?"
    result = rag_system.query(query)
    
    # Verify query result
    assert "answer" in result, "Should return answer"
    assert result["chunks_used"] > 0, "Should use chunks from indexed documents"
    assert len(result["sources"]) > 0, "Should have source citations"
    
    # Verify answer quality
    answer_lower = result["answer"].lower()
    assert "revenue" in answer_lower or "394.3" in answer_lower or "billion" in answer_lower, \
        "Answer should contain relevant information from indexed documents"


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_end_to_end_multiple_queries(populated_e2e_system):
    """Test multiple queries on indexed documents."""
    rag_system = populated_e2e_system["rag_system"]
    
    queries = [
        "What was the total revenue for fiscal year 2023?",
        "What are the main risk factors?",
        "What was the cash from operating activities in 2023?",
        "What is the asset allocation strategy?",
        "What were the market performance trends in 2023?",
    ]
    
    results = []
    for query in queries:
        result = rag_system.query(query)
        results.append(result)
        
        assert "answer" in result, f"Query '{query}' should return answer"
        assert result["chunks_used"] > 0, f"Query '{query}' should use chunks"
        assert len(result["answer"]) > 20, f"Query '{query}' should return substantial answer"
    
    # Verify all queries returned different answers
    answers = [r["answer"] for r in results]
    assert len(set(answers)) == len(answers), "Different queries should return different answers"


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_end_to_end_similarity_search(populated_e2e_system):
    """Test similarity search through pipeline."""
    pipeline = populated_e2e_system["pipeline"]
    
    query = "revenue recognition and financial reporting"
    similar_docs = pipeline.search_similar(query, n_results=3)
    
    assert len(similar_docs) > 0, "Should find similar documents"
    assert len(similar_docs) <= 3, "Should respect n_results"
    
    # Verify documents contain relevant content
    content_lower = " ".join([doc.page_content.lower() for doc in similar_docs])
    assert "revenue" in content_lower, "Should find revenue-related documents"


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_end_to_end_citation_tracking(populated_e2e_system):
    """Test that citations are properly tracked in RAG responses."""
    rag_system = populated_e2e_system["rag_system"]
    
    query = "What information is available about revenue?"
    result = rag_system.query(query)
    
    # Verify citations
    assert "sources" in result, "Result should contain sources"
    assert len(result["sources"]) > 0, "Should have at least one source"
    
    # Verify source metadata
    for source in result["sources"]:
        assert isinstance(source, dict), "Source should be a dictionary"
        assert "source" in source or "filename" in source, \
            "Source should contain source information"


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_end_to_end_top_k_variation(populated_e2e_system):
    """Test that top_k parameter affects results."""
    rag_system = populated_e2e_system["rag_system"]
    
    query = "What are the key financial metrics?"
    
    # Test with different top_k values
    result_k2 = rag_system.query(query, top_k=2)
    result_k5 = rag_system.query(query, top_k=5)
    result_k10 = rag_system.query(query, top_k=10)
    
    # Verify top_k is respected
    assert result_k2["chunks_used"] <= 2, "Should respect top_k=2"
    assert result_k5["chunks_used"] <= 5, "Should respect top_k=5"
    assert result_k10["chunks_used"] <= 10, "Should respect top_k=10"
    
    # Verify all queries returned answers
    assert len(result_k2["answer"]) > 0, "Top_k=2 should return answer"
    assert len(result_k5["answer"]) > 0, "Top_k=5 should return answer"
    assert len(result_k10["answer"]) > 0, "Top_k=10 should return answer"


@pytest.mark.integration
@pytest.mark.ollama
def test_end_to_end_empty_collection(end_to_end_system):
    """Test end-to-end workflow with empty collection."""
    rag_system = end_to_end_system["rag_system"]
    
    query = "What is the revenue?"
    result = rag_system.query(query)
    
    assert "answer" in result, "Should return answer even with empty collection"
    assert result["chunks_used"] == 0, "Should have 0 chunks when collection is empty"
    assert "couldn't find" in result["answer"].lower() or "no relevant" in result["answer"].lower(), \
        "Should indicate no documents found"

