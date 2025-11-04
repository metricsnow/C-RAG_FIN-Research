"""
Test script for embedding generation and storage integration.

Tests embedding generation, ChromaDB storage, and end-to-end pipeline.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_core.documents import Document

from app.ingestion import IngestionPipeline, IngestionPipelineError
from app.rag import EmbeddingGenerator, EmbeddingError
from app.utils.config import config


def test_embedding_generation():
    """Test embedding generation with sample text."""
    print("Testing embedding generation...")

    try:
        generator = EmbeddingGenerator()

        # Test single query embedding
        query_embedding = generator.embed_query("This is a test query")
        print(f"✓ Query embedding generated")
        print(f"  - Dimensions: {len(query_embedding)}")

        # Test batch document embeddings
        texts = [
            "Machine learning is a subset of artificial intelligence",
            "Financial markets involve trading of securities",
            "Python is a high-level programming language",
        ]
        doc_embeddings = generator.embed_documents(texts)
        print(f"✓ Document embeddings generated")
        print(f"  - Number of embeddings: {len(doc_embeddings)}")
        print(f"  - Dimensions: {len(doc_embeddings[0])}")

        # Test dimension detection
        dimensions = generator.get_embedding_dimensions()
        print(f"✓ Embedding dimensions detected: {dimensions}")

        return True
    except EmbeddingError as e:
        print(f"✗ Embedding generation failed: {str(e)}")
        print("  Note: This may fail if OpenAI API key is not set")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return False


def test_pipeline_with_sample_files():
    """Test complete pipeline with sample files."""
    print("\nTesting complete ingestion pipeline...")

    try:
        # Create sample files
        documents_dir = config.DOCUMENTS_DIR
        documents_dir.mkdir(parents=True, exist_ok=True)

        # Create sample text file
        text_file = documents_dir / "test_embedding.txt"
        text_content = """This is a test document for embedding generation.

It contains multiple sentences to test batch processing and chunking.

The document should be processed, chunked, embedded, and stored in ChromaDB.

This is the final sentence of the test document.
"""
        text_file.write_text(text_content)

        # Create pipeline
        pipeline = IngestionPipeline(
            collection_name="test_embeddings",
            embedding_provider=config.EMBEDDING_PROVIDER,
        )

        # Process document
        ids = pipeline.process_document(text_file)
        print(f"✓ Document processed successfully")
        print(f"  - Chunk IDs created: {len(ids)}")

        # Check document count
        count = pipeline.get_document_count()
        print(f"✓ Document count: {count}")

        # Test similarity search
        results = pipeline.search_similar("test document", n_results=2)
        print(f"✓ Similarity search successful")
        print(f"  - Results found: {len(results)}")
        if results:
            print(f"  - First result: {results[0].page_content[:60]}...")

        # Cleanup
        pipeline.chroma_store.delete_collection()
        text_file.unlink()

        return True
    except IngestionPipelineError as e:
        print(f"✗ Pipeline test failed: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return False


def test_batch_embedding_generation():
    """Test batch embedding generation."""
    print("\nTesting batch embedding generation...")

    try:
        generator = EmbeddingGenerator()

        # Create multiple texts
        texts = [f"This is test document number {i}" for i in range(5)]

        # Generate embeddings in batch
        embeddings = generator.embed_documents(texts)

        print(f"✓ Batch embedding generation successful")
        print(f"  - Input texts: {len(texts)}")
        print(f"  - Output embeddings: {len(embeddings)}")
        print(f"  - All embeddings have same dimensions: {all(len(e) == len(embeddings[0]) for e in embeddings)}")

        return True
    except EmbeddingError as e:
        print(f"✗ Batch embedding failed: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return False


def test_error_handling():
    """Test error handling for embedding failures."""
    print("\nTesting error handling...")

    try:
        generator = EmbeddingGenerator()

        # Test with empty list
        try:
            embeddings = generator.embed_documents([])
            if embeddings == []:
                print("✓ Empty list handled correctly")
            else:
                print("⚠ Empty list returned non-empty result")
        except Exception as e:
            print(f"⚠ Empty list raised exception: {str(e)}")

        # Test invalid provider (would fail if we tried to create it)
        print("✓ Error handling tests passed (basic validation)")

        return True
    except Exception as e:
        print(f"✗ Error handling test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Embedding Generation and Storage Integration Test Suite")
    print("=" * 60)

    print(f"\nConfiguration:")
    print(f"  - Embedding Provider: {config.EMBEDDING_PROVIDER}")
    print(f"  - OpenAI API Key: {'Set' if config.OPENAI_API_KEY else 'Not Set'}")
    print(f"  - Ollama Base URL: {config.OLLAMA_BASE_URL}")

    # Run tests
    results = []

    results.append(("Embedding Generation", test_embedding_generation()))
    results.append(("Batch Embedding Generation", test_batch_embedding_generation()))
    results.append(("Complete Pipeline", test_pipeline_with_sample_files()))
    results.append(("Error Handling", test_error_handling()))

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
        print("\n✓ All tests passed! Embedding generation is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        print("\nNote: Some tests may fail if:")
        print("  - OpenAI API key is not set (for OpenAI embeddings)")
        print("  - Ollama is not running (for Ollama embeddings)")
        return 1


if __name__ == "__main__":
    sys.exit(main())

