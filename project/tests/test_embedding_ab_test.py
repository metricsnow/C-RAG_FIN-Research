"""
Tests for embedding A/B testing framework.

Tests the A/B testing framework for comparing embedding models including
query execution, metrics calculation, statistical testing, and reporting.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.rag.embedding_ab_test import (
    EmbeddingABTest,
    ProviderMetrics,
    QueryResult,
    StatisticalTestResult,
)
from app.rag.embedding_factory import EmbeddingError


class TestQueryResult:
    """Test QueryResult dataclass."""

    def test_query_result_creation(self):
        """Test creating a QueryResult."""
        result = QueryResult(
            query="test query",
            provider="openai",
            response_time=1.5,
            chunks_retrieved=5,
            average_distance=0.3,
            min_distance=0.1,
            max_distance=0.5,
            answer_length=100,
        )

        assert result.query == "test query"
        assert result.provider == "openai"
        assert result.response_time == 1.5
        assert result.chunks_retrieved == 5
        assert result.average_distance == 0.3

    def test_query_result_to_dict(self):
        """Test converting QueryResult to dictionary."""
        result = QueryResult(
            query="test",
            provider="openai",
            response_time=1.0,
            chunks_retrieved=3,
            average_distance=0.2,
            min_distance=0.1,
            max_distance=0.3,
            answer_length=50,
        )

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["query"] == "test"
        assert result_dict["provider"] == "openai"
        assert isinstance(result_dict["timestamp"], str)


class TestProviderMetrics:
    """Test ProviderMetrics dataclass."""

    def test_provider_metrics_creation(self):
        """Test creating ProviderMetrics."""
        metrics = ProviderMetrics(
            provider="openai",
            total_queries=10,
            avg_response_time=1.5,
            median_response_time=1.4,
            std_response_time=0.2,
            avg_chunks_retrieved=5.0,
            avg_distance=0.3,
            median_distance=0.28,
            std_distance=0.1,
            min_distance=0.1,
            max_distance=0.5,
            avg_answer_length=150,
        )

        assert metrics.provider == "openai"
        assert metrics.total_queries == 10
        assert metrics.avg_response_time == 1.5

    def test_provider_metrics_to_dict(self):
        """Test converting ProviderMetrics to dictionary."""
        metrics = ProviderMetrics(
            provider="test",
            total_queries=5,
            avg_response_time=1.0,
            median_response_time=0.9,
            std_response_time=0.1,
            avg_chunks_retrieved=4.0,
            avg_distance=0.2,
            median_distance=0.19,
            std_distance=0.05,
            min_distance=0.1,
            max_distance=0.3,
            avg_answer_length=100,
        )

        metrics_dict = metrics.to_dict()
        assert isinstance(metrics_dict, dict)
        assert metrics_dict["provider"] == "test"
        assert metrics_dict["total_queries"] == 5


class TestStatisticalTestResult:
    """Test StatisticalTestResult dataclass."""

    def test_statistical_test_result_creation(self):
        """Test creating StatisticalTestResult."""
        result = StatisticalTestResult(
            test_name="t_test",
            provider_a="openai",
            provider_b="ollama",
            metric="response_time",
            statistic=2.5,
            p_value=0.01,
            significant=True,
        )

        assert result.test_name == "t_test"
        assert result.provider_a == "openai"
        assert result.significant is True
        assert result.p_value == 0.01


class TestEmbeddingABTest:
    """Test EmbeddingABTest framework."""

    @pytest.fixture
    def mock_embedding_generator(self):
        """Create a mock embedding generator."""
        mock_gen = Mock()
        mock_gen.embed_query.return_value = [0.1] * 1536  # Mock OpenAI embedding
        mock_gen.embed_documents.return_value = [[0.1] * 1536] * 5
        return mock_gen

    @pytest.fixture
    def mock_chroma_store(self):
        """Create a mock ChromaDB store."""
        mock_store = Mock()
        mock_store.query_by_embedding.return_value = {
            "ids": ["id1", "id2", "id3"],
            "distances": [0.1, 0.2, 0.3],
            "metadatas": [{}, {}, {}],
            "documents": ["doc1", "doc2", "doc3"],
        }
        return mock_store

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    def test_initialization(
        self, mock_chroma_class, mock_embedding_class, temp_output_dir
    ):
        """Test A/B test framework initialization."""
        mock_embedding_class.return_value = Mock()
        mock_chroma_class.return_value = Mock()

        ab_test = EmbeddingABTest(
            providers=["openai", "finbert"],
            output_dir=str(temp_output_dir),
        )

        assert len(ab_test.embedding_generators) == 2
        assert "openai" in ab_test.embedding_generators
        assert "finbert" in ab_test.embedding_generators

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    def test_initialization_invalid_provider(
        self, mock_chroma_class, mock_embedding_class, temp_output_dir
    ):
        """Test initialization with invalid provider."""
        mock_chroma_class.return_value = Mock()
        mock_embedding_class.side_effect = EmbeddingError("Invalid provider")

        with pytest.raises(EmbeddingError):
            EmbeddingABTest(
                providers=["invalid"],
                output_dir=str(temp_output_dir),
            )

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    @patch("app.rag.embedding_ab_test.time.time")
    def test_run_query_retrieval_only(
        self,
        mock_time,
        mock_chroma_class,
        mock_embedding_class,
        mock_embedding_generator,
        mock_chroma_store,
        temp_output_dir,
    ):
        """Test running a query with retrieval only (no RAG)."""
        mock_embedding_class.return_value = mock_embedding_generator
        mock_chroma_class.return_value = mock_chroma_store
        mock_time.side_effect = [0.0, 1.5]  # Start and end time

        ab_test = EmbeddingABTest(
            providers=["openai"],
            output_dir=str(temp_output_dir),
        )

        result = ab_test.run_query("test query", "openai", use_rag=False)

        assert result.query == "test query"
        assert result.provider == "openai"
        assert result.response_time == 1.5
        assert result.chunks_retrieved == 3
        assert abs(result.average_distance - 0.2) < 0.001  # Mean of [0.1, 0.2, 0.3]

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    @patch("app.rag.embedding_ab_test.RAGQuerySystem")
    @patch("app.rag.embedding_ab_test.time.time")
    def test_run_query_with_rag(
        self,
        mock_time,
        mock_rag_class,
        mock_chroma_class,
        mock_embedding_class,
        mock_embedding_generator,
        mock_chroma_store,
        temp_output_dir,
    ):
        """Test running a query with full RAG pipeline."""
        mock_embedding_class.return_value = mock_embedding_generator
        mock_chroma_class.return_value = mock_chroma_store
        mock_rag_instance = Mock()
        mock_rag_instance.query.return_value = "Test answer"
        mock_rag_class.return_value = mock_rag_instance
        mock_time.side_effect = [0.0, 2.0]  # Start and end time

        ab_test = EmbeddingABTest(
            providers=["openai"],
            output_dir=str(temp_output_dir),
        )

        result = ab_test.run_query("test query", "openai", use_rag=True)

        assert result.query == "test query"
        assert result.provider == "openai"
        assert result.response_time == 2.0
        assert result.answer_length == len("Test answer")

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    @patch("app.rag.embedding_ab_test.time.time")
    def test_run_query_invalid_provider(
        self,
        mock_time,
        mock_chroma_class,
        mock_embedding_class,
        temp_output_dir,
    ):
        """Test running query with invalid provider."""
        mock_embedding_class.return_value = Mock()
        mock_chroma_class.return_value = Mock()

        ab_test = EmbeddingABTest(
            providers=["openai"],
            output_dir=str(temp_output_dir),
        )

        with pytest.raises(EmbeddingError):
            ab_test.run_query("test", "invalid_provider")

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    @patch("app.rag.embedding_ab_test.time.time")
    def test_run_batch_queries(
        self,
        mock_time,
        mock_chroma_class,
        mock_embedding_class,
        mock_embedding_generator,
        mock_chroma_store,
        temp_output_dir,
    ):
        """Test running batch queries."""
        mock_embedding_class.return_value = mock_embedding_generator
        mock_chroma_class.return_value = mock_chroma_store
        # Times for 2 queries × 2 providers = 4 query executions
        # Each query needs start and end time
        mock_time.side_effect = [0.0, 1.0, 0.0, 1.5, 0.0, 1.2, 0.0, 1.8]

        ab_test = EmbeddingABTest(
            providers=["openai", "finbert"],
            output_dir=str(temp_output_dir),
        )

        queries = ["query1", "query2"]
        results = ab_test.run_batch_queries(queries, use_rag=False)

        # Should have 2 queries × 2 providers = 4 results
        assert len(results) == 4
        assert all(isinstance(r, QueryResult) for r in results)

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    def test_calculate_provider_metrics(
        self, mock_chroma_class, mock_embedding_class, temp_output_dir
    ):
        """Test calculating provider metrics."""
        mock_embedding_class.return_value = Mock()
        mock_chroma_class.return_value = Mock()

        ab_test = EmbeddingABTest(
            providers=["openai"],
            output_dir=str(temp_output_dir),
        )

        # Add some test results
        for i in range(5):
            ab_test.query_results.append(
                QueryResult(
                    query=f"query{i}",
                    provider="openai",
                    response_time=1.0 + i * 0.1,
                    chunks_retrieved=5,
                    average_distance=0.2 + i * 0.01,
                    min_distance=0.1,
                    max_distance=0.3,
                    answer_length=100,
                )
            )

        metrics = ab_test.calculate_provider_metrics("openai")

        assert metrics.provider == "openai"
        assert metrics.total_queries == 5
        assert metrics.avg_response_time > 0
        assert metrics.avg_distance > 0

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    def test_calculate_provider_metrics_no_results(
        self, mock_chroma_class, mock_embedding_class, temp_output_dir
    ):
        """Test calculating metrics with no results."""
        mock_embedding_class.return_value = Mock()
        mock_chroma_class.return_value = Mock()

        ab_test = EmbeddingABTest(
            providers=["openai"],
            output_dir=str(temp_output_dir),
        )

        metrics = ab_test.calculate_provider_metrics("openai")

        assert metrics.total_queries == 0
        assert metrics.avg_response_time == 0.0

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    def test_compare_providers(
        self, mock_chroma_class, mock_embedding_class, temp_output_dir
    ):
        """Test comparing two providers."""
        mock_embedding_class.return_value = Mock()
        mock_chroma_class.return_value = Mock()

        ab_test = EmbeddingABTest(
            providers=["openai", "finbert"],
            output_dir=str(temp_output_dir),
        )

        # Add results for both providers
        for provider in ["openai", "finbert"]:
            for i in range(10):
                ab_test.query_results.append(
                    QueryResult(
                        query=f"query{i}",
                        provider=provider,
                        response_time=1.0
                        + (i * 0.1 if provider == "openai" else i * 0.2),
                        chunks_retrieved=5,
                        average_distance=0.2
                        + (i * 0.01 if provider == "openai" else i * 0.02),
                        min_distance=0.1,
                        max_distance=0.3,
                        answer_length=100,
                    )
                )

        result = ab_test.compare_providers("openai", "finbert", metric="response_time")

        assert isinstance(result, StatisticalTestResult)
        assert result.provider_a == "openai"
        assert result.provider_b == "finbert"
        assert result.metric == "response_time"
        assert "p_value" in result.to_dict()

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    def test_compare_providers_insufficient_data(
        self, mock_chroma_class, mock_embedding_class, temp_output_dir
    ):
        """Test comparing providers with insufficient data."""
        mock_embedding_class.return_value = Mock()
        mock_chroma_class.return_value = Mock()

        ab_test = EmbeddingABTest(
            providers=["openai", "finbert"],
            output_dir=str(temp_output_dir),
        )

        with pytest.raises(ValueError):
            ab_test.compare_providers("openai", "finbert")

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    def test_compare_providers_invalid_metric(
        self, mock_chroma_class, mock_embedding_class, temp_output_dir
    ):
        """Test comparing providers with invalid metric."""
        mock_embedding_class.return_value = Mock()
        mock_chroma_class.return_value = Mock()

        ab_test = EmbeddingABTest(
            providers=["openai", "finbert"],
            output_dir=str(temp_output_dir),
        )

        # Add some results
        for i in range(5):
            ab_test.query_results.append(
                QueryResult(
                    query=f"query{i}",
                    provider="openai",
                    response_time=1.0,
                    chunks_retrieved=5,
                    average_distance=0.2,
                    min_distance=0.1,
                    max_distance=0.3,
                    answer_length=100,
                )
            )

        with pytest.raises(ValueError):
            ab_test.compare_providers("openai", "finbert", metric="invalid_metric")

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    def test_generate_report(
        self, mock_chroma_class, mock_embedding_class, temp_output_dir
    ):
        """Test generating test report."""
        mock_embedding_class.return_value = Mock()
        mock_chroma_class.return_value = Mock()

        ab_test = EmbeddingABTest(
            providers=["openai", "finbert"],
            output_dir=str(temp_output_dir),
        )

        # Add some test results
        for provider in ["openai", "finbert"]:
            for i in range(3):
                ab_test.query_results.append(
                    QueryResult(
                        query=f"query{i}",
                        provider=provider,
                        response_time=1.0,
                        chunks_retrieved=5,
                        average_distance=0.2,
                        min_distance=0.1,
                        max_distance=0.3,
                        answer_length=100,
                    )
                )

        report = ab_test.generate_report()

        assert "test_info" in report
        assert "provider_metrics" in report
        assert "statistical_tests" in report
        assert "raw_results" in report
        assert len(report["provider_metrics"]) == 2

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    def test_save_report(
        self, mock_chroma_class, mock_embedding_class, temp_output_dir
    ):
        """Test saving report to file."""
        mock_embedding_class.return_value = Mock()
        mock_chroma_class.return_value = Mock()

        ab_test = EmbeddingABTest(
            providers=["openai"],
            output_dir=str(temp_output_dir),
        )

        # Add a test result
        ab_test.query_results.append(
            QueryResult(
                query="test",
                provider="openai",
                response_time=1.0,
                chunks_retrieved=5,
                average_distance=0.2,
                min_distance=0.1,
                max_distance=0.3,
                answer_length=100,
            )
        )

        filepath = ab_test.save_report("test_report.json")

        assert filepath.exists()
        assert filepath.name == "test_report.json"

        # Verify file contents
        with open(filepath) as f:
            report = json.load(f)
            assert "test_info" in report
            assert "provider_metrics" in report

    @patch("app.rag.embedding_ab_test.EmbeddingGenerator")
    @patch("app.rag.embedding_ab_test.ChromaStore")
    @patch("builtins.print")
    def test_print_summary(
        self, mock_print, mock_chroma_class, mock_embedding_class, temp_output_dir
    ):
        """Test printing summary."""
        mock_embedding_class.return_value = Mock()
        mock_chroma_class.return_value = Mock()

        ab_test = EmbeddingABTest(
            providers=["openai"],
            output_dir=str(temp_output_dir),
        )

        # Add a test result
        ab_test.query_results.append(
            QueryResult(
                query="test",
                provider="openai",
                response_time=1.0,
                chunks_retrieved=5,
                average_distance=0.2,
                min_distance=0.1,
                max_distance=0.3,
                answer_length=100,
            )
        )

        ab_test.print_summary()

        # Verify print was called
        assert mock_print.called
