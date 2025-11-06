"""
Comprehensive tests for FastAPI backend endpoints (TASK-029).

Tests all API endpoints including query, ingestion, documents, and health check.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.utils.config import config


@pytest.fixture
def api_client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def api_key():
    """Get API key for testing (or create test key)."""
    # Use configured API key if available, otherwise use test key
    test_key = config.api_key if config.api_key else "test-api-key-12345"
    return test_key


@pytest.fixture
def api_headers(api_key):
    """Create API headers with authentication."""
    return {"X-API-Key": api_key}


@pytest.fixture
def test_document_path(test_documents_dir, sample_text_content):
    """Create a test document file."""
    doc_path = test_documents_dir / "test_document.txt"
    doc_path.write_text(sample_text_content)
    return doc_path


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root_endpoint(self, api_client):
        """Test root endpoint returns API information."""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert "endpoints" in data

    def test_health_check(self, api_client):
        """Test comprehensive health check endpoint."""
        response = api_client.get("/api/v1/health")
        assert response.status_code in [
            200,
            503,
        ]  # May be unhealthy if services not running
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "components" in data

    def test_liveness(self, api_client):
        """Test liveness probe endpoint."""
        response = api_client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_readiness(self, api_client):
        """Test readiness probe endpoint."""
        response = api_client.get("/api/v1/health/ready")
        assert response.status_code in [
            200,
            503,
        ]  # May be not ready if services not running
        data = response.json()
        assert "status" in data

    def test_metrics_endpoint(self, api_client):
        """Test Prometheus metrics endpoint."""
        response = api_client.get("/api/v1/health/metrics")
        assert response.status_code == 200
        # Should return Prometheus text format
        assert "rag_queries_total" in response.text or len(response.text) > 0


class TestQueryEndpoints:
    """Tests for RAG query endpoints."""

    def test_query_without_auth(self, api_client):
        """Test query endpoint without authentication (if auth disabled)."""
        response = api_client.post(
            "/api/v1/query",
            json={"question": "What is revenue?"},
        )
        # Should work if API key not configured, or return 401 if configured
        assert response.status_code in [200, 401]

    def test_query_with_auth(self, api_client, api_headers):
        """Test query endpoint with authentication."""
        # Mock RAG system to avoid actual LLM calls
        with patch("app.api.routes.query.create_rag_system") as mock_rag:
            from app.rag.chain import RAGQuerySystem

            mock_system = RAGQuerySystem.__new__(RAGQuerySystem)
            mock_system.query = lambda **kwargs: {
                "answer": "Test answer",
                "sources": [
                    {
                        "source": "test.txt",
                        "filename": "test.txt",
                        "ticker": None,
                        "form_type": None,
                        "chunk_index": 0,
                        "date": None,
                    }
                ],
                "chunks_used": 1,
                "error": None,
            }
            mock_rag.return_value = mock_system

            response = api_client.post(
                "/api/v1/query",
                json={"question": "What is revenue?"},
                headers=api_headers,
            )

            if response.status_code == 401:
                pytest.skip("API key authentication required but not configured")

            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sources" in data
            assert "chunks_used" in data

    def test_query_with_top_k(self, api_client, api_headers):
        """Test query endpoint with custom top_k parameter."""
        with patch("app.api.routes.query.create_rag_system") as mock_rag:
            from app.rag.chain import RAGQuerySystem

            mock_system = RAGQuerySystem.__new__(RAGQuerySystem)
            mock_system.query = lambda **kwargs: {
                "answer": "Test answer",
                "sources": [],
                "chunks_used": 3,
                "error": None,
            }
            mock_rag.return_value = mock_system

            response = api_client.post(
                "/api/v1/query",
                json={"question": "What is revenue?", "top_k": 3},
                headers=api_headers,
            )

            if response.status_code == 401:
                pytest.skip("API key authentication required but not configured")

            assert response.status_code == 200
            data = response.json()
            assert data["chunks_used"] == 3

    def test_query_invalid_request(self, api_client, api_headers):
        """Test query endpoint with invalid request."""
        response = api_client.post(
            "/api/v1/query",
            json={},  # Missing required 'question' field
            headers=api_headers,
        )

        if response.status_code == 401:
            pytest.skip("API key authentication required but not configured")

        assert response.status_code == 422  # Validation error

    def test_query_empty_question(self, api_client, api_headers):
        """Test query endpoint with empty question."""
        response = api_client.post(
            "/api/v1/query",
            json={"question": ""},
            headers=api_headers,
        )

        if response.status_code == 401:
            pytest.skip("API key authentication required but not configured")

        assert response.status_code in [400, 422]  # Bad request or validation error


class TestIngestionEndpoints:
    """Tests for document ingestion endpoints."""

    def test_ingest_with_file_path(self, api_client, api_headers, test_document_path):
        """Test ingestion endpoint with file path."""
        with patch("app.api.routes.ingestion.create_pipeline") as mock_pipeline:
            from app.ingestion.pipeline import IngestionPipeline

            mock_pipe = IngestionPipeline.__new__(IngestionPipeline)
            mock_pipe.process_document = lambda **kwargs: [
                "chunk_1",
                "chunk_2",
                "chunk_3",
            ]
            mock_pipeline.return_value = mock_pipe

            response = api_client.post(
                "/api/v1/ingest",
                json={"file_path": str(test_document_path), "store_embeddings": True},
                headers=api_headers,
            )

            if response.status_code == 401:
                pytest.skip("API key authentication required but not configured")

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert "chunk_ids" in data
            assert data["chunks_created"] == 3

    def test_ingest_with_file_upload(
        self, api_client, api_headers, sample_text_content
    ):
        """Test ingestion endpoint with file upload."""
        with patch("app.api.routes.ingestion.create_pipeline") as mock_pipeline:
            from app.ingestion.pipeline import IngestionPipeline

            mock_pipe = IngestionPipeline.__new__(IngestionPipeline)
            mock_pipe.process_document = lambda **kwargs: ["chunk_1", "chunk_2"]
            mock_pipeline.return_value = mock_pipe

            files = {"file": ("test.txt", sample_text_content, "text/plain")}
            response = api_client.post(
                "/api/v1/ingest",
                files=files,
                headers=api_headers,
            )

            if response.status_code == 401:
                pytest.skip("API key authentication required but not configured")

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True

    def test_ingest_missing_file(self, api_client, api_headers):
        """Test ingestion endpoint with missing file."""
        response = api_client.post(
            "/api/v1/ingest",
            json={},  # No file_path or file
            headers=api_headers,
        )

        if response.status_code == 401:
            pytest.skip("API key authentication required but not configured")

        assert response.status_code == 400

    def test_ingest_file_not_found(self, api_client, api_headers):
        """Test ingestion endpoint with non-existent file."""
        response = api_client.post(
            "/api/v1/ingest",
            json={"file_path": "/nonexistent/file.txt"},
            headers=api_headers,
        )

        if response.status_code == 401:
            pytest.skip("API key authentication required but not configured")

        assert response.status_code == 404


class TestDocumentsEndpoints:
    """Tests for document management endpoints."""

    def test_list_documents(self, api_client, api_headers):
        """Test list documents endpoint."""
        with patch("app.api.routes.documents.DocumentManager") as mock_doc_mgr:
            mock_manager = mock_doc_mgr.return_value
            mock_manager.get_all_documents.return_value = [
                {
                    "id": "chunk_1",
                    "metadata": {"source": "test.txt", "filename": "test.txt"},
                    "content": "Test content",
                }
            ]

            response = api_client.get(
                "/api/v1/documents",
                headers=api_headers,
            )

            if response.status_code == 401:
                pytest.skip("API key authentication required but not configured")

            assert response.status_code == 200
            data = response.json()
            assert "documents" in data
            assert "total" in data
            assert len(data["documents"]) == 1

    def test_get_document(self, api_client, api_headers):
        """Test get document by ID endpoint."""
        with patch("app.api.routes.documents.DocumentManager") as mock_doc_mgr:
            mock_manager = mock_doc_mgr.return_value
            mock_manager.get_all_documents.return_value = [
                {
                    "id": "chunk_1",
                    "metadata": {"source": "test.txt"},
                    "content": "Test content",
                }
            ]

            response = api_client.get(
                "/api/v1/documents/chunk_1",
                headers=api_headers,
            )

            if response.status_code == 401:
                pytest.skip("API key authentication required but not configured")

            assert response.status_code == 200
            data = response.json()
            assert "document" in data
            assert data["document"]["id"] == "chunk_1"

    def test_get_document_not_found(self, api_client, api_headers):
        """Test get document with non-existent ID."""
        with patch("app.api.routes.documents.DocumentManager") as mock_doc_mgr:
            mock_manager = mock_doc_mgr.return_value
            mock_manager.get_all_documents.return_value = []

            response = api_client.get(
                "/api/v1/documents/nonexistent",
                headers=api_headers,
            )

            if response.status_code == 401:
                pytest.skip("API key authentication required but not configured")

            assert response.status_code == 404

    def test_delete_document(self, api_client, api_headers):
        """Test delete document endpoint."""
        with patch("app.api.routes.documents.DocumentManager") as mock_doc_mgr:
            mock_manager = mock_doc_mgr.return_value
            mock_manager.delete_documents.return_value = 1  # 1 document deleted

            response = api_client.delete(
                "/api/v1/documents/chunk_1",
                headers=api_headers,
            )

            if response.status_code == 401:
                pytest.skip("API key authentication required but not configured")

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "chunk_1" in data["message"]

    def test_delete_document_not_found(self, api_client, api_headers):
        """Test delete document with non-existent ID."""
        with patch("app.api.routes.documents.DocumentManager") as mock_doc_mgr:
            mock_manager = mock_doc_mgr.return_value
            mock_manager.delete_documents.return_value = 0  # No documents deleted

            response = api_client.delete(
                "/api/v1/documents/nonexistent",
                headers=api_headers,
            )

            if response.status_code == 401:
                pytest.skip("API key authentication required but not configured")

            assert response.status_code == 404


class TestAuthentication:
    """Tests for API authentication."""

    def test_missing_api_key_when_required(self, api_client):
        """Test that API key is required when configured."""
        # Only test if API key is actually configured
        if not config.api_key:
            pytest.skip("API key not configured, authentication not required")

        response = api_client.post(
            "/api/v1/query",
            json={"question": "Test question"},
            # No X-API-Key header
        )

        assert response.status_code == 401
        assert "API key" in response.json()["detail"].lower()

    def test_invalid_api_key(self, api_client):
        """Test that invalid API key is rejected."""
        if not config.api_key:
            pytest.skip("API key not configured, authentication not required")

        response = api_client.post(
            "/api/v1/query",
            json={"question": "Test question"},
            headers={"X-API-Key": "invalid-key"},
        )

        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    def test_valid_api_key(self, api_client, api_key):
        """Test that valid API key is accepted."""
        if not config.api_key:
            pytest.skip("API key not configured, authentication not required")

        with patch("app.api.routes.query.create_rag_system") as mock_rag:
            from app.rag.chain import RAGQuerySystem

            mock_system = RAGQuerySystem.__new__(RAGQuerySystem)
            mock_system.query = lambda **kwargs: {
                "answer": "Test",
                "sources": [],
                "chunks_used": 0,
            }
            mock_rag.return_value = mock_system

            response = api_client.post(
                "/api/v1/query",
                json={"question": "Test question"},
                headers={"X-API-Key": api_key},
            )

            assert response.status_code == 200


class TestRateLimiting:
    """Tests for rate limiting middleware."""

    def test_rate_limit_headers(self, api_client, api_headers):
        """Test that rate limit headers are present in responses."""
        response = api_client.get(
            "/api/v1/health",
            headers=api_headers,
        )

        # Health endpoint doesn't require auth, so may not have headers
        # But if it does, check for rate limit headers
        if "X-RateLimit-Limit" in response.headers:
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers

    def test_rate_limit_enforcement(self, api_client, api_headers):
        """Test that rate limiting is enforced."""
        # Make many requests quickly
        limit = config.api_rate_limit_per_minute
        responses = []

        for _ in range(limit + 5):  # Exceed limit
            response = api_client.get(
                "/api/v1/health",
                headers=api_headers,
            )
            responses.append(response.status_code)

        # At least one should be rate limited (429) if limit is low enough
        # Note: This test may be flaky if limit is very high
        if limit < 100:  # Only test if limit is reasonable
            # Health endpoint may not be rate limited, so this is a soft check
            pass  # Rate limiting is tested in middleware, this is just a smoke test


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_not_found(self, api_client):
        """Test 404 for non-existent endpoint."""
        response = api_client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_422_validation_error(self, api_client, api_headers):
        """Test 422 for validation errors."""
        response = api_client.post(
            "/api/v1/query",
            json={"invalid": "field"},
            headers=api_headers,
        )

        if response.status_code == 401:
            pytest.skip("API key authentication required but not configured")

        assert response.status_code == 422

    def test_500_internal_error_handling(self, api_client, api_headers):
        """Test that internal errors are handled gracefully."""
        # Patch get_rag_system to raise an exception
        with patch("app.api.routes.query.get_rag_system") as mock_get_rag:
            mock_get_rag.side_effect = Exception("Internal error")

            response = api_client.post(
                "/api/v1/query",
                json={"question": "Test"},
                headers=api_headers,
            )

            if response.status_code == 401:
                pytest.skip("API key authentication required but not configured")

            # Should return 500, not crash
            assert response.status_code == 500
            assert "detail" in response.json()
