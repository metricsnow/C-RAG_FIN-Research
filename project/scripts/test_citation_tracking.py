"""
Test script for Citation Tracking System (TASK-009).

Tests the citation tracking implementation:
1. Source metadata extraction from retrieved chunks
2. Citation formatting (simple string format)
3. Single source citation display
4. Multiple source citation display
5. Integration with RAG query system
"""

import time
from pathlib import Path
from typing import List, Dict, Any

from app.rag import RAGQuerySystem, RAGQueryError, create_rag_system
from app.ingestion import IngestionPipeline
from app.ui.app import format_citations


def test_citation_formatting():
    """Test 1: Citation formatting function."""
    print("\n" + "="*60)
    print("Test 1: Citation Formatting Function")
    print("="*60)
    
    # Test with single source
    sources_single = [
        {"filename": "document.pdf", "source": "/path/to/document.pdf", "type": "text"}
    ]
    citation_single = format_citations(sources_single)
    print(f"Single source: {citation_single}")
    assert citation_single == "Source: document.pdf", f"Expected 'Source: document.pdf', got '{citation_single}'"
    print("✓ Single source citation formatted correctly")
    
    # Test with multiple sources
    sources_multiple = [
        {"filename": "document1.pdf", "source": "/path/to/document1.pdf", "type": "text"},
        {"filename": "document2.txt", "source": "/path/to/document2.txt", "type": "text"},
        {"filename": "document1.pdf", "source": "/path/to/document1.pdf", "type": "text"},  # Duplicate
    ]
    citation_multiple = format_citations(sources_multiple)
    print(f"Multiple sources: {citation_multiple}")
    assert "Sources:" in citation_multiple, "Multiple sources should use 'Sources:' prefix"
    assert "document1.pdf" in citation_multiple, "Should include document1.pdf"
    assert "document2.txt" in citation_multiple, "Should include document2.txt"
    print("✓ Multiple source citation formatted correctly")
    
    # Test with empty sources
    citation_empty = format_citations([])
    print(f"Empty sources: '{citation_empty}'")
    assert citation_empty == "", "Empty sources should return empty string"
    print("✓ Empty sources handled correctly")
    
    # Test with source path (no filename field)
    sources_path = [
        {"source": "/path/to/document.pdf", "type": "text"}
    ]
    citation_path = format_citations(sources_path)
    print(f"Source from path: {citation_path}")
    assert "document.pdf" in citation_path, "Should extract filename from path"
    print("✓ Source path extraction working correctly")
    
    return True


def test_citation_with_rag_query():
    """Test 2: Citation tracking with RAG query system."""
    print("\n" + "="*60)
    print("Test 2: Citation Tracking with RAG Query")
    print("="*60)
    
    try:
        # Create test documents
        test_doc1_path = Path("data/documents/test_finance1.txt")
        test_doc2_path = Path("data/documents/test_finance2.txt")
        test_doc1_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create test document 1
        doc1_content = """
        Financial Markets Overview
        
        The stock market is a financial market where shares of publicly traded companies are bought and sold.
        Stock prices fluctuate based on supply and demand, company performance, economic indicators, and market sentiment.
        """
        
        # Create test document 2
        doc2_content = """
        Investment Strategies
        
        Investment strategies include diversification, asset allocation, and risk management.
        Diversification helps reduce portfolio risk by spreading investments across different assets.
        """
        
        with open(test_doc1_path, "w") as f:
            f.write(doc1_content)
        with open(test_doc2_path, "w") as f:
            f.write(doc2_content)
        
        # Ingest documents
        pipeline = IngestionPipeline(collection_name="test_citations")
        chunk_ids1 = pipeline.process_document(test_doc1_path)
        chunk_ids2 = pipeline.process_document(test_doc2_path)
        print(f"✓ Documents ingested: {len(chunk_ids1)} + {len(chunk_ids2)} chunks")
        
        # Query the system
        rag_system = create_rag_system(collection_name="test_citations", top_k=5)
        
        question = "What is the stock market?"
        result = rag_system.query(question)
        
        print(f"✓ Query processed: '{question}'")
        print(f"  - Answer length: {len(result['answer'])} chars")
        print(f"  - Chunks used: {result['chunks_used']}")
        print(f"  - Sources count: {len(result['sources'])}")
        
        # Validate sources are returned
        assert "sources" in result, "Result should include 'sources' field"
        assert len(result['sources']) > 0, "Should have at least one source"
        assert result['chunks_used'] == len(result['sources']), "Chunks used should match sources count"
        
        # Test citation formatting
        citation = format_citations(result['sources'])
        print(f"  - Citation: {citation}")
        assert citation.startswith("Source") or citation.startswith("Sources"), \
            "Citation should start with 'Source' or 'Sources'"
        
        # Display source metadata
        print("\n  Source metadata:")
        for i, source in enumerate(result['sources'], 1):
            print(f"    {i}. filename: {source.get('filename', 'N/A')}")
            print(f"       source: {source.get('source', 'N/A')}")
            print(f"       type: {source.get('type', 'N/A')}")
        
        print("✓ Citation tracking with RAG query working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_source_citations():
    """Test 3: Multiple source citation handling."""
    print("\n" + "="*60)
    print("Test 3: Multiple Source Citations")
    print("="*60)
    
    try:
        rag_system = create_rag_system(collection_name="test_citations", top_k=10)
        
        # Query that should retrieve chunks from multiple documents
        question = "Explain investment strategies and stock markets"
        result = rag_system.query(question, top_k=10)
        
        print(f"✓ Query processed: '{question}'")
        print(f"  - Chunks used: {result['chunks_used']}")
        print(f"  - Sources count: {len(result['sources'])}")
        
        # Get unique source filenames
        source_filenames = set()
        for source in result['sources']:
            filename = source.get("filename") or Path(source.get("source", "")).name
            if filename and filename != "unknown":
                source_filenames.add(filename)
        
        print(f"  - Unique source files: {len(source_filenames)}")
        for filename in sorted(source_filenames):
            print(f"    - {filename}")
        
        # Format citation
        citation = format_citations(result['sources'])
        print(f"  - Citation: {citation}")
        
        # Validate citation format
        if len(source_filenames) == 1:
            assert citation.startswith("Source:"), "Single source should use 'Source:' prefix"
        else:
            assert citation.startswith("Sources:"), "Multiple sources should use 'Sources:' prefix"
            # Verify all filenames are in citation
            for filename in source_filenames:
                assert filename in citation, f"Citation should include {filename}"
        
        print("✓ Multiple source citations handled correctly")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_chunk_tracking():
    """Test 4: Verify chunks used are tracked correctly."""
    print("\n" + "="*60)
    print("Test 4: Chunk Usage Tracking")
    print("="*60)
    
    try:
        rag_system = create_rag_system(collection_name="test_citations")
        
        question = "What is diversification?"
        result = rag_system.query(question, top_k=3)
        
        print(f"✓ Query processed: '{question}'")
        print(f"  - Chunks used: {result['chunks_used']}")
        print(f"  - Sources returned: {len(result['sources'])}")
        
        # Validate chunks_used matches sources
        assert result['chunks_used'] == len(result['sources']), \
            f"chunks_used ({result['chunks_used']}) should match sources count ({len(result['sources'])})"
        assert result['chunks_used'] <= 3, "Should not exceed top_k=3"
        
        # Validate each source has metadata
        for i, source in enumerate(result['sources'], 1):
            assert isinstance(source, dict), f"Source {i} should be a dictionary"
            assert "filename" in source or "source" in source, \
                f"Source {i} should have filename or source metadata"
        
        print("✓ Chunk usage tracking verified")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_citation_format_compliance():
    """Test 5: Verify citation format matches task requirements."""
    print("\n" + "="*60)
    print("Test 5: Citation Format Compliance")
    print("="*60)
    
    # Test cases matching task requirements
    test_cases = [
        {
            "name": "Single source PDF",
            "sources": [{"filename": "document.pdf", "source": "/path/to/document.pdf"}],
            "expected_pattern": "Source: document.pdf"
        },
        {
            "name": "Single source TXT",
            "sources": [{"filename": "report.txt", "source": "/path/to/report.txt"}],
            "expected_pattern": "Source: report.txt"
        },
        {
            "name": "Multiple sources",
            "sources": [
                {"filename": "doc1.pdf", "source": "/path/to/doc1.pdf"},
                {"filename": "doc2.txt", "source": "/path/to/doc2.txt"}
            ],
            "expected_pattern": "Sources:"  # Should contain this prefix
        }
    ]
    
    all_passed = True
    for test_case in test_cases:
        citation = format_citations(test_case["sources"])
        print(f"\n  {test_case['name']}:")
        print(f"    Citation: {citation}")
        print(f"    Expected pattern: {test_case['expected_pattern']}")
        
        if test_case['expected_pattern'] in citation:
            print(f"    ✓ Format matches requirements")
        else:
            print(f"    ✗ Format does not match requirements")
            all_passed = False
    
    if all_passed:
        print("\n✓ All citation formats comply with task requirements")
        return True
    else:
        print("\n✗ Some citation formats do not comply")
        return False


def main():
    """Run all citation tracking tests."""
    print("\n" + "="*60)
    print("Citation Tracking System Test Suite (TASK-009)")
    print("="*60)
    
    results = []
    
    # Test 1: Citation formatting
    results.append(test_citation_formatting())
    
    # Test 2: Citation with RAG query
    results.append(test_citation_with_rag_query())
    
    # Test 3: Multiple source citations
    results.append(test_multiple_source_citations())
    
    # Test 4: Chunk tracking
    results.append(test_chunk_tracking())
    
    # Test 5: Format compliance
    results.append(test_citation_format_compliance())
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All citation tracking tests passed!")
        print("\nCitation Tracking Implementation Status:")
        print("  ✓ Source metadata extraction from chunks")
        print("  ✓ Citation formatting (simple string)")
        print("  ✓ Single source citation display")
        print("  ✓ Multiple source citation display")
        print("  ✓ Chunk usage tracking")
        print("  ✓ Integration with RAG query system")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())

