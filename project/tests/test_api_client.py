"""
Unit tests for API client wrapper (TASK-045).

Tests cover:
- API client initialization
- Query functionality
- Document management operations
- Error handling
- Retry logic
"""

from unittest.mock import Mock, patch

import pytest
import requests

from app.ui.api_client import (
    APIClient,
    APIConnectionError,
    APIError,
)


class TestAPIClientInitialization:
    """Test API client initialization."""

    @patch("app.ui.api_client.config")
    def test_init_defaults(self, mock_config):
        """Test initialization with default values."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30

        client = APIClient()

        assert client.base_url == "http://localhost:8000"
        assert client.api_key == ""
        assert client.timeout == 30
        assert client.max_retries == 3

    @patch("app.ui.api_client.config")
    def test_init_custom_values(self, mock_config):
        """Test initialization with custom values."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30

        client = APIClient(
            base_url="http://custom:9000",
            api_key="test-key",
            timeout=60,
            max_retries=5,
        )

        assert client.base_url == "http://custom:9000"
        assert client.api_key == "test-key"
        assert client.timeout == 60
        assert client.max_retries == 5

    @patch("app.ui.api_client.config")
    def test_init_uses_api_key_fallback(self, mock_config):
        """Test initialization uses API_KEY if api_client_key is empty."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = "fallback-key"
        mock_config.api_client_timeout = 30

        client = APIClient()

        assert client.api_key == "fallback-key"


class TestAPIClientHealthCheck:
    """Test API client health check."""

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.APIClient._make_request")
    def test_health_check_success(self, mock_request, mock_config):
        """Test successful health check."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_request.return_value = {"status": "healthy"}

        client = APIClient()
        result = client.health_check()

        assert result == {"status": "healthy"}
        mock_request.assert_called_once_with("GET", "/api/v1/health")

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.APIClient._make_request")
    def test_health_check_failure(self, mock_request, mock_config):
        """Test health check failure."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_request.side_effect = APIConnectionError("Connection failed")

        client = APIClient()

        with pytest.raises(APIConnectionError):
            client.health_check()


class TestAPIClientQuery:
    """Test API client query functionality."""

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.APIClient._make_request")
    def test_query_success(self, mock_request, mock_config):
        """Test successful query."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_request.return_value = {
            "answer": "Test answer",
            "sources": [
                {
                    "source": "doc1.pdf",
                    "filename": "doc1.pdf",
                    "ticker": "AAPL",
                    "form_type": "10-K",
                    "chunk_index": 0,
                    "date": "2023-01-01",
                }
            ],
            "chunks_used": 1,
        }

        client = APIClient()
        result = client.query("Test question")

        assert result["answer"] == "Test answer"
        assert len(result["sources"]) == 1
        assert result["sources"][0]["filename"] == "doc1.pdf"
        assert result["chunks_used"] == 1
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api/v1/query"
        assert call_args[1]["json_data"]["question"] == "Test question"

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.APIClient._make_request")
    def test_query_with_filters(self, mock_request, mock_config):
        """Test query with filters."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_request.return_value = {
            "answer": "Test answer",
            "sources": [],
            "chunks_used": 0,
        }

        client = APIClient()
        filters = {"ticker": "AAPL", "form_type": "10-K"}
        client.query("Test question", filters=filters)

        call_args = mock_request.call_args
        assert call_args[1]["json_data"]["filters"] == filters

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.APIClient._make_request")
    def test_query_with_conversation_history(self, mock_request, mock_config):
        """Test query with conversation history."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_request.return_value = {
            "answer": "Test answer",
            "sources": [],
            "chunks_used": 0,
        }

        client = APIClient()
        history = [{"role": "user", "content": "Previous question"}]
        client.query("Test question", conversation_history=history)

        call_args = mock_request.call_args
        assert call_args[1]["json_data"]["conversation_history"] == history


class TestAPIClientDocumentOperations:
    """Test API client document management operations."""

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.APIClient._make_request")
    def test_list_documents_success(self, mock_request, mock_config):
        """Test successful document listing."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_request.return_value = {
            "documents": [
                {
                    "id": "doc1",
                    "metadata": {"ticker": "AAPL"},
                    "content": "Test content",
                }
            ],
            "total": 1,
        }

        client = APIClient()
        result = client.list_documents()

        assert len(result) == 1
        assert result[0]["id"] == "doc1"
        mock_request.assert_called_once_with("GET", "/api/v1/documents")

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.APIClient._make_request")
    def test_get_document_success(self, mock_request, mock_config):
        """Test successful document retrieval."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_request.return_value = {
            "document": {
                "id": "doc1",
                "metadata": {"ticker": "AAPL"},
                "content": "Test content",
            }
        }

        client = APIClient()
        result = client.get_document("doc1")

        assert result["id"] == "doc1"
        assert result["content"] == "Test content"
        mock_request.assert_called_once_with("GET", "/api/v1/documents/doc1")

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.APIClient._make_request")
    def test_delete_document_success(self, mock_request, mock_config):
        """Test successful document deletion."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_request.return_value = {"message": "Deleted"}

        client = APIClient()
        result = client.delete_document("doc1")

        assert result is True
        mock_request.assert_called_once_with("DELETE", "/api/v1/documents/doc1")

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.APIClient._make_request")
    def test_delete_document_not_found(self, mock_request, mock_config):
        """Test document deletion when document not found."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_request.side_effect = APIError("Not found", status_code=404, response={})

        client = APIClient()
        result = client.delete_document("doc1")

        assert result is False


class TestAPIClientErrorHandling:
    """Test API client error handling."""

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.requests.Session")
    def test_connection_error(self, mock_session_class, mock_config):
        """Test handling of connection errors."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.request.side_effect = requests.ConnectionError("Connection failed")

        client = APIClient()

        with pytest.raises(APIConnectionError) as exc_info:
            client._make_request("GET", "/api/v1/health")

        assert "Failed to connect" in str(exc_info.value)

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.requests.Session")
    def test_timeout_error(self, mock_session_class, mock_config):
        """Test handling of timeout errors."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.request.side_effect = requests.Timeout("Request timeout")

        client = APIClient()

        with pytest.raises(APIConnectionError) as exc_info:
            client._make_request("GET", "/api/v1/health")

        assert "timeout" in str(exc_info.value).lower()

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.requests.Session")
    def test_api_error_400(self, mock_session_class, mock_config):
        """Test handling of 400 Bad Request errors."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Bad request"}
        mock_response.text = ""
        mock_session.request.return_value = mock_response

        client = APIClient()

        with pytest.raises(APIError) as exc_info:
            client._make_request("POST", "/api/v1/query", json_data={})

        assert exc_info.value.status_code == 400
        assert "Bad request" in str(exc_info.value)

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.requests.Session")
    def test_api_error_500(self, mock_session_class, mock_config):
        """Test handling of 500 Internal Server Error."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal error"}
        mock_response.text = ""
        mock_session.request.return_value = mock_response

        client = APIClient()

        with pytest.raises(APIError) as exc_info:
            client._make_request("GET", "/api/v1/documents")

        assert exc_info.value.status_code == 500


class TestAPIClientVersionHistory:
    """Test API client version history operations."""

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.APIClient._make_request")
    def test_get_version_history(self, mock_request, mock_config):
        """Test getting version history."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_request.return_value = {
            "versions": [
                {"version": 1, "version_date": "2023-01-01", "chunk_count": 10}
            ]
        }

        client = APIClient()
        result = client.get_version_history("doc.pdf")

        assert len(result) == 1
        assert result[0]["version"] == 1
        mock_request.assert_called_once_with(
            "GET", "/api/v1/documents/doc.pdf/versions"
        )

    @patch("app.ui.api_client.config")
    @patch("app.ui.api_client.APIClient._make_request")
    def test_compare_versions(self, mock_request, mock_config):
        """Test version comparison."""
        mock_config.api_client_base_url = "http://localhost:8000"
        mock_config.api_client_key = ""
        mock_config.api_key = ""
        mock_config.api_client_timeout = 30
        mock_request.return_value = {
            "version1_info": {"version": 1},
            "version2_info": {"version": 2},
            "differences": [],
        }

        client = APIClient()
        result = client.compare_versions("doc.pdf", 1, 2)

        assert "version1_info" in result
        assert "version2_info" in result
        mock_request.assert_called_once_with(
            "GET",
            "/api/v1/documents/doc.pdf/versions/compare",
            params={"version1": 1, "version2": 2},
        )
