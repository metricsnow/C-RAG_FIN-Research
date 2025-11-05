"""
Configuration management module.

Loads environment variables and provides configuration for the application.
Uses Pydantic for type-safe configuration with automatic validation.

This module provides a Pydantic-based configuration system that:
- Automatically loads environment variables from .env file and system environment
- Validates all configuration values with type checking and constraints
- Provides clear error messages for invalid configuration
- Maintains backward compatibility with existing code

The configuration is type-safe and validated at startup, catching configuration
errors before the application runs.

Example:
    >>> from app.utils.config import config
    >>> print(config.LLM_PROVIDER)  # 'ollama'
    >>> print(config.OLLAMA_BASE_URL)  # 'http://localhost:11434'
    >>> config.validate()  # True if valid

Configuration is automatically loaded from:
- .env file in project root (if exists)
- System environment variables
- Default values (if neither above provides a value)

All configuration values are validated:
- Types are checked (string, int, float, bool)
- Constraints are enforced (ranges, formats, allowed values)
- Custom validators run (URL format, log levels, etc.)
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
# Note: pydantic-settings handles .env loading automatically via env_file


class Config(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Uses Pydantic for type-safe configuration with automatic validation.
    Environment variables are automatically loaded from .env file and system environment.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
        populate_by_name=True,  # Allow both field name and alias
    )

    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
        description="Ollama base URL",
    )
    ollama_timeout: int = Field(
        default=30, ge=1, alias="OLLAMA_TIMEOUT", description="Request timeout in seconds"
    )
    ollama_max_retries: int = Field(
        default=3, ge=0, alias="OLLAMA_MAX_RETRIES", description="Maximum retry attempts"
    )
    ollama_temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, alias="OLLAMA_TEMPERATURE", description="LLM temperature"
    )
    ollama_priority: int = Field(
        default=1, ge=0, alias="OLLAMA_PRIORITY", description="Request priority"
    )
    ollama_enabled: bool = Field(
        default=True, alias="OLLAMA_ENABLED", description="Enable Ollama LLM provider"
    )

    # OpenAI Configuration (Optional - for embeddings)
    openai_api_key: str = Field(
        default="", alias="OPENAI_API_KEY", description="OpenAI API key for embeddings"
    )

    # ChromaDB Configuration
    chroma_db_path: str = Field(
        default="./data/chroma_db", alias="CHROMA_DB_PATH", description="ChromaDB database path"
    )
    chroma_persist_directory: str = Field(
        default="./data/chroma_db",
        alias="CHROMA_PERSIST_DIRECTORY",
        description="ChromaDB persist directory",
    )

    # Application Configuration
    max_document_size_mb: int = Field(
        default=10, ge=1, alias="MAX_DOCUMENT_SIZE_MB", description="Maximum document size in MB"
    )
    default_top_k: int = Field(
        default=5, ge=1, alias="DEFAULT_TOP_K", description="Default number of documents to retrieve"
    )

    # Embedding Configuration
    embedding_provider: str = Field(
        default="openai",
        alias="EMBEDDING_PROVIDER",
        description="Embedding provider (openai or ollama)",
    )

    # LLM Configuration
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER", description="LLM provider")
    llm_model: str = Field(default="llama3.2", alias="LLM_MODEL", description="LLM model name")

    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL", description="Logging level")
    log_file: Optional[str] = Field(
        default=None, alias="LOG_FILE", description="Log file path (None = console only)"
    )
    log_file_max_bytes: int = Field(
        default=10 * 1024 * 1024,
        ge=1024,
        alias="LOG_FILE_MAX_BYTES",
        description="Maximum log file size in bytes (10MB)",
    )
    log_file_backup_count: int = Field(
        default=5, ge=1, alias="LOG_FILE_BACKUP_COUNT", description="Number of backup log files to keep"
    )

    # Project paths (computed fields)
    _project_root: Optional[Path] = None
    _data_dir: Optional[Path] = None
    _documents_dir: Optional[Path] = None
    _chroma_db_dir: Optional[Path] = None

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_base_url(cls, v: str) -> str:
        """Validate Ollama base URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Ollama base URL must start with http:// or https://")
        return v

    @field_validator("ollama_enabled", mode="before")
    @classmethod
    def parse_ollama_enabled(cls, v) -> bool:
        """Parse enabled boolean from string."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    def __init__(self, **kwargs):
        """Initialize configuration and compute project paths."""
        super().__init__(**kwargs)
        # Compute project paths
        self._project_root = Path(__file__).parent.parent.parent
        self._data_dir = self._project_root / "data"
        self._documents_dir = self._data_dir / "documents"
        self._chroma_db_dir = self._data_dir / "chroma_db"

    # Backward compatibility properties for attribute access
    @property
    def OLLAMA_BASE_URL(self) -> str:
        """Ollama base URL (backward compatibility)."""
        return self.ollama_base_url

    @property
    def OLLAMA_TIMEOUT(self) -> int:
        """Ollama timeout (backward compatibility)."""
        return self.ollama_timeout

    @property
    def OLLAMA_MAX_RETRIES(self) -> int:
        """Ollama max retries (backward compatibility)."""
        return self.ollama_max_retries

    @property
    def OLLAMA_TEMPERATURE(self) -> float:
        """Ollama temperature (backward compatibility)."""
        return self.ollama_temperature

    @property
    def OLLAMA_PRIORITY(self) -> int:
        """Ollama priority (backward compatibility)."""
        return self.ollama_priority

    @property
    def OLLAMA_ENABLED(self) -> bool:
        """Ollama enabled (backward compatibility)."""
        return self.ollama_enabled

    @property
    def OPENAI_API_KEY(self) -> str:
        """OpenAI API key (backward compatibility)."""
        return self.openai_api_key

    @property
    def CHROMA_DB_PATH(self) -> str:
        """ChromaDB path (backward compatibility)."""
        return self.chroma_db_path

    @property
    def CHROMA_PERSIST_DIRECTORY(self) -> str:
        """ChromaDB persist directory (backward compatibility)."""
        return self.chroma_persist_directory

    @property
    def LOG_LEVEL(self) -> str:
        """Log level (backward compatibility)."""
        return self.log_level

    @property
    def LOG_FILE(self) -> Optional[str]:
        """Log file path (backward compatibility)."""
        return self.log_file

    @property
    def LOG_FILE_MAX_BYTES(self) -> int:
        """Log file max bytes (backward compatibility)."""
        return self.log_file_max_bytes

    @property
    def LOG_FILE_BACKUP_COUNT(self) -> int:
        """Log file backup count (backward compatibility)."""
        return self.log_file_backup_count

    @property
    def MAX_DOCUMENT_SIZE_MB(self) -> int:
        """Max document size in MB (backward compatibility)."""
        return self.max_document_size_mb

    @property
    def DEFAULT_TOP_K(self) -> int:
        """Default top K (backward compatibility)."""
        return self.default_top_k

    @property
    def EMBEDDING_PROVIDER(self) -> str:
        """Embedding provider (backward compatibility)."""
        return self.embedding_provider

    @property
    def LLM_PROVIDER(self) -> str:
        """LLM provider (backward compatibility)."""
        return self.llm_provider

    @property
    def LLM_MODEL(self) -> str:
        """LLM model (backward compatibility)."""
        return self.llm_model

    @property
    def PROJECT_ROOT(self) -> Path:
        """Project root directory (backward compatibility)."""
        if self._project_root is None:
            self._project_root = Path(__file__).parent.parent.parent
        return self._project_root

    @property
    def DATA_DIR(self) -> Path:
        """Data directory (backward compatibility)."""
        if self._data_dir is None:
            self._data_dir = self.PROJECT_ROOT / "data"
        return self._data_dir

    @property
    def DOCUMENTS_DIR(self) -> Path:
        """Documents directory (backward compatibility)."""
        if self._documents_dir is None:
            self._documents_dir = self.DATA_DIR / "documents"
        return self._documents_dir

    @property
    def CHROMA_DB_DIR(self) -> Path:
        """ChromaDB directory (backward compatibility)."""
        if self._chroma_db_dir is None:
            self._chroma_db_dir = self.DATA_DIR / "chroma_db"
        return self._chroma_db_dir

    def validate(self) -> bool:
        """
        Validate configuration settings.

        This method provides enhanced validation with better error messages.
        Pydantic already validates types and constraints, this adds business logic validation.

        Returns:
            bool: True if configuration is valid, False otherwise

        Raises:
            ValueError: If configuration is invalid with detailed error message
        """
        errors = []

        # Validate LLM provider configuration
        if self.llm_provider == "ollama" and not self.ollama_enabled:
            errors.append(
                "Invalid configuration: Ollama is disabled but LLM provider is set to 'ollama'"
            )

        # Validate embedding provider configuration
        if self.embedding_provider == "openai" and not self.openai_api_key:
            errors.append(
                "Warning: OpenAI embedding provider selected but no API key found. "
                "Embeddings will fail until API key is provided."
            )

        if errors:
            error_msg = "\n".join(errors)
            # For warnings, we don't raise but log them
            if "Warning:" in error_msg:
                print(error_msg)
                return True
            raise ValueError(error_msg)

        return True

    def get_ollama_config(self) -> dict:
        """
        Get Ollama configuration dictionary.

        Returns:
            dict: Ollama configuration parameters
        """
        return {
            "base_url": self.ollama_base_url,
            "timeout": self.ollama_timeout,
            "temperature": self.ollama_temperature,
            "model": self.llm_model,
        }


# Create global config instance
# Pydantic will automatically load from .env file and environment variables
try:
    config = Config()
    # Validate configuration on initialization
    config.validate()
except Exception as e:
    # If validation fails, create a minimal config and log the error
    # This allows the application to start but with warnings
    print(f"Configuration validation warning: {e}")
    print("Using default configuration. Please check your .env file.")
    config = Config()  # Use defaults
