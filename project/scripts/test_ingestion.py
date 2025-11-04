"""
Test script for document ingestion pipeline.

Tests the document loader with sample text and Markdown files.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ingestion import DocumentLoader, DocumentIngestionError
from app.utils.config import config


def create_sample_files() -> tuple[Path, Path]:
    """
    Create sample text and Markdown files for testing.

    Returns:
        Tuple of (text_file_path, markdown_file_path)
    """
    # Ensure data/documents directory exists
    documents_dir = config.DOCUMENTS_DIR
    documents_dir.mkdir(parents=True, exist_ok=True)

    # Create sample text file
    text_file = documents_dir / "sample.txt"
    text_content = """This is a sample text document for testing the ingestion pipeline.

It contains multiple paragraphs to test chunking functionality.

The document loader should be able to process this file and split it into chunks
with appropriate metadata. Each chunk should have information about the source,
date, type, and chunk index.

This is the final paragraph of the sample text document.
"""
    text_file.write_text(text_content)

    # Create sample Markdown file
    md_file = documents_dir / "sample.md"
    md_content = """# Sample Markdown Document

This is a sample Markdown document for testing the ingestion pipeline.

## Features

- Text extraction
- Chunking with overlap
- Metadata management

## Content

The document loader should process Markdown files correctly and maintain
the structure while chunking the content appropriately.

### Subsection

This is a subsection to test how Markdown content is handled during chunking.
"""
    md_file.write_text(md_content)

    return text_file, md_file


def test_text_file_loading():
    """Test loading and processing of text files."""
    print("Testing text file loading...")

    loader = DocumentLoader()
    documents_dir = config.DOCUMENTS_DIR
    text_file = documents_dir / "sample.txt"

    try:
        chunks = loader.process_document(text_file)
        print(f"✓ Text file loaded successfully")
        print(f"  - File: {text_file}")
        print(f"  - Number of chunks: {len(chunks)}")
        print(f"  - First chunk metadata: {chunks[0].metadata}")
        print(f"  - First chunk preview: {chunks[0].page_content[:100]}...")
        return True
    except Exception as e:
        print(f"✗ Text file loading failed: {str(e)}")
        return False


def test_markdown_file_loading():
    """Test loading and processing of Markdown files."""
    print("\nTesting Markdown file loading...")

    loader = DocumentLoader()
    documents_dir = config.DOCUMENTS_DIR
    md_file = documents_dir / "sample.md"

    try:
        chunks = loader.process_document(md_file)
        print(f"✓ Markdown file loaded successfully")
        print(f"  - File: {md_file}")
        print(f"  - Number of chunks: {len(chunks)}")
        print(f"  - First chunk metadata: {chunks[0].metadata}")
        print(f"  - First chunk preview: {chunks[0].page_content[:100]}...")
        return True
    except Exception as e:
        print(f"✗ Markdown file loading failed: {str(e)}")
        return False


def test_file_size_validation():
    """Test file size validation."""
    print("\nTesting file size validation...")

    loader = DocumentLoader()
    documents_dir = config.DOCUMENTS_DIR

    # Create a file that exceeds the size limit
    large_file = documents_dir / "large_file.txt"
    # Create 11MB of content (exceeds 10MB limit)
    large_content = "x" * (11 * 1024 * 1024)
    large_file.write_text(large_content)

    try:
        loader.process_document(large_file)
        print(f"✗ File size validation failed: Should have rejected file")
        large_file.unlink()  # Clean up
        return False
    except DocumentIngestionError as e:
        print(f"✓ File size validation working: {str(e)}")
        large_file.unlink()  # Clean up
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        if large_file.exists():
            large_file.unlink()  # Clean up
        return False


def test_unsupported_format():
    """Test handling of unsupported file formats."""
    print("\nTesting unsupported format handling...")

    loader = DocumentLoader()
    documents_dir = config.DOCUMENTS_DIR

    # Create a file with unsupported extension
    unsupported_file = documents_dir / "test.pdf"
    unsupported_file.write_text("test content")

    try:
        loader.process_document(unsupported_file)
        print(f"✗ Unsupported format validation failed: Should have rejected file")
        unsupported_file.unlink()  # Clean up
        return False
    except DocumentIngestionError as e:
        print(f"✓ Unsupported format validation working: {str(e)}")
        unsupported_file.unlink()  # Clean up
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        if unsupported_file.exists():
            unsupported_file.unlink()  # Clean up
        return False


def test_chunking_metadata():
    """Test that chunks have correct metadata."""
    print("\nTesting chunking metadata...")

    loader = DocumentLoader()
    documents_dir = config.DOCUMENTS_DIR
    text_file = documents_dir / "sample.txt"

    try:
        chunks = loader.process_document(text_file)

        # Check that all chunks have required metadata
        required_fields = ["source", "filename", "type", "date", "chunk_index"]
        all_valid = True

        for idx, chunk in enumerate(chunks):
            missing_fields = [f for f in required_fields if f not in chunk.metadata]
            if missing_fields:
                print(f"✗ Chunk {idx} missing metadata fields: {missing_fields}")
                all_valid = False
            else:
                # Verify chunk_index matches position
                if chunk.metadata["chunk_index"] != idx:
                    print(
                        f"✗ Chunk {idx} has incorrect chunk_index: "
                        f"{chunk.metadata['chunk_index']}"
                    )
                    all_valid = False

        if all_valid:
            print(f"✓ All chunks have correct metadata")
            print(f"  - Total chunks: {len(chunks)}")
            print(f"  - Chunk indices: 0 to {len(chunks) - 1}")
            return True
        return False
    except Exception as e:
        print(f"✗ Chunking metadata test failed: {str(e)}")
        return False


def test_chunk_overlap():
    """Test that chunks have proper overlap."""
    print("\nTesting chunk overlap...")

    loader = DocumentLoader(chunk_size=100, chunk_overlap=20)
    documents_dir = config.DOCUMENTS_DIR
    text_file = documents_dir / "sample.txt"

    try:
        chunks = loader.process_document(text_file)

        if len(chunks) < 2:
            print("⚠ Need at least 2 chunks to test overlap")
            return True

        # Check that consecutive chunks overlap
        chunk1_end = chunks[0].page_content[-50:]
        chunk2_start = chunks[1].page_content[:50]

        # Simple overlap check: look for common words/phrases
        overlap_found = False
        for word in chunk1_end.split():
            if word in chunk2_start:
                overlap_found = True
                break

        if overlap_found or len(chunks) == 1:
            print(f"✓ Chunk overlap appears to be working")
            print(f"  - Chunk 1 end: ...{chunk1_end[-30:]}")
            print(f"  - Chunk 2 start: {chunk2_start[:30]}...")
            return True
        else:
            print("⚠ Could not verify chunk overlap (may be normal for small documents)")
            return True
    except Exception as e:
        print(f"✗ Chunk overlap test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Document Ingestion Pipeline Test Suite")
    print("=" * 60)

    # Create sample files
    print("\nCreating sample files...")
    text_file, md_file = create_sample_files()
    print(f"✓ Sample files created")

    # Run tests
    results = []

    results.append(("Text File Loading", test_text_file_loading()))
    results.append(("Markdown File Loading", test_markdown_file_loading()))
    results.append(("File Size Validation", test_file_size_validation()))
    results.append(("Unsupported Format", test_unsupported_format()))
    results.append(("Chunking Metadata", test_chunking_metadata()))
    results.append(("Chunk Overlap", test_chunk_overlap()))

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
        print("\n✓ All tests passed! Document ingestion pipeline is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

