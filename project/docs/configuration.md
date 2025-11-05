# Configuration Management

## Overview

The application uses **Pydantic-based configuration management** for type-safe configuration with automatic validation. This provides robust configuration handling with clear error messages and prevents runtime errors from invalid configuration.

## Dependency Management

The project uses modern Python dependency management via `pyproject.toml` (PEP 621 standard). Dependencies are organized into groups for better management:

- **Core Dependencies**: Runtime dependencies required for the application
- **Optional Dependencies**: Development, testing, and documentation tools

**Installation**:
```bash
# Install core dependencies
pip install -e .

# Install with optional dependencies
pip install -e ".[dev,test,docs]"
```

**Development Dependencies** (`[dev]` group) include:
- **Code Quality Tools**: black (formatter), flake8 (linter), isort (import sorter), pre-commit (hooks)
- **Type Checking**: mypy (static type checker)
- **Testing**: pytest, pytest-cov (see `[test]` group)
- **Documentation**: sphinx, sphinx-rtd-theme (see `[docs]` group)

**Code Quality Tools**:
The project uses pre-commit hooks with black, flake8, and isort for automated code formatting and linting. After installing dev dependencies, set up hooks:
```bash
pre-commit install
```

For more details on code quality tools, see:
- [README.md](../README.md#pre-commit-hooks-code-formatting-and-linting)
- [Testing Documentation](testing.md#code-quality)

**Legacy Support**: The `requirements.txt` file is maintained for backward compatibility.

For more details, see the main [README.md](../README.md#step-3-install-dependencies).

## Configuration System

### Key Features

- **Type Safety**: All configuration fields are type-annotated and validated automatically
- **Automatic Validation**: Invalid configuration values are caught at startup with clear error messages
- **Environment Variables**: Supports both `.env` file and system environment variables
- **Backward Compatible**: All existing configuration access patterns continue to work
- **Enhanced Validation**: Custom validators for URLs, log levels, and business logic

### How It Works

The configuration system uses Pydantic's `BaseSettings` which:
1. Automatically loads environment variables from `.env` file (if present)
2. Loads from system environment variables
3. Validates all values against type annotations and constraints
4. Provides default values for missing configuration
5. Raises clear validation errors for invalid configuration

## Configuration Variables

### Ollama Configuration

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `OLLAMA_BASE_URL` | string | `http://localhost:11434` | Must start with `http://` or `https://` | Ollama server URL |
| `OLLAMA_TIMEOUT` | integer | `30` | Must be >= 1 | Request timeout in seconds |
| `OLLAMA_MAX_RETRIES` | integer | `3` | Must be >= 0 | Maximum retry attempts |
| `OLLAMA_TEMPERATURE` | float | `0.7` | Range: 0.0 - 2.0 | LLM temperature |
| `OLLAMA_PRIORITY` | integer | `1` | Must be >= 0 | Request priority |
| `OLLAMA_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable Ollama LLM provider |

### OpenAI Configuration

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `OPENAI_API_KEY` | string | `""` | - | OpenAI API key for embeddings (required if using OpenAI embeddings) |

### ChromaDB Configuration

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `CHROMA_DB_PATH` | string | `./data/chroma_db` | - | ChromaDB database path |
| `CHROMA_PERSIST_DIRECTORY` | string | `./data/chroma_db` | - | ChromaDB persist directory |

### LLM Configuration

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `LLM_PROVIDER` | string | `ollama` | Currently only `ollama` | LLM provider |
| `LLM_MODEL` | string | `llama3.2` | - | Ollama model name |

### Embedding Configuration

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `EMBEDDING_PROVIDER` | string | `openai` | Must be `openai` or `ollama` | Embedding provider |

### Logging Configuration

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `LOG_LEVEL` | string | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | Logging level |
| `LOG_FILE` | string | `None` | - | Log file path (None = console only) |
| `LOG_FILE_MAX_BYTES` | integer | `10485760` (10MB) | Must be >= 1024 | Maximum log file size before rotation |
| `LOG_FILE_BACKUP_COUNT` | integer | `5` | Must be >= 1 | Number of backup log files to keep |

### Monitoring and Observability Configuration

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `METRICS_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable Prometheus metrics collection |
| `METRICS_PORT` | integer | `8000` | Range: 1024 - 65535 | Port for Prometheus metrics HTTP server |
| `HEALTH_CHECK_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable health check endpoints |
| `HEALTH_CHECK_PORT` | integer | `8080` | Range: 1024 - 65535 | Port for health check HTTP server |

**Metrics Collection**:
- Metrics are automatically collected for all key operations
- Metrics are exposed in Prometheus format at `http://localhost:{METRICS_PORT}/metrics`
- Metrics include: RAG queries, document ingestion, vector DB operations, LLM requests, embeddings, and system health

**Health Check Endpoints**:
- `/health` - Comprehensive health check with component status
- `/health/live` - Liveness probe (application running)
- `/health/ready` - Readiness probe (application ready to serve)
- Available at `http://localhost:{HEALTH_CHECK_PORT}/health`

**Health Check Components**:
- ChromaDB connectivity and document count
- Ollama service availability (if using Ollama LLM provider)
- OpenAI API connectivity (if using OpenAI embeddings)
- System resource status

**Example Configuration**:
```bash
# Enable metrics and health checks
METRICS_ENABLED=true
METRICS_PORT=8000
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_PORT=8080
```

**Disabling Monitoring**:
```bash
# Disable metrics collection
METRICS_ENABLED=false

# Disable health checks
HEALTH_CHECK_ENABLED=false
```

### Application Configuration

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `MAX_DOCUMENT_SIZE_MB` | integer | `10` | Must be >= 1 | Maximum document size in MB |
| `DEFAULT_TOP_K` | integer | `5` | Must be >= 1 | Default number of chunks to retrieve |

### RAG Optimization Configuration (TASK-028)

The system includes advanced RAG optimizations for improved answer quality. All optimizations are configurable and can be enabled/disabled independently.

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `RAG_USE_HYBRID_SEARCH` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable hybrid search (semantic + BM25) |
| `RAG_USE_RERANKING` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable reranking with cross-encoder |
| `RAG_CHUNK_SIZE` | integer | `800` | Range: 100 - 2000 | Optimized chunk size for financial documents |
| `RAG_CHUNK_OVERLAP` | integer | `150` | Range: 0 - 500 | Optimized chunk overlap for context preservation |
| `RAG_TOP_K_INITIAL` | integer | `20` | Range: 5 - 100 | Initial retrieval count (before reranking) |
| `RAG_TOP_K_FINAL` | integer | `5` | Range: 1 - 20 | Final retrieval count (after reranking) |
| `RAG_RERANK_MODEL` | string | `cross-encoder/ms-marco-MiniLM-L-6-v2` | - | Reranking model name |
| `RAG_QUERY_EXPANSION` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable financial domain query expansion |
| `RAG_FEW_SHOT_EXAMPLES` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Include few-shot examples in prompts |

**Optimization Features**:

1. **Hybrid Search**: Combines semantic (vector similarity) and keyword (BM25) search for improved retrieval accuracy.
   - Semantic search finds documents by meaning
   - BM25 finds documents by exact keyword matches
   - Results are merged using Reciprocal Rank Fusion (RRF)

2. **Reranking**: Uses cross-encoder models to rerank retrieved documents for better relevance.
   - Initial retrieval: broad retrieval with high recall (top 20)
   - Reranking: reorder by relevance using cross-encoder
   - Final retrieval: top-k most relevant documents (top 5)

3. **Optimized Chunking**: Semantic chunking with structure-aware boundaries optimized for financial documents.
   - Smaller chunks (800 chars) for better precision
   - Strategic overlap (150 chars) for context preservation
   - Respects document structure (paragraphs, sections)

4. **Query Refinement**: Financial domain-specific query expansion and rewriting.
   - Expands financial terms (e.g., "revenue" → "revenue income sales earnings")
   - Normalizes query text
   - Adds domain context

5. **Prompt Engineering**: Financial domain-optimized prompts with few-shot examples.
   - Clear instructions for financial domain
   - Few-shot examples for better understanding
   - Enhanced context formatting

**Example Configuration**:
```bash
# Enable all optimizations (recommended for best quality)
RAG_USE_HYBRID_SEARCH=true
RAG_USE_RERANKING=true
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=150
RAG_TOP_K_INITIAL=20
RAG_TOP_K_FINAL=5
RAG_QUERY_EXPANSION=true
RAG_FEW_SHOT_EXAMPLES=true

# Disable optimizations for faster queries (lower quality)
RAG_USE_HYBRID_SEARCH=false
RAG_USE_RERANKING=false

# Customize chunking for your documents
RAG_CHUNK_SIZE=1000  # Larger chunks for longer documents
RAG_CHUNK_OVERLAP=200  # More overlap for better context
```

**Performance Considerations**:
- Hybrid search: Slightly slower but more accurate (recommended)
- Reranking: Adds latency but significantly improves relevance (recommended)
- Query expansion: Minimal overhead, improves retrieval (recommended)
- Few-shot examples: No performance impact, improves answer quality (recommended)

**Backward Compatibility**: All optimizations are backward compatible. If optimization components fail to load, the system gracefully falls back to basic retrieval.

## Validation

### Type Validation

All configuration values are automatically validated for correct types:
- Strings must be valid strings
- Integers must be valid integers
- Floats must be valid floats
- Booleans can be: `true`/`false`, `1`/`0`, `yes`/`no`

### Constraint Validation

Numeric constraints are enforced:
- `OLLAMA_TIMEOUT` must be >= 1
- `OLLAMA_TEMPERATURE` must be between 0.0 and 2.0
- `MAX_DOCUMENT_SIZE_MB` must be >= 1
- `DEFAULT_TOP_K` must be >= 1
- `LOG_FILE_MAX_BYTES` must be >= 1024
- `LOG_FILE_BACKUP_COUNT` must be >= 1
- `METRICS_PORT` must be between 1024 and 65535
- `HEALTH_CHECK_PORT` must be between 1024 and 65535
- `RAG_CHUNK_SIZE` must be between 100 and 2000
- `RAG_CHUNK_OVERLAP` must be between 0 and 500
- `RAG_TOP_K_INITIAL` must be between 5 and 100
- `RAG_TOP_K_FINAL` must be between 1 and 20

### Custom Validation

Custom validators enforce business rules:
- **Ollama URL**: Must start with `http://` or `https://`
- **Log Level**: Must be one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Business Logic**:
  - Warns if OpenAI embeddings are selected but no API key is provided
  - Validates that Ollama is enabled when LLM provider is set to 'ollama'

### Invalid Configuration Examples

```bash
# These will cause validation errors at startup:
OLLAMA_BASE_URL=invalid-url           # Must start with http:// or https://
LOG_LEVEL=INVALID                     # Must be valid log level
OLLAMA_TIMEOUT=0                      # Must be >= 1
OLLAMA_TEMPERATURE=3.0                # Must be <= 2.0
MAX_DOCUMENT_SIZE_MB=0                # Must be >= 1
```

### Error Messages

When validation fails, Pydantic provides clear error messages indicating:
- Which configuration variable is invalid
- What the expected type/format is
- What the actual value is
- How to fix it

Example error message:
```
1 validation error for Config
ollama_base_url
  Ollama base URL must start with http:// or https:// [type=value_error, input_value='invalid-url', input_type=str]
```

## Usage

### Basic Usage

```python
from app.utils.config import config

# Access configuration (backward compatible)
print(config.LLM_PROVIDER)  # 'ollama'
print(config.OLLAMA_BASE_URL)  # 'http://localhost:11434'
print(config.LOG_LEVEL)  # 'INFO'

# Validate configuration
config.validate()  # Returns True if valid, raises ValueError if invalid

# Get Ollama configuration dictionary
ollama_config = config.get_ollama_config()
# Returns: {'base_url': '...', 'timeout': 30, 'temperature': 0.7, 'model': 'llama3.2'}
```

### Environment Variables

Configuration is loaded from:
1. `.env` file in project root (if exists)
2. System environment variables
3. Default values (if neither above provides a value)

**Priority**: System environment variables override `.env` file values.

### Creating .env File

Create a `.env` file in the project root:

```bash
# OpenAI API Key (optional, recommended for embeddings)
OPENAI_API_KEY=your-api-key-here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=30
OLLAMA_TEMPERATURE=0.7
OLLAMA_ENABLED=true

# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2

# Embedding Configuration
EMBEDDING_PROVIDER=openai

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
LOG_FILE_MAX_BYTES=10485760
LOG_FILE_BACKUP_COUNT=5

# Application Configuration
MAX_DOCUMENT_SIZE_MB=10
DEFAULT_TOP_K=5
```

### Path Properties

The configuration also provides computed path properties:

```python
from app.utils.config import config

# Project paths
config.PROJECT_ROOT  # Path to project root
config.DATA_DIR      # Path to data directory
config.DOCUMENTS_DIR # Path to documents directory
config.CHROMA_DB_DIR # Path to ChromaDB directory
```

## Migration from Previous Configuration

The Pydantic migration maintains **100% backward compatibility**. All existing code continues to work without modification:

- All uppercase attribute access (`config.ATTRIBUTE_NAME`) works unchanged
- `get_ollama_config()` method works unchanged
- `validate()` method works unchanged (with enhanced validation)

No code changes are required in existing modules.

## Troubleshooting

### Configuration Validation Errors

If you see validation errors at startup:

1. **Check the error message**: It will indicate which variable is invalid
2. **Verify the value**: Ensure it matches the expected type and constraints
3. **Check .env file**: Ensure syntax is correct (no quotes needed for strings)
4. **Check environment variables**: System environment variables override .env

### Common Issues

**Issue**: `OLLAMA_BASE_URL` validation error
- **Solution**: Ensure URL starts with `http://` or `https://`

**Issue**: `LOG_LEVEL` validation error
- **Solution**: Use one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**Issue**: Numeric constraint error (e.g., `OLLAMA_TIMEOUT=0`)
- **Solution**: Ensure value meets the minimum constraint (>= 1 for timeout)

**Issue**: Boolean parsing error
- **Solution**: Use `true`/`false`, `1`/`0`, or `yes`/`no` for boolean values

## Best Practices

1. **Use .env file**: Store configuration in `.env` file (not committed to git)
2. **Set defaults**: Use sensible defaults for optional configuration
3. **Validate early**: Configuration is validated at startup, catching errors early
4. **Document values**: Document expected values and constraints in your `.env` file
5. **Test configuration**: Test configuration changes in development before production

## Implementation Details

The configuration system is implemented using:
- **Pydantic 2.x**: For type validation and settings management
- **pydantic-settings**: For environment variable loading
- **Field validators**: For custom validation logic
- **Property decorators**: For backward compatibility

The configuration class (`app.utils.config.Config`) extends `BaseSettings` and provides:
- Automatic environment variable loading
- Type validation
- Constraint validation
- Custom field validators
- Backward-compatible property accessors
