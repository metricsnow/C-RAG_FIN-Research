#!/usr/bin/env python3
"""
Streamlit UI Integration Test Script.

Tests the Streamlit frontend integration with the RAG system.
This script validates that the UI components work correctly with the backend.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.rag import create_rag_system
from app.ui.app import initialize_rag_system, format_citations
from app.utils.config import config


def test_rag_system_initialization():
    """Test RAG system initialization (used by Streamlit)."""
    print("="*60)
    print("Test: RAG System Initialization")
    print("="*60)
    
    try:
        rag_system = create_rag_system()
        print("✓ RAG system initialized successfully")
        print(f"  Collection: {rag_system.chroma_store.collection_name}")
        print(f"  Top K: {rag_system.top_k}")
        return True
    except Exception as e:
        print(f"✗ RAG system initialization failed: {e}")
        return False


def test_citation_formatting():
    """Test citation formatting function."""
    print("\n" + "="*60)
    print("Test: Citation Formatting")
    print("="*60)
    
    # Test with single source
    sources_single = [
        {"filename": "test_document.txt", "source": "data/documents/test_document.txt"}
    ]
    citation_single = format_citations(sources_single)
    print(f"✓ Single source: {citation_single}")
    assert "test_document.txt" in citation_single
    
    # Test with multiple sources
    sources_multiple = [
        {"filename": "doc1.txt", "source": "data/documents/doc1.txt"},
        {"filename": "doc2.txt", "source": "data/documents/doc2.txt"},
    ]
    citation_multiple = format_citations(sources_multiple)
    print(f"✓ Multiple sources: {citation_multiple}")
    assert "doc1.txt" in citation_multiple and "doc2.txt" in citation_multiple
    
    # Test with empty sources
    citation_empty = format_citations([])
    print(f"✓ Empty sources: '{citation_empty}'")
    assert citation_empty == ""
    
    # Test with path-based source
    sources_path = [
        {"source": "data/documents/nested/filename.txt"}
    ]
    citation_path = format_citations(sources_path)
    print(f"✓ Path-based source: {citation_path}")
    assert "filename.txt" in citation_path
    
    print("✓ All citation formatting tests passed")
    return True


def test_query_integration():
    """Test query integration (simulating Streamlit usage)."""
    print("\n" + "="*60)
    print("Test: Query Integration")
    print("="*60)
    
    try:
        rag_system = create_rag_system()
        
        test_queries = [
            "What is the stock market?",
            "Explain investment strategies",
        ]
        
        for query in test_queries:
            start_time = time.time()
            result = rag_system.query(query)
            elapsed_time = time.time() - start_time
            
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            citation = format_citations(sources)
            
            print(f"✓ Query: {query}")
            print(f"  Answer length: {len(answer)} chars")
            print(f"  Sources: {len(sources)}")
            print(f"  Citation: {citation}")
            print(f"  Response time: {elapsed_time:.2f}s")
            
            assert len(answer) > 0, "Should generate answer"
            assert isinstance(sources, list), "Sources should be a list"
        
        print("✓ Query integration tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Query integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling in query processing."""
    print("\n" + "="*60)
    print("Test: Error Handling")
    print("="*60)
    
    try:
        rag_system = create_rag_system()
        
        # Test empty query (should be handled gracefully)
        try:
            result = rag_system.query("")
            print("✗ Empty query should raise error")
            return False
        except Exception:
            print("✓ Empty query correctly raises error")
        
        # Test with valid query that might have no results
        # This should handle gracefully without crashing
        result = rag_system.query("xyzabc123nonexistent")
        assert "answer" in result, "Should return result dictionary"
        print("✓ Query with potentially no results handled gracefully")
        
        print("✓ Error handling tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def main():
    """Run all Streamlit integration tests."""
    print("\n" + "="*60)
    print("Streamlit UI Integration Test Suite")
    print("="*60)
    
    results = []
    
    results.append(test_rag_system_initialization())
    results.append(test_citation_formatting())
    results.append(test_query_integration())
    results.append(test_error_handling())
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All Streamlit integration tests passed!")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

