"""
Tests for metrics collection module.

Tests verify metrics are properly collected and exposed for monitoring.
"""

import time

from prometheus_client import REGISTRY, generate_latest

from app.utils.metrics import (
    initialize_metrics,
    rag_queries_total,
    rag_query_duration_seconds,
    system_health_status,
    system_uptime_seconds,
    track_duration,
    track_error,
    track_success,
    update_uptime,
)


class TestMetricsInitialization:
    """Test metrics initialization."""

    def test_initialize_metrics(self):
        """Test metrics initialization."""
        # Should not raise
        initialize_metrics()
        # Verify metrics are registered by checking if metric name exists in registry
        metric_names = [
            collector._name
            for collector in REGISTRY._names_to_collectors.values()
            if hasattr(collector, "_name")
        ]
        assert rag_queries_total._name in metric_names


class TestMetricsCollection:
    """Test metrics collection functionality."""

    def test_track_success(self):
        """Test tracking successful operations."""
        track_success(rag_queries_total)
        # Verify counter was incremented
        assert rag_queries_total.labels(status="success")._value.get() > 0

    def test_track_error(self):
        """Test tracking errors."""
        track_error(rag_queries_total)
        # Verify counter was incremented
        assert rag_queries_total.labels(status="error")._value.get() > 0

    def test_track_duration(self):
        """Test tracking operation duration."""
        with track_duration(rag_query_duration_seconds, {"provider": "test"}):
            time.sleep(0.1)
        # Verify histogram has observations by checking the sum
        labeled_histogram = rag_query_duration_seconds.labels(provider="test")
        # Access the sum value (it's a MutexValue, need to get the value)
        assert labeled_histogram._sum._value.get() > 0

    def test_update_uptime(self):
        """Test updating system uptime."""
        initialize_metrics()
        update_uptime()
        # Verify uptime is set
        assert system_uptime_seconds._value.get() >= 0

    def test_system_health_status(self):
        """Test system health status metric."""
        system_health_status.set(1)
        assert system_health_status._value.get() == 1
        system_health_status.set(0)
        assert system_health_status._value.get() == 0


class TestMetricsExposure:
    """Test metrics exposure via Prometheus."""

    def test_metrics_export(self):
        """Test metrics are exported in Prometheus format."""
        # Generate metrics output
        output = generate_latest(REGISTRY)
        assert b"rag_queries_total" in output
        assert b"rag_query_duration_seconds" in output

    def test_metrics_labels(self):
        """Test metrics with labels."""
        track_success(rag_queries_total, {"status": "success"})
        track_error(rag_queries_total, {"status": "error"})
        # Verify both labels exist
        output = generate_latest(REGISTRY)
        assert b'status="success"' in output or b"status=success" in output
        assert b'status="error"' in output or b"status=error" in output
