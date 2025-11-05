"""
Pytest tests for RAG System Optimizations (TASK-028).

Tests query refinement, prompt engineering, hybrid search, and reranking optimizations.
"""

import pytest

from app.rag.embedding_factory import EmbeddingGenerator
from app.rag.prompt_engineering import PromptEngineer
from app.rag.query_refinement import QueryRefiner
from app.rag.retrieval_optimizer import RetrievalOptimizer
from app.vector_db import ChromaStore


def test_query_refiner_initialization():
    """Test QueryRefiner initialization."""
    refiner = QueryRefiner(enable_expansion=True, enable_multi_query=False)
    assert refiner is not None
    assert refiner.enable_expansion is True
    assert refiner.enable_multi_query is False


def test_query_refinement():
    """Test query refinement functionality."""
    refiner = QueryRefiner(enable_expansion=True)

    # Test basic refinement
    query = "What is revenue?"
    refined = refiner.refine_query(query)
    assert refined is not None
    assert len(refined) >= len(query)  # Should expand or at least normalize

    # Test financial term expansion
    query2 = "company profit"
    refined2 = refiner.refine_query(query2)
    assert "profit" in refined2.lower() or "earnings" in refined2.lower()


def test_prompt_engineer_initialization():
    """Test PromptEngineer initialization."""
    engineer = PromptEngineer(include_few_shot=True)
    assert engineer is not None
    assert engineer.include_few_shot is True


def test_prompt_engineer_get_optimized_prompt():
    """Test optimized prompt generation."""
    engineer = PromptEngineer(include_few_shot=True)
    prompt = engineer.get_optimized_prompt()
    assert prompt is not None

    # Check prompt template has required placeholders
    prompt_text = (
        prompt.messages[0].prompt.template
        if hasattr(prompt, "messages")
        else str(prompt)
    )
    assert "{context}" in prompt_text or "context" in prompt_text.lower()
    assert "{question}" in prompt_text or "question" in prompt_text.lower()


def test_prompt_engineer_format_context():
    """Test enhanced context formatting."""
    from langchain_core.documents import Document

    engineer = PromptEngineer()
    docs = [
        Document(
            page_content="Test content",
            metadata={
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "form_type": "10-K",
            },
        )
    ]

    formatted = engineer.format_context_enhanced(docs)
    assert formatted is not None
    assert "Apple Inc." in formatted or "AAPL" in formatted
    assert "10-K" in formatted


@pytest.mark.skip(reason="Requires ChromaDB with documents indexed")
def test_retrieval_optimizer_initialization():
    """Test RetrievalOptimizer initialization."""
    chroma_store = ChromaStore(collection_name="test_optimizer")
    embedding_generator = EmbeddingGenerator(provider="openai")

    optimizer = RetrievalOptimizer(
        chroma_store=chroma_store,
        embedding_generator=embedding_generator,
        use_hybrid_search=True,
        use_reranking=False,  # Skip reranking for faster tests
        top_k_initial=10,
        top_k_final=5,
    )

    assert optimizer is not None
    assert optimizer.use_hybrid_search is True
    assert optimizer.use_reranking is False


def test_retrieval_optimizer_without_reranking():
    """Test RetrievalOptimizer without reranking (faster)."""
    chroma_store = ChromaStore(collection_name="test_optimizer_no_rerank")
    embedding_generator = EmbeddingGenerator(provider="openai")

    optimizer = RetrievalOptimizer(
        chroma_store=chroma_store,
        embedding_generator=embedding_generator,
        use_hybrid_search=False,  # Disable hybrid for faster test
        use_reranking=False,
        top_k_initial=10,
        top_k_final=5,
    )

    assert optimizer is not None
    assert optimizer.reranker is None


def test_query_refiner_multi_query():
    """Test multi-query generation."""
    refiner = QueryRefiner(enable_multi_query=True)

    query = "What is revenue and profit?"
    queries = refiner.generate_multi_queries(query, max_queries=3)

    assert len(queries) >= 1
    assert query in queries  # Original should be included


def test_query_refiner_decompose():
    """Test query decomposition."""
    refiner = QueryRefiner()

    query = "What is revenue and profit?"
    sub_queries = refiner.decompose_query(query)

    assert len(sub_queries) >= 1
    assert isinstance(sub_queries, list)
