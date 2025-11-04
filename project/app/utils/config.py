"""
Configuration management module.

Loads environment variables and provides configuration for the application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "30"))
    OLLAMA_MAX_RETRIES: int = int(os.getenv("OLLAMA_MAX_RETRIES", "3"))
    OLLAMA_TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
    OLLAMA_PRIORITY: int = int(os.getenv("OLLAMA_PRIORITY", "1"))
    OLLAMA_ENABLED: bool = os.getenv("OLLAMA_ENABLED", "true").lower() == "true"

    # OpenAI Configuration (Optional - for embeddings)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # ChromaDB Configuration
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
    CHROMA_PERSIST_DIRECTORY: str = os.getenv(
        "CHROMA_PERSIST_DIRECTORY", "./data/chroma_db"
    )

    # Application Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_DOCUMENT_SIZE_MB: int = int(os.getenv("MAX_DOCUMENT_SIZE_MB", "10"))
    DEFAULT_TOP_K: int = int(os.getenv("DEFAULT_TOP_K", "5"))

    # Embedding Configuration
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "openai")

    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3.2")

    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    DOCUMENTS_DIR: Path = DATA_DIR / "documents"
    CHROMA_DB_DIR: Path = DATA_DIR / "chroma_db"

    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration settings.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        if cls.LLM_PROVIDER == "ollama" and not cls.OLLAMA_ENABLED:
            print("Warning: Ollama is disabled but LLM provider is set to Ollama")
            return False

        if cls.EMBEDDING_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            print(
                "Warning: OpenAI embedding provider selected but no API key found"
            )
            print("This is optional - embeddings will fail until API key is provided")

        return True

    @classmethod
    def get_ollama_config(cls) -> dict:
        """
        Get Ollama configuration dictionary.

        Returns:
            dict: Ollama configuration parameters
        """
        return {
            "base_url": cls.OLLAMA_BASE_URL,
            "timeout": cls.OLLAMA_TIMEOUT,
            "temperature": cls.OLLAMA_TEMPERATURE,
            "model": cls.LLM_MODEL,
        }


# Create global config instance
config = Config()

