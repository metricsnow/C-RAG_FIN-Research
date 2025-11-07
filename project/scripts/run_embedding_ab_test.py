#!/usr/bin/env python3
"""
Script to run A/B testing for embedding models.

Usage:
    python scripts/run_embedding_ab_test.py --queries "query1" "query2" ...
    python scripts/run_embedding_ab_test.py --file queries.txt
    python scripts/run_embedding_ab_test.py --interactive
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.rag.embedding_ab_test import EmbeddingABTest  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def load_queries_from_file(filepath: str) -> list[str]:
    """Load queries from a text file (one per line)."""
    with open(filepath, "r") as f:
        queries = [line.strip() for line in f if line.strip()]
    return queries


def get_default_queries() -> list[str]:
    """Get default test queries for financial research."""
    return [
        "What are the key financial metrics for Apple Inc?",
        "Which companies have filed 10-K forms recently?",
        "What is the revenue growth trend for technology companies?",
        "Explain the balance sheet structure of major banks",
        "What are the earnings per share for top tech companies?",
        "Which companies have the highest market capitalization?",
        "What are the dividend policies of blue-chip stocks?",
        "Explain the cash flow statements of energy companies",
        "What are the debt-to-equity ratios for financial institutions?",
        "Which sectors show the strongest growth in recent quarters?",
    ]


def main():
    """Main function to run A/B testing."""
    parser = argparse.ArgumentParser(
        description="Run A/B testing for embedding models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--queries",
        nargs="+",
        help="List of queries to test",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="File containing queries (one per line)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode (prompt for queries)",
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        default=["openai", "ollama", "finbert"],
        help="Embedding providers to test (default: openai ollama finbert)",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="documents",
        help="ChromaDB collection name (default: documents)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of top chunks to retrieve (default: 5)",
    )
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Skip RAG answer generation (test retrieval only)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data/ab_test_results",
        help="Output directory for test results (default: ./data/ab_test_results)",
    )

    args = parser.parse_args()

    # Determine queries to use
    queries: list[str] = []
    if args.queries:
        queries = args.queries
    elif args.file:
        queries = load_queries_from_file(args.file)
    elif args.interactive:
        print("Enter queries (one per line, empty line to finish):")
        while True:
            query = input().strip()
            if not query:
                break
            queries.append(query)
    else:
        queries = get_default_queries()
        print(f"Using default queries ({len(queries)} queries)")

    if not queries:
        print("Error: No queries provided")
        sys.exit(1)

    print(f"\nRunning A/B test with {len(queries)} queries")
    print(f"Providers: {', '.join(args.providers)}")
    print(f"Collection: {args.collection}")
    print(f"Top-K: {args.top_k}")
    print(f"RAG: {'enabled' if not args.no_rag else 'disabled'}\n")

    try:
        # Initialize A/B test framework
        ab_test = EmbeddingABTest(
            providers=args.providers,
            collection_name=args.collection,
            top_k=args.top_k,
            output_dir=args.output_dir,
        )

        # Run batch queries
        ab_test.run_batch_queries(queries, use_rag=not args.no_rag)

        # Generate and save report
        report_path = ab_test.save_report()

        # Print summary
        ab_test.print_summary()

        print(f"\nFull report saved to: {report_path}")

    except Exception as e:
        logger.error(f"A/B test failed: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
