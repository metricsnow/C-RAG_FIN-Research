"""
Test script for ChromaDB integration.

Tests ChromaDB setup, document storage, and similarity search operations.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_core.documents import Document

from app.vector_db import ChromaStore, ChromaStoreError
from app.utils.config import config


def create_sample_embeddings(texts: list[str], dimensions: int = 384) -> list[list[float]]:
    """
    Create dummy embeddings for testing.

    In production, these would come from an embedding model.

    Args:
        texts: List of text strings
        dimensions: Embedding dimensions (default: 384 for small models)

    Returns:
        List of embedding vectors
    """
    embeddings = []
    for i, text in enumerate(texts):
        # Create simple dummy embeddings (normalized vectors)
        embedding = [float((i + j) % 10) / 10.0 for j in range(dimensions)]
        # Normalize
        norm = sum(x * x for x in embedding) ** 0.5
        embedding = [x / norm for x in embedding]
        embeddings.append(embedding)
    return embeddings


def test_chromadb_connection():
    """Test ChromaDB client connection."""
    print("Testing ChromaDB connection...")

    try:
        store = ChromaStore(collection_name="test_connection")
        print(f"✓ ChromaDB client connected successfully")
        print(f"  - Collection: {store.collection_name}")
        print(f"  - Persist directory: {config.CHROMA_DB_DIR}")
        return True, store
    except Exception as e:
        print(f"✗ ChromaDB connection failed: {str(e)}")
        return False, None


def test_add_documents(store: ChromaStore):
    """Test adding documents to ChromaDB."""
    print("\nTesting document addition...")

    try:
        # Create sample documents
        documents = [
            Document(
                page_content="This is a document about machine learning and artificial intelligence.",
                metadata={"source": "doc1.txt", "type": "text", "topic": "AI"},
            ),
            Document(
                page_content="Financial markets and trading strategies are complex topics.",
                metadata={"source": "doc2.txt", "type": "text", "topic": "finance"},
            ),
            Document(
                page_content="Python programming is essential for data science projects.",
                metadata={"source": "doc3.md", "type": "markdown", "topic": "programming"},
            ),
        ]

        # Create dummy embeddings
        embeddings = create_sample_embeddings([doc.page_content for doc in documents])

        # Add to ChromaDB
        ids = store.add_documents(documents, embeddings)
        print(f"✓ Documents added successfully")
        print(f"  - Number of documents: {len(documents)}")
        print(f"  - Document IDs: {ids[:3]}...")  # Show first 3 IDs
        return True, ids
    except Exception as e:
        print(f"✗ Document addition failed: {str(e)}")
        return False, None


def test_count(store: ChromaStore):
    """Test document count."""
    print("\nTesting document count...")

    try:
        count = store.count()
        print(f"✓ Document count retrieved: {count}")
        return True
    except Exception as e:
        print(f"✗ Document count failed: {str(e)}")
        return False


def test_query_by_embedding(store: ChromaStore):
    """Test similarity search by embedding."""
    print("\nTesting similarity search by embedding...")

    try:
        # Create a query embedding (similar to first document)
        query_embedding = create_sample_embeddings(["machine learning"])[0]

        # Query
        results = store.query_by_embedding(query_embedding, n_results=2)

        print(f"✓ Similarity search successful")
        print(f"  - Results found: {len(results['ids'])}")
        if results["ids"]:
            print(f"  - First result ID: {results['ids'][0]}")
            print(f"  - First result distance: {results['distances'][0]:.4f}")
            print(f"  - First result content: {results['documents'][0][:60]}...")
        return True
    except Exception as e:
        print(f"✗ Similarity search failed: {str(e)}")
        return False


def test_get_by_ids(store: ChromaStore, document_ids: list[str]):
    """Test retrieving documents by IDs."""
    print("\nTesting document retrieval by ID...")

    try:
        if not document_ids:
            print("⚠ No document IDs available for testing")
            return True

        # Get first document
        results = store.get_by_ids([document_ids[0]])

        print(f"✓ Document retrieval successful")
        print(f"  - Retrieved documents: {len(results['ids'])}")
        if results["ids"]:
            print(f"  - Document ID: {results['ids'][0]}")
            print(f"  - Document content: {results['documents'][0][:60]}...")
            print(f"  - Document metadata: {results['metadatas'][0]}")
        return True
    except Exception as e:
        print(f"✗ Document retrieval failed: {str(e)}")
        return False


def test_get_all(store: ChromaStore):
    """Test retrieving all documents."""
    print("\nTesting get all documents...")

    try:
        results = store.get_all()

        print(f"✓ Get all documents successful")
        print(f"  - Total documents: {len(results['ids'])}")
        return True
    except Exception as e:
        print(f"✗ Get all documents failed: {str(e)}")
        return False


def test_metadata_filtering(store: ChromaStore):
    """Test metadata filtering in queries."""
    print("\nTesting metadata filtering...")

    try:
        # Create query embedding
        query_embedding = create_sample_embeddings(["test query"])[0]

        # Query with metadata filter
        results = store.query_by_embedding(
            query_embedding,
            n_results=5,
            where={"topic": "finance"},  # Filter by topic
        )

        print(f"✓ Metadata filtering successful")
        print(f"  - Filtered results: {len(results['ids'])}")
        if results["ids"]:
            print(f"  - First result metadata: {results['metadatas'][0]}")
        return True
    except Exception as e:
        print(f"✗ Metadata filtering failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("ChromaDB Integration Test Suite")
    print("=" * 60)

    # Test connection
    success, store = test_chromadb_connection()
    if not success:
        print("\n✗ Cannot proceed without ChromaDB connection")
        return 1

    # Run tests
    results = []

    results.append(("ChromaDB Connection", success))

    # Add documents
    success, document_ids = test_add_documents(store)
    results.append(("Add Documents", success))

    results.append(("Document Count", test_count(store)))
    results.append(("Query by Embedding", test_query_by_embedding(store)))
    results.append(("Get by IDs", test_get_by_ids(store, document_ids or [])))
    results.append(("Get All Documents", test_get_all(store)))
    results.append(("Metadata Filtering", test_metadata_filtering(store)))

    # Cleanup: Delete test collection
    print("\nCleaning up test collection...")
    try:
        store.delete_collection()
        print("✓ Test collection deleted")
    except Exception as e:
        print(f"⚠ Failed to delete test collection: {str(e)}")

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! ChromaDB integration is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

