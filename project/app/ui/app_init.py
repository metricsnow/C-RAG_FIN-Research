"""
Initialization functions for main Streamlit app.

Provides functions for initializing API client and RAG system.
"""

import streamlit as st

from app.rag import RAGQueryError, RAGQuerySystem, create_rag_system
from app.ui.api_client import APIClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


def initialize_api_client() -> APIClient:
    """
    Initialize API client for FastAPI backend.

    Returns:
        APIClient instance
    """
    if "api_client" not in st.session_state:
        logger.info("Initializing API client for Streamlit app")
        try:
            st.session_state.api_client = APIClient()
            logger.info("API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize API client: {str(e)}", exc_info=True)
            st.error(f"Failed to initialize API client: {str(e)}")
            st.info(
                "💡 **Tip:** Make sure the FastAPI backend is running. "
                "You can start it with: python scripts/start_api.py"
            )
            st.stop()

    return st.session_state.api_client


def initialize_rag_system(
    llm_provider: str = None, llm_model: str = None
) -> RAGQuerySystem:
    """
    Initialize RAG query system with optional LLM provider override.

    Used as fallback when API client is disabled.

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
