"""
Tests for conversation export utility module.

Tests cover:
- JSON export functionality
- Markdown export functionality
- TXT export functionality
- Export filename generation
- Error handling
"""

import json
from datetime import datetime

import pytest

from app.utils.conversation_export import (
    export_conversation,
    export_to_json,
    export_to_markdown,
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
