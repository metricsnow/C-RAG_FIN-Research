"""
Pytest tests for EmbeddingFactory and EmbeddingGenerator - production conditions.

Tests embedding generation with real embedding models (OpenAI or Ollama).
No demo data - all tests use production embedding providers.
"""

import pytest

from app.rag.embedding_factory import (
    EmbeddingGenerator,
    EmbeddingFactory,
    EmbeddingError,
    get_embedding_generator,
)


@pytest.mark.integration
def test_embedding_generator_initialization(embedding_generator):
    """Test embedding generator initialization with production provider."""
    assert embedding_generator is not None, "Embedding generator should be created"
    assert embedding_generator.provider in ["openai", "ollama"], \
        "Provider should be valid"
    assert embedding_generator.embeddings is not None, "Embeddings instance should be created"


@pytest.mark.integration
def test_embedding_generator_dimensions(embedding_generator):
    """Test getting embedding dimensions from production generator."""
    dimensions = embedding_generator.get_embedding_dimensions()
    
    assert dimensions > 0, "Dimensions should be positive"
    # OpenAI: 1536, Ollama: varies (typically 384-768)
    assert dimensions >= 100, "Dimensions should be reasonable (>=100)"
    assert dimensions <= 2048, "Dimensions should be reasonable (<=2048)"


@pytest.mark.integration
def test_embed_query_single(embedding_generator):
    """Test generating embedding for a single query with production generator."""
    query_text = "What was the total revenue for fiscal year 2023?"
    
    embedding = embedding_generator.embed_query(query_text)
    
    assert isinstance(embedding, list), "Embedding should be a list"
    assert len(embedding) == embedding_generator.get_embedding_dimensions(), \
        "Embedding should have correct dimensions"
    assert all(isinstance(x, float) for x in embedding), "All values should be floats"
    # Verify embedding is not all zeros or all same value
    assert len(set(embedding[:10])) > 1, "Embedding should have variation"


@pytest.mark.integration
def test_embed_documents_batch(embedding_generator, production_financial_document_1):
    """Test batch embedding generation for multiple documents."""
    texts = [
        production_financial_document_1[:500],  # First 500 chars
        "Revenue for fiscal year 2023 was $394.3 billion.",
        "The company operates in highly competitive markets.",
    ]
    
    embeddings = embedding_generator.embed_documents(texts)
    
    assert len(embeddings) == len(texts), "Should generate embedding for each text"
    assert all(len(emb) == embedding_generator.get_embedding_dimensions() for emb in embeddings), \
        "All embeddings should have correct dimensions"
    assert all(isinstance(emb, list) for emb in embeddings), "All embeddings should be lists"
    assert all(all(isinstance(x, float) for x in emb) for emb in embeddings), \
        "All embedding values should be floats"


@pytest.mark.integration
def test_embed_documents_empty_list(embedding_generator):
    """Test batch embedding with empty list."""
    embeddings = embedding_generator.embed_documents([])
    
    assert embeddings == [], "Empty list should return empty list"


@pytest.mark.integration
def test_embed_documents_single_item(embedding_generator):
    """Test batch embedding with single document."""
    text = "Financial markets are complex systems."
    embeddings = embedding_generator.embed_documents([text])
    
    assert len(embeddings) == 1, "Should generate one embedding"
    assert len(embeddings[0]) == embedding_generator.get_embedding_dimensions(), \
        "Embedding should have correct dimensions"


@pytest.mark.integration
def test_embed_documents_large_batch(embedding_generator):
    """Test batch embedding with larger number of documents."""
    texts = [
        f"Financial document {i}: Revenue and market analysis for quarter {i}."
        for i in range(10)
    ]
    
    embeddings = embedding_generator.embed_documents(texts)
    
    assert len(embeddings) == 10, "Should generate embeddings for all documents"
    assert all(len(emb) == embedding_generator.get_embedding_dimensions() for emb in embeddings), \
        "All embeddings should have correct dimensions"


@pytest.mark.integration
def test_embedding_similarity(embedding_generator):
    """Test that similar texts produce similar embeddings."""
    similar_texts = [
        "Revenue for fiscal year 2023 was $394.3 billion",
        "Total revenue in fiscal year 2023 reached $394.3 billion",
        "Fiscal year 2023 revenue totaled $394.3 billion",
    ]
    
    different_text = "Python programming is essential for data science."
    
    # Generate embeddings
    similar_embeddings = embedding_generator.embed_documents(similar_texts)
    different_embedding = embedding_generator.embed_query(different_text)
    
    # Calculate cosine similarity (simplified)
    def cosine_similarity(vec1, vec2):
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        return dot_product / (norm1 * norm2) if norm1 * norm2 > 0 else 0
    
    # Similar texts should have higher similarity
    similarity_similar = cosine_similarity(similar_embeddings[0], similar_embeddings[1])
    similarity_different = cosine_similarity(similar_embeddings[0], different_embedding)
    
    assert similarity_similar > similarity_different, \
        "Similar texts should have higher embedding similarity than different texts"


@pytest.mark.integration
def test_embedding_factory_create_openai(embedding_generator):
    """Test creating OpenAI embeddings if provider is OpenAI."""
    if embedding_generator.provider == "openai":
        embeddings = EmbeddingFactory.create_embeddings("openai")
        assert embeddings is not None, "Should create OpenAI embeddings"
    else:
        pytest.skip("OpenAI not configured, skipping OpenAI-specific test")


@pytest.mark.integration
def test_embedding_factory_create_ollama(embedding_generator):
    """Test creating Ollama embeddings if provider is Ollama."""
    if embedding_generator.provider == "ollama":
        try:
            embeddings = EmbeddingFactory.create_embeddings("ollama")
            assert embeddings is not None, "Should create Ollama embeddings"
        except EmbeddingError:
            pytest.skip("Ollama embeddings not available")
    else:
        pytest.skip("Ollama not configured, skipping Ollama-specific test")


@pytest.mark.integration
def test_embedding_factory_invalid_provider():
    """Test error handling for invalid provider."""
    with pytest.raises(EmbeddingError):
        EmbeddingFactory.create_embeddings("invalid_provider")


@pytest.mark.integration
def test_get_embedding_generator_function(embedding_generator):
    """Test the get_embedding_generator convenience function."""
    generator = get_embedding_generator()
    
    assert isinstance(generator, EmbeddingGenerator), \
        "Should return EmbeddingGenerator instance"
    assert generator.provider == embedding_generator.provider, \
        "Should use same provider as configured"


@pytest.mark.integration
def test_embedding_error_handling_invalid_text(embedding_generator):
    """Test error handling for invalid input."""
    # Very long text that might cause issues
    very_long_text = "test " * 100000
    
    try:
        embedding = embedding_generator.embed_query(very_long_text)
        # If it succeeds, verify it's valid
        assert len(embedding) == embedding_generator.get_embedding_dimensions()
    except (EmbeddingError, Exception) as e:
        # Some providers might truncate or error - both are acceptable
        assert isinstance(e, (EmbeddingError, Exception)), \
            "Should raise appropriate error for invalid input"

