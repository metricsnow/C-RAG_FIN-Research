"""
Document list UI component.

Provides UI for listing, viewing, and managing documents with pagination and sorting.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from app.ui.api_client import (
    APIClient,
    APIConnectionError,
    APIError,
)
from app.ui.document_helpers import extract_filename, sort_documents
from app.utils.document_manager import DocumentManager, DocumentManagerError
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Items per page for pagination
ITEMS_PER_PAGE = 20


def render_documents_list(
    api_client: Optional[APIClient], doc_manager: Optional[DocumentManager]
) -> None:
    """
    Render the documents list with pagination, sorting, and deletion.

    Args:
        api_client: APIClient instance (if using API)
        doc_manager: DocumentManager instance (if using direct calls)
    """
    st.subheader("All Documents")

    try:
        # Get all documents via API or direct call
        if api_client:
            all_documents = api_client.list_documents()
        elif doc_manager:
            all_documents = doc_manager.get_all_documents()
        else:
            st.error("Neither API client nor DocumentManager available")
            return

        if not all_documents:
            st.info("No documents found in the database.")
            return

        # Pagination state
        if "doc_page" not in st.session_state:
            st.session_state.doc_page = 0

        # Sort options
        sort_by = st.selectbox(
            "Sort by",
            ["Date (Newest)", "Date (Oldest)", "Ticker", "Form Type", "Filename"],
            key="doc_sort_by",
        )

        # Apply sorting (using helper from document_helpers)
        sorted_docs = sort_documents(all_documents, sort_by)

        # Pagination
        total_pages = (len(sorted_docs) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        page = st.session_state.doc_page

        # Page navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("◀ Previous", disabled=page == 0, key="prev_page"):
                st.session_state.doc_page = max(0, page - 1)
                st.rerun()
        with col2:
            st.caption(
                f"Page {page + 1} of {total_pages} ({len(sorted_docs)} total documents)"
            )
        with col3:
            if st.button("Next ▶", disabled=page >= total_pages - 1, key="next_page"):
                st.session_state.doc_page = min(total_pages - 1, page + 1)
                st.rerun()

        # Get documents for current page
        start_idx = page * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, len(sorted_docs))
        page_docs = sorted_docs[start_idx:end_idx]

        # Create DataFrame for display
        df_data = []
        for doc in page_docs:
            metadata = doc.get("metadata", {})
            df_data.append(
                {
                    "ID": doc["id"][:8] + "...",  # Truncate ID for display
                    "Filename": extract_filename(metadata),
                    "Ticker": metadata.get("ticker", "N/A"),
                    "Form Type": metadata.get("form_type", "N/A"),
                    "Date": metadata.get("filing_date") or metadata.get("date", "N/A"),
                    "Chunk": metadata.get("chunk_index", "N/A"),
                }
            )

        df = pd.DataFrame(df_data)

        # Display table with selection
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            key="documents_table",
        )

        # Document details and deletion
        st.divider()
        st.subheader("Document Actions")
        selected_doc_idx = st.selectbox(
            "Select document to view or delete",
            range(len(page_docs)),
            format_func=lambda x: f"{df_data[x]['Filename']} ({df_data[x]['Ticker']})",
            key="selected_doc",
        )

        if selected_doc_idx is not None:
            selected_doc = page_docs[selected_doc_idx]

            # Display document details
            with st.expander("📄 View Document Details", expanded=False):
                render_document_details(selected_doc)

            # Version history (imported from main module to avoid circular dependency)
            source_name = extract_filename(selected_doc.get("metadata", {}))
            try:
                if api_client:
                    version_history = api_client.get_version_history(source_name)
                elif doc_manager:
                    version_history = doc_manager.get_version_history(source_name)
                else:
                    version_history = []

                if version_history:
                    # Import here to avoid circular dependency
                    from app.ui.document_management import render_version_history

                    with st.expander("📚 Version History", expanded=False):
                        render_version_history(
                            version_history, source_name, api_client, doc_manager
                        )
            except Exception as e:
                logger.debug(f"Could not load version history: {str(e)}")

            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("🔄 Re-index Document", key="reindex_single"):
                    st.session_state.reindex_source = source_name
                    st.session_state.reindex_doc_id = selected_doc["id"]
                    st.rerun()

            with col2:
                if st.button("🗑️ Delete Document", type="primary", key="delete_single"):
                    st.session_state.delete_confirm_id = selected_doc["id"]
                    st.session_state.delete_confirm_filename = source_name
                    st.rerun()

            # Re-index confirmation and file upload
            if "reindex_source" in st.session_state:
                st.info("📤 Please upload the updated document file to re-index")
                uploaded_file = st.file_uploader(
                    "Upload Document File",
                    type=["txt", "md", "pdf"],
                    key="reindex_file_upload",
                )

                if uploaded_file is not None:
                    # Save uploaded file temporarily
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
                            key="reindex_preserve_metadata",
                        )
                        increment_version = st.checkbox(
                            "Increment version number",
                            value=True,
                            key="reindex_increment_version",
                        )

                        if st.button(
                            "✅ Confirm Re-index", type="primary", key="confirm_reindex"
                        ):
                            try:
                                # Re-indexing requires DocumentManager
                                # (file upload via API is complex)
                                if not doc_manager:
                                    st.error(
                                        "Re-indexing requires DocumentManager. "
                                        "Please disable API client mode "
                                        "for re-indexing."
                                    )
                                    if tmp_path.exists():
                                        os.unlink(tmp_path)
                                    return

                                result = doc_manager.reindex_document(
                                    tmp_path,
                                    preserve_metadata=preserve_metadata,
                                    increment_version=increment_version,
                                )
                                st.success(
                                    f"✅ Re-indexed successfully! "
                                    f"Deleted {result['old_chunks_deleted']} "
                                    f"old chunks, created "
                                    f"{result['new_chunks_created']} new chunks, "
                                    f"version {result['version']}"
                                )
                                # Clean up
                                os.unlink(tmp_path)
                                del st.session_state.reindex_source
                                del st.session_state.reindex_doc_id
                                if "document_manager" in st.session_state:
                                    del st.session_state.document_manager
                                st.rerun()
                            except DocumentManagerError as e:
                                st.error(f"Error re-indexing document: {str(e)}")
                                logger.error(
                                    f"Failed to re-index document: {str(e)}",
                                    exc_info=True,
                                )
                                if tmp_path.exists():
                                    os.unlink(tmp_path)

                    with col2:
                        if st.button("❌ Cancel", key="cancel_reindex"):
                            if tmp_path.exists():
                                os.unlink(tmp_path)
                            del st.session_state.reindex_source
                            del st.session_state.reindex_doc_id
                            st.rerun()

            # Confirmation dialog
            if "delete_confirm_id" in st.session_state:
                st.warning(
                    f"⚠️ Are you sure you want to delete "
                    f"'{st.session_state.delete_confirm_filename}'? "
                    f"This action cannot be undone."
                )
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button(
                        "✅ Confirm Delete", type="primary", key="confirm_delete"
                    ):
                        try:
                            if api_client:
                                success = api_client.delete_document(
                                    st.session_state.delete_confirm_id
                                )
                                if success:
                                    st.success("✅ Deleted document successfully!")
                                else:
                                    st.error("Failed to delete document.")
                            elif doc_manager:
                                deleted_count = doc_manager.delete_documents(
                                    [st.session_state.delete_confirm_id]
                                )
                                if deleted_count > 0:
                                    st.success("✅ Deleted document successfully!")
                                else:
                                    st.error("Failed to delete document.")
                            else:
                                st.error(
                                    "Neither API client nor DocumentManager available"
                                )
                                return

                            # Clear confirmation state
                            del st.session_state.delete_confirm_id
                            del st.session_state.delete_confirm_filename
                            # Reset page to 0
                            st.session_state.doc_page = 0
                            # Clear cache to refresh data
                            if "document_manager" in st.session_state:
                                del st.session_state.document_manager
                            if "api_client" in st.session_state:
                                # Force refresh on next call
                                pass
                            st.rerun()
                        except (
                            DocumentManagerError,
                            APIError,
                            APIConnectionError,
                        ) as e:
                            st.error(f"Error deleting document: {str(e)}")
                            logger.error(
                                f"Failed to delete document: {str(e)}", exc_info=True
                            )

                with col2:
                    if st.button("❌ Cancel", key="cancel_delete"):
                        del st.session_state.delete_confirm_id
                        del st.session_state.delete_confirm_filename
                        st.rerun()

    except (DocumentManagerError, APIError, APIConnectionError) as e:
        st.error(f"Error loading documents: {str(e)}")
        logger.error(f"Failed to load documents: {str(e)}", exc_info=True)
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        logger.error(f"Unexpected error in document list: {str(e)}", exc_info=True)


def render_document_details(doc: Dict[str, Any]) -> None:
    """
    Render detailed view of a document.

    Args:
        doc: Document dictionary with id, metadata, and content
    """
    metadata = doc.get("metadata", {})
    content = doc.get("content", "")

    st.markdown("### Document Information")
    st.json(
        {
            "ID": doc["id"],
            "Filename": extract_filename(metadata),
            "Ticker": metadata.get("ticker", "N/A"),
            "Form Type": metadata.get("form_type", "N/A"),
            "Filing Date": metadata.get("filing_date") or metadata.get("date", "N/A"),
            "Chunk Index": metadata.get("chunk_index", "N/A"),
            "Source": metadata.get("source", "N/A"),
            "Content Length": len(content),
        }
    )

    st.markdown("### Document Content")
    st.text_area("Content", content, height=300, key="doc_content_view", disabled=True)
