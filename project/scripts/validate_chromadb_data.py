#!/usr/bin/env python3
"""
Script to validate ChromaDB data integrity and check for corruption.

This script performs comprehensive checks on the vector database:
- Collection existence and metadata
- Document count and sample retrieval
- Metadata validation
- Content validation
- Query functionality test
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.logger import get_logger  # noqa: E402
from app.vector_db.chroma_store import ChromaStore, ChromaStoreError  # noqa: E402

logger = get_logger(__name__)


def validate_chromadb_data():
    """Validate ChromaDB data integrity."""
    print("=" * 60)
    print("ChromaDB Data Validation Report")
    print("=" * 60)
    print()

    issues = []
    warnings = []

    try:
        # Initialize store
        store = ChromaStore()
        print("✅ ChromaDB connection successful")

        # Check document count
        count = store.count()
        print(f"📊 Total documents in collection: {count}")

        if count == 0:
            issues.append("No documents found in ChromaDB")
            print("❌ ERROR: ChromaDB is empty!")
        else:
            print("✅ Documents found in database")

        # Test query functionality
        print("\n" + "-" * 60)
        print("Testing Query Functionality")
        print("-" * 60)

        test_queries = [
            "financial",
            "revenue",
            "risk",
            "earnings",
        ]

        for query in test_queries:
            try:
                results = store.query_by_text(query, n_results=5)
                result_count = len(results.get("ids", []))
                print(f"  Query '{query}': {result_count} results")

                if result_count == 0:
                    warnings.append(f"Query '{query}' returned no results")
            except Exception as e:
                issues.append(f"Query '{query}' failed: {str(e)}")
                print(f"  ❌ Query '{query}' failed: {e}")

        # Validate sample documents
        print("\n" + "-" * 60)
        print("Validating Sample Documents")
        print("-" * 60)

        try:
            results = store.query_by_text("financial documents", n_results=10)

            if not results.get("ids") or len(results["ids"]) == 0:
                issues.append("Cannot retrieve sample documents")
                print("❌ ERROR: Cannot retrieve sample documents")
            else:
                ids = results["ids"]
                metadatas = results.get("metadatas", [])
                documents = results.get("documents", [])

                print(f"  Retrieved {len(ids)} sample documents")

                # Validate each sample
                valid_count = 0
                invalid_count = 0

                for i, doc_id in enumerate(ids[:10]):
                    is_valid = True
                    issues_found = []

                    # Check document content
                    if i < len(documents):
                        doc_content = documents[i]
                        if not doc_content or len(doc_content.strip()) == 0:
                            issues_found.append("Empty document content")
                            is_valid = False
                        elif len(doc_content) < 10:
                            doc_id_short = doc_id[:20]
                            warnings.append(
                                f"Document {doc_id_short}... has very short "
                                f"content ({len(doc_content)} chars)"
                            )
                    else:
                        issues_found.append("Missing document content")
                        is_valid = False

                    # Check metadata
                    if i < len(metadatas):
                        metadata = metadatas[i]
                        if not metadata:
                            warnings.append(
                                f"Document {doc_id[:20]}... has no metadata"
                            )
                        else:
                            # Check for required metadata fields
                            if "source" not in metadata and "filename" not in metadata:
                                doc_id_short = doc_id[:20]
                                warnings.append(
                                    f"Document {doc_id_short}... missing "
                                    f"source/filename metadata"
                                )
                    else:
                        warnings.append(f"Document {doc_id[:20]}... missing metadata")

                    if is_valid:
                        valid_count += 1
                    else:
                        invalid_count += 1
                        issues.append(
                            f"Document {doc_id[:20]}...: {', '.join(issues_found)}"
                        )

                print(f"  ✅ Valid documents: {valid_count}")
                if invalid_count > 0:
                    print(f"  ❌ Invalid documents: {invalid_count}")

                # Show sample metadata
                if metadatas:
                    print("\n  Sample Metadata:")
                    sample_meta = metadatas[0] if metadatas else {}
                    for key, value in list(sample_meta.items())[:5]:
                        value_str = (
                            str(value)[:50] + "..."
                            if len(str(value)) > 50
                            else str(value)
                        )
                        print(f"    {key}: {value_str}")

                # Show sample document content
                if documents:
                    print("\n  Sample Document Content:")
                    sample_doc = documents[0][:300] if documents[0] else "No content"
                    print(f"    {sample_doc}...")

        except Exception as e:
            issues.append(f"Document validation failed: {str(e)}")
            print(f"❌ ERROR: Document validation failed: {e}")
            logger.exception("Document validation error")

        # Check metadata statistics
        print("\n" + "-" * 60)
        print("Metadata Statistics")
        print("-" * 60)

        try:
            results = store.query_by_text("test", n_results=100)
            if results.get("metadatas") and len(results["metadatas"]) > 0:
                all_metadata = results["metadatas"]
                metadata_keys = set()
                for meta in all_metadata:
                    metadata_keys.update(meta.keys())

                print(f"  Metadata keys found: {sorted(metadata_keys)}")

                # Count documents by source
                sources = {}
                for meta in all_metadata:
                    source = meta.get("source") or meta.get("filename", "unknown")
                    sources[source] = sources.get(source, 0) + 1

                print("\n  Document sources (sample):")
                for source, count in sorted(
                    sources.items(), key=lambda x: x[1], reverse=True
                )[:10]:
                    source_name = Path(source).name if source != "unknown" else source
                    print(f"    {source_name}: {count} chunks")
            else:
                warnings.append("Cannot retrieve metadata for statistics")

        except Exception as e:
            warnings.append(f"Metadata statistics failed: {str(e)}")

    except ChromaStoreError as e:
        issues.append(f"ChromaDB error: {str(e)}")
        print(f"❌ ERROR: ChromaDB error: {e}")
    except Exception as e:
        issues.append(f"Unexpected error: {str(e)}")
        print(f"❌ ERROR: Unexpected error: {e}")
        logger.exception("Validation error")

    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    if not issues:
        print("✅ All checks passed! ChromaDB data appears to be valid.")
    else:
        print(f"❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")

    if warnings:
        print(f"\n⚠️  {len(warnings)} warnings:")
        for warning in warnings[:10]:  # Show first 10 warnings
            print(f"  - {warning}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more warnings")

    print()
    return len(issues) == 0


if __name__ == "__main__":
    success = validate_chromadb_data()
    sys.exit(0 if success else 1)
