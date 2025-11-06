# TASK-045: Streamlit Frontend API Integration

## Task Information

| Field | Value |
|-------|-------|
| **Task ID** | TASK-045 |
| **Task Name** | Streamlit Frontend API Integration |
| **Priority** | Medium |
| **Status** | Waiting |
| **Impact** | Medium |
| **Created** | 2025-11-06 |
| **Related PRD** | Phase 2 - Frontend/Backend Separation |
| **Dependencies** | TASK-029 (FastAPI Backend) ✅, TASK-008 (Streamlit UI) ✅ |
| **Estimated Effort** | 6-8 hours |
| **Type** | Integration |

---

## Objective

Migrate the Streamlit frontend to use FastAPI REST endpoints instead of direct RAG system calls. This creates proper separation between frontend and backend, enables multiple frontend clients, improves testability, and provides consistent error handling across the application.

---

## Background

**Current State:**
- Streamlit frontend (`app/ui/app.py`) calls RAG system directly via `app/rag/chain.py`
- No API layer between frontend and backend
- Tight coupling between UI and business logic
- Difficult to test frontend independently
- Cannot easily swap frontends or scale independently
- FastAPI backend exists but is not used by Streamlit

**Required State:**
- Streamlit frontend uses HTTP client to call FastAPI endpoints
- All queries go through `/api/v1/query` endpoint
- Document management uses `/api/v1/documents` endpoints
- Proper error handling from API responses
- Frontend can work independently of backend implementation
- Easy to test with mocked API calls
- Support for multiple frontend clients

---

## Technical Requirements

### Functional Requirements

1. **Query Integration**
   - Replace direct `RAGQuerySystem.query()` calls with HTTP POST to `/api/v1/query`
   - Handle API responses and error codes (400, 401, 404, 500)
   - Parse `QueryResponse` from API JSON
   - Display API errors to users appropriately

2. **Document Management Integration**
   - Replace direct `DocumentManager` calls with HTTP requests
   - Use `GET /api/v1/documents` for listing documents
   - Use `GET /api/v1/documents/{doc_id}` for document details
   - Use `DELETE /api/v1/documents/{doc_id}` for deletion
   - Handle API responses and errors

3. **Error Handling**
   - Handle network errors (connection failures, timeouts)
   - Handle API error responses (4xx, 5xx status codes)
   - Display user-friendly error messages
   - Fallback behavior when API is unavailable

4. **Configuration**
   - API base URL configuration (default: `http://localhost:8000`)
   - API key configuration (if authentication enabled)
   - Environment variable support for API configuration
   - Graceful degradation if API is not available

5. **Backward Compatibility**
   - Maintain existing UI functionality
   - No breaking changes to user experience
   - Same features and capabilities
   - Optional: Add configuration to switch between direct calls and API

### Technical Specifications

**Files to Modify:**
- `app/ui/app.py` - Replace direct RAG calls with API calls
- `app/ui/document_management.py` - Replace direct DocumentManager calls with API calls
- `app/utils/config.py` - Add API client configuration options

**Files to Create:**
- `app/ui/api_client.py` - HTTP client wrapper for FastAPI endpoints
  - `APIClient` class with methods for all endpoints
  - Error handling and retry logic
  - Request/response serialization
  - Connection pooling and timeout management

**Dependencies:**
- `httpx` or `requests` for HTTP client (httpx recommended for async support)
- Existing FastAPI backend (TASK-029)

---

## Acceptance Criteria

### Must Have

- [ ] Streamlit frontend uses API endpoints for all operations
- [ ] Query functionality works through `/api/v1/query` endpoint
- [ ] Document listing works through `/api/v1/documents` endpoint
- [ ] Document deletion works through `/api/v1/documents/{doc_id}` endpoint
- [ ] Error handling for API failures implemented
- [ ] API base URL configurable via environment variables
- [ ] API key authentication supported (if enabled)
- [ ] All existing UI functionality preserved
- [ ] No regression in user experience
- [ ] Unit tests for API client wrapper
- [ ] Integration tests for frontend-API interaction

### Should Have

- [ ] Connection retry logic for transient failures
- [ ] Request timeout configuration
- [ ] API health check before operations
- [ ] Graceful degradation when API unavailable
- [ ] Loading indicators during API calls
- [ ] Request/response logging for debugging

### Nice to Have

- [ ] Async HTTP client for better performance
- [ ] Request caching for repeated queries
- [ ] API response caching
- [ ] Configuration option to switch between direct calls and API
- [ ] API connection status indicator in UI

---

## Implementation Plan

### Phase 1: API Client Wrapper
1. Create `app/ui/api_client.py` with `APIClient` class
2. Implement methods for all required endpoints:
   - `query(question, top_k, conversation_history)`
   - `list_documents()`
   - `get_document(doc_id)`
   - `delete_document(doc_id)`
   - `health_check()`
3. Add error handling and retry logic
4. Add request/response serialization
5. Write unit tests for API client

### Phase 2: Configuration
1. Add API configuration to `app/utils/config.py`:
   - `api_base_url` (default: `http://localhost:8000`)
   - `api_key` (optional)
   - `api_timeout` (default: 30 seconds)
   - `api_enabled` (default: True)
2. Add environment variable support
3. Update configuration documentation

### Phase 3: Streamlit App Migration
1. Update `app/ui/app.py`:
   - Replace `RAGQuerySystem` instantiation with `APIClient`
   - Replace `rag_system.query()` calls with `api_client.query()`
   - Update error handling for API responses
   - Add loading indicators for API calls
2. Update `app/ui/document_management.py`:
   - Replace `DocumentManager` calls with `APIClient` methods
   - Update error handling
3. Test all UI functionality

### Phase 4: Error Handling and UX
1. Implement comprehensive error handling:
   - Network errors (connection failures, timeouts)
   - API errors (4xx, 5xx status codes)
   - Parse error messages from API responses
2. Display user-friendly error messages
3. Add API health check indicator
4. Implement graceful degradation

### Phase 5: Testing and Documentation
1. Write integration tests for frontend-API interaction
2. Test error scenarios (API down, network failures)
3. Test with API authentication enabled/disabled
4. Update documentation for API integration
5. Update deployment documentation

---

## Technical Considerations

### API Client Design

**Option 1: Synchronous Client (requests)**
- Simpler implementation
- Works well with Streamlit (synchronous by nature)
- Easier to debug
- Recommended for initial implementation

**Option 2: Asynchronous Client (httpx)**
- Better performance for concurrent requests
- More complex implementation
- Requires async/await in Streamlit (possible but more complex)

**Recommendation:** Start with synchronous client (requests or httpx sync), can upgrade to async later if needed.

### Error Handling Strategy

1. **Network Errors:**
   - Connection failures → Show "API unavailable" message
   - Timeouts → Show timeout error, suggest retry
   - DNS errors → Show configuration error

2. **API Errors:**
   - 400 Bad Request → Show validation error message
   - 401 Unauthorized → Show authentication error
   - 404 Not Found → Show "resource not found" message
   - 500 Internal Server Error → Show generic error, log details

3. **Fallback Behavior:**
   - Option 1: Show error and disable functionality
   - Option 2: Fall back to direct calls (if configured)
   - Option 3: Cache last successful response

### Configuration Management

```python
# app/utils/config.py additions
api_client_base_url: str = Field(
    default="http://localhost:8000",
    alias="API_CLIENT_BASE_URL",
    description="Base URL for FastAPI backend"
)
api_client_key: str = Field(
    default="",
    alias="API_CLIENT_KEY",
    description="API key for authentication (if required)"
)
api_client_timeout: int = Field(
    default=30,
    alias="API_CLIENT_TIMEOUT",
    description="Request timeout in seconds"
)
api_client_enabled: bool = Field(
    default=True,
    alias="API_CLIENT_ENABLED",
    description="Enable API client (False = use direct calls)"
)
```

---

## Risk Assessment

### Risks

1. **Risk:** API latency may affect user experience
   - **Impact:** Medium
   - **Probability:** Medium
   - **Mitigation:**
     - Add loading indicators
     - Implement request timeouts
     - Consider async client for better performance
     - Add response caching for repeated queries

2. **Risk:** API unavailability breaks frontend
   - **Impact:** High
   - **Probability:** Low
   - **Mitigation:**
     - Implement graceful error handling
     - Add API health checks
     - Consider fallback to direct calls (optional)
     - Show clear error messages

3. **Risk:** Breaking changes to existing functionality
   - **Impact:** High
   - **Probability:** Low
   - **Mitigation:**
     - Comprehensive testing
     - Maintain backward compatibility
     - Gradual migration with feature flags

4. **Risk:** Authentication complexity
   - **Impact:** Low
   - **Probability:** Low
   - **Mitigation:**
     - API key is optional
     - Simple header-based authentication
     - Clear configuration documentation

---

## Testing Strategy

### Unit Tests

1. **API Client Tests:**
   - Test all API client methods
   - Test error handling (network errors, API errors)
   - Test request/response serialization
   - Test retry logic
   - Mock HTTP responses

2. **Configuration Tests:**
   - Test API configuration loading
   - Test environment variable parsing
   - Test default values

### Integration Tests

1. **Frontend-API Integration:**
   - Test query flow through API
   - Test document management through API
   - Test error scenarios
   - Test with API server running
   - Test with API server down

2. **End-to-End Tests:**
   - Test complete user workflows
   - Test error recovery
   - Test with authentication enabled/disabled

### Manual Testing

1. Test all UI functionality
2. Test error scenarios
3. Test with API server on different ports
4. Test with API authentication
5. Test performance and latency

---

## Dependencies

- **TASK-029** (FastAPI Backend) - ✅ Complete
  - Required for API endpoints
  - Must be running for frontend to work

- **TASK-008** (Streamlit UI) - ✅ Complete
  - Required for frontend to modify
  - Existing UI functionality to preserve

---

## Success Metrics

- ✅ All UI functionality works through API
- ✅ No regression in user experience
- ✅ Error handling works correctly
- ✅ API client is testable and maintainable
- ✅ Configuration is flexible and documented
- ✅ Unit and integration tests passing
- ✅ Performance is acceptable (<500ms additional latency)

---

## Notes

- This task creates proper separation of concerns
- Enables multiple frontend clients (web, mobile, CLI)
- Improves testability and maintainability
- Aligns with microservices architecture principles
- Can be implemented incrementally (feature by feature)
- Consider keeping direct calls as fallback option initially

---

## Related Tasks

- **TASK-029**: FastAPI Backend Implementation - Provides API endpoints
- **TASK-008**: Streamlit Frontend - Frontend to modify
- **TASK-043**: Export and Sharing Functionality - May benefit from API integration

---

**End of Task**
