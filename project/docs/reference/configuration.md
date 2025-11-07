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
| `EMBEDDING_PROVIDER` | string | `openai` | Must be `openai`, `ollama`, or `finbert` | Embedding provider |
| `FINBERT_MODEL_NAME` | string | `sentence-transformers/all-MiniLM-L6-v2` | - | FinBERT/sentence-transformer model name for financial embeddings |

**Embedding Providers**:

1. **OpenAI** (`openai`): Cloud-based embeddings using OpenAI API
   - Model: `text-embedding-3-small` (1536 dimensions)
   - Requires: `OPENAI_API_KEY` environment variable
   - Pros: High quality, fast, reliable
   - Cons: Requires API key, costs per request

2. **Ollama** (`ollama`): Local embeddings using Ollama
   - Model: `llama3.2` (dimensions vary, typically 3072)
   - Requires: Ollama server running locally
   - Pros: Free, no API costs, privacy
   - Cons: Slower, requires local setup

3. **FinBERT** (`finbert`): Financial domain embeddings using sentence-transformers
   - Model: Configurable via `FINBERT_MODEL_NAME` (default: `sentence-transformers/all-MiniLM-L6-v2`)
   - Dimensions: 384 (default model) or varies by model
   - Requires: `sentence-transformers` library (already included)
   - Pros: Financial domain optimized, free, local execution
   - Cons: Slower than OpenAI API, requires model download on first use

**Model Selection Guidelines**:

- **For best quality**: Use `openai` (requires API key)
- **For privacy/cost**: Use `finbert` (local, free, financial domain optimized)
- **For local LLM stack**: Use `ollama` (if already using Ollama for LLM)

**FinBERT Model Options**:

The `FINBERT_MODEL_NAME` can be set to any HuggingFace sentence-transformer model:
- `sentence-transformers/all-MiniLM-L6-v2` (default): Fast, 384 dimensions, good general performance
- `sentence-transformers/all-mpnet-base-v2`: Better quality, 768 dimensions, slower
- Custom financial domain models: If available, can be configured here

**Dimension Compatibility**:

Different embedding providers use different dimensions:
- OpenAI: 1536 dimensions
- Ollama: Varies (typically 3072)
- FinBERT: 384 dimensions (default model)

**Important**: When switching embedding providers, you may need to re-index documents in ChromaDB, as embeddings with different dimensions are not compatible. Consider using separate ChromaDB collections for different embedding providers.

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

### Conversation Memory Configuration (TASK-024)

The system includes conversation memory functionality that maintains context across multiple queries in the same session. This enables follow-up questions and multi-turn conversations.

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `CONVERSATION_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable conversation memory for context in queries |
| `CONVERSATION_MAX_TOKENS` | integer | `2000` | Range: 100 - 10000 | Maximum tokens for conversation context |
| `CONVERSATION_MAX_HISTORY` | integer | `10` | Range: 1 - 50 | Maximum number of previous messages to include |
| `CONVERSATION_USE_LANGCHAIN_MEMORY` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Use LangChain memory components for conversation management (TASK-031) |

**Conversation Memory Features**:

1. **Context Preservation**: Maintains conversation history across multiple queries in the same session.
   - Follow-up questions can reference previous messages
   - Context automatically included in RAG queries
   - Recent messages prioritized over older ones

2. **LangChain Memory Integration** (TASK-031): Uses LangChain-compatible memory components for robust conversation management.
   - `ConversationBufferMemory`-like interface for conversation history
   - LangChain message format compatibility
   - Seamless integration with RAG chain
   - Automatic memory synchronization with Streamlit session state
   - Memory statistics and status display in UI

3. **Token Management**: Prevents context window overflow with intelligent token counting.
   - Uses `tiktoken` for accurate token counting
   - Automatically trims conversation history to fit within limits
   - Prioritizes recent messages when trimming
   - Works with both LangChain memory and legacy conversation memory

4. **Configurable Limits**: Adjustable limits for conversation context.
   - `CONVERSATION_MAX_TOKENS`: Maximum tokens for conversation context (default: 2000)
   - `CONVERSATION_MAX_HISTORY`: Maximum number of messages to include (default: 10)
   - `CONVERSATION_USE_LANGCHAIN_MEMORY`: Enable LangChain memory components (default: true)

**Example Configuration**:
```bash
# Enable conversation memory with LangChain integration (recommended)
CONVERSATION_ENABLED=true
CONVERSATION_USE_LANGCHAIN_MEMORY=true
CONVERSATION_MAX_TOKENS=2000
CONVERSATION_MAX_HISTORY=10

# Disable conversation memory (single-turn queries only)
CONVERSATION_ENABLED=false

# Use legacy conversation memory (without LangChain components)
CONVERSATION_ENABLED=true
CONVERSATION_USE_LANGCHAIN_MEMORY=false
CONVERSATION_MAX_TOKENS=2000
CONVERSATION_MAX_HISTORY=10

# Increase context window for longer conversations
CONVERSATION_MAX_TOKENS=4000
CONVERSATION_MAX_HISTORY=20

# Reduce context for faster queries
CONVERSATION_MAX_TOKENS=1000
CONVERSATION_MAX_HISTORY=5
```

**How It Works**:
- **LangChain Memory Mode** (default, `CONVERSATION_USE_LANGCHAIN_MEMORY=true`):
  - Uses `ConversationBufferMemory`-compatible interface for conversation management
  - Conversation history stored in LangChain message format (HumanMessage, AIMessage)
  - Automatically syncs with Streamlit session state on each query
  - Memory statistics displayed in UI (message count, token count, limits)
  - Memory cleared when conversation is cleared in UI
- **Legacy Memory Mode** (`CONVERSATION_USE_LANGCHAIN_MEMORY=false`):
  - Uses original conversation memory implementation
  - Conversation history stored in Streamlit session state (`st.session_state.messages`)
  - When a query is made, previous messages are automatically included as context
- **Common Behavior**:
  - Token counting ensures conversation context doesn't exceed LLM context window
  - Recent messages are prioritized when trimming conversation history
  - Backward compatible: works with or without conversation history

**Performance Considerations**:
- Conversation memory adds minimal overhead (< 10% performance impact)
- Token counting is efficient and cached
- Context formatting is optimized for prompt inclusion

**Backward Compatibility**: Conversation memory is fully backward compatible. If `conversation_history` is not provided, queries work exactly as before (single-turn mode).

### API Configuration (TASK-029)

The system includes a FastAPI backend for RESTful API access. All API configuration is managed via environment variables.

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `API_HOST` | string | `0.0.0.0` | - | API server host address |
| `API_PORT` | integer | `8000` | Range: 1024 - 65535 | API server port |
| `API_TITLE` | string | `Financial Research Assistant API` | - | API title for OpenAPI documentation |
| `API_VERSION` | string | `1.0.0` | - | API version |
| `API_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable API server |
| `API_KEY` | string | `""` | - | API key for authentication (empty = disabled) |
| `API_RATE_LIMIT_PER_MINUTE` | integer | `60` | Must be >= 1 | Rate limit per minute per API key/IP |
| `API_CORS_ORIGINS` | string | `*` | - | CORS allowed origins (comma-separated, * for all) |

**API Features**:

1. **RESTful Endpoints**: All core functionality available via REST API
   - Query endpoint: `POST /api/v1/query`
   - Ingestion endpoint: `POST /api/v1/ingest`
   - Document management: `GET /api/v1/documents`, `GET /api/v1/documents/{id}`, `DELETE /api/v1/documents/{id}`
   - Health checks: `GET /api/v1/health`, `GET /api/v1/health/live`, `GET /api/v1/health/ready`
   - Metrics: `GET /api/v1/health/metrics`

2. **Authentication**: Optional API key authentication
   - Set `API_KEY` to enable authentication
   - API key provided via `X-API-Key` header
   - If `API_KEY` is empty, authentication is disabled

3. **Rate Limiting**: Per-API-key/IP rate limiting
   - Default: 60 requests per minute
   - Configurable via `API_RATE_LIMIT_PER_MINUTE`
   - Rate limit headers in responses: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

4. **CORS Support**: Cross-origin resource sharing
   - Default: Allows all origins (`*`)
   - Configurable via `API_CORS_ORIGINS` (comma-separated list)
   - Example: `API_CORS_ORIGINS=http://localhost:3000,https://example.com`

5. **OpenAPI Documentation**: Auto-generated API documentation
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   - OpenAPI JSON: `http://localhost:8000/openapi.json`

**Example Configuration**:
```bash
# Enable API server
API_ENABLED=true
API_HOST=0.0.0.0
API_PORT=8000

# Enable authentication (optional)
API_KEY=your-secret-api-key-here

# Configure rate limiting
API_RATE_LIMIT_PER_MINUTE=60

# Configure CORS (production: restrict to known domains)
API_CORS_ORIGINS=*
```

### API Client Configuration (TASK-045) ✅

The Streamlit frontend uses an API client to communicate with the FastAPI backend. The API client configuration allows you to control how the frontend connects to the backend.

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `API_CLIENT_BASE_URL` | string | `http://localhost:8000` | Must be valid URL | Base URL for FastAPI backend |
| `API_CLIENT_KEY` | string | `""` | - | API key for authentication (uses `API_KEY` if empty) |
| `API_CLIENT_TIMEOUT` | integer | `30` | Range: 1 - 300 | Request timeout in seconds |
| `API_CLIENT_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable API client (false = use direct RAG calls) |

**API Client Features**:

1. **Automatic Fallback**: If API is unavailable, automatically falls back to direct RAG calls
2. **Health Checks**: Verifies API health before operations
3. **Retry Logic**: Automatically retries transient failures (429, 500, 502, 503, 504) with exponential backoff
4. **Connection Pooling**: Efficient HTTP session management
5. **Error Handling**: Comprehensive error handling with user-friendly messages

**Example Configuration**:
```bash
# Enable API client (recommended for production)
API_CLIENT_ENABLED=true
API_CLIENT_BASE_URL=http://localhost:8000

# Use custom API key (optional, uses API_KEY if empty)
API_CLIENT_KEY=your-api-key-here

# Configure timeout
API_CLIENT_TIMEOUT=30

# Disable API client (use direct RAG calls)
API_CLIENT_ENABLED=false
```

**When to Use API Client**:
- **Production deployments**: Enables proper frontend/backend separation
- **Multiple frontend clients**: Supports web, mobile, and CLI clients
- **Improved testability**: Frontend can be tested with mocked API calls
- **Scalability**: Backend can be scaled independently

**When to Disable API Client**:
- **Development**: Faster iteration without API server
- **Standalone deployments**: Single-process deployments
- **Legacy compatibility**: Maintains backward compatibility

**Backward Compatibility**: The frontend maintains full backward compatibility. If `API_CLIENT_ENABLED=false` or the API is unavailable, the system automatically falls back to direct RAG calls, preserving all existing functionality.

**Starting the API Server**:
```bash
# Using startup script
python scripts/start_api.py

# Or using uvicorn directly
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

**Security Recommendations**:
- Use strong, randomly generated API keys in production
- Restrict CORS origins to known domains in production
- Use HTTPS in production (configure reverse proxy with SSL/TLS)

### yfinance Configuration (TASK-030)

The system includes yfinance integration for fetching stock market data from Yahoo Finance. All yfinance settings are configurable via environment variables.

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `YFINANCE_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable yfinance stock data integration |
| `YFINANCE_RATE_LIMIT_SECONDS` | float | `1.0` | Range: 0.1 - 60.0 | Rate limit between yfinance API calls in seconds |
| `YFINANCE_HISTORY_PERIOD` | string | `1y` | Valid periods: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max` | Default period for historical price data |
| `YFINANCE_HISTORY_INTERVAL` | string | `1d` | Valid intervals: `1m`, `2m`, `5m`, `15m`, `30m`, `60m`, `90m`, `1h`, `1d`, `5d`, `1wk`, `1mo`, `3mo` | Default interval for historical price data |

**yfinance Features**:

1. **Stock Data Fetching**: Comprehensive stock market data retrieval
   - Company information and financial metrics (P/E, P/B, market cap, etc.)
   - Historical price data (OHLCV) with configurable period and interval
   - Dividend history and payment dates
   - Earnings data (quarterly and annual)
   - Analyst recommendations and price targets

2. **Rate Limiting**: Built-in rate limiting to prevent API abuse
   - Default: 1 second between API calls
   - Configurable via `YFINANCE_RATE_LIMIT_SECONDS`
   - Prevents Yahoo Finance API rate limiting issues

3. **Data Normalization**: Automatic conversion to text format
   - All data types normalized to searchable text
   - Proper metadata tagging (ticker, data type, date, source)
   - Optimized for RAG queries and vector search

4. **Error Handling**: Robust error handling for API failures
   - Graceful handling of missing data
   - Continues processing other tickers if one fails
   - Comprehensive logging for debugging

**Example Configuration**:
```bash
# Enable yfinance integration (default)
YFINANCE_ENABLED=true

# Adjust rate limiting (conservative to avoid API issues)
YFINANCE_RATE_LIMIT_SECONDS=1.0

# Configure historical data period
YFINANCE_HISTORY_PERIOD=1y  # 1 year of historical data
YFINANCE_HISTORY_INTERVAL=1d  # Daily intervals

# For more historical data
YFINANCE_HISTORY_PERIOD=5y  # 5 years
YFINANCE_HISTORY_INTERVAL=1wk  # Weekly intervals

# For recent data only
YFINANCE_HISTORY_PERIOD=1mo  # 1 month
YFINANCE_HISTORY_INTERVAL=1d  # Daily intervals
```

**Usage**:
```bash
# Fetch stock data via script
python scripts/fetch_stock_data.py AAPL MSFT GOOGL

# Programmatic usage
from app.ingestion.pipeline import IngestionPipeline

pipeline = IngestionPipeline()
chunk_ids = pipeline.process_stock_data("AAPL", include_history=True)
```

**Performance Considerations**:
- Rate limiting: Conservative default (1 second) prevents API issues but slows batch processing
- Historical data: Larger periods/intervals increase processing time and storage
- Data volume: Each ticker generates multiple document chunks (info, history, dividends, earnings, recommendations)

**Backward Compatibility**: yfinance integration is optional and can be disabled by setting `YFINANCE_ENABLED=false`. The system continues to work normally without stock data integration.

For complete yfinance integration documentation, see: **[yfinance Integration Guide](yfinance_integration.md)**

### Enhanced EDGAR Integration Configuration (TASK-032)

The system includes enhanced SEC EDGAR integration with support for additional form types and XBRL financial statement parsing. All enhanced EDGAR settings are configurable via environment variables.

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `EDGAR_ENHANCED_PARSING` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable enhanced parsing for Form 4, S-1, DEF 14A, and XBRL |
| `EDGAR_FORM_TYPES` | string | `10-K,10-Q,8-K,4,S-1,DEF 14A` | Comma-separated list of form types | Form types to fetch from SEC EDGAR |
| `EDGAR_XBRL_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable XBRL financial statement extraction for 10-K and 10-Q filings |

**Enhanced EDGAR Features**:

1. **Enhanced Form Parsing**: Specialized parsers for additional SEC form types
   - **Form 4**: Insider trading transactions, insider names, positions, transaction details
   - **Form S-1**: IPO offering details, risk factors, company information
   - **DEF 14A**: Proxy statements, voting items, executive compensation, board members
   - All enhanced forms include structured metadata extraction

2. **XBRL Financial Statement Extraction**: Structured financial data from XBRL files
   - Automatic XBRL file detection and download for 10-K and 10-Q filings
   - Balance sheet data extraction (assets, liabilities, equity)
   - Income statement data extraction (revenue, expenses, net income)
   - Cash flow statement data extraction (operating, investing, financing activities)
   - Fallback mode: Uses basic XML parsing if Arelle library is unavailable

3. **Graceful Degradation**: System continues to work if enhanced features are unavailable
   - If enhanced parsers fail to load, basic parsing is used
   - If XBRL parsing fails, filing text is still extracted
   - All enhanced features are optional and can be disabled

**Example Configuration**:
```bash
# Enable all enhanced features (recommended)
EDGAR_ENHANCED_PARSING=true
EDGAR_XBRL_ENABLED=true
EDGAR_FORM_TYPES=10-K,10-Q,8-K,4,S-1,DEF 14A

# Disable enhanced parsing (use basic parsing only)
EDGAR_ENHANCED_PARSING=false

# Disable XBRL extraction (faster, but no structured financial data)
EDGAR_XBRL_ENABLED=false

# Fetch only specific form types
EDGAR_FORM_TYPES=10-K,10-Q  # Only annual and quarterly reports

# Fetch only insider trading forms
EDGAR_FORM_TYPES=4  # Only Form 4 filings
```

**Dependencies**:
- Enhanced parsing requires: `beautifulsoup4>=4.12.0`, `lxml>=5.0.0`
- XBRL parsing requires: `arelle>=2.0.0` (optional, fallback available)
- All dependencies are listed in `requirements.txt`

**Performance Considerations**:
- Enhanced parsing: Adds minimal overhead (< 5% processing time)
- XBRL parsing: Adds moderate overhead (10-20% for 10-K/10-Q filings)
- Form-specific parsing: Automatically applied based on form type
- Graceful degradation: No performance impact if enhanced features are disabled

**Backward Compatibility**: Enhanced EDGAR integration is fully backward compatible. If enhanced parsing is disabled or parsers fail to load, the system falls back to basic HTML text extraction. All existing EDGAR integration code continues to work without modification.

For complete EDGAR integration documentation, see: **[EDGAR Integration Guide](../integrations/edgar_integration.md)**

### Earnings Call Transcripts Configuration (TASK-033)

The system includes earnings call transcript integration for fetching and indexing earnings call transcripts using the **API Ninjas Earnings Call Transcript API** (recommended) with optional web scraping fallback. All transcript settings are configurable via environment variables.

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `TRANSCRIPT_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable earnings call transcript integration |
| `API_NINJAS_API_KEY` | string | `""` | String | API Ninjas API key for earnings call transcripts (free tier available at https://api-ninjas.com) |
| `TRANSCRIPT_USE_API_NINJAS` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Use API Ninjas API for transcripts (recommended, default: true) |
| `TRANSCRIPT_USE_WEB_SCRAPING` | boolean | `false` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable web scraping fallback (not recommended, default: false) |
| `TRANSCRIPT_RATE_LIMIT_SECONDS` | float | `1.0` | Range: 0.1 - 60.0 | Rate limit between transcript requests in seconds |

**✅ IMPLEMENTED**: API Ninjas integration is complete and enabled by default. Web scraping is available as fallback but disabled by default.

**Example Configuration**:
```bash
# Enable transcript integration
TRANSCRIPT_ENABLED=true

# API Ninjas API Key (required for transcript fetching)
# Get free API key at: https://api-ninjas.com
API_NINJAS_API_KEY=your-api-key-here

# Use API Ninjas API (recommended, default: true)
TRANSCRIPT_USE_API_NINJAS=true

# Enable web scraping fallback (not recommended, default: false)
TRANSCRIPT_USE_WEB_SCRAPING=false

# Rate limiting for transcript requests
TRANSCRIPT_RATE_LIMIT_SECONDS=1.0
```

**Backward Compatibility**: Transcript integration is optional and can be disabled by setting `TRANSCRIPT_ENABLED=false`. The system continues to work normally without transcript integration.

**API Ninjas Integration**: The system uses API Ninjas as the primary source for earnings call transcripts (enabled by default). Web scraping is available as a fallback but is disabled by default due to potential Terms of Service violations. Users should obtain a free API key from https://api-ninjas.com and add it to their `.env` file.

For complete transcript integration documentation, see: **[Transcript Integration Guide](../integrations/transcript_integration.md)**.

### Financial News Aggregation Configuration (TASK-034)

The system includes financial news aggregation for fetching and indexing news articles from RSS feeds and web scraping. All news settings are configurable via environment variables.

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `NEWS_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable financial news aggregation |
| `NEWS_USE_RSS` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable RSS feed parsing for news |
| `NEWS_USE_SCRAPING` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable web scraping for news articles |
| `NEWS_RSS_RATE_LIMIT_SECONDS` | float | `1.0` | Range: 0.1 - 60.0 | Rate limit between RSS feed requests in seconds |
| `NEWS_SCRAPING_RATE_LIMIT_SECONDS` | float | `2.0` | Range: 0.1 - 60.0 | Rate limit between web scraping requests in seconds |
| `NEWS_SCRAPE_FULL_CONTENT` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Scrape full article content (not just RSS summaries) |

**News Aggregation Features**:

1. **RSS Feed Parsing**: Parse RSS feeds from major financial news sources
   - Reuters Finance, CNBC, MarketWatch, Financial Times
   - Automatic source detection from feed URL
   - Extracts title, content, date, author, source metadata

2. **Web Scraping**: Scrape full article content with respectful rate limiting
   - Support for Reuters, Bloomberg, CNBC, Financial Times
   - Source-specific content selectors
   - Proper user agents and rate limiting

3. **Ticker Detection**: Automatic extraction of ticker symbols
   - Regex pattern matching (1-5 uppercase letters)
   - Filters out common words
   - Stored as comma-separated list in metadata

4. **Article Categorization**: Automatic categorization based on content
   - Categories: earnings, markets, analysis, m&a, ipo, general
   - Keyword-based detection
   - Stored in article metadata

5. **Deduplication**: URL-based deduplication to avoid duplicate articles

**Example Configuration**:
```bash
# Enable news aggregation (default)
NEWS_ENABLED=true

# Enable RSS feed parsing
NEWS_USE_RSS=true

# Enable web scraping
NEWS_USE_SCRAPING=true

# Rate limiting for RSS feeds (conservative to respect servers)
NEWS_RSS_RATE_LIMIT_SECONDS=1.0

# Rate limiting for web scraping (more conservative)
NEWS_SCRAPING_RATE_LIMIT_SECONDS=2.0

# Scrape full content for RSS articles (recommended)
NEWS_SCRAPE_FULL_CONTENT=true

# RSS-only mode (no scraping)
NEWS_USE_SCRAPING=false
NEWS_SCRAPE_FULL_CONTENT=false

# Scraping-only mode (no RSS)
NEWS_USE_RSS=false
```

**Usage**:
```bash
# Fetch news from RSS feeds
python scripts/fetch_news.py --feeds https://www.reuters.com/finance/rss

# Scrape specific articles
python scripts/fetch_news.py --urls https://www.reuters.com/article/example

# Programmatic usage
from app.ingestion.pipeline import IngestionPipeline

pipeline = IngestionPipeline()
chunk_ids = pipeline.process_news(
    feed_urls=["https://www.reuters.com/finance/rss"],
    enhance_with_scraping=True
)
```

**Performance Considerations**:
- Rate limiting: Conservative defaults prevent being blocked but slow batch processing
- RSS feeds: Faster than scraping, but may have limited content
- Web scraping: Slower but provides full article content
- Deduplication: Prevents duplicate articles but adds processing overhead

**Backward Compatibility**: News aggregation is optional and can be disabled by setting `NEWS_ENABLED=false`. The system continues to work normally without news integration.

For complete news aggregation documentation, see: **[News Aggregation Integration Guide](../integrations/news_aggregation.md)**

For complete API documentation, see [API Documentation](api.md).

### FRED API Configuration (TASK-036)

The system includes FRED (Federal Reserve Economic Data) API integration for fetching and indexing economic time series data. All FRED settings are configurable via environment variables.

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `FRED_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable FRED API integration |
| `FRED_API_KEY` | string | `""` | Non-empty string | FRED API key (required for API access) |
| `FRED_RATE_LIMIT_SECONDS` | float | `0.2` | Range: 0.0 - 60.0 | Rate limit between FRED API requests in seconds |

**FRED API Features**:

1. **Time Series Fetching**: Access to 840,000+ economic time series
   - Interest rates (Federal Funds Rate, Treasury yields)
   - Exchange rates (USD/EUR, USD/JPY, USD/GBP, etc.)
   - Inflation indicators (CPI, PPI, Core inflation)
   - Employment data (Unemployment rate, Non-farm payrolls)
   - GDP and economic growth indicators
   - Monetary indicators (Money supply M1, M2, Bank reserves)
   - And many more economic indicators

2. **Series Search**: Text-based search for discovering series
   - Search by keywords (e.g., "unemployment rate", "inflation")
   - Returns series ID, title, units, frequency
   - Helps discover relevant series for your use case

3. **Date Range Filtering**: Flexible date range support
   - Filter by start and end dates
   - Supports historical data retrieval
   - Automatic handling of date formats

4. **Rate Limiting**: Built-in rate limiting to respect API limits
   - Default: 0.2 seconds between API calls (300 requests per minute)
   - Free tier: 120 requests per minute
   - Configurable via `FRED_RATE_LIMIT_SECONDS`
   - Prevents API rate limiting issues

5. **Data Formatting**: Automatic conversion to text format
   - All time series normalized to searchable text
   - Rich metadata tagging (series_id, title, units, frequency, etc.)
   - Summary statistics included (mean, min, max, latest value)
   - Optimized for RAG queries and vector search

6. **Error Handling**: Robust error handling for API failures
   - Graceful handling of missing data
   - Continues processing other series if one fails
   - Comprehensive logging for debugging

**Example Configuration**:
```bash
# Enable FRED integration (default)
FRED_ENABLED=true

# FRED API key (required - get free key at https://fred.stlouisfed.org/docs/api/api_key.html)
FRED_API_KEY=your-fred-api-key-here

# Adjust rate limiting (default: 0.2 seconds = 300 requests/min)
# For free tier (120 requests/min), use 0.5 seconds
FRED_RATE_LIMIT_SECONDS=0.2

# For more conservative rate limiting
FRED_RATE_LIMIT_SECONDS=0.5  # 120 requests per minute
FRED_RATE_LIMIT_SECONDS=1.0  # 60 requests per minute
```

**Usage**:
```bash
# Fetch specific series via script
python scripts/fetch_fred_data.py --series GDP UNRATE FEDFUNDS

# Fetch with date range
python scripts/fetch_fred_data.py --series GDP --start-date 2020-01-01 --end-date 2024-12-31

# Search for series
python scripts/fetch_fred_data.py --search "unemployment rate"

# Programmatic usage
from app.ingestion.pipeline import IngestionPipeline

pipeline = IngestionPipeline()
chunk_ids = pipeline.process_fred_series(
    series_ids=["GDP", "UNRATE", "FEDFUNDS"],
    start_date="2020-01-01",
    end_date="2024-12-31",
    store_embeddings=True
)
```

**Common Series IDs**:
- `GDP`: Gross Domestic Product
- `UNRATE`: Unemployment Rate
- `FEDFUNDS`: Federal Funds Rate
- `CPIAUCSL`: Consumer Price Index for All Urban Consumers
- `PPIACO`: Producer Price Index for All Commodities
- `M2SL`: M2 Money Stock
- `DEXUSEU`: U.S. / Euro Foreign Exchange Rate
- `DEXJPUS`: Japanese Yen to U.S. Dollar Spot Exchange Rate
- `DGS10`: 10-Year Treasury Constant Maturity Rate
- `DGS30`: 30-Year Treasury Constant Maturity Rate

**Backward Compatibility**: FRED integration is optional and can be disabled by setting `FRED_ENABLED=false`. The system continues to work normally without FRED integration.

**API Key**: A free FRED API key is available at https://fred.stlouisfed.org/docs/api/api_key.html. The free tier provides 120 requests per minute, which is sufficient for most use cases.

For complete FRED integration documentation, see: **[FRED API Integration Guide](../integrations/fred_integration.md)**.

### World Bank API Configuration (TASK-037)

The system includes World Bank Open Data API integration for fetching and indexing global economic data. All World Bank settings are configurable via environment variables.

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `WORLD_BANK_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable World Bank Open Data API integration |
| `WORLD_BANK_RATE_LIMIT_SECONDS` | float | `1.0` | Range: 0.1 - 60.0 | Rate limit between World Bank API requests in seconds |

**World Bank API Features**:

1. **Global Economic Data**: Access to economic indicators for 188+ countries
   - GDP (current US$, per capita, growth)
   - Population statistics
   - Inflation indicators (consumer prices, annual %)
   - Unemployment rate (% of total labor force)
   - Trade balance (% of GDP)
   - And thousands of other indicators

2. **Indicator Search**: Text-based search for discovering indicators
   - Search by keywords (e.g., "gdp", "inflation", "unemployment")
   - Returns indicator code, name, source, topic
   - Helps discover relevant indicators for your use case

3. **Country and Year Filtering**: Flexible filtering support
   - Filter by country ISO codes (e.g., "USA", "CHN")
   - Filter by start and end year
   - Supports historical data retrieval

4. **Rate Limiting**: Built-in rate limiting to respect API limits
   - Default: 1.0 seconds between API calls (60 requests per minute)
   - Configurable via `WORLD_BANK_RATE_LIMIT_SECONDS`
   - Prevents API rate limiting issues

5. **Data Formatting**: Automatic conversion to text format
   - All indicator data normalized to searchable text
   - Rich metadata tagging (indicator_code, name, source, topic, unit, etc.)
   - Summary statistics included (mean, min, max, latest values)
   - Optimized for RAG queries and vector search

6. **Error Handling**: Robust error handling for API failures
   - Graceful handling of missing data
   - Continues processing other indicators if one fails
   - Comprehensive logging for debugging

**Example Configuration**:
```bash
# Enable World Bank integration (default)
WORLD_BANK_ENABLED=true

# Adjust rate limiting (default: 1.0 seconds = 60 requests/min)
WORLD_BANK_RATE_LIMIT_SECONDS=1.0

# For more conservative rate limiting
WORLD_BANK_RATE_LIMIT_SECONDS=2.0  # 30 requests per minute
```

**Usage**:
```bash
# Fetch specific indicators via script
python scripts/fetch_world_bank_data.py --indicators NY.GDP.MKTP.CD SP.POP.TOTL

# Fetch with country and year filters
python scripts/fetch_world_bank_data.py --indicators NY.GDP.MKTP.CD --countries USA CHN --start-year 2020

# Search for indicators
python scripts/fetch_world_bank_data.py --search "gdp"

# List available countries
python scripts/fetch_world_bank_data.py --list-countries

# Programmatic usage
from app.ingestion.pipeline import IngestionPipeline

pipeline = IngestionPipeline()
chunk_ids = pipeline.process_world_bank_indicators(
    indicator_codes=["NY.GDP.MKTP.CD", "SP.POP.TOTL"],
    country_codes=["USA", "CHN"],
    start_year=2020,
    end_year=2023,
    store_embeddings=True
)
```

**Common Indicator Codes**:
- `NY.GDP.MKTP.CD`: GDP (current US$)
- `SP.POP.TOTL`: Population, total
- `FP.CPI.TOTL.ZG`: Inflation, consumer prices (annual %)
- `SL.UEM.TOTL.ZS`: Unemployment, total (% of total labor force)
- `NE.TRD.GNFS.ZS`: Trade (% of GDP)
- `NY.GDP.PCAP.CD`: GDP per capita (current US$)

**Backward Compatibility**: World Bank integration is optional and can be disabled by setting `WORLD_BANK_ENABLED=false`. The system continues to work normally without World Bank integration.

**API Key**: No API key required. World Bank Open Data API is free and open.

For complete World Bank integration documentation, see: **[IMF and World Bank Integration Guide](../integrations/imf_world_bank_integration.md)**.

### IMF Data Portal API Configuration (TASK-037)

The system includes IMF Data Portal API integration for fetching and indexing global economic data from the International Monetary Fund. All IMF settings are configurable via environment variables.

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `IMF_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable IMF Data Portal API integration |
| `IMF_RATE_LIMIT_SECONDS` | float | `1.0` | Range: 0.1 - 60.0 | Rate limit between IMF API requests in seconds |

**IMF API Features**:

1. **Global Economic Data**: Access to IMF economic databases
   - World Economic Outlook (WEO) database
   - International Financial Statistics (IFS)
   - GDP growth rates (annual %)
   - Unemployment rates (%)
   - Consumer price inflation (annual %)
   - Current account balance (US$)
   - And many more economic indicators

2. **Indicator Discovery**: List available indicators
   - Get all available indicators with codes and descriptions
   - Helps discover relevant indicators for your use case
   - Filter by country and year range

3. **Country and Year Filtering**: Flexible filtering support
   - Filter by country ISO codes (e.g., "US", "CN")
   - Filter by start and end year
   - Supports historical data retrieval

4. **Rate Limiting**: Built-in rate limiting to respect API limits
   - Default: 1.0 seconds between API calls (60 requests per minute)
   - Configurable via `IMF_RATE_LIMIT_SECONDS`
   - Prevents API rate limiting issues

5. **Data Formatting**: Automatic conversion to text format
   - All indicator data normalized to searchable text
   - Rich metadata tagging (indicator_code, name, description, unit, etc.)
   - Summary statistics included (mean, min, max, latest values)
   - Optimized for RAG queries and vector search

6. **Error Handling**: Robust error handling for API failures
   - Graceful handling of missing data
   - Continues processing other indicators if one fails
   - Comprehensive logging for debugging

**Example Configuration**:
```bash
# Enable IMF integration (default)
IMF_ENABLED=true

# Adjust rate limiting (default: 1.0 seconds = 60 requests/min)
IMF_RATE_LIMIT_SECONDS=1.0

# For more conservative rate limiting
IMF_RATE_LIMIT_SECONDS=2.0  # 30 requests per minute
```

**Usage**:
```bash
# Fetch specific indicators via script
python scripts/fetch_imf_data.py --indicators NGDP_RPCH LUR

# Fetch with country and year filters
python scripts/fetch_imf_data.py --indicators NGDP_RPCH --countries US CN --start-year 2020

# List available indicators
python scripts/fetch_imf_data.py --list-indicators

# List available countries
python scripts/fetch_imf_data.py --list-countries

# Programmatic usage
from app.ingestion.pipeline import IngestionPipeline

pipeline = IngestionPipeline()
chunk_ids = pipeline.process_imf_indicators(
    indicator_codes=["NGDP_RPCH", "LUR"],
    country_codes=["US", "CN"],
    start_year=2020,
    end_year=2023,
    store_embeddings=True
)
```

**Common Indicator Codes**:
- `NGDP_RPCH`: GDP growth rate (annual %)
- `LUR`: Unemployment rate (%)
- `PCPI_PCH`: Consumer price inflation (annual %)
- `NGDPD`: GDP (current prices, US$)
- `BCA`: Current account balance (US$)

**Backward Compatibility**: IMF integration is optional and can be disabled by setting `IMF_ENABLED=false`. The system continues to work normally without IMF integration.

**API Key**: No API key required. IMF Data Portal API is free and open.

For complete IMF integration documentation, see: **[IMF and World Bank Integration Guide](../integrations/imf_world_bank_integration.md)**.

### Central Bank Data Configuration (TASK-038)

The system includes central bank data integration for fetching and indexing FOMC (Federal Reserve) communications including statements, meeting minutes, and press conference transcripts. All central bank settings are configurable via environment variables.

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `CENTRAL_BANK_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable central bank data integration (FOMC statements, minutes, press conferences) |
| `CENTRAL_BANK_RATE_LIMIT_SECONDS` | float | `2.0` | Range: 0.1 - 60.0 | Rate limit between central bank web scraping requests in seconds |
| `CENTRAL_BANK_USE_WEB_SCRAPING` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable web scraping for central bank data (FOMC website) |

### Financial Sentiment Analysis Configuration (TASK-039)

The system includes comprehensive financial sentiment analysis using multiple models (FinBERT, TextBlob, VADER) for analyzing earnings calls, MD&A sections, and news articles. Sentiment analysis is automatically applied during document ingestion and results are stored as metadata.

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|------------|-------------|
| `SENTIMENT_ENABLED` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Enable financial sentiment analysis |
| `SENTIMENT_USE_FINBERT` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Use FinBERT model for financial sentiment analysis (recommended) |
| `SENTIMENT_USE_TEXTBLOB` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Use TextBlob for rule-based sentiment scoring |
| `SENTIMENT_USE_VADER` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Use VADER sentiment analyzer for financial text |
| `SENTIMENT_EXTRACT_GUIDANCE` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Extract forward guidance statements from documents |
| `SENTIMENT_EXTRACT_RISKS` | boolean | `true` | `true`/`false`, `1`/`0`, `yes`/`no` | Extract risk factors from documents |

**Sentiment Analysis Features**:

1. **Multiple Model Support**: Three sentiment analysis models for comprehensive analysis
   - **FinBERT**: Financial domain-specific BERT model (ProsusAI/finbert) - recommended for financial text
   - **TextBlob**: Rule-based sentiment scoring with polarity and subjectivity
   - **VADER**: Financial text-optimized sentiment analyzer with compound scores
   - Automatic model selection (prefers FinBERT → VADER → TextBlob)

2. **Forward Guidance Extraction**: Automatic extraction of forward-looking statements
   - Keyword-based detection (guidance, outlook, forecast, expect, anticipate, etc.)
   - Sentence-level extraction
   - Count and presence metadata

3. **Risk Factor Analysis**: Automatic identification of risk factors
   - Keyword-based detection (risk, uncertainty, volatility, challenge, concern, etc.)
   - Sentence-level extraction
   - Count and presence metadata

4. **Metadata Storage**: Sentiment scores stored as document metadata
   - Overall sentiment (positive/negative/neutral)
   - Overall sentiment score (-1.0 to 1.0)
   - Model-specific scores (FinBERT, VADER, TextBlob)
   - Forward guidance count and presence flags
   - Risk factors count and presence flags

**Example Configuration**:
```bash
# Enable all sentiment analysis features (recommended)
SENTIMENT_ENABLED=true
SENTIMENT_USE_FINBERT=true
SENTIMENT_USE_TEXTBLOB=true
SENTIMENT_USE_VADER=true
SENTIMENT_EXTRACT_GUIDANCE=true
SENTIMENT_EXTRACT_RISKS=true

# Use only FinBERT for faster processing
SENTIMENT_USE_FINBERT=true
SENTIMENT_USE_TEXTBLOB=false
SENTIMENT_USE_VADER=false

# Disable extraction features for faster processing
SENTIMENT_EXTRACT_GUIDANCE=false
SENTIMENT_EXTRACT_RISKS=false
```

**Performance Considerations**:
- FinBERT: Requires model download on first use (~400MB), slower but most accurate for financial text
- TextBlob: Fast, lightweight, good for general sentiment
- VADER: Fast, optimized for financial text, good balance of speed and accuracy
- Forward guidance extraction: Minimal overhead, keyword-based matching
- Risk factor extraction: Minimal overhead, keyword-based matching

**Model Requirements**:
- FinBERT requires `transformers` and `torch` libraries
- TextBlob requires `textblob` library
- VADER requires `vaderSentiment` library
- All dependencies are included in `requirements.txt`

**Metadata Fields Added to Documents**:
- `sentiment`: Overall sentiment label (positive/negative/neutral)
- `sentiment_score`: Overall sentiment score (-1.0 to 1.0)
- `sentiment_model`: Model used for overall sentiment (finbert/vader/textblob)
- `sentiment_finbert`: FinBERT-specific sentiment label
- `sentiment_finbert_score`: FinBERT-specific score
- `sentiment_finbert_confidence`: FinBERT confidence score
- `sentiment_vader`: VADER-specific sentiment label
- `sentiment_vader_score`: VADER compound score
- `sentiment_textblob`: TextBlob-specific sentiment label
- `sentiment_textblob_score`: TextBlob polarity score
- `forward_guidance_count`: Number of forward guidance statements found
- `has_forward_guidance`: Boolean indicating presence of forward guidance
- `risk_factors_count`: Number of risk factors identified
- `has_risk_factors`: Boolean indicating presence of risk factors

For complete sentiment analysis integration documentation, see: **[Sentiment Analysis Integration Guide](../integrations/sentiment_analysis.md)**.

**Central Bank Data Features**:

1. **FOMC Communications**: Access to Federal Reserve monetary policy communications
   - FOMC statements after meetings
   - Meeting minutes (released 3 weeks after meetings)
   - Press conference transcripts with the Chair

2. **Forward Guidance Extraction**: Automatic extraction of forward guidance statements
   - Keyword-based detection
   - Automatic counting and metadata tagging
   - Included in RAG-formatted text

3. **Metadata Tagging**: Rich metadata for all communications
   - Bank name (Federal Reserve)
   - Communication type (statement, minutes, press conference)
   - Date, URL, title
   - Forward guidance indicators

4. **Rate Limiting**: Configurable rate limiting for web scraping
   - Default: 2.0 seconds between requests
   - Prevents overloading Federal Reserve website
   - Configurable via `CENTRAL_BANK_RATE_LIMIT_SECONDS`

5. **Data Formatting**: Automatic conversion to text format
   - All communications formatted for RAG ingestion
   - Forward guidance statements highlighted
   - Rich metadata tagging
   - Optimized for RAG queries and vector search

6. **Error Handling**: Robust error handling for web scraping failures
   - Graceful handling of network errors
   - Continues processing other communications if one fails
   - Comprehensive logging for debugging

**Example Configuration**:
```bash
# Enable central bank integration (default)
CENTRAL_BANK_ENABLED=true

# Adjust rate limiting (default: 2.0 seconds)
CENTRAL_BANK_RATE_LIMIT_SECONDS=2.0

# For more conservative rate limiting
CENTRAL_BANK_RATE_LIMIT_SECONDS=3.0  # Slower but more respectful

# Enable web scraping (default: true)
CENTRAL_BANK_USE_WEB_SCRAPING=true
```

**Usage**:
```bash
# Fetch all communication types via script
python scripts/fetch_central_bank_data.py --types all

# Fetch specific types
python scripts/fetch_central_bank_data.py --types fomc_statement fomc_minutes

# Fetch with date range
python scripts/fetch_central_bank_data.py --types fomc_statement \
    --start-date 2025-01-01 --end-date 2025-01-31

# Fetch with limit
python scripts/fetch_central_bank_data.py --types fomc_statement --limit 5

# Fetch and store in ChromaDB
python scripts/fetch_central_bank_data.py --types all --store

# Programmatic usage
from app.ingestion.pipeline import IngestionPipeline

pipeline = IngestionPipeline()
chunk_ids = pipeline.process_central_bank(
    comm_types=["fomc_statement", "fomc_minutes", "fomc_press_conference"],
    start_date="2025-01-01",
    end_date="2025-01-31",
    limit=10,
    store_embeddings=True
)
```

**Communication Types**:
- `fomc_statement`: FOMC monetary policy statements after meetings
- `fomc_minutes`: Detailed minutes from FOMC meetings (released 3 weeks after meetings)
- `fomc_press_conference`: Transcripts from FOMC press conferences with the Chair

**Backward Compatibility**: Central bank integration is optional and can be disabled by setting `CENTRAL_BANK_ENABLED=false`. The system continues to work normally without central bank integration.

**API Key**: No API key required. Data is fetched via web scraping from the Federal Reserve website. Rate limiting is important to respect website resources.

**Note**: The Federal Reserve website structure may change over time. If web scraping fails, check the website structure and update the fetcher code if necessary.

For complete central bank integration documentation, see: **[Central Bank Integration Guide](../integrations/central_bank_integration.md)**.

### Conversation History Management (TASK-025)

The system includes conversation history management features that allow users to clear and export their conversation history.

**Features:**

1. **Clear Conversation**: Users can clear their conversation history with a confirmation dialog to prevent accidental loss.
   - Button located in the main UI
   - Confirmation dialog prevents accidental clearing
   - Only clears conversation messages, preserves other session state (RAG system, tickers, etc.)

2. **Export Conversation**: Users can export their conversation history in multiple formats.
   - **JSON Format**: Structured data with complete metadata, sources, and conversation information
   - **Markdown Format**: Readable format with proper formatting and citations
   - **TXT Format**: Plain text format for easy reading
   - Export includes message content, sources, metadata (model, timestamps, conversation ID)
   - Filenames include timestamp and conversation ID for easy organization
   - Download via Streamlit download button

**Usage:**
- Clear conversation: Click "Clear Conversation" button, confirm in dialog
- Export conversation: Select format (JSON/Markdown/TXT), click "Export", then "Download Export"
- Export files are automatically named with timestamp and conversation ID

**Export File Formats:**

**JSON Format:**
```json
{
  "conversation_id": "uuid",
  "created_at": "2025-01-27T12:00:00",
  "messages": [
    {
      "role": "user",
      "content": "What is revenue?",
      "timestamp": "..."
    },
    {
      "role": "assistant",
      "content": "Revenue is...",
      "sources": [...]
    }
  ],
  "metadata": {
    "model": "ollama/llama3.2",
    "total_messages": 2,
    "user_messages": 1,
    "assistant_messages": 1
  }
}
```

**Markdown Format:**
```markdown
# Conversation Export
**Date:** 2025-01-27 12:00:00
**Model:** ollama/llama3.2

## Messages

### User
What is revenue?

### Assistant
Revenue is...

**Sources:** document1.pdf, document2.txt
```

**TXT Format:**
```
Conversation Export
==================================================
Date: 2025-01-27 12:00:00
Model: ollama/llama3.2
==================================================

[1] USER
--------------------------------------------------
What is revenue?

[2] ASSISTANT
--------------------------------------------------
Revenue is...

Source: document1.pdf
```

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
- `CONVERSATION_MAX_TOKENS` must be between 100 and 10000
- `CONVERSATION_MAX_HISTORY` must be between 1 and 50
- `YFINANCE_RATE_LIMIT_SECONDS` must be between 0.1 and 60.0
- `TRANSCRIPT_RATE_LIMIT_SECONDS` must be between 0.1 and 60.0
- `NEWS_RSS_RATE_LIMIT_SECONDS` must be between 0.1 and 60.0
- `NEWS_SCRAPING_RATE_LIMIT_SECONDS` must be between 0.1 and 60.0

### Custom Validation

Custom validators enforce business rules:
- **Ollama URL**: Must start with `http://` or `https://`
- **Log Level**: Must be one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Business Logic**:
  - Warns if OpenAI embeddings are selected but no API key is provided
  - Validates that Ollama is enabled when LLM provider is set to 'ollama'
  - FinBERT embeddings require `sentence-transformers` library (included in dependencies)

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
EMBEDDING_PROVIDER=openai  # Options: openai, ollama, finbert
# FINBERT_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2  # Only used if EMBEDDING_PROVIDER=finbert

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
LOG_FILE_MAX_BYTES=10485760
LOG_FILE_BACKUP_COUNT=5

# Application Configuration
MAX_DOCUMENT_SIZE_MB=10
DEFAULT_TOP_K=5

# Conversation Memory Configuration (TASK-024)
CONVERSATION_ENABLED=true
CONVERSATION_MAX_TOKENS=2000
CONVERSATION_MAX_HISTORY=10

# RAG Optimization Configuration (TASK-028)
RAG_USE_HYBRID_SEARCH=true
RAG_USE_RERANKING=true
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=150
RAG_TOP_K_INITIAL=20
RAG_TOP_K_FINAL=5
RAG_QUERY_EXPANSION=true
RAG_FEW_SHOT_EXAMPLES=true
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
