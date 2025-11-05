"""
Pytest tests for RAG query system functionality.

Tests the RAGQuerySystem for end-to-end RAG functionality.
"""

import pytest

from app.rag.chain import RAGQuerySystem, create_rag_system
from app.utils.config import config


@pytest.mark.integration
@pytest.mark.ollama
def test_rag_system_initialization():
    """Test RAG system initialization."""
    # Validate configuration
    assert config.validate(), "Configuration should be valid"

    # Create RAG system
    rag_system = create_rag_system(collection_name="test_rag", top_k=3)
    assert rag_system is not None, "RAG system should be created"
    assert isinstance(rag_system, RAGQuerySystem), "Should be RAGQuerySystem instance"


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow
def test_rag_query_empty_collection():
    """Test query with empty collection."""
    rag_system = create_rag_system(collection_name="test_empty", top_k=3)

    result = rag_system.query("What is the stock market?")

    assert "answer" in result, "Result should contain answer"
    assert "chunks_used" in result, "Result should contain chunks_used"
    assert result["chunks_used"] == 0, "Should have 0 chunks when collection is empty"
    assert isinstance(result["answer"], str), "Answer should be a string"
