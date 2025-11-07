# Embedding A/B Testing Framework (TASK-041)

## Overview

The system includes a comprehensive A/B testing framework for comparing embedding model quality across different providers (OpenAI, Ollama, FinBERT). This enables data-driven embedding model selection based on query performance and accuracy metrics.

## Features

### Core Capabilities

1. **Multi-Provider Comparison**
   - Compare OpenAI, Ollama, and FinBERT embedding models
   - Support for custom provider combinations
   - Automatic provider initialization and validation

2. **Performance Metrics Tracking**
   - Query response time (mean, median, std dev)
   - Retrieval accuracy (distance metrics: min, max, average)
   - Number of chunks retrieved
   - Answer quality metrics (answer length)

3. **Statistical Significance Testing**
   - Two-sample t-test for comparing providers
   - Configurable significance levels (default: 0.05)
   - P-value and test statistic reporting
   - Multiple metrics support (response_time, distance, chunks_retrieved)

4. **Comprehensive Reporting**
   - JSON report generation with full test data
   - Human-readable summary printing
   - Provider metrics comparison
   - Statistical test results with interpretations

5. **Flexible Testing Modes**
   - Full RAG pipeline testing (with LLM answer generation)
   - Retrieval-only mode (embedding quality testing)
   - Batch query processing with provider randomization

## Installation

The A/B testing framework requires additional dependencies:

```bash
pip install scipy>=1.11.0 numpy>=1.24.0
```

These are automatically installed when you install project dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Python API

#### Basic Usage

```python
from app.rag.embedding_ab_test import EmbeddingABTest

# Initialize A/B test with multiple providers
ab_test = EmbeddingABTest(
    providers=["openai", "ollama", "finbert"],
    collection_name="documents",
    top_k=5,
    output_dir="./data/ab_test_results"
)

# Run batch queries
queries = [
    "What are Apple's financial metrics?",
    "Explain balance sheet structure",
    "Which companies have the highest revenue?"
]
results = ab_test.run_batch_queries(queries, use_rag=True)

# Generate and save report
report_path = ab_test.save_report()
ab_test.print_summary()
```

#### Single Query Testing

```python
# Run a single query with a specific provider
result = ab_test.run_query(
    query="What is Apple's revenue?",
    provider="openai",
    use_rag=True
)

print(f"Response time: {result.response_time:.3f}s")
print(f"Chunks retrieved: {result.chunks_retrieved}")
print(f"Average distance: {result.average_distance:.4f}")
```

#### Retrieval-Only Mode

Test embedding quality without LLM overhead:

```python
# Test retrieval quality only (faster, no LLM costs)
results = ab_test.run_batch_queries(
    queries,
    use_rag=False,  # Skip RAG answer generation
    randomize=True   # Randomize provider order
)
```

#### Provider Metrics

```python
# Calculate aggregated metrics for a provider
metrics = ab_test.calculate_provider_metrics("openai")

print(f"Total queries: {metrics.total_queries}")
print(f"Avg response time: {metrics.avg_response_time:.3f}s")
print(f"Avg distance: {metrics.avg_distance:.4f}")
print(f"Median distance: {metrics.median_distance:.4f}")
```

#### Statistical Comparison

```python
# Compare two providers statistically
comparison = ab_test.compare_providers(
    provider_a="openai",
    provider_b="finbert",
    metric="response_time",
    significance_level=0.05
)

print(f"Test: {comparison.test_name}")
print(f"P-value: {comparison.p_value:.4f}")
print(f"Significant: {comparison.significant}")
print(f"Interpretation: {comparison.interpretation}")
```

### Command-Line Interface

#### Basic Usage

Run A/B test with default queries:

```bash
python scripts/run_embedding_ab_test.py
```

#### Custom Queries

```bash
python scripts/run_embedding_ab_test.py \
    --queries "What is Apple's revenue?" "Explain balance sheets"
```

#### Query File

Create a file with queries (one per line):

```bash
# queries.txt
What are the key financial metrics for Apple Inc?
Which companies have filed 10-K forms recently?
What is the revenue growth trend for technology companies?

# Run with file
python scripts/run_embedding_ab_test.py --file queries.txt
```

#### Interactive Mode

```bash
python scripts/run_embedding_ab_test.py --interactive
# Enter queries one per line, empty line to finish
```

#### Advanced Options

```bash
# Specify providers
python scripts/run_embedding_ab_test.py \
    --providers openai finbert \
    --queries "query1" "query2"

# Use different collection
python scripts/run_embedding_ab_test.py \
    --collection my_collection \
    --queries "query1"

# Retrieval-only mode (no RAG)
python scripts/run_embedding_ab_test.py \
    --no-rag \
    --queries "query1" "query2"

# Custom output directory
python scripts/run_embedding_ab_test.py \
    --output-dir ./my_results \
    --queries "query1"
```

#### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--queries` | List of queries to test | Default queries |
| `--file` | File containing queries (one per line) | - |
| `--interactive` | Interactive mode (prompt for queries) | - |
| `--providers` | Embedding providers to test | `openai ollama finbert` |
| `--collection` | ChromaDB collection name | `documents` |
| `--top-k` | Number of top chunks to retrieve | `5` |
| `--no-rag` | Skip RAG answer generation | `False` |
| `--output-dir` | Output directory for reports | `./data/ab_test_results` |

## Report Format

### JSON Report Structure

```json
{
  "test_info": {
    "providers": ["openai", "ollama", "finbert"],
    "collection_name": "documents",
    "top_k": 5,
    "total_queries": 30,
    "timestamp": "2025-11-07T09:00:00"
  },
  "provider_metrics": {
    "openai": {
      "provider": "openai",
      "total_queries": 10,
      "avg_response_time": 1.234,
      "median_response_time": 1.200,
      "std_response_time": 0.150,
      "avg_chunks_retrieved": 5.0,
      "avg_distance": 0.234,
      "median_distance": 0.230,
      "std_distance": 0.020,
      "min_distance": 0.180,
      "max_distance": 0.290,
      "avg_answer_length": 245
    },
    "ollama": { ... },
    "finbert": { ... }
  },
  "statistical_tests": [
    {
      "test_name": "two_sample_t_test",
      "provider_a": "openai",
      "provider_b": "finbert",
      "metric": "response_time",
      "statistic": 2.345,
      "p_value": 0.0234,
      "significant": true,
      "significance_level": 0.05,
      "interpretation": "openai is significantly different from finbert in response_time (p=0.0234, significant)"
    }
  ],
  "raw_results": [ ... ]
}
```

### Human-Readable Summary

The `print_summary()` method generates a formatted summary:

```
================================================================================
A/B TEST SUMMARY
================================================================================

Test Configuration:
  Providers: openai, ollama, finbert
  Collection: documents
  Total Queries: 30

Provider Metrics
--------------------------------------------------------------------------------

OPENAI:
  Total Queries: 10
  Avg Response Time: 1.234s
  Median Response Time: 1.200s
  Avg Distance: 0.2340
  Median Distance: 0.2300
  Avg Chunks Retrieved: 5.0
  Avg Answer Length: 245 chars

OLLAMA:
  ...

Statistical Comparisons
--------------------------------------------------------------------------------

openai vs finbert (response_time):
  ✓ SIGNIFICANT
  p-value: 0.0234
  statistic: 2.3450
```

## Metrics Explained

### Response Time

- **Average**: Mean query execution time
- **Median**: Middle value (less affected by outliers)
- **Std Dev**: Variability in response times
- **Lower is better**: Faster queries improve user experience

### Distance Metrics

- **Average Distance**: Mean similarity distance to retrieved chunks
- **Median Distance**: Middle distance value
- **Min/Max Distance**: Range of distances
- **Lower is better**: Closer distances indicate better relevance

### Chunks Retrieved

- **Average**: Mean number of chunks retrieved per query
- **Consistency**: Should match `top_k` setting
- **Higher is better**: More chunks provide more context (up to top_k limit)

### Answer Length

- **Average**: Mean length of generated answers
- **Relevance**: Longer answers may indicate more comprehensive responses
- **Context-dependent**: Optimal length varies by query type

## Statistical Testing

### Two-Sample T-Test

The framework uses SciPy's `ttest_ind` for comparing providers:

- **Null Hypothesis**: No significant difference between providers
- **Alternative Hypothesis**: Significant difference exists
- **Significance Level**: Default 0.05 (5% chance of false positive)
- **P-value**: Probability of observing the difference by chance
- **Interpretation**: p < 0.05 indicates significant difference

### Metrics Tested

1. **response_time**: Query execution time comparison
2. **distance**: Retrieval accuracy comparison
3. **chunks_retrieved**: Retrieval consistency comparison

### Example Interpretation

```python
comparison = ab_test.compare_providers("openai", "finbert", "response_time")

if comparison.significant:
    if comparison.statistic > 0:
        print("OpenAI is significantly slower than FinBERT")
    else:
        print("OpenAI is significantly faster than FinBERT")
else:
    print("No significant difference in response time")
```

## Best Practices

### Query Selection

1. **Diverse Queries**: Include various query types (factual, analytical, comparative)
2. **Domain-Specific**: Use financial domain queries relevant to your use case
3. **Realistic**: Use queries similar to actual user queries
4. **Sufficient Sample Size**: At least 10-20 queries per provider for statistical validity

### Testing Strategy

1. **Start with Retrieval-Only**: Test embedding quality first (faster, cheaper)
2. **Then Test Full RAG**: Evaluate end-to-end performance
3. **Randomize Provider Order**: Avoid order bias in results
4. **Run Multiple Batches**: Increase sample size for better statistics

### Interpreting Results

1. **Statistical Significance**: Look for p < 0.05 for meaningful differences
2. **Practical Significance**: Consider if differences matter in practice
3. **Multiple Metrics**: Don't rely on a single metric
4. **Context Matters**: Best provider may vary by query type

### Example Workflow

```python
# 1. Initialize test
ab_test = EmbeddingABTest(providers=["openai", "finbert"])

# 2. Run retrieval-only test (fast)
queries = load_test_queries()
ab_test.run_batch_queries(queries, use_rag=False)

# 3. Analyze retrieval quality
for provider in ["openai", "finbert"]:
    metrics = ab_test.calculate_provider_metrics(provider)
    print(f"{provider}: avg_distance={metrics.avg_distance:.4f}")

# 4. Compare statistically
comparison = ab_test.compare_providers("openai", "finbert", "distance")
print(f"Significant difference: {comparison.significant}")

# 5. If retrieval quality is similar, test full RAG
if not comparison.significant:
    ab_test.run_batch_queries(queries, use_rag=True)
    ab_test.save_report()
    ab_test.print_summary()
```

## Troubleshooting

### Provider Initialization Fails

**Error**: `EmbeddingError: Provider not initialized`

**Solution**: Ensure provider is properly configured:
- OpenAI: Set `OPENAI_API_KEY` in `.env`
- Ollama: Ensure Ollama server is running
- FinBERT: Ensure `sentence-transformers` is installed

### Insufficient Data for Comparison

**Error**: `ValueError: Insufficient data`

**Solution**: Run more queries to collect sufficient data (minimum 5-10 queries per provider)

### Collection Not Found

**Error**: `ChromaStoreError: Collection not found`

**Solution**: Ensure ChromaDB collection exists and contains documents. Use correct `collection_name` parameter.

### Statistical Test Fails

**Error**: Test returns NaN or invalid results

**Solution**:
- Ensure sufficient data (at least 5 queries per provider)
- Check for extreme outliers in metrics
- Verify data distribution is reasonable

## Integration with Other Features

### RAG Optimization

A/B testing can be used to evaluate RAG optimizations:

```python
# Test with optimizations enabled
ab_test_optimized = EmbeddingABTest(...)
# ... run tests with RAG optimizations

# Test without optimizations
ab_test_basic = EmbeddingABTest(...)
# ... run tests without optimizations

# Compare results
```

### Document Re-indexing

Test embedding quality after re-indexing:

```python
# Test before re-indexing
ab_test_before = EmbeddingABTest(...)
ab_test_before.run_batch_queries(queries)

# Re-index documents
# ... re-indexing code ...

# Test after re-indexing
ab_test_after = EmbeddingABTest(...)
ab_test_after.run_batch_queries(queries)

# Compare results
```

## Related Documentation

- [Configuration Documentation](../reference/configuration.md#embedding-configuration) - Embedding provider configuration
- [RAG Optimization Features](../../README.md#rag-optimization-features) - RAG system optimizations
- [Embedding Factory](../../app/rag/embedding_factory.py) - Embedding model implementation

## API Reference

See `app/rag/embedding_ab_test.py` for complete API documentation:

- `EmbeddingABTest`: Main A/B testing class
- `QueryResult`: Single query result data class
- `ProviderMetrics`: Aggregated provider metrics
- `StatisticalTestResult`: Statistical test results
