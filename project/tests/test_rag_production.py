"""
Pytest tests for RAG Query System - production conditions.

Tests the complete RAG system with real embeddings, production financial documents,
and end-to-end query processing. No demo data - all tests use production conditions.
"""

import pytest

from app.ingestion import IngestionPipeline
from app.rag.chain import RAGQuerySystem, create_rag_system, RAGQueryError


@pytest.fixture
def production_rag_system(embedding_generator):
    """Create RAG system with real embeddings for production testing."""
    return create_rag_system(
        collection_name="test_rag_production",
        top_k=5,
        embedding_provider=embedding_generator.provider,
    )


@pytest.fixture
def populated_rag_system(
    production_rag_system,
    production_financial_document_1,
    production_financial_document_2,
    production_financial_document_3,
    production_financial_document_4,
    embedding_generator,
):
    """Create RAG system with production financial documents indexed."""
    from langchain_core.documents import Document
    
    # Create documents
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
            metadata={"source": "investment_report.txt", "type": "report", "topic": "portfolio"},
        ),
    ]
    
    # Index documents using pipeline
    pipeline = IngestionPipeline(
        embedding_provider=embedding_generator.provider,
        collection_name="test_rag_production",
    )
    pipeline.process_document_objects(documents)
    
    return production_rag_system


@pytest.mark.integration
@pytest.mark.ollama
def test_rag_system_initialization(production_rag_system):
    """Test RAG system initialization with production configuration."""
    assert production_rag_system is not None, "RAG system should be created"
    assert production_rag_system.top_k == 5, "Top-k should be set correctly"
    assert production_rag_system.chroma_store is not None, "ChromaDB store should be initialized"
    assert production_rag_system.embedding_generator is not None, "Embedding generator should be initialized"


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_rag_query_with_revenue_document(populated_rag_system):
    """Test RAG query on revenue-related financial document."""
    query = "What was the total revenue for fiscal year 2023?"
    
    result = populated_rag_system.query(query)
    
    # Verify result structure
    assert "answer" in result, "Result should contain answer"
    assert "sources" in result, "Result should contain sources"
    assert "chunks_used" in result, "Result should contain chunks_used"
    
    # Verify answer quality
    assert isinstance(result["answer"], str), "Answer should be a string"
    assert len(result["answer"]) > 0, "Answer should not be empty"
    
    # Verify chunks were used
    assert result["chunks_used"] > 0, "Should use at least one chunk"
    assert result["chunks_used"] <= 5, "Should not exceed top_k"
    
    # Verify sources
    assert len(result["sources"]) > 0, "Should have at least one source"
    assert any("revenue" in str(source).lower() or "10-K" in str(source) for source in result["sources"]), \
        "Should include revenue-related sources"
    
    # Verify answer contains relevant information
    answer_lower = result["answer"].lower()
    assert "revenue" in answer_lower or "394.3" in answer_lower or "billion" in answer_lower, \
        "Answer should contain revenue-related information"


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_rag_query_with_risk_document(populated_rag_system):
    """Test RAG query on risk factors document."""
    query = "What are the main risk factors mentioned in the 10-K filing?"
    
    result = populated_rag_system.query(query)
    
    assert "answer" in result, "Result should contain answer"
    assert result["chunks_used"] > 0, "Should use chunks for answer"
    assert len(result["answer"]) > 50, "Answer should be substantial"
    
    answer_lower = result["answer"].lower()
    # Should mention risk-related content
    assert any(keyword in answer_lower for keyword in ["risk", "market", "regulation", "legal"]), \
        "Answer should contain risk-related information"


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_rag_query_with_liquidity_document(populated_rag_system):
    """Test RAG query on liquidity and cash flow document."""
    query = "What was the cash provided by operating activities in fiscal 2023?"
    
    result = populated_rag_system.query(query)
    
    assert "answer" in result, "Result should contain answer"
    assert result["chunks_used"] > 0, "Should use chunks"
    
    answer_lower = result["answer"].lower()
    # Should mention cash flow information
    assert any(keyword in answer_lower for keyword in ["cash", "110.5", "billion", "operating"]), \
        "Answer should contain cash flow information"


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_rag_query_top_k_variation(populated_rag_system):
    """Test RAG query with different top_k values."""
    query = "What are the key financial metrics for fiscal year 2023?"
    
    # Test with default top_k
    result1 = populated_rag_system.query(query, top_k=None)
    chunks_default = result1["chunks_used"]
    
    # Test with custom top_k
    result2 = populated_rag_system.query(query, top_k=2)
    chunks_custom = result2["chunks_used"]
    
    # Test with larger top_k
    result3 = populated_rag_system.query(query, top_k=10)
    chunks_large = result3["chunks_used"]
    
    # Verify top_k is respected
    assert chunks_custom <= 2, "Should respect top_k=2"
    assert chunks_large <= 10, "Should respect top_k=10"
    assert chunks_default <= 5, "Should respect default top_k=5"
    
    # Verify all queries returned answers
    assert len(result1["answer"]) > 0, "Default top_k should return answer"
    assert len(result2["answer"]) > 0, "Top_k=2 should return answer"
    assert len(result3["answer"]) > 0, "Top_k=10 should return answer"


@pytest.mark.integration
@pytest.mark.ollama
def test_rag_query_empty_collection(production_rag_system):
    """Test RAG query with empty collection - should handle gracefully."""
    query = "What is the revenue for fiscal year 2023?"
    
    result = production_rag_system.query(query)
    
    assert "answer" in result, "Result should contain answer"
    assert result["chunks_used"] == 0, "Should have 0 chunks when collection is empty"
    assert "couldn't find" in result["answer"].lower() or "no relevant" in result["answer"].lower(), \
        "Should indicate no documents found"


@pytest.mark.integration
@pytest.mark.ollama
def test_rag_query_error_handling_empty_question(populated_rag_system):
    """Test error handling for empty question."""
    with pytest.raises(RAGQueryError):
        populated_rag_system.query("")
    
    with pytest.raises(RAGQueryError):
        populated_rag_system.query("   ")


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_rag_query_simple_interface(populated_rag_system):
    """Test simple query interface that returns only answer string."""
    query = "What was the total revenue for fiscal year 2023?"
    
    answer = populated_rag_system.query_simple(query)
    
    assert isinstance(answer, str), "Should return string"
    assert len(answer) > 0, "Answer should not be empty"
    assert "revenue" in answer.lower() or "394.3" in answer.lower() or "billion" in answer.lower(), \
        "Answer should contain relevant information"


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_rag_query_multiple_queries(populated_rag_system):
    """Test multiple sequential queries on production documents."""
    queries = [
        "What was the total revenue for fiscal year 2023?",
        "What are the main risk factors?",
        "What was the cash from operating activities?",
    ]
    
    results = []
    for query in queries:
        result = populated_rag_system.query(query)
        results.append(result)
        
        assert "answer" in result, f"Query '{query}' should return answer"
        assert result["chunks_used"] > 0, f"Query '{query}' should use chunks"
        assert len(result["answer"]) > 20, f"Query '{query}' should return substantial answer"
    
    # Verify all queries returned different answers
    answers = [r["answer"] for r in results]
    assert len(set(answers)) == len(answers), "Different queries should return different answers"

