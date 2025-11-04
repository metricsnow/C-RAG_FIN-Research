"""
Streamlit frontend application for RAG-powered financial research assistant.

Provides a basic chat interface for querying documents with simple citations.
"""

import streamlit as st
from pathlib import Path
from typing import List, Dict, Any

from app.rag import RAGQuerySystem, RAGQueryError, create_rag_system


def initialize_rag_system() -> RAGQuerySystem:
    """
    Initialize RAG query system.
    
    Returns:
        RAGQuerySystem instance
    """
    if "rag_system" not in st.session_state:
        try:
            st.session_state.rag_system = create_rag_system()
        except RAGQueryError as e:
            st.error(f"Failed to initialize RAG system: {str(e)}")
            st.stop()
    return st.session_state.rag_system


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
    # Page configuration
    st.set_page_config(
        page_title="Financial Research Assistant",
        page_icon="📊",
        layout="wide",
    )
    
    # Title and description
    st.title("📊 Financial Research Assistant")
    st.markdown(
        "Ask questions about your financial documents. "
        "Answers are generated using RAG (Retrieval-Augmented Generation) technology."
    )
    
    # Initialize RAG system
    rag_system = initialize_rag_system()
    
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
                    # Query RAG system
                    result = rag_system.query(prompt)
                    
                    answer = result.get("answer", "I'm sorry, I couldn't generate an answer.")
                    sources = result.get("sources", [])
                    
                    # Display answer
                    st.markdown(answer)
                    
                    # Display citations
                    if sources:
                        citation = format_citations(sources)
                        if citation:
                            st.caption(citation)
                    
                    # Add assistant message to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    })
                    
                except RAGQueryError as e:
                    error_msg = f"Error processing query: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "sources": [],
                    })
                except Exception as e:
                    error_msg = f"Unexpected error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "sources": [],
                    })


if __name__ == "__main__":
    main()

