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
    Environment variables are automatically loaded from .env file and
    system environment.
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
        default=30,
        ge=1,
        alias="OLLAMA_TIMEOUT",
        description="Request timeout in seconds",
    )
    ollama_max_retries: int = Field(
        default=3,
        ge=0,
        alias="OLLAMA_MAX_RETRIES",
        description="Maximum retry attempts",
    )
    ollama_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        alias="OLLAMA_TEMPERATURE",
        description="LLM temperature",
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
        default="./data/chroma_db",
        alias="CHROMA_DB_PATH",
        description="ChromaDB database path",
    )
    chroma_persist_directory: str = Field(
        default="./data/chroma_db",
        alias="CHROMA_PERSIST_DIRECTORY",
        description="ChromaDB persist directory",
    )

    # Application Configuration
    max_document_size_mb: int = Field(
        default=10,
        ge=1,
        alias="MAX_DOCUMENT_SIZE_MB",
        description="Maximum document size in MB",
    )
    default_top_k: int = Field(
        default=5,
        ge=1,
        alias="DEFAULT_TOP_K",
        description="Default number of documents to retrieve",
    )

    # Embedding Configuration
    embedding_provider: str = Field(
        default="openai",
        alias="EMBEDDING_PROVIDER",
        description="Embedding provider (openai, ollama, or finbert)",
    )
    finbert_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="FINBERT_MODEL_NAME",
        description="FinBERT/sentence-transformer model name for financial embeddings",
    )

    # LLM Configuration
    llm_provider: str = Field(
        default="ollama", alias="LLM_PROVIDER", description="LLM provider"
    )
    llm_model: str = Field(
        default="llama3.2", alias="LLM_MODEL", description="LLM model name"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO", alias="LOG_LEVEL", description="Logging level"
    )
    log_file: Optional[str] = Field(
        default=None,
        alias="LOG_FILE",
        description="Log file path (None = console only)",
    )
    log_file_max_bytes: int = Field(
        default=10 * 1024 * 1024,
        ge=1024,
        alias="LOG_FILE_MAX_BYTES",
        description="Maximum log file size in bytes (10MB)",
    )
    log_file_backup_count: int = Field(
        default=5,
        ge=1,
        alias="LOG_FILE_BACKUP_COUNT",
        description="Number of backup log files to keep",
    )

    # Metrics Configuration
    metrics_enabled: bool = Field(
        default=True,
        alias="METRICS_ENABLED",
        description="Enable Prometheus metrics collection",
    )
    metrics_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        alias="METRICS_PORT",
        description="Port for Prometheus metrics HTTP server",
    )

    # Health Check Configuration
    health_check_enabled: bool = Field(
        default=True,
        alias="HEALTH_CHECK_ENABLED",
        description="Enable health check endpoints",
    )
    health_check_port: int = Field(
        default=8080,
        ge=1024,
        le=65535,
        alias="HEALTH_CHECK_PORT",
        description="Port for health check HTTP server",
    )

    # RAG Optimization Configuration
    rag_use_hybrid_search: bool = Field(
        default=True,
        alias="RAG_USE_HYBRID_SEARCH",
        description="Enable hybrid search (semantic + BM25)",
    )
    rag_use_reranking: bool = Field(
        default=True,
        alias="RAG_USE_RERANKING",
        description="Enable reranking with cross-encoder",
    )
    rag_chunk_size: int = Field(
        default=800,
        ge=100,
        le=2000,
        alias="RAG_CHUNK_SIZE",
        description="Optimized chunk size for financial documents",
    )
    rag_chunk_overlap: int = Field(
        default=150,
        ge=0,
        le=500,
        alias="RAG_CHUNK_OVERLAP",
        description="Optimized chunk overlap for context preservation",
    )
    rag_top_k_initial: int = Field(
        default=20,
        ge=5,
        le=100,
        alias="RAG_TOP_K_INITIAL",
        description="Initial retrieval count (before reranking)",
    )
    rag_top_k_final: int = Field(
        default=5,
        ge=1,
        le=20,
        alias="RAG_TOP_K_FINAL",
        description="Final retrieval count (after reranking)",
    )
    rag_rerank_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        alias="RAG_RERANK_MODEL",
        description="Reranking model name",
    )
    rag_query_expansion: bool = Field(
        default=True,
        alias="RAG_QUERY_EXPANSION",
        description="Enable financial domain query expansion",
    )
    rag_few_shot_examples: bool = Field(
        default=True,
        alias="RAG_FEW_SHOT_EXAMPLES",
        description="Include few-shot examples in prompts",
    )

    # Conversation Memory Configuration
    conversation_enabled: bool = Field(
        default=True,
        alias="CONVERSATION_ENABLED",
        description="Enable conversation memory for context in queries",
    )
    conversation_max_tokens: int = Field(
        default=2000,
        ge=100,
        le=10000,
        alias="CONVERSATION_MAX_TOKENS",
        description="Maximum tokens for conversation context",
    )
    conversation_max_history: int = Field(
        default=10,
        ge=1,
        le=50,
        alias="CONVERSATION_MAX_HISTORY",
        description="Maximum number of previous messages to include",
    )
    conversation_use_langchain_memory: bool = Field(
        default=True,
        alias="CONVERSATION_USE_LANGCHAIN_MEMORY",
        description="Use LangChain memory components for conversation management",
    )

    # API Configuration (TASK-029)
    api_host: str = Field(
        default="0.0.0.0",
        alias="API_HOST",
        description="API server host address",
    )
    api_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        alias="API_PORT",
        description="API server port",
    )
    api_title: str = Field(
        default="Financial Research Assistant API",
        alias="API_TITLE",
        description="API title for OpenAPI documentation",
    )
    api_version: str = Field(
        default="1.0.0",
        alias="API_VERSION",
        description="API version",
    )
    api_enabled: bool = Field(
        default=True,
        alias="API_ENABLED",
        description="Enable API server",
    )
    api_key: str = Field(
        default="",
        alias="API_KEY",
        description="API key for authentication (empty = disabled)",
    )
    api_rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        alias="API_RATE_LIMIT_PER_MINUTE",
        description="API rate limit per minute per API key/IP",
    )
    api_cors_origins: str = Field(
        default="*",
        alias="API_CORS_ORIGINS",
        description="CORS allowed origins (comma-separated, * for all)",
    )

    # yfinance Configuration (TASK-030)
    yfinance_enabled: bool = Field(
        default=True,
        alias="YFINANCE_ENABLED",
        description="Enable yfinance stock data integration",
    )
    yfinance_rate_limit_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        alias="YFINANCE_RATE_LIMIT_SECONDS",
        description="Rate limit between yfinance API calls in seconds",
    )
    yfinance_history_period: str = Field(
        default="1y",
        alias="YFINANCE_HISTORY_PERIOD",
        description=(
            "Default period for historical data "
            "(1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)"
        ),
    )
    yfinance_history_interval: str = Field(
        default="1d",
        alias="YFINANCE_HISTORY_INTERVAL",
        description=(
            "Default interval for historical data "
            "(1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)"
        ),
    )

    # Enhanced EDGAR Integration Configuration (TASK-032)
    edgar_enhanced_parsing: bool = Field(
        default=True,
        alias="EDGAR_ENHANCED_PARSING",
        description="Enable enhanced parsing for Form 4, S-1, DEF 14A, and XBRL",
    )
    edgar_form_types: str = Field(
        default="10-K,10-Q,8-K,4,S-1,DEF 14A",
        alias="EDGAR_FORM_TYPES",
        description="Comma-separated list of form types to fetch",
    )
    edgar_xbrl_enabled: bool = Field(
        default=True,
        alias="EDGAR_XBRL_ENABLED",
        description="Enable XBRL financial statement extraction",
    )

    # Earnings Call Transcripts Configuration (TASK-033)
    # Uses API Ninjas Earnings Call Transcript API (recommended)
    # with web scraping fallback
    transcript_enabled: bool = Field(
        default=True,
        alias="TRANSCRIPT_ENABLED",
        description="Enable earnings call transcript integration",
    )
    transcript_rate_limit_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        alias="TRANSCRIPT_RATE_LIMIT_SECONDS",
        description="Rate limit between transcript requests in seconds",
    )
    api_ninjas_api_key: str = Field(
        default="",
        alias="API_NINJAS_API_KEY",
        description=(
            "API Ninjas API key for earnings call transcripts " "(free tier available)"
        ),
    )
    transcript_use_api_ninjas: bool = Field(
        default=True,
        alias="TRANSCRIPT_USE_API_NINJAS",
        description=(
            "Use API Ninjas API for transcripts "
            "(recommended, requires API_NINJAS_API_KEY)"
        ),
    )
    transcript_use_web_scraping: bool = Field(
        default=False,
        alias="TRANSCRIPT_USE_WEB_SCRAPING",
        description=(
            "Enable web scraping for transcripts " "(fallback only, not recommended)"
        ),
    )

    # Financial News Aggregation Configuration (TASK-034)
    news_enabled: bool = Field(
        default=True,
        alias="NEWS_ENABLED",
        description="Enable financial news aggregation",
    )
    news_use_rss: bool = Field(
        default=True,
        alias="NEWS_USE_RSS",
        description="Enable RSS feed parsing for news",
    )
    news_use_scraping: bool = Field(
        default=True,
        alias="NEWS_USE_SCRAPING",
        description="Enable web scraping for news articles",
    )
    news_rss_rate_limit_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        alias="NEWS_RSS_RATE_LIMIT_SECONDS",
        description="Rate limit between RSS feed requests in seconds",
    )
    news_scraping_rate_limit_seconds: float = Field(
        default=2.0,
        ge=0.1,
        le=60.0,
        alias="NEWS_SCRAPING_RATE_LIMIT_SECONDS",
        description="Rate limit between web scraping requests in seconds",
    )
    news_scrape_full_content: bool = Field(
        default=True,
        alias="NEWS_SCRAPE_FULL_CONTENT",
        description="Scrape full article content (not just RSS summaries)",
    )

    # Economic Calendar Configuration (TASK-035)
    economic_calendar_enabled: bool = Field(
        default=True,
        alias="ECONOMIC_CALENDAR_ENABLED",
        description="Enable economic calendar integration",
    )
    economic_calendar_rate_limit_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        alias="ECONOMIC_CALENDAR_RATE_LIMIT_SECONDS",
        description="Rate limit between economic calendar requests in seconds",
    )
    trading_economics_api_key: str = Field(
        default="",
        alias="TRADING_ECONOMICS_API_KEY",
        description=(
            "Trading Economics API key for economic calendar "
            "(free tier available at https://tradingeconomics.com/api)"
        ),
    )
    economic_calendar_use_trading_economics: bool = Field(
        default=True,
        alias="ECONOMIC_CALENDAR_USE_TRADING_ECONOMICS",
        description=(
            "Use Trading Economics API for economic calendar "
            "(recommended, requires TRADING_ECONOMICS_API_KEY)"
        ),
    )

    # FRED API Configuration (TASK-036)
    fred_enabled: bool = Field(
        default=True,
        alias="FRED_ENABLED",
        description="Enable FRED API integration for economic data",
    )
    fred_api_key: str = Field(
        default="",
        alias="FRED_API_KEY",
        description=(
            "FRED API key (free API key available at "
            "https://fred.stlouisfed.org/docs/api/api_key.html)"
        ),
    )
    fred_rate_limit_seconds: float = Field(
        default=0.2,
        ge=0.0,
        alias="FRED_RATE_LIMIT_SECONDS",
        description="Rate limit between FRED API requests in seconds",
    )

    # World Bank API Configuration (TASK-037)
    world_bank_enabled: bool = Field(
        default=True,
        alias="WORLD_BANK_ENABLED",
        description="Enable World Bank Open Data API integration",
    )
    world_bank_rate_limit_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        alias="WORLD_BANK_RATE_LIMIT_SECONDS",
        description="Rate limit between World Bank API requests in seconds",
    )

    # IMF Data Portal API Configuration (TASK-037)
    imf_enabled: bool = Field(
        default=True,
        alias="IMF_ENABLED",
        description="Enable IMF Data Portal API integration",
    )
    imf_rate_limit_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        alias="IMF_RATE_LIMIT_SECONDS",
        description="Rate limit between IMF API requests in seconds",
    )

    # Central Bank Data Configuration (TASK-038)
    central_bank_enabled: bool = Field(
        default=True,
        alias="CENTRAL_BANK_ENABLED",
        description=(
            "Enable central bank data integration "
            "(FOMC statements, minutes, press conferences)"
        ),
    )
    central_bank_rate_limit_seconds: float = Field(
        default=2.0,
        ge=0.1,
        le=60.0,
        alias="CENTRAL_BANK_RATE_LIMIT_SECONDS",
        description="Rate limit between central bank web scraping requests in seconds",
    )
    central_bank_use_web_scraping: bool = Field(
        default=True,
        alias="CENTRAL_BANK_USE_WEB_SCRAPING",
        description="Enable web scraping for central bank data (FOMC website)",
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
    def FINBERT_MODEL_NAME(self) -> str:
        """FinBERT model name (backward compatibility)."""
        return self.finbert_model_name

    @property
    def LLM_PROVIDER(self) -> str:
        """LLM provider (backward compatibility)."""
        return self.llm_provider

    @property
    def LLM_MODEL(self) -> str:
        """LLM model (backward compatibility)."""
        return self.llm_model

    @property
    def RAG_USE_HYBRID_SEARCH(self) -> bool:
        """RAG hybrid search enabled (backward compatibility)."""
        return self.rag_use_hybrid_search

    @property
    def RAG_USE_RERANKING(self) -> bool:
        """RAG reranking enabled (backward compatibility)."""
        return self.rag_use_reranking

    @property
    def RAG_CHUNK_SIZE(self) -> int:
        """RAG chunk size (backward compatibility)."""
        return self.rag_chunk_size

    @property
    def RAG_CHUNK_OVERLAP(self) -> int:
        """RAG chunk overlap (backward compatibility)."""
        return self.rag_chunk_overlap

    @property
    def RAG_TOP_K_INITIAL(self) -> int:
        """RAG initial top K (backward compatibility)."""
        return self.rag_top_k_initial

    @property
    def RAG_TOP_K_FINAL(self) -> int:
        """RAG final top K (backward compatibility)."""
        return self.rag_top_k_final

    @property
    def CONVERSATION_ENABLED(self) -> bool:
        """Conversation memory enabled (backward compatibility)."""
        return self.conversation_enabled

    @property
    def CONVERSATION_MAX_TOKENS(self) -> int:
        """Conversation max tokens (backward compatibility)."""
        return self.conversation_max_tokens

    @property
    def CONVERSATION_MAX_HISTORY(self) -> int:
        """Conversation max history (backward compatibility)."""
        return self.conversation_max_history

    @property
    def CONVERSATION_USE_LANGCHAIN_MEMORY(self) -> bool:
        """Use LangChain memory (backward compatibility)."""
        return self.conversation_use_langchain_memory

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
        Pydantic already validates types and constraints, this adds business
        logic validation.

        Returns:
            bool: True if configuration is valid, False otherwise

        Raises:
            ValueError: If configuration is invalid with detailed error message
        """
        errors = []

        # Validate LLM provider configuration
        if self.llm_provider == "ollama" and not self.ollama_enabled:
            errors.append(
                "Invalid configuration: Ollama is disabled but LLM provider "
                "is set to 'ollama'"
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
