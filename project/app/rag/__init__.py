"""
RAG (Retrieval-Augmented Generation) chain implementation.

Handles query processing, document retrieval, and answer generation.
"""

from app.rag.chain import (
    RAGQueryError,
    RAGQuerySystem,
    create_rag_system,
)
from app.rag.embedding_factory import (
    EmbeddingError,
    EmbeddingFactory,
    EmbeddingGenerator,
    get_embedding_generator,
)
from app.rag.llm_factory import create_ollama_llm, get_llm

__all__ = [
    "RAGQuerySystem",
    "RAGQueryError",
    "create_rag_system",
    "create_ollama_llm",
    "get_llm",
    "EmbeddingError",
    "EmbeddingFactory",
    "EmbeddingGenerator",
    "get_embedding_generator",
]
