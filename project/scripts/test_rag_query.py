"""
Test script for RAG Query System (TASK-007).

Tests the complete RAG query pipeline:
1. Query embedding generation
2. Vector similarity search in ChromaDB
3. Context retrieval (top-k chunks)
4. Prompt construction with context
5. LLM answer generation (Ollama)
"""

import time
from pathlib import Path

from app.rag import RAGQuerySystem, RAGQueryError, create_rag_system
from app.ingestion import IngestionPipeline
from app.utils.config import config


def test_rag_initialization():
    """Test 1: RAG system initialization."""
    print("\n" + "="*60)
    print("Test 1: RAG System Initialization")
    print("="*60)
    
    try:
        rag_system = create_rag_system(top_k=5)
        print("✓ RAG system initialized successfully")
        print(f"  - Top K: {rag_system.top_k}")
        print(f"  - Collection: {rag_system.chroma_store.collection_name}")
        return rag_system
    except Exception as e:
        print(f"✗ RAG system initialization failed: {str(e)}")
        return None


def test_query_with_no_documents():
    """Test 2: Query with no documents in database."""
    print("\n" + "="*60)
    print("Test 2: Query with No Documents")
    print("="*60)
    
    try:
        rag_system = create_rag_system(collection_name="test_empty")
        
        result = rag_system.query("What is the stock market?")
        
        print(f"✓ Query processed successfully")
        print(f"  - Answer: {result['answer'][:100]}...")
        print(f"  - Chunks used: {result['chunks_used']}")
        print(f"  - Sources: {len(result['sources'])}")
        
        # Should handle gracefully
        assert result['chunks_used'] == 0, "Should have 0 chunks when database is empty"
        assert "couldn't find" in result['answer'].lower() or "no relevant" in result['answer'].lower(), \
            "Should indicate no documents found"
        print("✓ Graceful handling of empty database confirmed")
        return True
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False


def test_query_with_documents():
    """Test 3: Query with documents in database."""
    print("\n" + "="*60)
    print("Test 3: Query with Documents")
    print("="*60)
    
    try:
        # First, ingest a test document
        test_doc_path = Path("data/documents/test_financial.txt")
        test_doc_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a simple test document
        test_content = """
        Financial Markets Overview
        
        The stock market is a financial market where shares of publicly traded companies are bought and sold.
        Stock prices fluctuate based on supply and demand, company performance, economic indicators, and market sentiment.
        
        Bonds are debt securities issued by governments or corporations to raise capital.
        Bond prices are inversely related to interest rates - when rates rise, bond prices fall.
        
        Investment strategies include diversification, asset allocation, and risk management.
        Diversification helps reduce portfolio risk by spreading investments across different assets.
        """
        
        with open(test_doc_path, "w") as f:
            f.write(test_content)
        
        # Ingest document
        pipeline = IngestionPipeline(collection_name="test_rag")
        chunk_ids = pipeline.process_document(test_doc_path)
        print(f"✓ Test document ingested: {len(chunk_ids)} chunks")
        
        # Query the system
        rag_system = create_rag_system(collection_name="test_rag", top_k=3)
        
        question = "What is the stock market?"
        start_time = time.time()
        result = rag_system.query(question)
        elapsed_time = time.time() - start_time
        
        print(f"✓ Query processed successfully")
        print(f"  - Question: {question}")
        print(f"  - Answer: {result['answer'][:200]}...")
        print(f"  - Chunks used: {result['chunks_used']}")
        print(f"  - Response time: {elapsed_time:.2f} seconds")
        print(f"  - Sources: {len(result['sources'])}")
        
        # Validate results
        assert result['chunks_used'] > 0, "Should have retrieved chunks"
        assert len(result['answer']) > 0, "Should have generated an answer"
        assert result['chunks_used'] <= 3, "Should not exceed top_k"
        assert elapsed_time < 30, "Response should be reasonable (under 30s)"
        
        if elapsed_time < 5:
            print("✓ Response time < 5 seconds (target met)")
        else:
            print(f"⚠ Response time {elapsed_time:.2f}s (target: <5s, acceptable for local Ollama)")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_top_k_variation():
    """Test 4: Test different top_k values."""
    print("\n" + "="*60)
    print("Test 4: Top-K Variation")
    print("="*60)
    
    try:
        rag_system = create_rag_system(collection_name="test_rag", top_k=5)
        
        question = "What are investment strategies?"
        
        # Test with default top_k
        result1 = rag_system.query(question, top_k=None)
        print(f"✓ Query with default top_k ({rag_system.top_k}): {result1['chunks_used']} chunks")
        
        # Test with custom top_k
        result2 = rag_system.query(question, top_k=2)
        print(f"✓ Query with top_k=2: {result2['chunks_used']} chunks")
        
        result3 = rag_system.query(question, top_k=10)
        print(f"✓ Query with top_k=10: {result3['chunks_used']} chunks")
        
        # Validate
        assert result2['chunks_used'] <= 2, "Should respect top_k=2"
        assert result3['chunks_used'] <= 10, "Should respect top_k=10"
        print("✓ Top-k parameter working correctly")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False


def test_error_handling():
    """Test 5: Error handling."""
    print("\n" + "="*60)
    print("Test 5: Error Handling")
    print("="*60)
    
    try:
        rag_system = create_rag_system()
        
        # Test empty question
        try:
            rag_system.query("")
            print("✗ Should have raised error for empty question")
            return False
        except RAGQueryError:
            print("✓ Empty question correctly raises error")
        
        # Test whitespace-only question
        try:
            rag_system.query("   ")
            print("✗ Should have raised error for whitespace-only question")
            return False
        except RAGQueryError:
            print("✓ Whitespace-only question correctly raises error")
        
        print("✓ Error handling working correctly")
        return True
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False


def test_query_simple():
    """Test 6: Simple query interface."""
    print("\n" + "="*60)
    print("Test 6: Simple Query Interface")
    print("="*60)
    
    try:
        rag_system = create_rag_system(collection_name="test_rag")
        
        question = "What is diversification?"
        answer = rag_system.query_simple(question)
        
        print(f"✓ Simple query processed")
        print(f"  - Question: {question}")
        print(f"  - Answer: {answer[:200]}...")
        
        assert len(answer) > 0, "Should return an answer"
        assert isinstance(answer, str), "Should return a string"
        print("✓ Simple query interface working correctly")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False


def test_multiple_queries():
    """Test 7: Multiple queries with different topics."""
    print("\n" + "="*60)
    print("Test 7: Multiple Queries")
    print("="*60)
    
    try:
        rag_system = create_rag_system(collection_name="test_rag")
        
        questions = [
            "What is the stock market?",
            "Explain bonds",
            "What are investment strategies?",
        ]
        
        for i, question in enumerate(questions, 1):
            start_time = time.time()
            result = rag_system.query(question)
            elapsed_time = time.time() - start_time
            
            print(f"✓ Query {i}: {question}")
            print(f"  - Answer length: {len(result['answer'])} chars")
            print(f"  - Chunks: {result['chunks_used']}")
            print(f"  - Time: {elapsed_time:.2f}s")
            
            assert result['chunks_used'] > 0, f"Query {i} should retrieve chunks"
            assert len(result['answer']) > 0, f"Query {i} should generate answer"
        
        print("✓ Multiple queries processed successfully")
        return True
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("RAG Query System Test Suite (TASK-007)")
    print("="*60)
    
    results = []
    
    # Test 1: Initialization
    rag_system = test_rag_initialization()
    results.append(rag_system is not None)
    
    # Test 2: Empty database
    results.append(test_query_with_no_documents())
    
    # Test 3: Query with documents (requires ingestion)
    results.append(test_query_with_documents())
    
    # Test 4: Top-k variation
    results.append(test_top_k_variation())
    
    # Test 5: Error handling
    results.append(test_error_handling())
    
    # Test 6: Simple query
    results.append(test_query_simple())
    
    # Test 7: Multiple queries
    results.append(test_multiple_queries())
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())

