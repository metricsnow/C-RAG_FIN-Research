"""
Example script demonstrating ChromaDB usage.

This script shows how to:
1. Initialize ChromaDB with persistent storage
2. Add documents with embeddings
3. Query for similar documents
4. Retrieve documents by ID
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_core.documents import Document

from app.utils.config import config
from app.vector_db import ChromaStore


def create_dummy_embeddings(
    texts: list[str], dimensions: int = 384
) -> list[list[float]]:
    """
    Create dummy embeddings for demonstration.

    In production, use OpenAI or Ollama embeddings.

    Args:
        texts: List of text strings
        dimensions: Embedding dimensions

    Returns:
        List of embedding vectors
    """
    import random

    embeddings = []
    for text in texts:
        # Create random normalized vector
        embedding = [random.random() for _ in range(dimensions)]
        norm = sum(x * x for x in embedding) ** 0.5
        embedding = [x / norm for x in embedding]
        embeddings.append(embedding)
    return embeddings


def main():
    """Demonstrate ChromaDB usage."""
    print("=" * 60)
    print("ChromaDB Usage Example")
    print("=" * 60)

    # Step 1: Initialize ChromaDB
    print("\n1. Initializing ChromaDB...")
    store = ChromaStore(
        collection_name="example_collection",
        persist_directory=config.CHROMA_DB_DIR,
    )
    print(f"   ✓ ChromaDB initialized")
    print(f"   - Collection: {store.collection_name}")
    print(f"   - Storage: {config.CHROMA_DB_DIR}")

    # Step 2: Create sample documents
    print("\n2. Creating sample documents...")
    documents = [
        Document(
            page_content="Python is a high-level programming language known for its simplicity.",
            metadata={
                "source": "python_intro.txt",
                "topic": "programming",
                "type": "text",
            },
        ),
        Document(
            page_content="Machine learning enables computers to learn from data without explicit programming.",
            metadata={"source": "ml_intro.txt", "topic": "AI", "type": "text"},
        ),
        Document(
            page_content="Financial markets involve trading securities like stocks and bonds.",
            metadata={
                "source": "finance_intro.txt",
                "topic": "finance",
                "type": "text",
            },
        ),
    ]
    print(f"   ✓ Created {len(documents)} documents")

    # Step 3: Generate embeddings (dummy for demonstration)
    print("\n3. Generating embeddings (dummy for demonstration)...")
    embeddings = create_dummy_embeddings([doc.page_content for doc in documents])
    print(f"   ✓ Generated {len(embeddings)} embeddings")
    print(f"   - Embedding dimensions: {len(embeddings[0])}")

    # Step 4: Add documents to ChromaDB
    print("\n4. Adding documents to ChromaDB...")
    ids = store.add_documents(documents, embeddings)
    print(f"   ✓ Added {len(ids)} documents")
    print(f"   - Document IDs: {ids}")

    # Step 5: Query for similar documents
    print("\n5. Querying for similar documents...")
    # Create query embedding (similar to first document)
    query_embedding = create_dummy_embeddings(["programming language"])[0]
    results = store.query_by_embedding(query_embedding, n_results=2)

    print(f"   ✓ Found {len(results['ids'])} similar documents")
    for i, (doc_id, distance, content) in enumerate(
        zip(results["ids"], results["distances"], results["documents"]), 1
    ):
        print(f"   Result {i}:")
        print(f"     - ID: {doc_id}")
        print(f"     - Distance: {distance:.4f}")
        print(f"     - Content: {content[:60]}...")

    # Step 6: Retrieve document by ID
    print("\n6. Retrieving document by ID...")
    retrieved = store.get_by_ids([ids[0]])
    if retrieved["ids"]:
        print(f"   ✓ Retrieved document")
        print(f"     - ID: {retrieved['ids'][0]}")
        print(f"     - Content: {retrieved['documents'][0][:60]}...")
        print(f"     - Metadata: {retrieved['metadatas'][0]}")

    # Step 7: Get document count
    print("\n7. Getting document count...")
    count = store.count()
    print(f"   ✓ Collection contains {count} documents")

    # Step 8: Query with metadata filtering
    print("\n8. Querying with metadata filter (topic='finance')...")
    query_embedding = create_dummy_embeddings(["finance"])[0]
    filtered_results = store.query_by_embedding(
        query_embedding,
        n_results=5,
        where={"topic": "finance"},
    )
    print(f"   ✓ Found {len(filtered_results['ids'])} documents matching filter")

    # Cleanup
    print("\n9. Cleaning up...")
    store.delete_collection()
    print("   ✓ Collection deleted")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nTo use ChromaDB in your code:")
    print("  1. Import: from app.vector_db import ChromaStore")
    print("  2. Initialize: store = ChromaStore(collection_name='my_collection')")
    print("  3. Add documents: store.add_documents(docs, embeddings)")
    print("  4. Query: store.query_by_embedding(query_embedding, n_results=5)")
    print("  5. Retrieve: store.get_by_ids([id1, id2])")


if __name__ == "__main__":
    main()
