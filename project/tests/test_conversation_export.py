"""
Tests for conversation export utility module.

Tests cover:
- JSON export functionality
- Markdown export functionality
- TXT export functionality
- PDF export functionality
- DOCX export functionality
- CSV export functionality
- Batch export functionality
- Export filename generation
- Error handling
"""

import csv
import io
import json
from datetime import datetime

import pytest

from app.utils.conversation_export import (
    batch_export_conversations,
    export_conversation,
    export_to_csv,
    export_to_docx,
    export_to_json,
    export_to_markdown,
    export_to_pdf,
    export_to_txt,
    generate_export_filename,
)


class TestExportToJSON:
    """Test JSON export functionality."""

    def test_export_to_json_basic(self):
        """Test basic JSON export."""
        messages = [
            {"role": "user", "content": "What is revenue?"},
            {
                "role": "assistant",
                "content": "Revenue is...",
                "sources": [{"filename": "doc1.pdf"}],
            },
        ]

        result = export_to_json(messages, model="gpt-4o-mini")

        data = json.loads(result)
        assert data["conversation_id"] is not None
        assert data["created_at"] is not None
        assert len(data["messages"]) == 2
        assert data["metadata"]["model"] == "gpt-4o-mini"
        assert data["metadata"]["total_messages"] == 2
        assert data["metadata"]["user_messages"] == 1
        assert data["metadata"]["assistant_messages"] == 1

    def test_export_to_json_with_sources(self):
        """Test JSON export includes sources."""
        messages = [
            {
                "role": "assistant",
                "content": "Answer",
                "sources": [
                    {"filename": "doc1.pdf", "source": "path/to/doc1.pdf"},
                    {"filename": "doc2.txt"},
                ],
            }
        ]

        result = export_to_json(messages)
        data = json.loads(result)

        assert "sources" in data["messages"][0]
        assert len(data["messages"][0]["sources"]) == 2

    def test_export_to_json_with_timestamp(self):
        """Test JSON export includes timestamps if available."""
        timestamp = datetime.now().isoformat()
        messages = [{"role": "user", "content": "Question", "timestamp": timestamp}]

        result = export_to_json(messages)
        data = json.loads(result)

        assert data["messages"][0]["timestamp"] == timestamp

    def test_export_to_json_empty_messages(self):
        """Test JSON export with empty messages."""
        messages = []

        result = export_to_json(messages)
        data = json.loads(result)

        assert len(data["messages"]) == 0
        assert data["metadata"]["total_messages"] == 0


class TestExportToMarkdown:
    """Test Markdown export functionality."""

    def test_export_to_markdown_basic(self):
        """Test basic Markdown export."""
        messages = [
            {"role": "user", "content": "What is revenue?"},
            {
                "role": "assistant",
                "content": "Revenue is...",
                "sources": [{"filename": "doc1.pdf"}],
            },
        ]

        result = export_to_markdown(messages, model="gpt-4o-mini")

        assert "# Conversation Export" in result
        assert "**Date:**" in result
        assert "**Model:** gpt-4o-mini" in result
        assert "## Messages" in result
        assert "### User" in result
        assert "### Assistant" in result
        assert "What is revenue?" in result
        assert "Revenue is..." in result

    def test_export_to_markdown_with_sources(self):
        """Test Markdown export includes sources."""
        messages = [
            {
                "role": "assistant",
                "content": "Answer",
                "sources": [{"filename": "doc1.pdf"}],
            }
        ]

        result = export_to_markdown(messages)

        assert "**Source:** doc1.pdf" in result

    def test_export_to_markdown_multiple_sources(self):
        """Test Markdown export with multiple sources."""
        messages = [
            {
                "role": "assistant",
                "content": "Answer",
                "sources": [
                    {"filename": "doc1.pdf"},
                    {"filename": "doc2.txt"},
                ],
            }
        ]

        result = export_to_markdown(messages)

        assert "**Sources:**" in result
        assert "doc1.pdf" in result
        assert "doc2.txt" in result


class TestExportToTXT:
    """Test TXT export functionality."""

    def test_export_to_txt_basic(self):
        """Test basic TXT export."""
        messages = [
            {"role": "user", "content": "What is revenue?"},
            {"role": "assistant", "content": "Revenue is..."},
        ]

        result = export_to_txt(messages, model="gpt-4o-mini")

        assert "Conversation Export" in result
        assert "Date:" in result
        assert "Model: gpt-4o-mini" in result
        assert "[1] USER" in result
        assert "[2] ASSISTANT" in result
        assert "What is revenue?" in result
        assert "Revenue is..." in result

    def test_export_to_txt_with_sources(self):
        """Test TXT export includes sources."""
        messages = [
            {
                "role": "assistant",
                "content": "Answer",
                "sources": [{"filename": "doc1.pdf"}],
            }
        ]

        result = export_to_txt(messages)

        assert "Source: doc1.pdf" in result


class TestExportConversation:
    """Test main export_conversation function."""

    def test_export_conversation_json(self):
        """Test export_conversation with JSON format."""
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"},
        ]

        content, filename = export_conversation(messages, "json", model="test-model")

        assert filename.endswith(".json")
        assert "conversation" in filename.lower()
        # Verify it's valid JSON
        data = json.loads(content)
        assert data["metadata"]["model"] == "test-model"

    def test_export_conversation_markdown(self):
        """Test export_conversation with Markdown format."""
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"},
        ]

        content, filename = export_conversation(
            messages, "markdown", model="test-model"
        )

        assert filename.endswith(".md")
        assert "# Conversation Export" in content

    def test_export_conversation_txt(self):
        """Test export_conversation with TXT format."""
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"},
        ]

        content, filename = export_conversation(messages, "txt", model="test-model")

        assert filename.endswith(".txt")
        assert "Conversation Export" in content

    def test_export_conversation_empty_messages(self):
        """Test export_conversation raises error for empty messages."""
        messages = []

        with pytest.raises(ValueError, match="Cannot export empty conversation"):
            export_conversation(messages, "json")

    def test_export_conversation_invalid_format(self):
        """Test export_conversation raises error for invalid format."""
        messages = [{"role": "user", "content": "Question"}]

        with pytest.raises(ValueError, match="Unsupported format type"):
            export_conversation(messages, "invalid_format")


class TestGenerateExportFilename:
    """Test export filename generation."""

    def test_generate_export_filename_json(self):
        """Test filename generation for JSON format."""
        filename = generate_export_filename("json")

        assert filename.endswith(".json")
        assert "conversation" in filename.lower()

    def test_generate_export_filename_markdown(self):
        """Test filename generation for Markdown format."""
        filename = generate_export_filename("markdown")

        assert filename.endswith(".md")
        assert "conversation" in filename.lower()

    def test_generate_export_filename_txt(self):
        """Test filename generation for TXT format."""
        filename = generate_export_filename("txt")

        assert filename.endswith(".txt")
        assert "conversation" in filename.lower()

    def test_generate_export_filename_with_conversation_id(self):
        """Test filename generation includes conversation ID."""
        conv_id = "test-conversation-id"
        filename = generate_export_filename("json", conversation_id=conv_id)

        assert "test-con" in filename  # First 8 chars of ID

    def test_generate_export_filename_pdf(self):
        """Test filename generation for PDF format."""
        filename = generate_export_filename("pdf")

        assert filename.endswith(".pdf")
        assert "conversation" in filename.lower()

    def test_generate_export_filename_docx(self):
        """Test filename generation for DOCX format."""
        filename = generate_export_filename("docx")

        assert filename.endswith(".docx")
        assert "conversation" in filename.lower()

    def test_generate_export_filename_csv(self):
        """Test filename generation for CSV format."""
        filename = generate_export_filename("csv")

        assert filename.endswith(".csv")
        assert "conversation" in filename.lower()


class TestExportToPDF:
    """Test PDF export functionality."""

    def test_export_to_pdf_basic(self):
        """Test basic PDF export."""
        pytest.importorskip("reportlab")

        messages = [
            {"role": "user", "content": "What is revenue?"},
            {"role": "assistant", "content": "Revenue is..."},
        ]

        result = export_to_pdf(messages, model="gpt-4o-mini")

        assert isinstance(result, bytes)
        assert len(result) > 0
        # Verify it's a PDF (starts with PDF header)
        assert result[:4] == b"%PDF"

    def test_export_to_pdf_with_sources(self):
        """Test PDF export includes sources."""
        pytest.importorskip("reportlab")

        messages = [
            {
                "role": "assistant",
                "content": "Answer",
                "sources": [{"filename": "doc1.pdf"}],
            }
        ]

        result = export_to_pdf(messages)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_export_to_pdf_missing_library(self):
        """Test PDF export raises ImportError when reportlab is missing."""
        # This test assumes reportlab might not be installed
        # In practice, we'd mock the import
        messages = [{"role": "user", "content": "Question"}]

        # If reportlab is not available, this should raise ImportError
        # We can't easily test this without mocking, so we'll skip if available
        try:
            import reportlab  # noqa: F401

            # If reportlab is available, test that it works
            result = export_to_pdf(messages)
            assert isinstance(result, bytes)
        except ImportError:
            # If reportlab is not available, test that error is raised
            with pytest.raises(ImportError, match="reportlab is required"):
                export_to_pdf(messages)


class TestExportToDOCX:
    """Test DOCX export functionality."""

    def test_export_to_docx_basic(self):
        """Test basic DOCX export."""
        pytest.importorskip("docx")

        messages = [
            {"role": "user", "content": "What is revenue?"},
            {"role": "assistant", "content": "Revenue is..."},
        ]

        result = export_to_docx(messages, model="gpt-4o-mini")

        assert isinstance(result, bytes)
        assert len(result) > 0
        # Verify it's a DOCX (ZIP file format, starts with PK)
        assert result[:2] == b"PK"

    def test_export_to_docx_with_sources(self):
        """Test DOCX export includes sources."""
        pytest.importorskip("docx")

        messages = [
            {
                "role": "assistant",
                "content": "Answer",
                "sources": [{"filename": "doc1.pdf"}],
            }
        ]

        result = export_to_docx(messages)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_export_to_docx_missing_library(self):
        """Test DOCX export raises ImportError when python-docx is missing."""
        messages = [{"role": "user", "content": "Question"}]

        try:
            from docx import Document  # noqa: F401

            # If python-docx is available, test that it works
            result = export_to_docx(messages)
            assert isinstance(result, bytes)
        except ImportError:
            # If python-docx is not available, test that error is raised
            with pytest.raises(ImportError, match="python-docx is required"):
                export_to_docx(messages)


class TestExportToCSV:
    """Test CSV export functionality."""

    def test_export_to_csv_basic(self):
        """Test basic CSV export."""
        messages = [
            {"role": "user", "content": "What is revenue?"},
            {"role": "assistant", "content": "Revenue is..."},
        ]

        result = export_to_csv(messages, model="gpt-4o-mini")

        assert isinstance(result, str)
        # Parse CSV to verify structure
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 3  # Header + 2 messages
        assert rows[0] == [
            "Message Number",
            "Role",
            "Content",
            "Sources",
            "Timestamp",
            "Model",
            "Conversation ID",
        ]
        assert rows[1][1] == "user"
        assert rows[2][1] == "assistant"

    def test_export_to_csv_with_sources(self):
        """Test CSV export includes sources."""
        messages = [
            {
                "role": "assistant",
                "content": "Answer",
                "sources": [{"filename": "doc1.pdf"}],
            }
        ]

        result = export_to_csv(messages)
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        assert rows[1][3] == "doc1.pdf"  # Sources column

    def test_export_to_csv_with_timestamp(self):
        """Test CSV export includes timestamps."""
        timestamp = datetime.now().isoformat()
        messages = [{"role": "user", "content": "Question", "timestamp": timestamp}]

        result = export_to_csv(messages)
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        assert rows[1][4] == timestamp  # Timestamp column


class TestExportConversationExtended:
    """Test export_conversation with new formats."""

    def test_export_conversation_pdf(self):
        """Test export_conversation with PDF format."""
        pytest.importorskip("reportlab")

        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"},
        ]

        content, filename = export_conversation(messages, "pdf", model="test-model")

        assert filename.endswith(".pdf")
        assert isinstance(content, bytes)
        assert content[:4] == b"%PDF"

    def test_export_conversation_docx(self):
        """Test export_conversation with DOCX format."""
        pytest.importorskip("docx")

        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"},
        ]

        content, filename = export_conversation(messages, "docx", model="test-model")

        assert filename.endswith(".docx")
        assert isinstance(content, bytes)
        assert content[:2] == b"PK"

    def test_export_conversation_csv(self):
        """Test export_conversation with CSV format."""
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"},
        ]

        content, filename = export_conversation(messages, "csv", model="test-model")

        assert filename.endswith(".csv")
        assert isinstance(content, str)
        assert "Message Number" in content


class TestBatchExport:
    """Test batch export functionality."""

    def test_batch_export_conversations(self):
        """Test batch export of multiple conversations."""
        conversations = [
            {
                "messages": [
                    {"role": "user", "content": "Question 1"},
                    {"role": "assistant", "content": "Answer 1"},
                ],
                "conversation_id": "conv-1",
                "model": "model-1",
            },
            {
                "messages": [
                    {"role": "user", "content": "Question 2"},
                    {"role": "assistant", "content": "Answer 2"},
                ],
                "conversation_id": "conv-2",
                "model": "model-2",
            },
        ]

        results = batch_export_conversations(conversations, "json")

        assert len(results) == 2
        for content, filename in results:
            assert filename.endswith(".json")
            assert isinstance(content, str)
            data = json.loads(content)
            assert len(data["messages"]) == 2

    def test_batch_export_empty_conversations(self):
        """Test batch export raises error for empty conversations list."""
        with pytest.raises(ValueError, match="Cannot export empty conversations"):
            batch_export_conversations([], "json")

    def test_batch_export_skips_empty_messages(self):
        """Test batch export skips conversations with no messages."""
        conversations = [
            {"messages": [], "conversation_id": "conv-1"},
            {
                "messages": [
                    {"role": "user", "content": "Question"},
                    {"role": "assistant", "content": "Answer"},
                ],
                "conversation_id": "conv-2",
            },
        ]

        results = batch_export_conversations(conversations, "json")

        # Should only export the conversation with messages
        assert len(results) == 1
