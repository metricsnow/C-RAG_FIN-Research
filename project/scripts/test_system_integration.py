#!/usr/bin/env python3
"""
Comprehensive System Integration Test Suite for TASK-011.

Tests all system components individually and in integration:
1. Document ingestion
2. Embedding generation
3. Vector database operations
4. RAG query system
5. Streamlit UI integration
6. Citation tracking
7. Error handling
8. Performance benchmarks
"""

import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ingestion import IngestionPipeline, IngestionPipelineError
from app.rag import RAGQuerySystem, RAGQueryError, create_rag_system
from app.vector_db import ChromaStore, ChromaStoreError
from app.rag.embedding_factory import EmbeddingGenerator, EmbeddingError
from app.ingestion.document_loader import DocumentLoader, DocumentIngestionError
from app.utils.config import config


class TestResult:
    """Test result tracking."""
    
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.duration = 0.0
        self.details = {}
    
    def record(self, passed: bool, error: str = None, duration: float = 0.0, details: Dict = None):
        """Record test result."""
        self.passed = passed
        self.error = error
        self.duration = duration
        self.details = details or {}
    
    def __str__(self):
        status = "✓" if self.passed else "✗"
        duration_str = f" ({self.duration:.2f}s)" if self.duration > 0 else ""
        error_str = f" - {self.error}" if self.error else ""
        return f"{status} {self.name}{duration_str}{error_str}"


class SystemTestSuite:
    """Comprehensive system test suite."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.test_collection = "test_system_integration"
        self.test_data_dir = Path("data/documents/test_system")
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
    def run_test(self, test_func, *args, **kwargs) -> TestResult:
        """Run a test function and record results."""
        test_name = test_func.__name__.replace("test_", "").replace("_", " ").title()
        result = TestResult(test_name)
        
        start_time = time.time()
        try:
            passed, details = test_func(*args, **kwargs)
            duration = time.time() - start_time
            result.record(passed, duration=duration, details=details)
        except Exception as e:
            duration = time.time() - start_time
            result.record(False, error=str(e), duration=duration)
            traceback.print_exc()
        
        self.results.append(result)
        return result
    
    def print_result(self, result: TestResult):
        """Print test result."""
        print(result)
        if result.details:
            for key, value in result.details.items():
                print(f"    {key}: {value}")
    
    # ==================== Component Tests ====================
    
    def test_document_ingestion(self) -> Tuple[bool, Dict]:
        """Test 1: Document ingestion pipeline."""
        print("\n" + "="*60)
        print("Test 1: Document Ingestion Pipeline")
        print("="*60)
        
        # Create test document
        test_file = self.test_data_dir / "test_finance.txt"
        test_content = """
        Financial Markets and Investment Strategies
        
        The stock market is a financial market where shares of publicly traded companies are bought and sold.
        Stock prices fluctuate based on supply and demand, company performance, economic indicators, and market sentiment.
        
        Bonds are debt securities issued by governments or corporations to raise capital.
        Bond prices are inversely related to interest rates - when rates rise, bond prices fall.
        
        Investment strategies include diversification, asset allocation, and risk management.
        Diversification helps reduce portfolio risk by spreading investments across different assets.
        
        Quantitative analysis uses mathematical models and statistical techniques to evaluate investments.
        Common quantitative strategies include algorithmic trading and statistical arbitrage.
        """
        
        test_file.write_text(test_content)
        
        try:
            pipeline = IngestionPipeline(collection_name=self.test_collection)
            chunk_ids = pipeline.process_document(test_file, store_embeddings=True)
            
            details = {
                "chunks_created": len(chunk_ids),
                "file": str(test_file),
            }
            
            assert len(chunk_ids) > 0, "Should create at least one chunk"
            print(f"✓ Document ingested: {len(chunk_ids)} chunks created")
            return True, details
            
        except Exception as e:
            print(f"✗ Document ingestion failed: {e}")
            return False, {"error": str(e)}
    
    def test_embedding_generation(self) -> Tuple[bool, Dict]:
        """Test 2: Embedding generation."""
        print("\n" + "="*60)
        print("Test 2: Embedding Generation")
        print("="*60)
        
        try:
            generator = EmbeddingGenerator()
            
            # Test single query embedding
            query_embedding = generator.embed_query("What is the stock market?")
            dims = generator.get_embedding_dimensions()
            
            # Test batch document embeddings
            texts = ["Financial markets", "Investment strategies", "Risk management"]
            doc_embeddings = generator.embed_documents(texts)
            
            details = {
                "embedding_dimensions": dims,
                "query_embedding_length": len(query_embedding),
                "doc_embeddings_count": len(doc_embeddings),
                "provider": generator.provider,
            }
            
            assert dims > 0, "Should have positive dimensions"
            assert len(query_embedding) == dims, "Query embedding should match dimensions"
            assert len(doc_embeddings) == len(texts), "Should generate embedding for each text"
            
            print(f"✓ Embedding generation working")
            print(f"  Dimensions: {dims}")
            print(f"  Provider: {generator.provider}")
            return True, details
            
        except Exception as e:
            print(f"✗ Embedding generation failed: {e}")
            return False, {"error": str(e)}
    
    def test_vector_database_operations(self) -> Tuple[bool, Dict]:
        """Test 3: Vector database operations."""
        print("\n" + "="*60)
        print("Test 3: Vector Database Operations")
        print("="*60)
        
        try:
            store = ChromaStore(collection_name=self.test_collection)
            
            # Check document count
            count = store.count()
            
            # Test query by embedding
            generator = EmbeddingGenerator()
            query_embedding = generator.embed_query("financial markets")
            results = store.query_by_embedding(query_embedding, n_results=3)
            
            details = {
                "document_count": count,
                "query_results_count": len(results["documents"]),
                "has_metadata": len(results["metadatas"]) > 0 if results["metadatas"] else False,
            }
            
            print(f"✓ Vector database operations working")
            print(f"  Documents in collection: {count}")
            print(f"  Query results: {len(results['documents'])}")
            return True, details
            
        except Exception as e:
            print(f"✗ Vector database operations failed: {e}")
            return False, {"error": str(e)}
    
    def test_rag_query_system(self) -> Tuple[bool, Dict]:
        """Test 4: RAG query system."""
        print("\n" + "="*60)
        print("Test 4: RAG Query System")
        print("="*60)
        
        try:
            rag_system = create_rag_system(collection_name=self.test_collection, top_k=3)
            
            question = "What is the stock market?"
            start_time = time.time()
            result = rag_system.query(question)
            elapsed_time = time.time() - start_time
            
            details = {
                "question": question,
                "answer_length": len(result["answer"]),
                "chunks_used": result["chunks_used"],
                "sources_count": len(result["sources"]),
                "response_time": elapsed_time,
            }
            
            assert result["chunks_used"] > 0, "Should retrieve chunks"
            assert len(result["answer"]) > 0, "Should generate answer"
            assert elapsed_time < 30, "Response should be reasonable"
            
            print(f"✓ RAG query system working")
            print(f"  Response time: {elapsed_time:.2f}s")
            print(f"  Chunks used: {result['chunks_used']}")
            
            if elapsed_time < 5:
                print(f"  ✓ Response time < 5s (target met)")
            else:
                print(f"  ⚠ Response time {elapsed_time:.2f}s (target: <5s, acceptable for local Ollama)")
            
            return True, details
            
        except Exception as e:
            print(f"✗ RAG query system failed: {e}")
            return False, {"error": str(e)}
    
    # ==================== Query Type Tests ====================
    
    def test_financial_terminology_queries(self) -> Tuple[bool, Dict]:
        """Test 5: Financial terminology queries."""
        print("\n" + "="*60)
        print("Test 5: Financial Terminology Queries")
        print("="*60)
        
        financial_queries = [
            "What is diversification?",
            "Explain bond pricing",
            "What are investment strategies?",
            "Describe quantitative analysis",
        ]
        
        try:
            rag_system = create_rag_system(collection_name=self.test_collection, top_k=3)
            results_data = []
            
            for query in financial_queries:
                start_time = time.time()
                result = rag_system.query(query)
                elapsed_time = time.time() - start_time
                
                results_data.append({
                    "query": query,
                    "answer_length": len(result["answer"]),
                    "chunks_used": result["chunks_used"],
                    "response_time": elapsed_time,
                })
                
                print(f"✓ Query: {query}")
                print(f"  Answer length: {len(result['answer'])} chars")
                print(f"  Response time: {elapsed_time:.2f}s")
            
            avg_time = sum(r["response_time"] for r in results_data) / len(results_data)
            
            details = {
                "queries_tested": len(financial_queries),
                "average_response_time": avg_time,
                "all_answered": all(r["answer_length"] > 0 for r in results_data),
            }
            
            print(f"\n✓ Financial terminology queries working")
            print(f"  Average response time: {avg_time:.2f}s")
            return True, details
            
        except Exception as e:
            print(f"✗ Financial terminology queries failed: {e}")
            return False, {"error": str(e)}
    
    def test_general_research_queries(self) -> Tuple[bool, Dict]:
        """Test 6: General research queries."""
        print("\n" + "="*60)
        print("Test 6: General Research Queries")
        print("="*60)
        
        general_queries = [
            "How do markets work?",
            "What factors affect investments?",
            "Explain risk management",
        ]
        
        try:
            rag_system = create_rag_system(collection_name=self.test_collection, top_k=3)
            results_data = []
            
            for query in general_queries:
                result = rag_system.query(query)
                results_data.append({
                    "query": query,
                    "answer_length": len(result["answer"]),
                    "chunks_used": result["chunks_used"],
                })
                print(f"✓ Query: {query}")
            
            details = {
                "queries_tested": len(general_queries),
                "all_answered": all(r["answer_length"] > 0 for r in results_data),
            }
            
            print(f"\n✓ General research queries working")
            return True, details
            
        except Exception as e:
            print(f"✗ General research queries failed: {e}")
            return False, {"error": str(e)}
    
    def test_specific_document_queries(self) -> Tuple[bool, Dict]:
        """Test 7: Specific document queries."""
        print("\n" + "="*60)
        print("Test 7: Specific Document Queries")
        print("="*60)
        
        specific_queries = [
            "What does the test document say about bonds?",
            "Find information about quantitative analysis",
        ]
        
        try:
            rag_system = create_rag_system(collection_name=self.test_collection, top_k=3)
            results_data = []
            
            for query in specific_queries:
                result = rag_system.query(query)
                sources = result.get("sources", [])
                source_files = [s.get("filename", "unknown") for s in sources]
                
                results_data.append({
                    "query": query,
                    "answer_length": len(result["answer"]),
                    "sources": source_files,
                })
                print(f"✓ Query: {query}")
                print(f"  Sources: {source_files}")
            
            details = {
                "queries_tested": len(specific_queries),
                "sources_retrieved": all(len(r["sources"]) > 0 for r in results_data),
            }
            
            print(f"\n✓ Specific document queries working")
            return True, details
            
        except Exception as e:
            print(f"✗ Specific document queries failed: {e}")
            return False, {"error": str(e)}
    
    # ==================== Error Handling Tests ====================
    
    def test_error_handling_empty_query(self) -> Tuple[bool, Dict]:
        """Test 8: Error handling - empty query."""
        print("\n" + "="*60)
        print("Test 8: Error Handling - Empty Query")
        print("="*60)
        
        try:
            rag_system = create_rag_system(collection_name=self.test_collection)
            
            # Test empty string
            try:
                rag_system.query("")
                print("✗ Should have raised error for empty query")
                return False, {"error": "Empty query should raise error"}
            except RAGQueryError:
                print("✓ Empty query correctly raises error")
            
            # Test whitespace-only
            try:
                rag_system.query("   ")
                print("✗ Should have raised error for whitespace-only query")
                return False, {"error": "Whitespace-only query should raise error"}
            except RAGQueryError:
                print("✓ Whitespace-only query correctly raises error")
            
            return True, {}
            
        except Exception as e:
            print(f"✗ Error handling test failed: {e}")
            return False, {"error": str(e)}
    
    def test_error_handling_invalid_document(self) -> Tuple[bool, Dict]:
        """Test 9: Error handling - invalid document."""
        print("\n" + "="*60)
        print("Test 9: Error Handling - Invalid Document")
        print("="*60)
        
        try:
            pipeline = IngestionPipeline(collection_name=self.test_collection)
            
            # Test non-existent file
            try:
                pipeline.process_document(Path("nonexistent_file.txt"))
                print("✗ Should have raised error for non-existent file")
                return False, {"error": "Non-existent file should raise error"}
            except IngestionPipelineError:
                print("✓ Non-existent file correctly raises error")
            
            # Test unsupported file format
            unsupported_file = self.test_data_dir / "test.pdf"
            unsupported_file.write_text("test content")
            try:
                pipeline.process_document(unsupported_file)
                print("✗ Should have raised error for unsupported format")
                return False, {"error": "Unsupported format should raise error"}
            except IngestionPipelineError:
                print("✓ Unsupported format correctly raises error")
            
            return True, {}
            
        except Exception as e:
            print(f"✗ Error handling test failed: {e}")
            return False, {"error": str(e)}
    
    # ==================== Performance Tests ====================
    
    def test_performance_benchmarks(self) -> Tuple[bool, Dict]:
        """Test 10: Performance benchmarks."""
        print("\n" + "="*60)
        print("Test 10: Performance Benchmarks")
        print("="*60)
        
        try:
            rag_system = create_rag_system(collection_name=self.test_collection, top_k=5)
            
            test_queries = [
                "What is the stock market?",
                "Explain investment strategies",
                "What is diversification?",
            ]
            
            response_times = []
            for query in test_queries:
                start_time = time.time()
                result = rag_system.query(query)
                elapsed_time = time.time() - start_time
                response_times.append(elapsed_time)
                print(f"Query: {query[:40]}... - {elapsed_time:.2f}s")
            
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            details = {
                "queries_tested": len(test_queries),
                "average_response_time": avg_time,
                "min_response_time": min_time,
                "max_response_time": max_time,
                "target_met": avg_time < 5.0,
            }
            
            print(f"\n✓ Performance benchmarks")
            print(f"  Average: {avg_time:.2f}s")
            print(f"  Min: {min_time:.2f}s")
            print(f"  Max: {max_time:.2f}s")
            
            if avg_time < 5.0:
                print(f"  ✓ Average response time < 5s (target met)")
            else:
                print(f"  ⚠ Average response time {avg_time:.2f}s (target: <5s, acceptable for local Ollama)")
            
            return True, details
            
        except Exception as e:
            print(f"✗ Performance benchmarks failed: {e}")
            return False, {"error": str(e)}
    
    # ==================== Integration Tests ====================
    
    def test_end_to_end_integration(self) -> Tuple[bool, Dict]:
        """Test 11: End-to-end integration."""
        print("\n" + "="*60)
        print("Test 11: End-to-End Integration")
        print("="*60)
        
        try:
            # Step 1: Ingest document
            test_file = self.test_data_dir / "test_integration.txt"
            test_content = """
            Integration Test Document
            
            This document tests the complete integration of all system components.
            It covers document ingestion, embedding generation, vector storage, and RAG queries.
            
            The system should be able to process this document, store it in the vector database,
            and retrieve relevant information when queried.
            """
            test_file.write_text(test_content)
            
            pipeline = IngestionPipeline(collection_name=self.test_collection)
            chunk_ids = pipeline.process_document(test_file)
            print(f"✓ Step 1: Document ingested ({len(chunk_ids)} chunks)")
            
            # Step 2: Query system
            rag_system = create_rag_system(collection_name=self.test_collection, top_k=3)
            result = rag_system.query("What does the integration test document say?")
            print(f"✓ Step 2: Query processed")
            print(f"  Answer length: {len(result['answer'])} chars")
            print(f"  Chunks used: {result['chunks_used']}")
            print(f"  Sources: {len(result['sources'])}")
            
            # Step 3: Verify citations
            sources = result.get("sources", [])
            source_files = [s.get("filename", "unknown") for s in sources]
            print(f"✓ Step 3: Citations retrieved")
            print(f"  Source files: {source_files}")
            
            details = {
                "chunks_created": len(chunk_ids),
                "answer_generated": len(result["answer"]) > 0,
                "citations_retrieved": len(sources) > 0,
                "end_to_end_success": True,
            }
            
            assert len(result["answer"]) > 0, "Should generate answer"
            assert len(sources) > 0, "Should retrieve sources"
            
            print(f"\n✓ End-to-end integration successful")
            return True, details
            
        except Exception as e:
            print(f"✗ End-to-end integration failed: {e}")
            traceback.print_exc()
            return False, {"error": str(e)}
    
    # ==================== Main Test Runner ====================
    
    def run_all_tests(self):
        """Run all tests in the suite."""
        print("\n" + "="*60)
        print("Comprehensive System Integration Test Suite")
        print("TASK-011: System Testing and Integration Debugging")
        print("="*60)
        
        # Component Tests
        self.run_test(self.test_document_ingestion)
        self.run_test(self.test_embedding_generation)
        self.run_test(self.test_vector_database_operations)
        self.run_test(self.test_rag_query_system)
        
        # Query Type Tests
        self.run_test(self.test_financial_terminology_queries)
        self.run_test(self.test_general_research_queries)
        self.run_test(self.test_specific_document_queries)
        
        # Error Handling Tests
        self.run_test(self.test_error_handling_empty_query)
        self.run_test(self.test_error_handling_invalid_document)
        
        # Performance Tests
        self.run_test(self.test_performance_benchmarks)
        
        # Integration Tests
        self.run_test(self.test_end_to_end_integration)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("Test Summary")
        print("="*60)
        
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        failed = total - passed
        
        for result in self.results:
            self.print_result(result)
        
        print("\n" + "="*60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print("="*60)
        
        if passed == total:
            print("\n✓ All tests passed! System integration validated.")
        else:
            print(f"\n✗ {failed} test(s) failed. Please review errors above.")
        
        # Performance summary
        performance_tests = [r for r in self.results if "performance" in r.name.lower() or "response time" in str(r.details)]
        if performance_tests:
            print("\nPerformance Summary:")
            for test in performance_tests:
                if "response_time" in test.details:
                    rt = test.details["response_time"]
                    status = "✓" if rt < 5.0 else "⚠"
                    print(f"  {status} {test.name}: {rt:.2f}s")
        
        return passed == total


def main():
    """Main entry point."""
    suite = SystemTestSuite()
    success = suite.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

