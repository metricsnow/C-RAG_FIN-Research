"""
Streamlit frontend application for RAG-powered financial research assistant.

Provides a basic chat interface for querying documents with simple citations.
"""

import os
import sys
from pathlib import Path

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

from app.ui.api_client import APIConnectionError  # noqa: E402
from app.ui.app_helpers import get_available_tickers  # noqa: E402
from app.ui.app_init import initialize_api_client, initialize_rag_system  # noqa: E402
from app.ui.chat_interface import render_chat_interface  # noqa: E402
from app.ui.document_management import render_document_management  # noqa: E402
from app.utils.config import config  # noqa: E402
from app.utils.health import start_health_check_server  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402
from app.utils.metrics import initialize_metrics  # noqa: E402

logger = get_logger(__name__)


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

    # Initialize API client or RAG system based on configuration
    api_client = None
    rag_system = None

    if config.api_client_enabled:
        try:
            api_client = initialize_api_client()
            # Check API health
            try:
                health = api_client.health_check()
                if health.get("status") != "healthy":
                    st.warning(
                        "⚠️ API health check failed. Falling back to direct RAG calls."
                    )
                    api_client = None
            except APIConnectionError:
                st.warning(
                    "⚠️ Cannot connect to API. Falling back to direct RAG calls. "
                    "Make sure the FastAPI backend is running."
                )
                api_client = None
        except Exception as e:
            logger.warning(f"API client initialization failed: {str(e)}")
            st.warning("⚠️ API client unavailable. Falling back to direct RAG calls.")
            api_client = None

    # Fallback to direct RAG system if API client is disabled or unavailable
    if not api_client:
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

    # Main content area with tabs
    # Create main tabs for Chat and Document Management
    main_tab1, main_tab2 = st.tabs(["💬 Chat", "📄 Document Management"])

    with main_tab1:
        render_chat_interface(api_client, rag_system, model_provider, model_name)

    with main_tab2:
        render_document_management()


if __name__ == "__main__":
    main()
