"""
Metrics collection module for application monitoring and observability.

Provides Prometheus metrics for tracking:
- RAG query performance
- Document ingestion metrics
- Vector database operations
- LLM response times
- System health metrics

Metrics are collected using the Prometheus Python client library.
"""

import time
from contextlib import contextmanager
from typing import Optional

from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    start_http_server,
)

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create custom registry for application metrics
metrics_registry = CollectorRegistry()

# RAG Query Metrics
rag_queries_total = Counter(
    "rag_queries_total",
    "Total number of RAG queries processed",
    ["status"],  # status: success, error
    registry=metrics_registry,
)

rag_query_duration_seconds = Histogram(
    "rag_query_duration_seconds",
    "RAG query processing duration in seconds",
    ["provider"],  # provider: ollama, openai
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, float("inf")],
    registry=metrics_registry,
)

rag_query_tokens = Histogram(
    "rag_query_tokens",
    "Number of tokens in RAG queries and responses",
    ["type"],  # type: query, response
    buckets=[10, 50, 100, 500, 1000, 2000, 5000, 10000, float("inf")],
    registry=metrics_registry,
)

rag_context_chunks_retrieved = Histogram(
    "rag_context_chunks_retrieved",
    "Number of context chunks retrieved per query",
    buckets=[1, 3, 5, 10, 20, 50, 100, float("inf")],
    registry=metrics_registry,
)

# Document Ingestion Metrics
document_ingestion_total = Counter(
    "document_ingestion_total",
    "Total number of documents ingested",
    ["status"],  # status: success, error
    registry=metrics_registry,
)

document_ingestion_duration_seconds = Histogram(
    "document_ingestion_duration_seconds",
    "Document ingestion processing duration in seconds",
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, float("inf")],
    registry=metrics_registry,
)

document_chunks_created = Histogram(
    "document_chunks_created",
    "Number of chunks created per document",
    buckets=[1, 5, 10, 20, 50, 100, 200, 500, float("inf")],
    registry=metrics_registry,
)

document_size_bytes = Histogram(
    "document_size_bytes",
    "Size of ingested documents in bytes",
    buckets=[
        1024,  # 1KB
        10240,  # 10KB
        102400,  # 100KB
        1048576,  # 1MB
        10485760,  # 10MB
        104857600,  # 100MB
        float("inf"),
    ],
    registry=metrics_registry,
)

# Vector Database Metrics
vector_db_operations_total = Counter(
    "vector_db_operations_total",
    "Total number of vector database operations",
    ["operation", "status"],  # operation: query, add, delete; status: success, error
    registry=metrics_registry,
)

vector_db_operation_duration_seconds = Histogram(
    "vector_db_operation_duration_seconds",
    "Vector database operation duration in seconds",
    ["operation"],  # operation: query, add, delete
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, float("inf")],
    registry=metrics_registry,
)

vector_db_collection_size = Gauge(
    "vector_db_collection_size",
    "Total number of documents in vector database collection",
    ["collection"],
    registry=metrics_registry,
)

# LLM Metrics
llm_requests_total = Counter(
    "llm_requests_total",
    "Total number of LLM requests",
    ["provider", "model", "status"],  # status: success, error
    registry=metrics_registry,
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["provider", "model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, float("inf")],
    registry=metrics_registry,
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total number of tokens processed by LLM",
    ["provider", "model", "type"],  # type: input, output
    registry=metrics_registry,
)

# Embedding Metrics
embedding_requests_total = Counter(
    "embedding_requests_total",
    "Total number of embedding generation requests",
    ["provider", "status"],  # status: success, error
    registry=metrics_registry,
)

embedding_request_duration_seconds = Histogram(
    "embedding_request_duration_seconds",
    "Embedding generation duration in seconds",
    ["provider"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, float("inf")],
    registry=metrics_registry,
)

embedding_dimensions = Histogram(
    "embedding_dimensions",
    "Dimension size of generated embeddings",
    ["provider"],
    buckets=[128, 256, 512, 768, 1024, 1536, 2048, 4096, float("inf")],
    registry=metrics_registry,
)

# System Health Metrics
system_health_status = Gauge(
    "system_health_status",
    "System health status (1 = healthy, 0 = unhealthy)",
    registry=metrics_registry,
)

system_uptime_seconds = Gauge(
    "system_uptime_seconds",
    "System uptime in seconds",
    registry=metrics_registry,
)

# Track startup time for uptime calculation
_startup_time: Optional[float] = None


def initialize_metrics() -> None:
    """
    Initialize metrics collection system.

    Registers metrics with the default Prometheus registry and starts
    the metrics HTTP server if enabled.
    """
    global _startup_time
    _startup_time = time.time()

    # Register all metrics with default registry as well for compatibility
    for metric in metrics_registry._collector_to_names.keys():
        if hasattr(metric, "_name"):
            REGISTRY.register(metric)

    # Start metrics HTTP server if enabled
    if config.metrics_enabled:
        metrics_port = config.metrics_port
        try:
            start_http_server(metrics_port, registry=metrics_registry)
            logger.info(
                f"Metrics server started on port {metrics_port}. "
                f"Metrics available at http://localhost:{metrics_port}/metrics"
            )
        except OSError as e:
            logger.warning(
                f"Failed to start metrics server on port {metrics_port}: {e}. "
                "Metrics collection will continue but metrics endpoint unavailable."
            )


def update_uptime() -> None:
    """Update system uptime metric."""
    if _startup_time is not None:
        uptime = time.time() - _startup_time
        system_uptime_seconds.set(uptime)


@contextmanager
def track_duration(histogram: Histogram, labels: Optional[dict] = None):
    """
    Context manager for tracking operation duration.

    Args:
        histogram: Histogram metric to record duration
        labels: Optional dictionary of label values

    Example:
        >>> with track_duration(rag_query_duration_seconds, {"provider": "ollama"}):
        ...     # Operation to time
        ...     pass
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        if labels:
            histogram.labels(**labels).observe(duration)
        else:
            histogram.observe(duration)


def track_error(counter: Counter, labels: Optional[dict] = None) -> None:
    """
    Track error occurrence in metrics.

    Args:
        counter: Counter metric to increment
        labels: Optional dictionary of label values including 'status'
    """
    if labels is None:
        labels = {}
    labels.setdefault("status", "error")
    counter.labels(**labels).inc()


def track_success(counter: Counter, labels: Optional[dict] = None) -> None:
    """
    Track successful operation in metrics.

    Args:
        counter: Counter metric to increment
        labels: Optional dictionary of label values including 'status'
    """
    if labels is None:
        labels = {}
    labels.setdefault("status", "success")
    counter.labels(**labels).inc()


def get_metrics() -> bytes:
    """
    Get Prometheus metrics in text format.

    Returns:
        Metrics in Prometheus text format as bytes
    """
    return generate_latest(metrics_registry)
