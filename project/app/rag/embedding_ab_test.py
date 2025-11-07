"""
A/B Testing Framework for Embedding Models.

Provides comprehensive A/B testing capabilities to compare embedding model
quality (OpenAI, Ollama, FinBERT) and optimize embedding selection based on
query performance and accuracy metrics.
"""

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from scipy import stats

from app.rag.chain import RAGQueryError, RAGQuerySystem
from app.rag.embedding_factory import EmbeddingError, EmbeddingGenerator
from app.utils.logger import get_logger
from app.vector_db import ChromaStore

logger = get_logger(__name__)


@dataclass
class QueryResult:
    """Result of a single query execution."""

    query: str
    provider: str
    response_time: float
    chunks_retrieved: int
    average_distance: float
    min_distance: float
    max_distance: float
    answer_length: int
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class ProviderMetrics:
    """Aggregated metrics for an embedding provider."""

    provider: str
    total_queries: int
    avg_response_time: float
    median_response_time: float
    std_response_time: float
    avg_chunks_retrieved: float
    avg_distance: float
    median_distance: float
    std_distance: float
    min_distance: float
    max_distance: float
    avg_answer_length: float
    response_times: List[float] = field(default_factory=list)
    distances: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "provider": self.provider,
            "total_queries": self.total_queries,
            "avg_response_time": self.avg_response_time,
            "median_response_time": self.median_response_time,
            "std_response_time": self.std_response_time,
            "avg_chunks_retrieved": self.avg_chunks_retrieved,
            "avg_distance": self.avg_distance,
            "median_distance": self.median_distance,
            "std_distance": self.std_distance,
            "min_distance": self.min_distance,
            "max_distance": self.max_distance,
            "avg_answer_length": self.avg_answer_length,
        }


@dataclass
class StatisticalTestResult:
    """Result of statistical significance testing."""

    test_name: str
    provider_a: str
    provider_b: str
    metric: str
    statistic: float
    p_value: float
    significant: bool
    significance_level: float = 0.05
    interpretation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class EmbeddingABTest:
    """
    A/B Testing Framework for comparing embedding models.

    Compares multiple embedding providers (OpenAI, Ollama, FinBERT) on:
    - Query response time
    - Retrieval accuracy (distance metrics)
    - Number of chunks retrieved
    - Answer quality metrics
    """

    def __init__(
        self,
        providers: Optional[List[str]] = None,
        collection_name: str = "documents",
        top_k: int = 5,
        output_dir: Optional[str] = None,
    ):
        """
        Initialize A/B testing framework.

        Args:
            providers: List of embedding providers to test.
                Default: ['openai', 'ollama', 'finbert']
            collection_name: ChromaDB collection name
            top_k: Number of top chunks to retrieve
            output_dir: Directory to save test results. Default: ./data/ab_test_results

        Raises:
            EmbeddingError: If provider initialization fails
        """
        self.providers = providers or ["openai", "ollama", "finbert"]
        self.collection_name = collection_name
        self.top_k = top_k
        self.output_dir = Path(output_dir or "./data/ab_test_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize embedding generators for each provider
        self.embedding_generators: Dict[str, EmbeddingGenerator] = {}
        self.chroma_store = ChromaStore(collection_name=collection_name)

        logger.info(f"Initializing A/B test framework for providers: {self.providers}")
        for provider in self.providers:
            try:
                self.embedding_generators[provider] = EmbeddingGenerator(
                    provider=provider
                )
                logger.info(f"Initialized embedding generator for {provider}")
            except EmbeddingError as e:
                logger.error(f"Failed to initialize {provider}: {str(e)}")
                raise

        # Store query results
        self.query_results: List[QueryResult] = []

    def run_query(self, query: str, provider: str, use_rag: bool = True) -> QueryResult:
        """
        Run a single query with specified embedding provider.

        Args:
            query: Query text
            provider: Embedding provider to use
            use_rag: If True, use full RAG pipeline. If False, only test retrieval.

        Returns:
            QueryResult with performance metrics

        Raises:
            EmbeddingError: If provider is invalid
            RAGQueryError: If query execution fails
        """
        if provider not in self.embedding_generators:
            raise EmbeddingError(f"Provider {provider} not initialized")

        logger.debug(f"Running query with {provider}: '{query[:50]}...'")
        start_time = time.time()

        try:
            # Generate query embedding
            embedding_gen = self.embedding_generators[provider]
            query_embedding = embedding_gen.embed_query(query)

            # Query ChromaDB
            results = self.chroma_store.query_by_embedding(
                query_embedding=query_embedding, n_results=self.top_k
            )

            # Calculate metrics
            distances = results.get("distances", [])
            chunks_retrieved = len(distances)
            avg_distance = np.mean(distances) if distances else 0.0
            min_distance = np.min(distances) if distances else 0.0
            max_distance = np.max(distances) if distances else 0.0

            # If using RAG, generate answer
            answer_length = 0
            if use_rag:
                try:
                    rag_system = RAGQuerySystem(
                        collection_name=self.collection_name,
                        top_k=self.top_k,
                        embedding_provider=provider,
                    )
                    answer = rag_system.query(query)
                    answer_length = len(answer) if answer else 0
                except Exception as e:
                    logger.warning(f"RAG query failed for {provider}: {str(e)}")
                    # Continue with retrieval-only metrics

            response_time = time.time() - start_time

            result = QueryResult(
                query=query,
                provider=provider,
                response_time=response_time,
                chunks_retrieved=chunks_retrieved,
                average_distance=avg_distance,
                min_distance=min_distance,
                max_distance=max_distance,
                answer_length=answer_length,
            )

            self.query_results.append(result)
            logger.debug(
                f"Query completed: {provider}, time={response_time:.3f}s, "
                f"chunks={chunks_retrieved}, avg_dist={avg_distance:.4f}"
            )

            return result

        except Exception as e:
            logger.error(f"Query failed for {provider}: {str(e)}", exc_info=True)
            raise RAGQueryError(f"Query failed for {provider}: {str(e)}") from e

    def run_batch_queries(
        self, queries: List[str], use_rag: bool = True, randomize: bool = True
    ) -> List[QueryResult]:
        """
        Run batch of queries across all providers.

        Args:
            queries: List of query texts
            use_rag: If True, use full RAG pipeline
            randomize: If True, randomize provider order for each query

        Returns:
            List of QueryResult objects
        """
        logger.info(
            f"Running batch of {len(queries)} queries "
            f"across {len(self.providers)} providers"
        )

        results: List[QueryResult] = []
        provider_order = self.providers.copy()

        for query in queries:
            if randomize:
                np.random.shuffle(provider_order)

            for provider in provider_order:
                try:
                    result = self.run_query(query, provider, use_rag=use_rag)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to run query with {provider}: {str(e)}")
                    # Continue with other providers

        logger.info(f"Completed batch: {len(results)} query results collected")
        return results

    def calculate_provider_metrics(self, provider: str) -> ProviderMetrics:
        """
        Calculate aggregated metrics for a provider.

        Args:
            provider: Provider name

        Returns:
            ProviderMetrics with aggregated statistics
        """
        provider_results = [r for r in self.query_results if r.provider == provider]

        if not provider_results:
            logger.warning(f"No results found for provider {provider}")
            return ProviderMetrics(
                provider=provider,
                total_queries=0,
                avg_response_time=0.0,
                median_response_time=0.0,
                std_response_time=0.0,
                avg_chunks_retrieved=0.0,
                avg_distance=0.0,
                median_distance=0.0,
                std_distance=0.0,
                min_distance=0.0,
                max_distance=0.0,
                avg_answer_length=0.0,
            )

        response_times = [r.response_time for r in provider_results]
        distances = [r.average_distance for r in provider_results]
        chunks = [r.chunks_retrieved for r in provider_results]
        answer_lengths = [r.answer_length for r in provider_results]

        return ProviderMetrics(
            provider=provider,
            total_queries=len(provider_results),
            avg_response_time=np.mean(response_times),
            median_response_time=np.median(response_times),
            std_response_time=np.std(response_times),
            avg_chunks_retrieved=np.mean(chunks),
            avg_distance=np.mean(distances),
            median_distance=np.median(distances),
            std_distance=np.std(distances),
            min_distance=np.min(distances) if distances else 0.0,
            max_distance=np.max(distances) if distances else 0.0,
            avg_answer_length=np.mean(answer_lengths),
            response_times=response_times,
            distances=distances,
        )

    def compare_providers(
        self,
        provider_a: str,
        provider_b: str,
        metric: str = "response_time",
        significance_level: float = 0.05,
    ) -> StatisticalTestResult:
        """
        Compare two providers using statistical significance testing.

        Args:
            provider_a: First provider name
            provider_b: Second provider name
            metric: Metric to compare ('response_time', 'distance', 'chunks_retrieved')
            significance_level: Significance level for testing (default: 0.05)

        Returns:
            StatisticalTestResult with test results
        """
        results_a = [r for r in self.query_results if r.provider == provider_a]
        results_b = [r for r in self.query_results if r.provider == provider_b]

        if not results_a or not results_b:
            raise ValueError(
                f"Insufficient data: {provider_a} has {len(results_a)} results, "
                f"{provider_b} has {len(results_b)} results"
            )

        # Extract metric values
        if metric == "response_time":
            values_a = [r.response_time for r in results_a]
            values_b = [r.response_time for r in results_b]
        elif metric == "distance":
            values_a = [r.average_distance for r in results_a]
            values_b = [r.average_distance for r in results_b]
        elif metric == "chunks_retrieved":
            values_a = [r.chunks_retrieved for r in results_a]
            values_b = [r.chunks_retrieved for r in results_b]
        else:
            raise ValueError(f"Unknown metric: {metric}")

        # Perform two-sample t-test
        statistic, p_value = stats.ttest_ind(values_a, values_b)

        significant = p_value < significance_level
        sig_text = "significantly" if significant else "not significantly"
        sig_result = "significant" if significant else "not significant"
        interpretation = (
            f"{provider_a} is {sig_text} "
            f"different from {provider_b} in {metric} "
            f"(p={p_value:.4f}, {sig_result})"
        )

        return StatisticalTestResult(
            test_name="two_sample_t_test",
            provider_a=provider_a,
            provider_b=provider_b,
            metric=metric,
            statistic=float(statistic),
            p_value=float(p_value),
            significant=significant,
            significance_level=significance_level,
            interpretation=interpretation,
        )

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive A/B test report.

        Returns:
            Dictionary with report data
        """
        logger.info("Generating A/B test report")

        # Calculate metrics for each provider
        provider_metrics = {
            provider: self.calculate_provider_metrics(provider)
            for provider in self.providers
        }

        # Perform pairwise comparisons
        comparisons = []
        for i, provider_a in enumerate(self.providers):
            for provider_b in self.providers[i + 1 :]:
                for metric in ["response_time", "distance", "chunks_retrieved"]:
                    try:
                        comparison = self.compare_providers(
                            provider_a, provider_b, metric
                        )
                        comparisons.append(comparison)
                    except ValueError as e:
                        logger.warning(f"Comparison failed: {str(e)}")

        # Generate summary
        report = {
            "test_info": {
                "providers": self.providers,
                "collection_name": self.collection_name,
                "top_k": self.top_k,
                "total_queries": len(self.query_results),
                "timestamp": datetime.now().isoformat(),
            },
            "provider_metrics": {
                provider: metrics.to_dict()
                for provider, metrics in provider_metrics.items()
            },
            "statistical_tests": [comp.to_dict() for comp in comparisons],
            "raw_results": [r.to_dict() for r in self.query_results],
        }

        return report

    def save_report(self, filename: Optional[str] = None) -> Path:
        """
        Save test report to JSON file.

        Args:
            filename: Optional filename. Default: ab_test_report_YYYYMMDD_HHMMSS.json

        Returns:
            Path to saved file
        """
        report = self.generate_report()

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ab_test_report_{timestamp}.json"

        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved to {filepath}")
        return filepath

    def print_summary(self) -> None:
        """Print human-readable summary of test results."""
        report = self.generate_report()

        print("\n" + "=" * 80)
        print("A/B TEST SUMMARY")
        print("=" * 80)
        print("\nTest Configuration:")
        print(f"  Providers: {', '.join(self.providers)}")
        print(f"  Collection: {self.collection_name}")
        print(f"  Total Queries: {len(self.query_results)}")

        print(f"\n{'Provider Metrics':^80}")
        print("-" * 80)
        for provider, metrics_dict in report["provider_metrics"].items():
            print(f"\n{provider.upper()}:")
            print(f"  Total Queries: {metrics_dict['total_queries']}")
            print(f"  Avg Response Time: {metrics_dict['avg_response_time']:.3f}s")
            print(
                f"  Median Response Time: {metrics_dict['median_response_time']:.3f}s"
            )
            print(f"  Avg Distance: {metrics_dict['avg_distance']:.4f}")
            print(f"  Median Distance: {metrics_dict['median_distance']:.4f}")
            print(f"  Avg Chunks Retrieved: {metrics_dict['avg_chunks_retrieved']:.1f}")
            print(f"  Avg Answer Length: {metrics_dict['avg_answer_length']:.0f} chars")

        print(f"\n{'Statistical Comparisons':^80}")
        print("-" * 80)
        for test in report["statistical_tests"]:
            significance = (
                "✓ SIGNIFICANT" if test["significant"] else "✗ Not significant"
            )
            print(f"\n{test['provider_a']} vs {test['provider_b']} ({test['metric']}):")
            print(f"  {significance}")
            print(f"  p-value: {test['p_value']:.4f}")
            print(f"  statistic: {test['statistic']:.4f}")

        print("\n" + "=" * 80)
