"""
Embedding factory module for generating document embeddings.

Supports OpenAI and Ollama embedding models with batch processing
and error handling.
"""

from typing import List, Optional

try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    # Fallback to langchain_community for older versions
    from langchain_community.embeddings import OpenAIEmbeddings

from langchain_core.embeddings import Embeddings

from app.utils.config import config


class EmbeddingError(Exception):
    """Custom exception for embedding generation errors."""

    pass


class EmbeddingFactory:
    """
    Factory for creating embedding models.

    Supports OpenAI and Ollama embedding providers with automatic
    configuration based on environment settings.
    """

    @staticmethod
    def create_embeddings(provider: Optional[str] = None) -> Embeddings:
        """
        Create embeddings instance based on provider.

        Args:
            provider: Embedding provider ('openai' or 'ollama').
                If None, uses config.EMBEDDING_PROVIDER

        Returns:
            Embeddings instance

        Raises:
            EmbeddingError: If provider is invalid or configuration is missing
        """
        if provider is None:
            provider = config.EMBEDDING_PROVIDER

        provider = provider.lower()

        if provider == "openai":
            return EmbeddingFactory._create_openai_embeddings()
        elif provider == "ollama":
            return EmbeddingFactory._create_ollama_embeddings()
        else:
            raise EmbeddingError(
                f"Unsupported embedding provider: {provider}. "
                "Supported providers: 'openai', 'ollama'"
            )

    @staticmethod
    def _create_openai_embeddings() -> OpenAIEmbeddings:
        """
        Create OpenAI embeddings instance.

        Returns:
            OpenAIEmbeddings instance

        Raises:
            EmbeddingError: If OpenAI API key is not configured
        """
        if not config.OPENAI_API_KEY:
            raise EmbeddingError(
                "OpenAI API key not found. Please set OPENAI_API_KEY in .env file"
            )

        try:
            return OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=config.OPENAI_API_KEY,
                chunk_size=1000,
                max_retries=3,
            )
        except Exception as e:
            raise EmbeddingError(f"Failed to create OpenAI embeddings: {str(e)}") from e

    @staticmethod
    def _create_ollama_embeddings() -> Embeddings:
        """
        Create Ollama embeddings instance.

        Note: Ollama embeddings require langchain_community.embeddings.OllamaEmbeddings
        which may not be available in all versions. This implementation provides
        a fallback or alternative approach.

        Returns:
            Embeddings instance

        Raises:
            EmbeddingError: If Ollama embeddings are not available or configured
        """
        try:
            # Try to import OllamaEmbeddings
            from langchain_community.embeddings import OllamaEmbeddings

            return OllamaEmbeddings(
                base_url=config.OLLAMA_BASE_URL,
                model="llama3.2",  # Using same model as LLM
            )
        except ImportError:
            raise EmbeddingError(
                "Ollama embeddings not available. "
                "Please install langchain-community or use OpenAI embeddings."
            )
        except Exception as e:
            raise EmbeddingError(f"Failed to create Ollama embeddings: {str(e)}") from e


class EmbeddingGenerator:
    """
    High-level embedding generator with batch processing and error handling.

    Provides convenient methods for generating embeddings from text
    and document chunks.
    """

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize embedding generator.

        Args:
            provider: Embedding provider ('openai' or 'ollama').
                If None, uses config.EMBEDDING_PROVIDER
        """
        self.provider = provider or config.EMBEDDING_PROVIDER
        self.embeddings = EmbeddingFactory.create_embeddings(self.provider)

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats

        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            raise EmbeddingError(f"Failed to generate query embedding: {str(e)}") from e

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents (batch processing).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not texts:
            return []

        try:
            return self.embeddings.embed_documents(texts)
        except Exception as e:
            raise EmbeddingError(
                f"Failed to generate document embeddings: {str(e)}"
            ) from e

    def get_embedding_dimensions(self) -> int:
        """
        Get the dimensions of embeddings generated by this model.

        Returns:
            Number of dimensions in embedding vectors

        Raises:
            EmbeddingError: If dimensions cannot be determined
        """
        try:
            # Generate a test embedding to determine dimensions
            test_embedding = self.embed_query("test")
            return len(test_embedding)
        except Exception as e:
            raise EmbeddingError(
                f"Failed to determine embedding dimensions: {str(e)}"
            ) from e


def get_embedding_generator(provider: Optional[str] = None) -> EmbeddingGenerator:
    """
    Get an embedding generator instance.

    Args:
        provider: Embedding provider ('openai' or 'ollama').
            If None, uses config.EMBEDDING_PROVIDER

    Returns:
        EmbeddingGenerator instance
    """
    return EmbeddingGenerator(provider=provider)

