"""
Tests for Streamlit UI application module.

Tests cover:
- RAG system initialization
- Citation formatting
- Error handling
- Session state management (mocked)
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.rag import RAGQueryError, RAGQuerySystem
from app.ui.app import format_citations, initialize_rag_system


class TestFormatCitations:
    """Test citation formatting function."""

    def test_format_citations_empty(self):
        """Test formatting with empty sources."""
        result = format_citations([])
        assert result == ""

    def test_format_citations_single_source(self):
        """Test formatting with single source."""
        sources = [{"filename": "document.pdf", "content": "test"}]
        result = format_citations(sources)
        assert result == "Source: document.pdf"

    def test_format_citations_multiple_sources(self):
        """Test formatting with multiple sources."""
        sources = [
            {"filename": "doc1.pdf", "content": "test1"},
            {"filename": "doc2.txt", "content": "test2"},
        ]
        result = format_citations(sources)
        assert "doc1.pdf" in result
        assert "doc2.txt" in result
        assert "Sources:" in result

    def test_format_citations_with_path(self):
        """Test formatting with file path."""
        sources = [{"filename": "/path/to/document.pdf", "content": "test"}]
        result = format_citations(sources)
        assert result == "Source: document.pdf"  # Should extract just filename

    def test_format_citations_with_source_field(self):
        """Test formatting using 'source' field when 'filename' not available."""
        sources = [{"source": "document.pdf", "content": "test"}]
        result = format_citations(sources)
        assert result == "Source: document.pdf"

    def test_format_citations_unknown_source(self):
        """Test formatting when source is unknown."""
        sources = [{"content": "test"}]  # No filename or source
        result = format_citations(sources)
        assert result == "Source: unknown"

    def test_format_citations_duplicate_sources(self):
        """Test formatting removes duplicate sources."""
        sources = [
            {"filename": "document.pdf", "content": "test1"},
            {"filename": "document.pdf", "content": "test2"},
        ]
        result = format_citations(sources)
        assert result == "Source: document.pdf"  # Should deduplicate
        assert result.count("document.pdf") == 1

    def test_format_citations_sorted_sources(self):
        """Test formatting sorts multiple sources."""
        sources = [
            {"filename": "zebra.pdf", "content": "test"},
            {"filename": "apple.pdf", "content": "test"},
        ]
        result = format_citations(sources)
        # Should be sorted alphabetically
        assert result.index("apple.pdf") < result.index("zebra.pdf")


class TestInitializeRAGSystem:
    """Test RAG system initialization."""

    @patch("app.ui.app.st")
    @patch("app.ui.app.create_rag_system")
    def test_initialize_rag_system_first_call(self, mock_create, mock_st):
        """Test initialization on first call."""
        mock_st.session_state = {}
        mock_rag_system = Mock(spec=RAGQuerySystem)
        mock_create.return_value = mock_rag_system

        result = initialize_rag_system()

        assert result == mock_rag_system
        assert mock_st.session_state["rag_system"] == mock_rag_system
        mock_create.assert_called_once()

    @patch("app.ui.app.st")
    @patch("app.ui.app.create_rag_system")
    def test_initialize_rag_system_cached(self, mock_create, mock_st):
        """Test initialization uses cached system on second call."""
        mock_rag_system = Mock(spec=RAGQuerySystem)
        mock_st.session_state = {"rag_system": mock_rag_system}

        result = initialize_rag_system()

        assert result == mock_rag_system
        mock_create.assert_not_called()  # Should not create again

    @patch("app.ui.app.st")
    @patch("app.ui.app.create_rag_system")
    def test_initialize_rag_system_error(self, mock_create, mock_st):
        """Test initialization handles RAGQueryError."""
        mock_st.session_state = {}
        mock_st.error = Mock()
        mock_st.stop = Mock()
        mock_create.side_effect = RAGQueryError("Initialization failed")

        result = initialize_rag_system()

        # Should call st.error and st.stop
        mock_st.error.assert_called_once()
        assert "Failed to initialize RAG system" in str(mock_st.error.call_args[0][0])
        mock_st.stop.assert_called_once()
        # Should not return anything (st.stop() halts execution)

    @patch("app.ui.app.st")
    @patch("app.ui.app.create_rag_system")
    def test_initialize_rag_system_general_error(self, mock_create, mock_st):
        """Test initialization handles general exceptions."""
        mock_st.session_state = {}
        mock_st.error = Mock()
        mock_st.stop = Mock()
        mock_create.side_effect = Exception("Unexpected error")

        # Should raise the exception (st.error/stop only called for RAGQueryError)
        with pytest.raises(Exception):
            initialize_rag_system()


class TestMainFunction:
    """Test main Streamlit application function."""

    @patch("app.ui.app.st")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_page_config(self, mock_format, mock_init, mock_st):
        """Test main function sets page configuration."""
        mock_st.set_page_config = Mock()
        mock_st.title = Mock()
        mock_st.markdown = Mock()
        mock_st.chat_input = Mock(return_value=None)  # No input
        mock_st.session_state = {}

        from app.ui.app import main

        main()

        mock_st.set_page_config.assert_called_once()
        call_kwargs = mock_st.set_page_config.call_args[1]
        assert call_kwargs["page_title"] == "Financial Research Assistant"
        assert call_kwargs["page_icon"] == "📊"

    @patch("app.ui.app.st")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_initializes_chat_history(self, mock_format, mock_init, mock_st):
        """Test main function initializes chat history."""
        mock_rag_system = Mock()
        mock_init.return_value = mock_rag_system
        mock_st.chat_input = Mock(return_value=None)
        mock_st.session_state = {}

        from app.ui.app import main

        main()

        assert "messages" in mock_st.session_state
        assert mock_st.session_state["messages"] == []

    @patch("app.ui.app.st")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_displays_chat_history(self, mock_format, mock_init, mock_st):
        """Test main function displays existing chat history."""
        mock_rag_system = Mock()
        mock_init.return_value = mock_rag_system
        mock_st.chat_input = Mock(return_value=None)
        mock_st.chat_message = MagicMock()
        mock_st.session_state = {
            "messages": [
                {"role": "user", "content": "Question 1"},
                {"role": "assistant", "content": "Answer 1", "sources": []},
            ]
        }

        from app.ui.app import main

        main()

        # Should iterate through messages
        assert mock_st.chat_message.call_count == 2

    @patch("app.ui.app.st")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_processes_query(self, mock_format, mock_init, mock_st):
        """Test main function processes user query."""
        mock_rag_system = Mock()
        mock_rag_system.query.return_value = {
            "answer": "Test answer",
            "sources": [{"filename": "doc.pdf"}],
        }
        mock_init.return_value = mock_rag_system
        mock_format.return_value = "Source: doc.pdf"
        mock_st.chat_input = Mock(return_value="Test question")
        mock_st.chat_message = MagicMock()
        mock_st.markdown = Mock()
        mock_st.spinner = MagicMock()
        mock_st.caption = Mock()
        mock_st.session_state = {}

        from app.ui.app import main

        main()

        # Should query RAG system
        mock_rag_system.query.assert_called_once_with("Test question")
        # Should add message to history
        assert len(mock_st.session_state["messages"]) == 2
        assert mock_st.session_state["messages"][0]["role"] == "user"
        assert mock_st.session_state["messages"][1]["role"] == "assistant"

    @patch("app.ui.app.st")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_handles_rag_query_error(self, mock_format, mock_init, mock_st):
        """Test main function handles RAGQueryError."""
        mock_rag_system = Mock()
        mock_rag_system.query.side_effect = RAGQueryError("Query failed")
        mock_init.return_value = mock_rag_system
        mock_st.chat_input = Mock(return_value="Test question")
        mock_st.chat_message = MagicMock()
        mock_st.markdown = Mock()
        mock_st.spinner = MagicMock()
        mock_st.error = Mock()
        mock_st.session_state = {}

        from app.ui.app import main

        main()

        # Should display error
        mock_st.error.assert_called_once()
        assert "Error processing query" in str(mock_st.error.call_args[0][0])
        # Should add error message to history
        assert mock_st.session_state["messages"][1]["role"] == "assistant"
        assert "error" in mock_st.session_state["messages"][1]["content"].lower()

    @patch("app.ui.app.st")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_handles_general_error(self, mock_format, mock_init, mock_st):
        """Test main function handles general exceptions."""
        mock_rag_system = Mock()
        mock_rag_system.query.side_effect = Exception("Unexpected error")
        mock_init.return_value = mock_rag_system
        mock_st.chat_input = Mock(return_value="Test question")
        mock_st.chat_message = MagicMock()
        mock_st.markdown = Mock()
        mock_st.spinner = MagicMock()
        mock_st.error = Mock()
        mock_st.session_state = {}

        from app.ui.app import main

        main()

        # Should display error
        mock_st.error.assert_called_once()
        assert "Unexpected error" in str(mock_st.error.call_args[0][0])

    @patch("app.ui.app.st")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_displays_citations(self, mock_format, mock_init, mock_st):
        """Test main function displays citations for assistant messages."""
        mock_rag_system = Mock()
        mock_rag_system.query.return_value = {
            "answer": "Test answer",
            "sources": [{"filename": "doc.pdf"}],
        }
        mock_init.return_value = mock_rag_system
        mock_format.return_value = "Source: doc.pdf"
        mock_st.chat_input = Mock(return_value="Test question")
        mock_st.chat_message = MagicMock()
        mock_st.markdown = Mock()
        mock_st.spinner = MagicMock()
        mock_st.caption = Mock()
        mock_st.session_state = {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Previous answer",
                    "sources": [{"filename": "doc1.pdf"}],
                }
            ]
        }

        from app.ui.app import main

        main()

        # Should display citations for existing messages
        mock_st.caption.assert_called()

    @patch("app.ui.app.st")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_no_sources(self, mock_format, mock_init, mock_st):
        """Test main function handles queries with no sources."""
        mock_rag_system = Mock()
        mock_rag_system.query.return_value = {"answer": "Test answer", "sources": []}
        mock_init.return_value = mock_rag_system
        mock_st.chat_input = Mock(return_value="Test question")
        mock_st.chat_message = MagicMock()
        mock_st.markdown = Mock()
        mock_st.spinner = MagicMock()
        mock_st.caption = Mock()
        mock_st.session_state = {}

        from app.ui.app import main

        main()

        # Should not call format_citations if no sources
        # (format_citations may still be called, but with empty list)
        # Should still add message to history
        assert len(mock_st.session_state["messages"]) == 2
