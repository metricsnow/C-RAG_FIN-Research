"""
Streamlit frontend application for RAG-powered financial research assistant.

Provides a basic chat interface for querying documents with simple citations.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to Python path before any app imports
# This is needed when Streamlit runs the file directly
_file_path = Path(__file__).resolve()

# Go up from app/ui/app.py to project root
# app/ui/app.py -> app/ui/ -> app/ -> project/
_project_root = _file_path.parent.parent.parent
_project_root_str = str(_project_root)

# CRITICAL: Change working directory to project root FIRST
# This ensures relative imports work correctly
os.chdir(_project_root_str)

# CRITICAL: Add project root to sys.path FIRST, before any other operations
# This must be the absolute first entry to ensure imports work
if _project_root_str not in sys.path:
    sys.path.insert(0, _project_root_str)

# Also add to PYTHONPATH environment variable for subprocesses
# Streamlit's scriptrunner runs in subprocess and needs this
existing_pythonpath = os.environ.get("PYTHONPATH", "")
if _project_root_str not in existing_pythonpath:
    if existing_pythonpath:
        os.environ["PYTHONPATH"] = _project_root_str + os.pathsep + existing_pythonpath
    else:
        os.environ["PYTHONPATH"] = _project_root_str

# Verify app package exists
_app_init = Path(_project_root_str) / "app" / "__init__.py"
if not _app_init.exists():
    raise RuntimeError(
        f"Cannot find app package at {_app_init}. "
        f"Project root: {_project_root_str}, "
        f"CWD: {os.getcwd()}, "
        f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'not set')}"
    )

import streamlit as st  # noqa: E402

from app.rag import RAGQueryError, RAGQuerySystem, create_rag_system  # noqa: E402
from app.utils.health import start_health_check_server  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402
from app.utils.metrics import initialize_metrics  # noqa: E402
from app.vector_db.chroma_store import ChromaStore  # noqa: E402

logger = get_logger(__name__)


def get_available_tickers() -> List[Dict[str, Any]]:
    """
    Get all available tickers from the database with company names.

    Returns:
        List of dictionaries with ticker and company information
    """
    if "available_tickers" not in st.session_state:
        try:
            store = ChromaStore()
            all_data = store.get_all()

            # Ticker to company name mapping
            ticker_to_company = {
                "AAPL": "Apple Inc.",
                "MSFT": "Microsoft Corporation",
                "GOOGL": "Alphabet Inc.",
                "AMZN": "Amazon.com Inc.",
                "META": "Meta Platforms Inc.",
                "TSLA": "Tesla, Inc.",
                "NVDA": "NVIDIA Corporation",
                "JPM": "JPMorgan Chase & Co.",
                "V": "Visa Inc.",
                "JNJ": "Johnson & Johnson",
            }

            # Get unique tickers and count documents
            ticker_counts = {}
            for meta in all_data.get("metadatas", []):
                ticker = meta.get("ticker")
                if ticker:
                    ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1

            # Create list of ticker info
            tickers = []
            for ticker in sorted(ticker_counts.keys()):
                company_name = ticker_to_company.get(ticker, ticker)
                count = ticker_counts[ticker]
                tickers.append(
                    {"ticker": ticker, "company": company_name, "count": count}
                )

            st.session_state.available_tickers = tickers
            logger.info(f"Loaded {len(tickers)} available tickers")
        except Exception as e:
            logger.error(f"Failed to load tickers: {str(e)}", exc_info=True)
            st.session_state.available_tickers = []

    return st.session_state.available_tickers


def initialize_rag_system(
    llm_provider: str = None, llm_model: str = None
) -> RAGQuerySystem:
    """
    Initialize RAG query system with optional LLM provider override.

    Args:
        llm_provider: LLM provider ('ollama' or 'openai'). If None, uses config default
        llm_model: LLM model name. If None, uses default for provider

    Returns:
        RAGQuerySystem instance
    """
    # Create a unique key based on provider and model to cache different instances
    cache_key = f"rag_system_{llm_provider}_{llm_model}"

    if cache_key not in st.session_state:
        logger.info(
            f"Initializing RAG system for Streamlit app "
            f"(provider={llm_provider}, model={llm_model})"
        )
        try:
            st.session_state[cache_key] = create_rag_system(
                llm_provider=llm_provider, llm_model=llm_model
            )
            logger.info("RAG system initialized successfully")
        except RAGQueryError as e:
            logger.error(f"Failed to initialize RAG system: {str(e)}", exc_info=True)
            st.error(f"Failed to initialize RAG system: {str(e)}")
            st.stop()
        except ValueError as e:
            logger.error(f"Failed to initialize LLM: {str(e)}", exc_info=True)
            st.error(f"Failed to initialize LLM: {str(e)}")
            st.info(
                "💡 **Tip:** Make sure OpenAI API key is set in .env file "
                "if using OpenAI"
            )
            st.stop()

    return st.session_state[cache_key]


def format_citations(sources: List[Dict[str, Any]]) -> str:
    """
    Format source citations as simple string.

    Args:
        sources: List of source metadata dictionaries

    Returns:
        Formatted citation string (e.g., "Source: document.pdf")
    """
    if not sources:
        return ""

    # Extract unique source filenames
    source_names = set()
    for source in sources:
        # Try to get filename from metadata
        filename = source.get("filename") or source.get("source", "unknown")
        # Extract just the filename if it's a path
        if isinstance(filename, str) and "/" in filename:
            filename = Path(filename).name
        source_names.add(filename)

    # Format as simple string
    if len(source_names) == 1:
        return f"Source: {list(source_names)[0]}"
    else:
        # Multiple sources
        sources_list = ", ".join(sorted(source_names))
        return f"Sources: {sources_list}"


def main():
    """Main Streamlit application."""
    # Initialize metrics and health checks (only once)
    if "monitoring_initialized" not in st.session_state:
        try:
            initialize_metrics()
            start_health_check_server()
            st.session_state.monitoring_initialized = True
            logger.info("Monitoring and health checks initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize monitoring: {e}")

    # Page configuration
    st.set_page_config(
        page_title="Financial Research Assistant",
        page_icon="📊",
        layout="wide",
    )

    # Model selection toggle at the top
    st.markdown("### Model Selection")
    col1, col2 = st.columns([1, 3])
    with col1:
        use_openai = st.toggle(
            "Use OpenAI",
            value=False,
            help=(
                "Switch between local Ollama (llama3.2) and "
                "OpenAI (gpt-4o-mini - cheapest)"
            ),
            key="model_toggle",
        )

    model_provider = "openai" if use_openai else "ollama"
    model_name = "gpt-4o-mini" if use_openai else "llama3.2"

    with col2:
        st.caption(f"Current: **{model_provider.upper()}** ({model_name})")

    st.divider()

    # Initialize RAG system with selected model
    rag_system = initialize_rag_system(
        llm_provider=model_provider, llm_model=model_name
    )

    # Sidebar with available tickers
    with st.sidebar:
        st.header("📈 Available Companies")
        st.markdown("Companies with documents in the database:")

        tickers = get_available_tickers()

        if tickers:
            # Display tickers in a clean list
            for ticker_info in tickers:
                ticker = ticker_info["ticker"]
                company = ticker_info["company"]
                count = ticker_info["count"]

                # Create expandable section for each company
                with st.expander(f"**{ticker}** - {company}", expanded=False):
                    st.markdown(f"**Ticker:** {ticker}")
                    st.markdown(f"**Company:** {company}")
                    st.markdown(f"**Documents:** {count} chunks")
        else:
            st.info("No companies found in database.")

        st.divider()
        st.markdown("**Total:** " + str(len(tickers)) + " companies")

    # Main content area
    # Title and description
    st.title("📊 Financial Research Assistant")
    st.markdown(
        "Ask questions about your financial documents. "
        "Answers are generated using RAG (Retrieval-Augmented Generation) technology."
    )

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

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

    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
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
                    # Query RAG system
                    result = rag_system.query(prompt)

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

                    # Add assistant message to chat history
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "sources": sources,
                        }
                    )

                except RAGQueryError as e:
                    error_msg = f"Error processing query: {str(e)}"
                    logger.error(f"RAG query error: {str(e)}", exc_info=True)
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


if __name__ == "__main__":
    main()
