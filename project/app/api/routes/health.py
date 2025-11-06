"""
Health check API routes.
"""

from fastapi import APIRouter

from app.utils.health import get_health_status
from app.utils.metrics import get_metrics

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict:
    """
    Comprehensive health check endpoint.

    Returns:
        Health status with component details
    """
    return get_health_status()


@router.get("/live")
async def liveness() -> dict:
    """
    Liveness probe endpoint (is the application running).

    Returns:
        Simple alive status
    """
    return {"status": "alive"}


@router.get("/ready")
async def readiness() -> dict:
    """
    Readiness probe endpoint (is the application ready to serve requests).

    Returns:
        Readiness status
    """
    health_status = get_health_status()
    components = health_status.get("components", {})

    # Check critical components
    chromadb_status = components.get("chromadb", {}).get("status", "unknown")
    ollama_status = components.get("ollama", {}).get("status", "unknown")

    if chromadb_status != "healthy":
        return {"status": "not_ready", "reason": "ChromaDB not available"}

    if ollama_status != "healthy":
        return {"status": "not_ready", "reason": "Ollama service not available"}

    return {"status": "ready"}


@router.get("/metrics")
async def metrics() -> str:
    """
    Prometheus metrics endpoint.

    Returns:
        Prometheus metrics in text format
    """
    return get_metrics().decode("utf-8")
