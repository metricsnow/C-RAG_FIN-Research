"""
Chat interface UI component for Streamlit app.

Provides the main chat interface for querying documents with RAG.
"""

from typing import Any, Dict, Optional

import streamlit as st

from app.rag import RAGQueryError, RAGQuerySystem
from app.ui.api_client import (
    APIClient,
    APIClientError,
    APIConnectionError,
    APIError,
)
from app.ui.app_helpers import format_citations
from app.utils.logger import get_logger

logger = get_logger(__name__)


def render_chat_interface(
    api_client: Optional[APIClient],
    rag_system: Optional[RAGQuerySystem],
    model_provider: str,
    model_name: str,
) -> None:
    """
    Render the chat interface.

    Args:
        api_client: APIClient instance (if using API)
        rag_system: Initialized RAG query system (if using direct calls)
        model_provider: Current model provider name
        model_name: Current model name
    """
    # Title and description
    st.title("📊 Financial Research Assistant")
    st.markdown(
        "Ask questions about your financial documents. "
        "Answers are generated using RAG (Retrieval-Augmented Generation) technology."
    )

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Memory status display
    if hasattr(rag_system, "memory") and rag_system.memory:
        try:
            memory_stats = rag_system.memory.get_memory_stats()
            st.caption(
                f"Memory: {memory_stats['message_count']} messages, "
                f"{memory_stats['token_count']} tokens "
                f"(max: {memory_stats['max_tokens']} tokens, "
                f"{memory_stats['max_history']} messages)"
            )
        except Exception as e:
            logger.debug(f"Could not get memory stats: {e}")

    # Conversation management buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        _render_clear_conversation_button(rag_system)

    with col2:
        _render_export_section(model_provider, model_name)

    with col3:
        _render_sharing_section()

    st.divider()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Display citations for assistant messages
            if message["role"] == "assistant" and "sources" in message:
                sources = message["sources"]
                if sources:
                    citation = format_citations(sources)
                    if citation:
                        st.caption(citation)

    # Advanced query builder (expandable)
    filters_dict, enable_parsing_to_use, use_advanced_query, advanced_query = (
        _render_advanced_query_builder()
    )

    # Chat input - check both advanced query and regular chat input
    prompt = None
    filters_to_use = None

    # Check if advanced query button was clicked
    if use_advanced_query and advanced_query:
        prompt = advanced_query
        filters_to_use = filters_dict
    else:
        enable_parsing_to_use = True

    # Also check regular chat input (only if advanced query not used)
    if not prompt:
        chat_input = st.chat_input("Ask a question about your documents...")
        if chat_input:
            prompt = chat_input

    if prompt:
        _process_user_query(
            prompt, api_client, rag_system, filters_to_use, enable_parsing_to_use
        )


def _render_clear_conversation_button(rag_system: Optional[RAGQuerySystem]) -> None:
    """Render clear conversation button with confirmation."""
    # Clear conversation button with confirmation
    if "show_clear_confirm" not in st.session_state:
        st.session_state.show_clear_confirm = False

    if st.session_state.show_clear_confirm:
        if st.button("✅ Confirm Clear", type="primary", key="confirm_clear"):
            st.session_state.messages = []
            # Clear LangChain memory if available
            if hasattr(rag_system, "memory") and rag_system.memory:
                try:
                    rag_system.memory.clear()
                except Exception as e:
                    logger.debug(f"Could not clear memory: {e}")
            st.session_state.show_clear_confirm = False
            st.rerun()
        if st.button("❌ Cancel", key="cancel_clear"):
            st.session_state.show_clear_confirm = False
            st.rerun()
    else:
        if st.button("🗑️ Clear Conversation", key="clear_conversation"):
            if len(st.session_state.messages) > 0:
                st.session_state.show_clear_confirm = True
                st.rerun()


def _render_export_section(model_provider: str, model_name: str) -> None:
    """Render export and download section."""
    # Export and sharing section
    if len(st.session_state.messages) > 0:
        # Export format selection
        export_format = st.selectbox(
            "Export Format",
            ["JSON", "Markdown", "TXT", "PDF", "Word (DOCX)", "CSV"],
            key="export_format",
            label_visibility="collapsed",
        )

        # Initialize export data in session state
        if "export_data" not in st.session_state:
            st.session_state.export_data = None
        if "export_filename" not in st.session_state:
            st.session_state.export_filename = None
        if "export_mime" not in st.session_state:
            st.session_state.export_mime = None

        # Export button
        if st.button("💾 Export", key="export_button"):
            try:
                from app.utils.conversation_export import export_conversation

                # Get current model info
                current_model = f"{model_provider}/{model_name}"
                # Map UI format names to export format names
                format_map = {
                    "JSON": "json",
                    "Markdown": "markdown",
                    "TXT": "txt",
                    "PDF": "pdf",
                    "Word (DOCX)": "docx",
                    "CSV": "csv",
                }
                export_format_lower = format_map.get(export_format, "json")

                # Export conversation
                content, filename = export_conversation(
                    messages=st.session_state.messages,
                    format_type=export_format_lower,
                    model=current_model,
                )
                # Store in session state for download button
                st.session_state.export_data = content
                st.session_state.export_filename = filename

                # Set MIME type based on format
                mime_types = {
                    "json": "application/json",
                    "markdown": "text/markdown",
                    "txt": "text/plain",
                    "pdf": "application/pdf",
                    "docx": (
                        "application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document"
                    ),
                    "csv": "text/csv",
                }
                st.session_state.export_mime = mime_types.get(
                    export_format_lower, "application/octet-stream"
                )
                st.rerun()
            except ImportError as e:
                logger.error(
                    f"Export failed - missing library: {str(e)}", exc_info=True
                )
                st.error(
                    f"Export failed: {str(e)}\n\n"
                    "Please install required library:\n"
                    "- For PDF: `pip install reportlab`\n"
                    "- For Word: `pip install python-docx`"
                )
            except Exception as e:
                logger.error(f"Export failed: {str(e)}", exc_info=True)
                st.error(f"Failed to export conversation: {str(e)}")

        # Show download button if export data is available
        if (
            st.session_state.export_data
            and st.session_state.export_filename
            and st.session_state.export_mime
        ):
            st.download_button(
                label="📥 Download Export",
                data=st.session_state.export_data,
                file_name=st.session_state.export_filename,
                mime=st.session_state.export_mime,
                key="download_export",
            )
    else:
        st.caption("No conversation to export")
        # Clear export data if no messages
        if "export_data" in st.session_state:
            st.session_state.export_data = None
        if "export_filename" in st.session_state:
            st.session_state.export_filename = None
        if "export_mime" in st.session_state:
            st.session_state.export_mime = None


def _render_sharing_section() -> None:
    """Render sharing section."""
    # Sharing section
    if len(st.session_state.messages) > 0:
        if st.button("🔗 Share", key="share_button"):
            try:
                from app.utils.sharing import create_shareable_conversation

                # Get base URL from query params or use default
                query_params = st.query_params
                base_url = query_params.get("base_url", "http://localhost:8501")

                # Create shareable link
                share_data = create_shareable_conversation(
                    messages=st.session_state.messages,
                    base_url=base_url,
                    shorten=False,  # Can be made configurable
                )

                # Store in session state
                st.session_state.share_link = share_data.get("link")
                st.session_state.share_short_link = share_data.get("short_link")
                st.rerun()
            except Exception as e:
                logger.error(f"Sharing failed: {str(e)}", exc_info=True)
                st.error(f"Failed to create shareable link: {str(e)}")

        # Show shareable link if available
        if "share_link" in st.session_state and st.session_state.share_link:
            st.text_input(
                "Shareable Link",
                value=st.session_state.share_link,
                key="share_link_display",
                disabled=True,
                label_visibility="collapsed",
            )
            # Copy button
            if st.button("📋 Copy Link", key="copy_share_link"):
                st.write("Link copied to clipboard!")
    else:
        st.caption("No conversation to share")
        if "share_link" in st.session_state:
            del st.session_state.share_link
        if "share_short_link" in st.session_state:
            del st.session_state.share_short_link


def _render_advanced_query_builder() -> (
    tuple[Optional[Dict[str, Any]], bool, bool, str]
):
    """
    Render advanced query builder.

    Returns:
        Tuple of (filters_dict, enable_parsing, use_advanced_query, advanced_query)
    """
    with st.expander("🔧 Advanced Query Builder", expanded=False):
        st.markdown("**Use filters and Boolean operators for precise queries**")

        # Query input
        advanced_query = st.text_area(
            "Query",
            placeholder="Enter your question here...",
            help=(
                "You can use Boolean operators (AND, OR, NOT) and "
                "filter keywords in your query"
            ),
            key="advanced_query_input",
        )

        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input(
                "Date From",
                value=None,
                help="Filter documents from this date onwards",
                key="filter_date_from",
            )
            ticker_filter = st.text_input(
                "Ticker",
                placeholder="e.g., AAPL, MSFT",
                help="Filter by ticker symbol",
                key="filter_ticker",
            )
            form_type_filter = st.selectbox(
                "Form Type",
                options=[None, "10-K", "10-Q", "8-K", "DEF 14A"],
                help="Filter by SEC form type",
                key="filter_form_type",
            )

        with col2:
            date_to = st.date_input(
                "Date To",
                value=None,
                help="Filter documents up to this date",
                key="filter_date_to",
            )
            document_type_filter = st.selectbox(
                "Document Type",
                options=[None, "edgar_filing", "news", "transcript", "economic_data"],
                help="Filter by document type",
                key="filter_document_type",
            )

        enable_parsing = st.checkbox(
            "Enable Query Parsing",
            value=True,
            help="Automatically extract filters and Boolean operators from query text",
            key="enable_query_parsing",
        )

        # Build filters dict
        filters_dict = None
        if any(
            [date_from, date_to, ticker_filter, form_type_filter, document_type_filter]
        ):
            filters_dict = {}
            if date_from:
                filters_dict["date_from"] = date_from.isoformat()
            if date_to:
                filters_dict["date_to"] = date_to.isoformat()
            if ticker_filter:
                filters_dict["ticker"] = ticker_filter.upper()
            if form_type_filter:
                filters_dict["form_type"] = form_type_filter
            if document_type_filter:
                filters_dict["document_type"] = document_type_filter

        # Query button
        use_advanced_query = st.button(
            "Query with Filters",
            type="primary",
            use_container_width=True,
        )

        # Query syntax help
        with st.expander("📖 Query Syntax Help", expanded=False):
            st.markdown(
                """
            **Boolean Operators:**
            - Use `AND` or `&` to require all terms: "revenue AND profit"
            - Use `OR` or `|` to match any term: "Apple OR Microsoft"
            - Use `NOT` or `!` to exclude terms: "revenue NOT loss"

            **Filter Keywords in Query:**
            - `from 2023-01-01` or `since 2023-01-01` - Date from filter
            - `before 2023-12-31` or `until 2023-12-31` - Date to filter
            - `between 2023-01-01 and 2023-12-31` - Date range
            - `ticker: AAPL` or `ticker=AAPL` - Ticker filter
            - `form: 10-K` or `form=10-K` - Form type filter
            - `type: edgar_filing` - Document type filter

            **Examples:**
            - "What was Apple's revenue from 2023-01-01?" (extracts date filter)
            - "ticker: AAPL revenue AND profit" (extracts ticker filter)
            - "10-K filings from 2023" (extracts form type and date)
            """
            )

    return filters_dict, enable_parsing, use_advanced_query, advanced_query


def _process_user_query(
    prompt: str,
    api_client: Optional[APIClient],
    rag_system: Optional[RAGQuerySystem],
    filters_to_use: Optional[Dict[str, Any]],
    enable_parsing_to_use: bool,
) -> None:
    """
    Process user query and generate response.

    Args:
        prompt: User query text
        api_client: APIClient instance (if using API)
        rag_system: RAGQuerySystem instance (if using direct calls)
        filters_to_use: Optional filters dictionary
        enable_parsing_to_use: Whether to enable query parsing
    """
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Searching documents and generating answer..."):
            try:
                logger.info(f"Processing user query: '{prompt[:50]}...'")
                # Get conversation history (all messages except current)
                # Current message was just added, so use all previous messages
                conversation_history = (
                    st.session_state.messages[:-1]
                    if len(st.session_state.messages) > 1
                    else []
                )

                # Query via API client or direct RAG system
                if api_client:
                    # Use API client
                    result = api_client.query(
                        question=prompt,
                        conversation_history=(
                            conversation_history if conversation_history else None
                        ),
                        filters=filters_to_use,
                        enable_query_parsing=enable_parsing_to_use,
                    )
                elif rag_system:
                    # Fallback to direct RAG system
                    result = rag_system.query(
                        prompt,
                        conversation_history=(
                            conversation_history if conversation_history else None
                        ),
                        filters=filters_to_use,
                        enable_query_parsing=enable_parsing_to_use,
                    )
                else:
                    raise RuntimeError("Neither API client nor RAG system available")

                answer = result.get(
                    "answer", "I'm sorry, I couldn't generate an answer."
                )
                sources = result.get("sources", [])

                logger.info(f"Generated answer with {len(sources)} sources")

                # Display answer
                st.markdown(answer)

                # Display citations
                if sources:
                    citation = format_citations(sources)
                    if citation:
                        st.caption(citation)

                # Display parsed query info if available
                parsed_query = result.get("parsed_query")
                if parsed_query:
                    with st.expander("🔍 Query Analysis", expanded=False):
                        st.json(parsed_query)

                # Add assistant message to chat history
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    }
                )

            except (RAGQueryError, APIError) as e:
                error_msg = f"Error processing query: {str(e)}"
                logger.error(f"Query error: {str(e)}", exc_info=True)
                st.error(error_msg)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_msg,
                        "sources": [],
                    }
                )
            except APIConnectionError as e:
                error_msg = (
                    f"⚠️ Cannot connect to API: {str(e)}. "
                    "Please ensure the FastAPI backend is running."
                )
                logger.error(f"API connection error: {str(e)}", exc_info=True)
                st.error(error_msg)
                st.info(
                    "💡 **Tip:** Start the API server with: "
                    "`python scripts/start_api.py`"
                )
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_msg,
                        "sources": [],
                    }
                )
            except APIClientError as e:
                error_msg = f"API client error: {str(e)}"
                logger.error(f"API client error: {str(e)}", exc_info=True)
                st.error(error_msg)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_msg,
                        "sources": [],
                    }
                )
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"Unexpected error in UI: {str(e)}", exc_info=True)
                st.error(error_msg)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_msg,
                        "sources": [],
                    }
                )
