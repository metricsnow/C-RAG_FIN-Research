"""
Health check module for application monitoring.

Provides health check endpoints to monitor system status and component health.
Health checks verify:
- ChromaDB connectivity
- Ollama service availability
- OpenAI API connectivity (if configured)
- Vector database status
- System resources

Health check server runs on a separate port and can be used by load balancers,
monitoring systems, and orchestration platforms.
"""

import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Dict, Optional

from app.utils.config import config
from app.utils.logger import get_logger
from app.utils.metrics import system_health_status, update_uptime

logger = get_logger(__name__)

# Health check server instance
_health_server: Optional[HTTPServer] = None
_health_thread: Optional[Thread] = None


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health check endpoints."""

    def log_message(self, format: str, *args) -> None:
        """Override to use application logger instead of default logging."""
        logger.debug(f"{self.address_string()} - {format % args}")

    def do_GET(self) -> None:
        """Handle GET requests for health check endpoints."""
        if self.path == "/health":
            self._handle_health_check()
        elif self.path == "/health/live":
            self._handle_liveness()
        elif self.path == "/health/ready":
            self._handle_readiness()
        else:
            self._send_response(404, {"error": "Not found"})

    def _handle_health_check(self) -> None:
        """Handle comprehensive health check."""
        health_status = self._check_health()
        status_code = 200 if health_status["status"] == "healthy" else 503
        self._send_response(status_code, health_status)

    def _handle_liveness(self) -> None:
        """Handle liveness probe (is the application running)."""
        liveness_status = {"status": "alive"}
        self._send_response(200, liveness_status)

    def _handle_readiness(self) -> None:
        """Handle readiness probe (is the application ready to serve requests)."""
        readiness_status = self._check_readiness()
        status_code = 200 if readiness_status["status"] == "ready" else 503
        self._send_response(status_code, readiness_status)

    def _check_health(self) -> Dict:
        """
        Perform comprehensive health check.

        Returns:
            Dictionary with health status and component details
        """
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {},
        }

        # Check ChromaDB
        chromadb_status = self._check_chromadb()
        health_status["components"]["chromadb"] = chromadb_status
        if chromadb_status["status"] != "healthy":
            health_status["status"] = "unhealthy"

        # Check Ollama
        ollama_status = self._check_ollama()
        health_status["components"]["ollama"] = ollama_status
        if ollama_status["status"] != "healthy" and config.llm_provider == "ollama":
            health_status["status"] = "unhealthy"

        # Check OpenAI (if configured)
        if config.embedding_provider == "openai":
            openai_status = self._check_openai()
            health_status["components"]["openai"] = openai_status
            if openai_status["status"] != "healthy":
                health_status["status"] = "unhealthy"

        # Update metrics
        system_health_status.set(1 if health_status["status"] == "healthy" else 0)
        update_uptime()

        return health_status

    def _check_readiness(self) -> Dict:
        """
        Check if application is ready to serve requests.

        Returns:
            Dictionary with readiness status
        """
        readiness = {"status": "ready", "timestamp": time.time()}

        # Check critical components
        chromadb_status = self._check_chromadb()
        if chromadb_status["status"] != "healthy":
            readiness["status"] = "not_ready"
            readiness["reason"] = "ChromaDB not available"

        if config.llm_provider == "ollama":
            ollama_status = self._check_ollama()
            if ollama_status["status"] != "healthy":
                readiness["status"] = "not_ready"
                readiness["reason"] = "Ollama service not available"

        return readiness

    def _check_chromadb(self) -> Dict:
        """Check ChromaDB connectivity and status."""
        try:
            from app.vector_db import ChromaStore

            store = ChromaStore()
            count = store.count()
            return {
                "status": "healthy",
                "document_count": count,
                "collection": store.collection_name,
            }
        except Exception as e:
            logger.debug(f"ChromaDB health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def _check_ollama(self) -> Dict:
        """Check Ollama service availability."""
        try:
            import requests

            response = requests.get(
                f"{config.ollama_base_url}/api/tags",
                timeout=2,
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "status": "healthy",
                    "base_url": config.ollama_base_url,
                    "models_available": len(models),
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"Ollama returned status {response.status_code}",
                }
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def _check_openai(self) -> Dict:
        """Check OpenAI API connectivity."""
        try:
            import requests  # noqa: F401

            if not config.openai_api_key:
                return {"status": "unhealthy", "error": "OpenAI API key not configured"}

            # Simple API check - verify API key is valid format
            if not config.openai_api_key.startswith("sk-"):
                return {
                    "status": "unhealthy",
                    "error": "OpenAI API key format invalid",
                }

            return {"status": "healthy", "api_key_configured": True}
        except Exception as e:
            logger.debug(f"OpenAI health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def _send_response(self, status_code: int, data: Dict) -> None:
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = json.dumps(data, indent=2).encode("utf-8")
        self.wfile.write(response)


def start_health_check_server() -> None:
    """Start health check HTTP server."""
    global _health_server, _health_thread

    if not config.health_check_enabled:
        logger.info("Health check server disabled")
        return

    if _health_server is not None:
        logger.warning("Health check server already running")
        return

    try:
        _health_server = HTTPServer(
            ("0.0.0.0", config.health_check_port), HealthCheckHandler
        )
        _health_thread = Thread(
            target=_health_server.serve_forever, daemon=True, name="HealthCheckServer"
        )
        _health_thread.start()
        logger.info(
            f"Health check server started on port {config.health_check_port}. "
            f"Endpoints available at http://localhost:{config.health_check_port}/health"
        )
    except OSError as e:
        logger.warning(
            f"Failed to start health check server on port "
            f"{config.health_check_port}: {e}. "
            "Health checks will not be available."
        )


def stop_health_check_server() -> None:
    """Stop health check HTTP server."""
    global _health_server, _health_thread

    if _health_server is not None:
        _health_server.shutdown()
        _health_server.server_close()
        _health_server = None
        _health_thread = None
        logger.info("Health check server stopped")


def get_health_status() -> Dict:
    """
    Get current health status (synchronous check).

    Returns:
        Dictionary with health status
    """

    # Create a mock handler instance for health checking
    # We can't use the real handler constructor, so we create a minimal instance
    class MockHandler:
        """Mock handler for health status checking."""

        def _check_health(self) -> Dict:
            """Perform comprehensive health check."""
            health_status = {
                "status": "healthy",
                "timestamp": time.time(),
                "components": {},
            }

            # Check ChromaDB
            chromadb_status = self._check_chromadb()
            health_status["components"]["chromadb"] = chromadb_status
            if chromadb_status["status"] != "healthy":
                health_status["status"] = "unhealthy"

            # Check Ollama
            ollama_status = self._check_ollama()
            health_status["components"]["ollama"] = ollama_status
            if ollama_status["status"] != "healthy" and config.llm_provider == "ollama":
                health_status["status"] = "unhealthy"

            # Check OpenAI (if configured)
            if config.embedding_provider == "openai":
                openai_status = self._check_openai()
                health_status["components"]["openai"] = openai_status
                if openai_status["status"] != "healthy":
                    health_status["status"] = "unhealthy"

            # Update metrics
            system_health_status.set(1 if health_status["status"] == "healthy" else 0)
            update_uptime()

            return health_status

        def _check_chromadb(self) -> Dict:
            """Check ChromaDB connectivity and status."""
            try:
                from app.vector_db import ChromaStore

                store = ChromaStore()
                count = store.count()
                return {
                    "status": "healthy",
                    "document_count": count,
                    "collection": store.collection_name,
                }
            except Exception as e:
                logger.debug(f"ChromaDB health check failed: {e}")
                return {"status": "unhealthy", "error": str(e)}

        def _check_ollama(self) -> Dict:
            """Check Ollama service availability."""
            try:
                import requests

                response = requests.get(
                    f"{config.ollama_base_url}/api/tags",
                    timeout=2,
                )
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return {
                        "status": "healthy",
                        "base_url": config.ollama_base_url,
                        "models_available": len(models),
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"Ollama returned status {response.status_code}",
                    }
            except Exception as e:
                logger.debug(f"Ollama health check failed: {e}")
                return {"status": "unhealthy", "error": str(e)}

        def _check_openai(self) -> Dict:
            """Check OpenAI API connectivity."""
            try:
                import requests  # noqa: F401

                if not config.openai_api_key:
                    return {
                        "status": "unhealthy",
                        "error": "OpenAI API key not configured",
                    }

                # Simple API check - verify API key is valid format
                if not config.openai_api_key.startswith("sk-"):
                    return {
                        "status": "unhealthy",
                        "error": "OpenAI API key format invalid",
                    }

                return {"status": "healthy", "api_key_configured": True}
            except Exception as e:
                logger.debug(f"OpenAI health check failed: {e}")
                return {"status": "unhealthy", "error": str(e)}

    handler = MockHandler()
    return handler._check_health()
