# FastAPI Backend API Documentation (TASK-029)

## Overview

The Financial Research Assistant includes a production-ready RESTful API built with FastAPI. The API provides programmatic access to all core functionality including RAG queries, document ingestion, and document management.

**Frontend Integration (TASK-045)**: The Streamlit frontend now uses the FastAPI backend via an API client wrapper, providing proper separation between frontend and backend. The frontend can fall back to direct RAG calls if the API is unavailable, maintaining backward compatibility.

## Base URL

Default: `http://localhost:8000`

The API base URL can be configured via environment variables:
- `API_HOST`: Server host (default: `0.0.0.0`)
- `API_PORT`: Server port (default: `8000`)

## API Versioning

All endpoints are versioned under `/api/v1/`. Future API versions will use `/api/v2/`, etc.

## Authentication

API key authentication is optional and configurable:

- **Enabled**: If `API_KEY` is set in `.env` file, all endpoints require authentication
- **Disabled**: If `API_KEY` is empty or not set, authentication is optional

### Using API Key Authentication

When enabled, include the API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/query
```

### Configuration

Set in `.env` file:
```bash
API_KEY=your-secret-api-key-here
```

**Security Note**: Use a strong, randomly generated API key in production. Never commit API keys to version control.

## Rate Limiting

The API includes rate limiting to prevent abuse:

- **Default Limit**: 60 requests per minute per API key/IP address
- **Configurable**: Set `API_RATE_LIMIT_PER_MINUTE` in `.env`
- **Headers**: Rate limit information included in responses:
  - `X-RateLimit-Limit`: Maximum requests per minute
  - `X-RateLimit-Remaining`: Remaining requests in current window

### Rate Limit Response

When rate limit is exceeded:
```json
{
  "detail": "Rate limit exceeded: 60 requests per minute",
  "retry_after": 60
}
```

Status Code: `429 Too Many Requests`

## CORS Configuration

CORS (Cross-Origin Resource Sharing) is configured to allow cross-origin requests:

- **Default**: Allows all origins (`*`)
- **Configurable**: Set `API_CORS_ORIGINS` in `.env` (comma-separated list)
- **Example**: `API_CORS_ORIGINS=http://localhost:3000,https://example.com`

## Endpoints

### Root Endpoint

**GET** `/`

Returns API information and available endpoints.

**Response**:
```json
{
  "name": "Financial Research Assistant API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/api/v1/health",
  "endpoints": {
    "query": "/api/v1/query",
    "ingest": "/api/v1/ingest",
    "documents": "/api/v1/documents",
    "health": "/api/v1/health",
    "metrics": "/api/v1/health/metrics"
  }
}
```

---

### Query Endpoint

**POST** `/api/v1/query`

Process a natural language query using the RAG system and return an answer with sources.

**Request Body**:
```json
{
  "question": "What was Apple's revenue in 2023?",
  "top_k": 5,
  "conversation_history": [
    {
      "role": "user",
      "content": "Tell me about Apple"
    },
    {
      "role": "assistant",
      "content": "Apple Inc. is a technology company..."
    }
  ],
  "filters": {
    "ticker": "AAPL",
    "form_type": "10-K",
    "date_from": "2023-01-01",
    "date_to": "2023-12-31",
    "document_type": "edgar_filing"
  },
  "enable_query_parsing": true
}
```

**Parameters**:
- `question` (string, required): Natural language question
- `top_k` (integer, optional): Number of top chunks to retrieve (1-20, default: 5)
- `conversation_history` (array, optional): Previous conversation messages for context
- `filters` (object, optional): Advanced query filters
  - `date_from` (string, optional): Start date filter (ISO format: YYYY-MM-DD)
  - `date_to` (string, optional): End date filter (ISO format: YYYY-MM-DD)
  - `document_type` (string, optional): Document type filter (e.g., "edgar_filing", "news", "transcript")
  - `ticker` (string, optional): Ticker symbol filter (e.g., "AAPL", "MSFT")
  - `form_type` (string, optional): Form type filter (e.g., "10-K", "10-Q", "8-K")
  - `source` (string, optional): Source identifier filter
  - `metadata` (object, optional): Custom metadata filters
- `enable_query_parsing` (boolean, optional): Enable automatic query parsing for filters and Boolean operators (default: true)

**Note**:
- Sentiment filtering is available when using the RAG system programmatically. See [Sentiment Analysis Documentation](../integrations/sentiment_analysis.md#rag-system-integration) for details.
- For advanced query features including Boolean operators and filter syntax, see [Advanced Query Features Documentation](../integrations/advanced_query_features.md).

**Response** (200 OK):
```json
{
  "answer": "Apple's revenue in 2023 was $383.3 billion...",
  "sources": [
    {
      "source": "data/documents/AAPL_10-K_2023.txt",
      "filename": "AAPL_10-K_2023.txt",
      "ticker": "AAPL",
      "form_type": "10-K",
      "chunk_index": 0,
      "date": "2023-09-30"
    }
  ],
  "chunks_used": 5,
  "error": null,
  "parsed_query": {
    "query_text": "What was Apple's revenue in 2023?",
    "boolean_operators": [],
    "filters": {
      "ticker": "AAPL",
      "form_type": "10-K"
    },
    "query_terms": ["apple", "revenue", "2023"]
  }
}
```

**Response Fields**:
- `answer` (string): Generated answer from the RAG system
- `sources` (array): List of source documents used with metadata
- `chunks_used` (integer): Number of document chunks used
- `error` (string, nullable): Error message if query failed
- `parsed_query` (object, optional): Parsed query information (if query parsing enabled)
  - `query_text` (string): Cleaned query text without filters
  - `boolean_operators` (array): List of Boolean operators detected (AND, OR, NOT)
  - `filters` (object): Extracted filter specifications
  - `query_terms` (array): List of extracted query terms

**Error Responses**:
- `400 Bad Request`: Invalid question or query processing failed
- `401 Unauthorized`: Missing or invalid API key (if authentication enabled)
- `422 Unprocessable Entity`: Validation error (missing required fields)
- `500 Internal Server Error`: Server error during query processing

**Examples**:

Basic query:
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "question": "What is revenue?",
    "top_k": 5
  }'
```

Query with filters:
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "question": "What was Apple'\''s revenue in 2023?",
    "filters": {
      "ticker": "AAPL",
      "form_type": "10-K",
      "date_from": "2023-01-01",
      "date_to": "2023-12-31"
    },
    "enable_query_parsing": true
  }'
```

Query with natural language filters (automatic extraction):
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "question": "ticker: AAPL form: 10-K revenue from 2023-01-01",
    "enable_query_parsing": true
  }'
```

---

### Document Ingestion Endpoint

**POST** `/api/v1/ingest`

Ingest a document into the vector database. Supports both file upload and file path.

**Request Options**:

**Option 1: File Upload** (multipart/form-data):
```
Content-Type: multipart/form-data

file: <file content>
store_embeddings: true
```

**Option 2: File Path** (application/json):
```json
{
  "file_path": "data/documents/document.txt",
  "store_embeddings": true
}
```

**Parameters**:
- `file` (file, optional): Uploaded file (multipart/form-data)
- `file_path` (string, optional): Path to document file (relative to project root)
- `store_embeddings` (boolean, optional): Whether to store embeddings (default: true)

**Note**: Either `file` or `file_path` must be provided.

**Response** (201 Created):
```json
{
  "success": true,
  "chunk_ids": ["chunk_1", "chunk_2", "chunk_3"],
  "chunks_created": 3,
  "message": "Document ingested successfully: 3 chunks created",
  "error": null
}
```

**Error Responses**:
- `400 Bad Request`: Missing file/file_path, file too large, or ingestion failed
- `401 Unauthorized`: Missing or invalid API key (if authentication enabled)
- `404 Not Found`: File not found (if using file_path)
- `500 Internal Server Error`: Server error during ingestion

**Example - File Upload**:
```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.txt" \
  -F "store_embeddings=true"
```

**Example - File Path**:
```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "file_path": "data/documents/document.txt",
    "store_embeddings": true
  }'
```

---

### Document Management Endpoints

#### List Documents

**GET** `/api/v1/documents`

Retrieve all documents in the vector database.

**Response** (200 OK):
```json
{
  "documents": [
    {
      "id": "chunk_1",
      "metadata": {
        "source": "data/documents/AAPL_10-K_2023.txt",
        "filename": "AAPL_10-K_2023.txt",
        "ticker": "AAPL",
        "form_type": "10-K",
        "chunk_index": 0,
        "date": "2023-09-30"
      },
      "content": "Apple Inc. is a technology company..."
    }
  ],
  "total": 1,
  "message": "Retrieved 1 documents successfully"
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents" \
  -H "X-API-Key: your-api-key"
```

#### Get Document by ID

**GET** `/api/v1/documents/{doc_id}`

Retrieve a specific document by its ID.

**Path Parameters**:
- `doc_id` (string, required): Document chunk ID

**Response** (200 OK):
```json
{
  "document": {
    "id": "chunk_1",
    "metadata": {
      "source": "data/documents/AAPL_10-K_2023.txt",
      "filename": "AAPL_10-K_2023.txt"
    },
    "content": "Apple Inc. is a technology company..."
  },
  "message": "Document retrieved successfully",
  "error": null
}
```

**Error Responses**:
- `404 Not Found`: Document not found
- `401 Unauthorized`: Missing or invalid API key (if authentication enabled)

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents/chunk_1" \
  -H "X-API-Key: your-api-key"
```

#### Delete Document

**DELETE** `/api/v1/documents/{doc_id}`

Delete a document from the vector database.

**Path Parameters**:
- `doc_id` (string, required): Document chunk ID

**Response** (200 OK):
```json
{
  "message": "Document chunk_1 deleted successfully",
  "doc_id": "chunk_1"
}
```

**Error Responses**:
- `404 Not Found`: Document not found
- `401 Unauthorized`: Missing or invalid API key (if authentication enabled)
- `500 Internal Server Error`: Server error during deletion

**Example**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/chunk_1" \
  -H "X-API-Key: your-api-key"
```

#### Re-index Document

**POST** `/api/v1/documents/reindex`

Re-index a document by uploading an updated version. This deletes old chunks and creates new ones with version tracking.

**Request Body** (multipart/form-data):
- `file` (file, required): Updated document file to re-index
- `preserve_metadata` (boolean, optional, default: true): Whether to preserve original metadata (ticker, form_type, etc.)
- `increment_version` (boolean, optional, default: true): Whether to increment version number

**Response** (200 OK):
```json
{
  "message": "Document re-indexed successfully",
  "old_chunks_deleted": 5,
  "new_chunks_created": 5,
  "version": 2,
  "new_chunk_ids": ["chunk_id_1", "chunk_id_2", ...]
}
```

**Error Responses**:
- `400 Bad Request`: Missing file or invalid request
- `401 Unauthorized`: Missing or invalid API key (if authentication enabled)
- `500 Internal Server Error`: Server error during re-indexing

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/reindex" \
  -H "X-API-Key: your-api-key" \
  -F "file=@updated_document.txt" \
  -F "preserve_metadata=true" \
  -F "increment_version=true"
```

#### Get Version History

**GET** `/api/v1/documents/{source}/versions`

Get version history for a document source.

**Path Parameters**:
- `source` (string, required): Source filename

**Response** (200 OK):
```json
{
  "source": "document.txt",
  "versions": [
    {
      "version": 1,
      "version_date": "2025-01-27T10:00:00",
      "chunk_count": 5,
      "chunk_ids": ["id1", "id2", ...],
      "metadata": {...}
    },
    {
      "version": 2,
      "version_date": "2025-01-27T11:00:00",
      "chunk_count": 5,
      "chunk_ids": ["id3", "id4", ...],
      "metadata": {...}
    }
  ],
  "total_versions": 2
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid API key (if authentication enabled)
- `500 Internal Server Error`: Server error during retrieval

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents/document.txt/versions" \
  -H "X-API-Key: your-api-key"
```

#### Compare Versions

**GET** `/api/v1/documents/{source}/versions/compare`

Compare two versions of a document.

**Path Parameters**:
- `source` (string, required): Source filename

**Query Parameters**:
- `version1` (integer, required): First version number to compare
- `version2` (integer, required): Second version number to compare

**Response** (200 OK):
```json
{
  "source": "document.txt",
  "version1": 1,
  "version2": 2,
  "comparison": {
    "version1_info": {
      "version": 1,
      "version_date": "2025-01-27T10:00:00",
      "chunk_count": 5,
      "metadata": {...}
    },
    "version2_info": {
      "version": 2,
      "version_date": "2025-01-27T11:00:00",
      "chunk_count": 5,
      "metadata": {...}
    },
    "differences": [
      {
        "field": "chunk_count",
        "version1": 5,
        "version2": 6
      },
      {
        "field": "ticker",
        "version1": "AAPL",
        "version2": "AAPL"
      }
    ]
  }
}
```

**Error Responses**:
- `400 Bad Request`: Missing version parameters
- `401 Unauthorized`: Missing or invalid API key (if authentication enabled)
- `404 Not Found`: Version not found
- `500 Internal Server Error`: Server error during comparison

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents/document.txt/versions/compare?version1=1&version2=2" \
  -H "X-API-Key: your-api-key"
```

---

### Health Check Endpoints

#### Comprehensive Health Check

**GET** `/api/v1/health`

Returns comprehensive health status including all components.

**Response** (200 OK or 503 Service Unavailable):
```json
{
  "status": "healthy",
  "timestamp": 1706380800.0,
  "components": {
    "chromadb": {
      "status": "healthy",
      "document_count": 586,
      "collection": "documents"
    },
    "ollama": {
      "status": "healthy",
      "base_url": "http://localhost:11434",
      "models_available": 1
    },
    "openai": {
      "status": "healthy",
      "api_key_configured": true
    }
  }
}
```

**Status Codes**:
- `200 OK`: All components healthy
- `503 Service Unavailable`: One or more components unhealthy

#### Liveness Probe

**GET** `/api/v1/health/live`

Simple liveness check (is the application running).

**Response** (200 OK):
```json
{
  "status": "alive"
}
```

#### Readiness Probe

**GET** `/api/v1/health/ready`

Readiness check (is the application ready to serve requests).

**Response** (200 OK or 503 Service Unavailable):
```json
{
  "status": "ready"
}
```

or

```json
{
  "status": "not_ready",
  "reason": "ChromaDB not available"
}
```

#### Prometheus Metrics

**GET** `/api/v1/health/metrics`

Returns Prometheus metrics in text format.

**Response** (200 OK):
```
# HELP rag_queries_total Total number of RAG queries processed
# TYPE rag_queries_total counter
rag_queries_total{status="success"} 100.0
rag_queries_total{status="error"} 5.0
...
```

**Example**:
```bash
curl "http://localhost:8000/api/v1/health/metrics"
```

---

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

### Swagger UI

Access at: `http://localhost:8000/docs`

- Interactive API explorer
- Try out endpoints directly in the browser
- View request/response schemas
- Test authentication

### ReDoc

Access at: `http://localhost:8000/redoc`

- Clean, readable API documentation
- Searchable endpoint list
- Schema definitions

### OpenAPI JSON

Access at: `http://localhost:8000/openapi.json`

- Machine-readable API specification
- Can be imported into API clients (Postman, Insomnia, etc.)
- Used for code generation

---

## Error Handling

All endpoints return consistent error responses:

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters or business logic error
- `401 Unauthorized`: Authentication required or invalid API key
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error (invalid request format)
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Validation Errors

When request validation fails (422), the response includes detailed field errors:

```json
{
  "detail": [
    {
      "loc": ["body", "question"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Request/Response Examples

### Python Client Example

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key"  # If configured

headers = {"X-API-Key": API_KEY} if API_KEY else {}

# Query endpoint
response = requests.post(
    f"{BASE_URL}/api/v1/query",
    json={
        "question": "What is revenue?",
        "top_k": 5
    },
    headers=headers
)
data = response.json()
print(f"Answer: {data['answer']}")
print(f"Sources: {len(data['sources'])} documents")

# List documents
response = requests.get(
    f"{BASE_URL}/api/v1/documents",
    headers=headers
)
documents = response.json()["documents"]
print(f"Total documents: {len(documents)}")

# Health check
response = requests.get(f"{BASE_URL}/api/v1/health")
health = response.json()
print(f"Status: {health['status']}")
```

### JavaScript/TypeScript Example

```typescript
const BASE_URL = 'http://localhost:8000';
const API_KEY = 'your-api-key'; // If configured

const headers: HeadersInit = {};
if (API_KEY) {
  headers['X-API-Key'] = API_KEY;
}

// Query endpoint
const queryResponse = await fetch(`${BASE_URL}/api/v1/query`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...headers,
  },
  body: JSON.stringify({
    question: 'What is revenue?',
    top_k: 5,
  }),
});

const queryData = await queryResponse.json();
console.log('Answer:', queryData.answer);
console.log('Sources:', queryData.sources.length);
```

### cURL Examples

**Query**:
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"question": "What is revenue?", "top_k": 5}'
```

**Ingest Document**:
```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.txt" \
  -F "store_embeddings=true"
```

**List Documents**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents" \
  -H "X-API-Key: your-api-key"
```

**Health Check**:
```bash
curl "http://localhost:8000/api/v1/health"
```

---

## Configuration

API configuration is managed via environment variables in `.env` file:

```bash
# API Server Configuration
API_HOST=0.0.0.0              # Server host address
API_PORT=8000                 # Server port (1024-65535)
API_TITLE=Financial Research Assistant API
API_VERSION=1.0.0
API_ENABLED=true              # Enable/disable API server

# Authentication
API_KEY=                      # API key for authentication (empty = disabled)

# Rate Limiting
API_RATE_LIMIT_PER_MINUTE=60  # Requests per minute per API key/IP

# CORS
API_CORS_ORIGINS=*            # Comma-separated list of allowed origins (* = all)
```

For complete configuration documentation, see [Configuration Guide](configuration.md#api-configuration-task-029).

---

## Performance Considerations

### Response Times

- **Query Endpoint**: 3-5 seconds average (depends on LLM and document retrieval)
- **Health Check**: < 1 second
- **Document List**: < 1 second (depends on document count)
- **Document Ingestion**: 5-30 seconds (depends on document size and embedding generation)

### Best Practices

1. **Use Async Clients**: For high-throughput scenarios, use async HTTP clients
2. **Connection Pooling**: Reuse HTTP connections when making multiple requests
3. **Error Handling**: Implement retry logic with exponential backoff
4. **Rate Limiting**: Respect rate limits and implement client-side throttling
5. **Caching**: Cache health check and document list responses when appropriate

---

## Troubleshooting

### API Server Not Starting

1. **Check Port Availability**:
   ```bash
   lsof -i :8000
   ```

2. **Check Configuration**:
   ```bash
   # Verify API_ENABLED is true
   grep API_ENABLED .env
   ```

3. **Check Logs**: Review application logs for startup errors

### Authentication Errors

1. **Verify API Key**: Ensure `API_KEY` is set correctly in `.env`
2. **Check Header**: Ensure `X-API-Key` header is included in requests
3. **Check Format**: API key should match exactly (case-sensitive)

### Rate Limiting Issues

1. **Check Rate Limit**: Review `API_RATE_LIMIT_PER_MINUTE` setting
2. **Monitor Headers**: Check `X-RateLimit-Remaining` header in responses
3. **Implement Backoff**: Add exponential backoff when receiving 429 errors

### Connection Errors

1. **Verify Server Running**: Check if API server is running
2. **Check Firewall**: Ensure port 8000 is not blocked
3. **Check Network**: Verify network connectivity to server

---

## Security Considerations

1. **API Key Security**:
   - Use strong, randomly generated API keys
   - Never commit API keys to version control
   - Rotate API keys regularly
   - Use different keys for different environments

2. **HTTPS in Production**:
   - Always use HTTPS in production deployments
   - Configure reverse proxy (Nginx, Traefik) with SSL/TLS
   - Use Let's Encrypt for free SSL certificates

3. **Rate Limiting**:
   - Configure appropriate rate limits for your use case
   - Monitor for abuse and adjust limits as needed
   - Consider IP-based blocking for persistent abuse

4. **CORS Configuration**:
   - Restrict CORS origins to known domains in production
   - Avoid using `*` for `API_CORS_ORIGINS` in production

5. **Input Validation**:
   - All inputs are validated by Pydantic models
   - File uploads are validated for size and type
   - Malicious inputs are rejected with clear error messages

---

## Testing

The FastAPI backend includes comprehensive test coverage:

### Test Suite

**Location**: `tests/test_api.py`

**Test Coverage**:
- **27 total tests** (24 passing, 3 skipped when API key not configured)
- **API Routes**: 75-92% code coverage
- **API Models**: 100% code coverage
- **API Middleware**: 94% code coverage

### Test Categories

1. **Health Endpoints** (5 tests)
   - Root endpoint
   - Comprehensive health check
   - Liveness probe
   - Readiness probe
   - Prometheus metrics

2. **Query Endpoints** (5 tests)
   - Query with/without authentication
   - Custom top_k parameter
   - Invalid request validation
   - Empty question handling

3. **Ingestion Endpoints** (4 tests)
   - File path ingestion
   - File upload ingestion
   - Missing file error handling
   - File not found error handling

4. **Document Management** (5 tests)
   - List documents
   - Get document by ID
   - Get document not found
   - Delete document
   - Delete document not found

5. **Authentication** (3 tests)
   - Missing API key when required
   - Invalid API key rejection
   - Valid API key acceptance

6. **Rate Limiting** (2 tests)
   - Rate limit headers
   - Rate limit enforcement

7. **Error Handling** (3 tests)
   - 404 not found
   - 422 validation error
   - 500 internal error handling

### Running Tests

```bash
# Run all API tests
pytest tests/test_api.py -v

# Run with coverage
pytest tests/test_api.py --cov=app.api --cov-report=term-missing

# Run specific test category
pytest tests/test_api.py::TestQueryEndpoints -v
```

### Test Results

All tests are passing:
- ✅ 24 tests passing
- ⏭️ 3 tests skipped (authentication tests when API key not configured - expected behavior)
- ❌ 0 tests failing

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review application logs
3. Check the interactive API documentation at `/docs`
4. Verify configuration in `.env` file
5. Review test suite in `tests/test_api.py` for usage examples

---

## Frontend Integration (TASK-045) ✅

### Overview

The Streamlit frontend uses an API client wrapper (`app/ui/api_client.py`) to communicate with the FastAPI backend instead of calling the RAG system directly. This provides:

- **Separation of Concerns**: Frontend and backend are decoupled
- **Multiple Frontend Support**: Enables web, mobile, and CLI clients
- **Improved Testability**: Frontend can be tested with mocked API calls
- **Consistent Error Handling**: Unified error handling across the application
- **Backward Compatibility**: Falls back to direct RAG calls if API is unavailable
- **Production Ready**: Fully implemented with comprehensive error handling and retry logic

### Configuration

The API client is configured via environment variables in `.env`:

```bash
# API Client Configuration
API_CLIENT_BASE_URL=http://localhost:8000  # FastAPI backend URL
API_CLIENT_KEY=                            # Optional: API key (uses API_KEY if empty)
API_CLIENT_TIMEOUT=30                      # Request timeout in seconds
API_CLIENT_ENABLED=true                    # Enable API client (false = use direct calls)
```

### Usage in Streamlit

The Streamlit app automatically uses the API client when `API_CLIENT_ENABLED=true`:

1. **Initialization**: The app checks API health on startup
2. **Fallback**: If API is unavailable, falls back to direct RAG calls
3. **Error Handling**: User-friendly error messages for connection failures

### API Client Features

- **Automatic Retry**: Retries transient failures (429, 500, 502, 503, 504) with exponential backoff
- **Connection Pooling**: Efficient HTTP session management with `requests.Session`
- **Timeout Management**: Configurable request timeouts (default: 30 seconds)
- **Error Handling**: Comprehensive error handling with specific exception types:
  - `APIConnectionError`: Network/connection failures
  - `APIError`: API error responses (4xx, 5xx)
  - `APIClientError`: General client errors
- **Health Checks**: Automatic API health verification before operations
- **Request/Response Logging**: Debug logging for troubleshooting
- **Version History Support**: Full support for document versioning operations

### Example: Using API Client Programmatically

```python
from app.ui.api_client import APIClient

# Initialize client
client = APIClient(
    base_url="http://localhost:8000",
    api_key="your-api-key",  # Optional
    timeout=30
)

# Check API health
health = client.health_check()
print(health)  # {"status": "healthy", ...}

# Query documents
result = client.query(
    question="What was Apple's revenue in 2023?",
    top_k=5,
    filters={"ticker": "AAPL", "form_type": "10-K"}
)
print(result["answer"])
print(result["sources"])

# List documents
documents = client.list_documents()
print(f"Found {len(documents)} documents")

# Get document details
doc = client.get_document("doc_id")
print(doc["content"])

# Delete document
success = client.delete_document("doc_id")
```

### Error Handling

The API client provides specific exception types:

```python
from app.ui.api_client import (
    APIClientError,
    APIConnectionError,
    APIError,
)

try:
    result = client.query("Test question")
except APIConnectionError as e:
    # API server is down or unreachable
    print(f"Connection failed: {e}")
except APIError as e:
    # API returned an error response
    print(f"API error ({e.status_code}): {e}")
except APIClientError as e:
    # General client error
    print(f"Client error: {e}")
```

### Backward Compatibility

The frontend maintains backward compatibility:

- **API Client Enabled**: Uses FastAPI backend via HTTP
- **API Client Disabled**: Falls back to direct RAG system calls
- **Automatic Detection**: Detects API availability and switches modes automatically

To disable API client and use direct calls:

```bash
API_CLIENT_ENABLED=false
```

This is useful for:
- Development and testing
- Standalone deployments without API server
- Legacy compatibility
