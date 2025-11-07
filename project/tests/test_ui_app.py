"""
Tests for Streamlit UI application module.

Tests cover:
- RAG system initialization
- API client initialization
- Citation formatting
- Error handling
- Session state management (mocked)
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from app.rag import RAGQueryError, RAGQuerySystem
from app.ui.api_client import APIClient
from app.ui.app import format_citations, initialize_api_client, initialize_rag_system


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


class TestInitializeAPIClient:
    """Test API client initialization."""

    @patch("app.ui.app.st")
    @patch("app.ui.app.APIClient")
    def test_initialize_api_client_first_call(self, mock_client_class, mock_st):
        """Test initialization on first call."""
        mock_st.session_state = {}
        mock_api_client = Mock(spec=APIClient)
        mock_client_class.return_value = mock_api_client

        result = initialize_api_client()

        assert result == mock_api_client
        assert mock_st.session_state["api_client"] == mock_api_client
        mock_client_class.assert_called_once()

    @patch("app.ui.app.st")
    @patch("app.ui.app.APIClient")
    def test_initialize_api_client_cached(self, mock_client_class, mock_st):
        """Test initialization uses cached client on second call."""
        mock_api_client = Mock(spec=APIClient)
        mock_st.session_state = {"api_client": mock_api_client}

        result = initialize_api_client()

        assert result == mock_api_client
        mock_client_class.assert_not_called()  # Should not create again

    @patch("app.ui.app.st")
    @patch("app.ui.app.APIClient")
    def test_initialize_api_client_error(self, mock_client_class, mock_st):
        """Test initialization handles errors."""
        mock_st.session_state = {}
        mock_st.error = Mock()
        mock_st.stop = Mock()
        mock_client_class.side_effect = Exception("Initialization failed")

        initialize_api_client()

        # Should call st.error and st.stop
        mock_st.error.assert_called_once()
        assert "Failed to initialize API client" in str(mock_st.error.call_args[0][0])
        mock_st.stop.assert_called_once()


class TestInitializeRAGSystem:
    """Test RAG system initialization (fallback mode)."""

    @patch("app.ui.app.st")
    @patch("app.ui.app.create_rag_system")
    def test_initialize_rag_system_first_call(self, mock_create, mock_st):
        """Test initialization on first call."""
        mock_st.session_state = {}
        mock_rag_system = Mock(spec=RAGQuerySystem)
        mock_create.return_value = mock_rag_system

        result = initialize_rag_system()

        assert result == mock_rag_system
        cache_key = "rag_system_None_None"
        assert mock_st.session_state[cache_key] == mock_rag_system
        mock_create.assert_called_once()

    @patch("app.ui.app.st")
    @patch("app.ui.app.create_rag_system")
    def test_initialize_rag_system_cached(self, mock_create, mock_st):
        """Test initialization uses cached system on second call."""
        mock_rag_system = Mock(spec=RAGQuerySystem)
        cache_key = "rag_system_None_None"
        mock_st.session_state = {cache_key: mock_rag_system}

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

        initialize_rag_system()

        # Should call st.error and st.stop
        mock_st.error.assert_called_once()
        assert "Failed to initialize RAG system" in str(mock_st.error.call_args[0][0])
        mock_st.stop.assert_called_once()

    @patch("app.ui.app.st")
    @patch("app.ui.app.create_rag_system")
    def test_initialize_rag_system_general_error(self, mock_create, mock_st):
        """Test initialization handles general exceptions."""
        mock_st.session_state = {}
        mock_st.error = Mock()
        mock_st.stop = Mock()
        mock_create.side_effect = Exception("Unexpected error")

        # Should raise the exception (st.error/stop only called for RAGQueryError)
        with pytest.raises(Exception, match="Unexpected error"):
            initialize_rag_system()


class TestMainFunction:
    """Test main Streamlit application function."""

    @patch("app.ui.app.st")
    @patch("app.ui.app.config")
    @patch("app.ui.app.initialize_api_client")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_page_config(
        self, mock_format, mock_init_rag, mock_init_api, mock_config, mock_st
    ):
        """Test main function sets page configuration."""
        mock_st.set_page_config = Mock()
        mock_st.markdown = Mock()
        mock_st.toggle = Mock(return_value=False)
        mock_st.caption = Mock()
        mock_st.divider = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.sidebar = MagicMock()
        mock_st.tabs = Mock(return_value=[MagicMock(), MagicMock()])
        mock_st.chat_input = Mock(return_value=None)  # No input
        mock_st.session_state = {}
        mock_config.api_client_enabled = False  # Use RAG system fallback
        mock_rag_system = Mock()
        mock_init_rag.return_value = mock_rag_system

        from app.ui.app import main

        main()

        mock_st.set_page_config.assert_called_once()
        call_kwargs = mock_st.set_page_config.call_args[1]
        assert call_kwargs["page_title"] == "Financial Research Assistant"
        assert call_kwargs["page_icon"] == "📊"

    @patch("app.ui.app.st")
    @patch("app.ui.app.config")
    @patch("app.ui.app.initialize_api_client")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_initializes_chat_history(
        self, mock_format, mock_init_rag, mock_init_api, mock_config, mock_st
    ):
        """Test main function initializes chat history."""
        mock_st.set_page_config = Mock()
        mock_st.markdown = Mock()
        mock_st.toggle = Mock(return_value=False)
        mock_st.caption = Mock()
        mock_st.divider = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.sidebar = MagicMock()
        mock_st.tabs = Mock(return_value=[MagicMock(), MagicMock()])
        mock_st.chat_input = Mock(return_value=None)
        mock_st.session_state = {}
        mock_config.api_client_enabled = False
        mock_rag_system = Mock()
        mock_init_rag.return_value = mock_rag_system

        from app.ui.app import main

        main()

        assert "messages" in mock_st.session_state
        assert mock_st.session_state["messages"] == []

    @patch("app.ui.app.st")
    @patch("app.ui.app.config")
    @patch("app.ui.app.initialize_api_client")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_displays_chat_history(
        self, mock_format, mock_init_rag, mock_init_api, mock_config, mock_st
    ):
        """Test main function displays existing chat history."""
        mock_st.set_page_config = Mock()
        mock_st.markdown = Mock()
        mock_st.toggle = Mock(return_value=False)
        mock_st.caption = Mock()
        mock_st.divider = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.sidebar = MagicMock()
        mock_tab = MagicMock()
        mock_st.tabs = Mock(return_value=[mock_tab, MagicMock()])
        mock_st.chat_input = Mock(return_value=None)
        mock_st.chat_message = MagicMock()
        mock_st.session_state = {
            "messages": [
                {"role": "user", "content": "Question 1"},
                {"role": "assistant", "content": "Answer 1", "sources": []},
            ]
        }
        mock_config.api_client_enabled = False
        mock_rag_system = Mock()
        mock_init_rag.return_value = mock_rag_system

        from app.ui.app import main

        main()

        # Should iterate through messages
        assert mock_st.chat_message.call_count == 2

    @patch("app.ui.app.st")
    @patch("app.ui.app.config")
    @patch("app.ui.app.initialize_api_client")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_processes_query(
        self, mock_format, mock_init_rag, mock_init_api, mock_config, mock_st
    ):
        """Test main function processes user query."""
        mock_st.set_page_config = Mock()
        mock_st.markdown = Mock()
        mock_st.toggle = Mock(return_value=False)
        mock_st.caption = Mock()
        mock_st.divider = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.sidebar = MagicMock()
        mock_tab = MagicMock()
        mock_st.tabs = Mock(return_value=[mock_tab, MagicMock()])
        mock_st.chat_input = Mock(return_value="Test question")
        mock_st.chat_message = MagicMock()
        mock_st.spinner = MagicMock()
        mock_st.session_state = {}
        mock_config.api_client_enabled = False
        mock_rag_system = Mock()
        mock_rag_system.query.return_value = {
            "answer": "Test answer",
            "sources": [{"filename": "doc.pdf"}],
        }
        mock_init_rag.return_value = mock_rag_system
        mock_format.return_value = "Source: doc.pdf"

        from app.ui.app import main

        main()

        # Should query RAG system
        mock_rag_system.query.assert_called_once()
        # Should add message to history
        assert len(mock_st.session_state["messages"]) == 2
        assert mock_st.session_state["messages"][0]["role"] == "user"
        assert mock_st.session_state["messages"][1]["role"] == "assistant"

    @patch("app.ui.app.st")
    @patch("app.ui.app.config")
    @patch("app.ui.app.initialize_api_client")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_handles_rag_query_error(
        self, mock_format, mock_init_rag, mock_init_api, mock_config, mock_st
    ):
        """Test main function handles RAGQueryError."""
        mock_st.set_page_config = Mock()
        mock_st.markdown = Mock()
        mock_st.toggle = Mock(return_value=False)
        mock_st.caption = Mock()
        mock_st.divider = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.sidebar = MagicMock()
        mock_tab = MagicMock()
        mock_st.tabs = Mock(return_value=[mock_tab, MagicMock()])
        mock_st.chat_input = Mock(return_value="Test question")
        mock_st.chat_message = MagicMock()
        mock_st.spinner = MagicMock()
        mock_st.error = Mock()
        mock_st.session_state = {}
        mock_config.api_client_enabled = False
        mock_rag_system = Mock()
        mock_rag_system.query.side_effect = RAGQueryError("Query failed")
        mock_init_rag.return_value = mock_rag_system

        from app.ui.app import main

        main()

        # Should display error
        mock_st.error.assert_called()
        # Should add error message to history
        assert len(mock_st.session_state["messages"]) == 2
        assert mock_st.session_state["messages"][1]["role"] == "assistant"

    @patch("app.ui.app.st")
    @patch("app.ui.app.config")
    @patch("app.ui.app.initialize_api_client")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_handles_general_error(
        self, mock_format, mock_init_rag, mock_init_api, mock_config, mock_st
    ):
        """Test main function handles general exceptions."""
        mock_st.set_page_config = Mock()
        mock_st.markdown = Mock()
        mock_st.toggle = Mock(return_value=False)
        mock_st.caption = Mock()
        mock_st.divider = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.sidebar = MagicMock()
        mock_tab = MagicMock()
        mock_st.tabs = Mock(return_value=[mock_tab, MagicMock()])
        mock_st.chat_input = Mock(return_value="Test question")
        mock_st.chat_message = MagicMock()
        mock_st.spinner = MagicMock()
        mock_st.error = Mock()
        mock_st.session_state = {}
        mock_config.api_client_enabled = False
        mock_rag_system = Mock()
        mock_rag_system.query.side_effect = Exception("Unexpected error")
        mock_init_rag.return_value = mock_rag_system

        from app.ui.app import main

        main()

        # Should display error
        mock_st.error.assert_called()

    @patch("app.ui.app.st")
    @patch("app.ui.app.config")
    @patch("app.ui.app.initialize_api_client")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_displays_citations(
        self, mock_format, mock_init_rag, mock_init_api, mock_config, mock_st
    ):
        """Test main function displays citations for assistant messages."""
        mock_st.set_page_config = Mock()
        mock_st.markdown = Mock()
        mock_st.toggle = Mock(return_value=False)
        mock_st.caption = Mock()
        mock_st.divider = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.sidebar = MagicMock()
        mock_tab = MagicMock()
        mock_st.tabs = Mock(return_value=[mock_tab, MagicMock()])
        mock_st.chat_input = Mock(return_value=None)
        mock_st.chat_message = MagicMock()
        mock_st.session_state = {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Previous answer",
                    "sources": [{"filename": "doc1.pdf"}],
                }
            ]
        }
        mock_config.api_client_enabled = False
        mock_rag_system = Mock()
        mock_init_rag.return_value = mock_rag_system
        mock_format.return_value = "Source: doc.pdf"

        from app.ui.app import main

        main()

        # Should display citations for existing messages
        mock_st.caption.assert_called()

    @patch("app.ui.app.st")
    @patch("app.ui.app.config")
    @patch("app.ui.app.initialize_api_client")
    @patch("app.ui.app.initialize_rag_system")
    @patch("app.ui.app.format_citations")
    def test_main_no_sources(
        self, mock_format, mock_init_rag, mock_init_api, mock_config, mock_st
    ):
        """Test main function handles queries with no sources."""
        mock_st.set_page_config = Mock()
        mock_st.markdown = Mock()
        mock_st.toggle = Mock(return_value=False)
        mock_st.caption = Mock()
        mock_st.divider = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.sidebar = MagicMock()
        mock_tab = MagicMock()
        mock_st.tabs = Mock(return_value=[mock_tab, MagicMock()])
        mock_st.chat_input = Mock(return_value="Test question")
        mock_st.chat_message = MagicMock()
        mock_st.spinner = MagicMock()
        mock_st.session_state = {}
        mock_config.api_client_enabled = False
        mock_rag_system = Mock()
        mock_rag_system.query.return_value = {"answer": "Test answer", "sources": []}
        mock_init_rag.return_value = mock_rag_system

        from app.ui.app import main

        main()

        # Should still add message to history
        assert len(mock_st.session_state["messages"]) == 2
