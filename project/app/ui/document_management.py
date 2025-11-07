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
from app.utils.config import config
from app.utils.document_manager import DocumentManager, DocumentManagerError
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Items per page for pagination
ITEMS_PER_PAGE = 20


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

        # Apply sorting
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

            # Version history
            source_name = extract_filename(selected_doc.get("metadata", {}))
            try:
                if api_client:
                    version_history = api_client.get_version_history(source_name)
                elif doc_manager:
                    version_history = doc_manager.get_version_history(source_name)
                else:
                    version_history = []

                if version_history:
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


def _compute_statistics(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute statistics from document list (client-side).

    Args:
        documents: List of document dictionaries

    Returns:
        Statistics dictionary
    """
    stats = {
        "total_documents": len(documents),
        "total_chunks": len(documents),
        "unique_tickers": set(),
        "unique_form_types": set(),
        "documents_by_ticker": {},
        "documents_by_form_type": {},
    }

    for doc in documents:
        metadata = doc.get("metadata", {})
        ticker = metadata.get("ticker")
        form_type = metadata.get("form_type")

        if ticker:
            stats["unique_tickers"].add(ticker)
            stats["documents_by_ticker"][ticker] = (
                stats["documents_by_ticker"].get(ticker, 0) + 1
            )

        if form_type:
            stats["unique_form_types"].add(form_type)
            stats["documents_by_form_type"][form_type] = (
                stats["documents_by_form_type"].get(form_type, 0) + 1
            )

    stats["unique_tickers"] = len(stats["unique_tickers"])
    stats["unique_form_types"] = len(stats["unique_form_types"])

    return stats


def render_statistics(
    api_client: Optional[APIClient], doc_manager: Optional[DocumentManager]
) -> None:
    """
    Render document statistics dashboard.

    Args:
        api_client: APIClient instance (if using API)
        doc_manager: DocumentManager instance (if using direct calls)
    """
    st.subheader("Document Statistics")

    try:
        if api_client:
            # Get documents via API and compute stats client-side
            all_documents = api_client.list_documents()
            stats = _compute_statistics(all_documents)
        elif doc_manager:
            # Use DocumentManager statistics
            stats = doc_manager.get_statistics()
        else:
            st.error("Neither API client nor DocumentManager available")
            return

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documents", stats["total_documents"])
        with col2:
            st.metric("Total Chunks", stats["total_chunks"])
        with col3:
            st.metric("Unique Tickers", stats["unique_tickers"])
        with col4:
            st.metric("Unique Form Types", stats["unique_form_types"])

        st.divider()

        # Documents by ticker
        if stats["documents_by_ticker"]:
            st.subheader("Documents by Ticker")
            ticker_df = pd.DataFrame(
                list(stats["documents_by_ticker"].items()),
                columns=["Ticker", "Count"],
            ).sort_values("Count", ascending=False)
            st.bar_chart(ticker_df.set_index("Ticker"))
            st.dataframe(ticker_df, use_container_width=True, hide_index=True)

        st.divider()

        # Documents by form type
        if stats["documents_by_form_type"]:
            st.subheader("Documents by Form Type")
            form_type_df = pd.DataFrame(
                list(stats["documents_by_form_type"].items()),
                columns=["Form Type", "Count"],
            ).sort_values("Count", ascending=False)
            st.bar_chart(form_type_df.set_index("Form Type"))
            st.dataframe(form_type_df, use_container_width=True, hide_index=True)

    except (DocumentManagerError, APIError, APIConnectionError) as e:
        st.error(f"Error loading statistics: {str(e)}")
        logger.error(f"Failed to load statistics: {str(e)}", exc_info=True)
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        logger.error(f"Unexpected error in statistics: {str(e)}", exc_info=True)


def _filter_documents(
    documents: List[Dict[str, Any]],
    ticker: Optional[str] = None,
    form_type: Optional[str] = None,
    filename: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filter documents by metadata (client-side).

    Args:
        documents: List of document dictionaries
        ticker: Ticker symbol filter
        form_type: Form type filter
        filename: Filename filter (partial match)

    Returns:
        Filtered list of documents
    """
    filtered = documents

    if ticker:
        ticker_upper = ticker.upper()
        filtered = [
            doc
            for doc in filtered
            if doc.get("metadata", {}).get("ticker", "").upper() == ticker_upper
        ]

    if form_type:
        filtered = [
            doc
            for doc in filtered
            if doc.get("metadata", {}).get("form_type") == form_type
        ]

    if filename:
        filename_lower = filename.lower()
        filtered = [
            doc
            for doc in filtered
            if filename_lower in extract_filename(doc.get("metadata", {})).lower()
        ]

    return filtered


def render_search_and_filter(
    api_client: Optional[APIClient], doc_manager: Optional[DocumentManager]
) -> None:
    """
    Render search and filter interface.

    Args:
        api_client: APIClient instance (if using API)
        doc_manager: DocumentManager instance (if using direct calls)
    """
    st.subheader("Search & Filter Documents")

    with st.form("search_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            ticker_filter = st.text_input("Ticker Symbol", key="search_ticker")
            form_type_filter = st.selectbox(
                "Form Type",
                ["All", "10-K", "10-Q", "8-K", "Other"],
                key="search_form_type",
            )
        with col2:
            filename_filter = st.text_input(
                "Filename (partial match)", key="search_filename"
            )

        submitted = st.form_submit_button("🔍 Search", type="primary")

        if submitted:
            # Apply filters
            ticker = ticker_filter.strip() if ticker_filter else None
            form_type = form_type_filter if form_type_filter != "All" else None
            filename = filename_filter.strip() if filename_filter else None

            try:
                if api_client:
                    # Get all documents and filter client-side
                    all_documents = api_client.list_documents()
                    filtered_docs = _filter_documents(
                        all_documents,
                        ticker=ticker,
                        form_type=form_type,
                        filename=filename,
                    )
                elif doc_manager:
                    # Use DocumentManager filtering
                    filtered_docs = doc_manager.get_documents_by_metadata(
                        ticker=ticker, form_type=form_type, filename=filename
                    )
                else:
                    st.error("Neither API client nor DocumentManager available")
                    return

                if not filtered_docs:
                    st.info("No documents found matching the search criteria.")
                else:
                    st.success(f"Found {len(filtered_docs)} documents")

                    # Display results
                    df_data = []
                    for doc in filtered_docs:
                        metadata = doc.get("metadata", {})
                        df_data.append(
                            {
                                "ID": doc["id"][:8] + "...",
                                "Filename": extract_filename(metadata),
                                "Ticker": metadata.get("ticker", "N/A"),
                                "Form Type": metadata.get("form_type", "N/A"),
                                "Date": metadata.get("filing_date")
                                or metadata.get("date", "N/A"),
                            }
                        )

                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Bulk delete option
                    st.divider()
                    st.subheader("Bulk Actions")

                    if st.button("🗑️ Delete All Filtered Documents", type="primary"):
                        st.session_state.bulk_delete_ids = [
                            doc["id"] for doc in filtered_docs
                        ]
                        st.session_state.bulk_delete_count = len(filtered_docs)
                        st.rerun()

                    # Bulk delete confirmation
                    if "bulk_delete_ids" in st.session_state:
                        st.warning(
                            f"⚠️ Are you sure you want to delete "
                            f"{st.session_state.bulk_delete_count} documents? "
                            f"This action cannot be undone."
                        )
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("✅ Confirm Bulk Delete", type="primary"):
                                try:
                                    if api_client:
                                        # Delete via API (one by one)
                                        deleted_count = 0
                                        for doc_id in st.session_state.bulk_delete_ids:
                                            if api_client.delete_document(doc_id):
                                                deleted_count += 1
                                        st.success(
                                            f"✅ Deleted {deleted_count} documents "
                                            f"successfully!"
                                        )
                                    elif doc_manager:
                                        deleted_count = doc_manager.delete_documents(
                                            st.session_state.bulk_delete_ids
                                        )
                                        st.success(
                                            f"✅ Deleted {deleted_count} documents "
                                            f"successfully!"
                                        )
                                    else:
                                        st.error(
                                            "Neither API client nor "
                                            "DocumentManager available"
                                        )
                                        return

                                    # Clear state
                                    del st.session_state.bulk_delete_ids
                                    del st.session_state.bulk_delete_count
                                    # Clear cache
                                    if "document_manager" in st.session_state:
                                        del st.session_state.document_manager
                                    st.rerun()
                                except (
                                    DocumentManagerError,
                                    APIError,
                                    APIConnectionError,
                                ) as e:
                                    st.error(f"Error deleting documents: {str(e)}")
                                    logger.error(
                                        f"Failed to delete documents: {str(e)}",
                                        exc_info=True,
                                    )

                        with col2:
                            if st.button("❌ Cancel", key="cancel_bulk_delete"):
                                del st.session_state.bulk_delete_ids
                                del st.session_state.bulk_delete_count
                                st.rerun()

            except (DocumentManagerError, APIError, APIConnectionError) as e:
                st.error(f"Error searching documents: {str(e)}")
                logger.error(f"Failed to search documents: {str(e)}", exc_info=True)


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


def sort_documents(
    documents: List[Dict[str, Any]], sort_by: str
) -> List[Dict[str, Any]]:
    """
    Sort documents by the specified criteria.

    Args:
        documents: List of document dictionaries
        sort_by: Sort criteria

    Returns:
        Sorted list of documents
    """
    if sort_by == "Date (Newest)":
        return sorted(
            documents,
            key=lambda x: x.get("metadata", {}).get("filing_date")
            or x.get("metadata", {}).get("date", ""),
            reverse=True,
        )
    elif sort_by == "Date (Oldest)":
        return sorted(
            documents,
            key=lambda x: x.get("metadata", {}).get("filing_date")
            or x.get("metadata", {}).get("date", ""),
        )
    elif sort_by == "Ticker":
        return sorted(
            documents,
            key=lambda x: x.get("metadata", {}).get("ticker", ""),
        )
    elif sort_by == "Form Type":
        return sorted(
            documents,
            key=lambda x: x.get("metadata", {}).get("form_type", ""),
        )
    elif sort_by == "Filename":
        return sorted(
            documents,
            key=lambda x: extract_filename(x.get("metadata", {})),
        )
    else:
        return documents


def extract_filename(metadata: Dict[str, Any]) -> str:
    """
    Extract filename from metadata.

    Args:
        metadata: Document metadata dictionary

    Returns:
        Filename string
    """
    filename = metadata.get("filename") or metadata.get("source", "unknown")
    if isinstance(filename, str) and "/" in filename:
        return Path(filename).name
    return str(filename)


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
