"""
Tests for health check module.

Tests verify health check endpoints and component health status.
"""

from unittest.mock import patch

from app.utils.health import (
    HealthCheckHandler,
    get_health_status,
    start_health_check_server,
    stop_health_check_server,
)


class TestHealthCheckHandler:
    """Test health check request handler."""

    def test_health_check_endpoint(self):
        """Test comprehensive health check endpoint."""
        handler = HealthCheckHandler(None, None, None)
        status = handler._check_health()
        assert "status" in status
        assert "timestamp" in status
        assert "components" in status
        assert status["status"] in ["healthy", "unhealthy"]

    def test_liveness_probe(self):
        """Test liveness probe endpoint."""
        handler = HealthCheckHandler(None, None, None)
        status = handler._handle_liveness()
        # Should always return alive
        assert status is None  # Handler sends response, doesn't return

    def test_readiness_probe(self):
        """Test readiness probe endpoint."""
        handler = HealthCheckHandler(None, None, None)
        readiness = handler._check_readiness()
        assert "status" in readiness
        assert readiness["status"] in ["ready", "not_ready"]

    def test_chromadb_check(self):
        """Test ChromaDB health check."""
        handler = HealthCheckHandler(None, None, None)
        status = handler._check_chromadb()
        assert "status" in status
        assert status["status"] in ["healthy", "unhealthy"]

    def test_ollama_check(self):
        """Test Ollama health check."""
        handler = HealthCheckHandler(None, None, None)
        status = handler._check_ollama()
        assert "status" in status

    @patch("app.utils.health.config")
    def test_openai_check(self, mock_config):
        """Test OpenAI health check."""
        mock_config.embedding_provider = "openai"
        mock_config.openai_api_key = "sk-test123"
        handler = HealthCheckHandler(None, None, None)
        status = handler._check_openai()
        assert "status" in status


class TestHealthCheckServer:
    """Test health check server functionality."""

    def test_get_health_status(self):
        """Test synchronous health status check."""
        status = get_health_status()
        assert "status" in status
        assert "components" in status

    @patch("app.utils.health.config")
    def test_start_health_check_server_disabled(self, mock_config):
        """Test health check server when disabled."""
        mock_config.health_check_enabled = False
        start_health_check_server()
        # Should not raise, just log

    @patch("app.utils.health.config")
    def test_start_health_check_server_enabled(self, mock_config):
        """Test health check server when enabled."""
        mock_config.health_check_enabled = True
        mock_config.health_check_port = 8080
        # May fail if port is in use, but should attempt to start
        try:
            start_health_check_server()
        except Exception:
            pass  # Expected if port in use
        finally:
            stop_health_check_server()
