"""
Document management UI components for Streamlit.

Provides UI for listing, searching, viewing, and deleting documents
from the ChromaDB vector database.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from app.ui.api_client import (
    APIClient,
    APIConnectionError,
    APIError,
)
from app.ui.document_list import render_documents_list
from app.ui.document_search import render_search_and_filter
from app.ui.document_stats import render_statistics
from app.utils.config import config
from app.utils.document_manager import DocumentManager, DocumentManagerError
from app.utils.logger import get_logger

logger = get_logger(__name__)


def render_document_management() -> None:
    """
    Render the document management interface.

    Creates tabs for different views: Documents List, Statistics, and Search.
    """
    st.header("📄 Document Management")

    # Initialize API client or document manager based on configuration
    api_client: Optional[APIClient] = None
    doc_manager: Optional[DocumentManager] = None

    if config.api_client_enabled:
        # Try to use API client
        if "api_client" not in st.session_state:
            try:
                st.session_state.api_client = APIClient()
            except Exception as e:
                logger.warning(
                    f"Failed to initialize API client: {str(e)}", exc_info=True
                )
                st.warning(
                    "⚠️ API client unavailable. Falling back to direct DocumentManager."
                )
        else:
            api_client = st.session_state.api_client
            # Check API health
            try:
                health = api_client.health_check()
                if health.get("status") != "healthy":
                    api_client = None
            except APIConnectionError:
                api_client = None

    # Fallback to direct DocumentManager if API client is disabled or unavailable
    if not api_client:
        if "document_manager" not in st.session_state:
            try:
                st.session_state.document_manager = DocumentManager()
            except Exception as e:
                logger.error(
                    f"Failed to initialize document manager: {str(e)}", exc_info=True
                )
                st.error(f"Failed to initialize document manager: {str(e)}")
                return
        doc_manager = st.session_state.document_manager

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📋 Documents List",
            "📊 Statistics",
            "🔍 Search & Filter",
            "🔄 Re-index & Versions",
        ]
    )

    with tab1:
        render_documents_list(api_client, doc_manager)

    with tab2:
        render_statistics(api_client, doc_manager)

    with tab3:
        render_search_and_filter(api_client, doc_manager)

    with tab4:
        render_reindex_interface(api_client, doc_manager)


def render_version_history(
    version_history: List[Dict[str, Any]],
    source: str,
    api_client: Optional[APIClient],
    doc_manager: Optional[DocumentManager],
) -> None:
    """
    Render version history for a document.

    Args:
        version_history: List of version information dictionaries
        source: Source filename
        api_client: APIClient instance (if using API)
        doc_manager: DocumentManager instance (if using direct calls)
    """
    st.markdown(f"### Version History for: {source}")

    if not version_history:
        st.info("No version history available.")
        return

    # Display version list
    version_df_data = []
    for version_info in version_history:
        version_df_data.append(
            {
                "Version": version_info["version"],
                "Date": version_info.get("version_date", "unknown"),
                "Chunks": version_info["chunk_count"],
            }
        )

    version_df = pd.DataFrame(version_df_data)
    st.dataframe(version_df, use_container_width=True, hide_index=True)

    # Version comparison
    if len(version_history) >= 2:
        st.divider()
        st.markdown("### Compare Versions")

        col1, col2 = st.columns(2)
        with col1:
            version1 = st.selectbox(
                "Version 1",
                [v["version"] for v in version_history],
                key="compare_version1",
            )
        with col2:
            version2 = st.selectbox(
                "Version 2",
                [v["version"] for v in version_history],
                key="compare_version2",
            )

        if st.button("🔍 Compare Versions", key="compare_versions"):
            try:
                if api_client:
                    comparison = api_client.compare_versions(source, version1, version2)
                elif doc_manager:
                    comparison = doc_manager.compare_versions(
                        source, version1, version2
                    )
                else:
                    st.error("Neither API client nor DocumentManager available")
                    return
                st.markdown("#### Comparison Results")

                # Display version info
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Version 1:**")
                    st.json(comparison["version1_info"])
                with col2:
                    st.markdown("**Version 2:**")
                    st.json(comparison["version2_info"])

                # Display differences
                if comparison["differences"]:
                    st.markdown("#### Differences")
                    diff_df = pd.DataFrame(comparison["differences"])
                    st.dataframe(diff_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No differences found between versions.")
            except (DocumentManagerError, APIError, APIConnectionError) as e:
                st.error(f"Error comparing versions: {str(e)}")
                logger.error(f"Failed to compare versions: {str(e)}", exc_info=True)


def render_reindex_interface(
    api_client: Optional[APIClient], doc_manager: Optional[DocumentManager]
) -> None:
    """
    Render re-indexing interface.

    Args:
        api_client: APIClient instance (if using API)
        doc_manager: DocumentManager instance (if using direct calls)
    """
    st.subheader("Document Re-indexing")

    # Re-indexing via API requires file upload which is complex
    # For now, only support re-indexing via DocumentManager
    if api_client and not doc_manager:
        st.info(
            "⚠️ Re-indexing via API is not yet fully supported. "
            "Please use direct DocumentManager mode (set API_CLIENT_ENABLED=false) "
            "or use the API endpoint directly for re-indexing."
        )
        return

    if not doc_manager:
        st.error("DocumentManager not available for re-indexing")
        return

    try:
        # Get all documents grouped by source
        grouped_docs = doc_manager.group_documents_by_source()

        if not grouped_docs:
            st.info("No documents found in the database.")
            return

        # Source selection
        source_names = sorted(grouped_docs.keys())
        selected_source = st.selectbox(
            "Select Document Source to Re-index",
            source_names,
            key="reindex_source_select",
        )

        if selected_source:
            chunks = grouped_docs[selected_source]
            st.info(f"Found {len(chunks)} chunks for '{selected_source}'")

            # Show current version
            try:
                current_version = doc_manager.get_current_version(selected_source)
                st.metric(
                    "Current Version", current_version if current_version > 0 else "N/A"
                )
            except Exception:
                st.metric("Current Version", "N/A")

            # File upload for re-indexing
            st.divider()
            st.markdown("### Upload Updated Document")

            uploaded_file = st.file_uploader(
                "Upload Document File",
                type=["txt", "md", "pdf"],
                key="reindex_batch_file_upload",
            )

            if uploaded_file is not None:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
                ) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = Path(tmp_file.name)

                col1, col2 = st.columns([1, 1])
                with col1:
                    preserve_metadata = st.checkbox(
                        "Preserve metadata (ticker, form_type, etc.)",
                        value=True,
                        key="reindex_batch_preserve_metadata",
                    )
                    increment_version = st.checkbox(
                        "Increment version number",
                        value=True,
                        key="reindex_batch_increment_version",
                    )

                    if st.button(
                        "🔄 Re-index Document",
                        type="primary",
                        key="reindex_batch_confirm",
                    ):
                        try:
                            with st.spinner("Re-indexing document..."):
                                result = doc_manager.reindex_document(
                                    tmp_path,
                                    preserve_metadata=preserve_metadata,
                                    increment_version=increment_version,
                                )
                            st.success(
                                f"✅ Re-indexed successfully!\n\n"
                                f"- **Old chunks deleted:** "
                                f"{result['old_chunks_deleted']}\n"
                                f"- **New chunks created:** "
                                f"{result['new_chunks_created']}\n"
                                f"- **New version:** {result['version']}"
                            )
                            # Clean up
                            os.unlink(tmp_path)
                            if "document_manager" in st.session_state:
                                del st.session_state.document_manager
                            st.rerun()
                        except DocumentManagerError as e:
                            st.error(f"Error re-indexing document: {str(e)}")
                            logger.error(
                                f"Failed to re-index document: {str(e)}", exc_info=True
                            )
                            if tmp_path.exists():
                                os.unlink(tmp_path)

                with col2:
                    if st.button("❌ Cancel", key="cancel_reindex_batch"):
                        if tmp_path.exists():
                            os.unlink(tmp_path)
                        st.rerun()

    except DocumentManagerError as e:
        st.error(f"Error loading documents: {str(e)}")
        logger.error(f"Failed to load documents: {str(e)}", exc_info=True)
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        logger.error(f"Unexpected error in re-index interface: {str(e)}", exc_info=True)
