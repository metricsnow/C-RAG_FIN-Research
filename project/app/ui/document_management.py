"""
Document management UI components for Streamlit.

Provides UI for listing, searching, viewing, and deleting documents
from the ChromaDB vector database.
"""

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

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

    # Initialize document manager
    if "document_manager" not in st.session_state:
        try:
            st.session_state.document_manager = DocumentManager()
        except Exception as e:
            logger.error(
                f"Failed to initialize document manager: {str(e)}", exc_info=True
            )
            st.error(f"Failed to initialize document manager: {str(e)}")
            return

    doc_manager: DocumentManager = st.session_state.document_manager

    # Create tabs
    tab1, tab2, tab3 = st.tabs(
        ["📋 Documents List", "📊 Statistics", "🔍 Search & Filter"]
    )

    with tab1:
        render_documents_list(doc_manager)

    with tab2:
        render_statistics(doc_manager)

    with tab3:
        render_search_and_filter(doc_manager)


def render_documents_list(doc_manager: DocumentManager) -> None:
    """
    Render the documents list with pagination, sorting, and deletion.

    Args:
        doc_manager: DocumentManager instance
    """
    st.subheader("All Documents")

    try:
        # Get all documents
        all_documents = doc_manager.get_all_documents()

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

            # Delete button with confirmation
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🗑️ Delete Document", type="primary", key="delete_single"):
                    st.session_state.delete_confirm_id = selected_doc["id"]
                    st.session_state.delete_confirm_filename = extract_filename(
                        selected_doc.get("metadata", {})
                    )
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
                            deleted_count = doc_manager.delete_documents(
                                [st.session_state.delete_confirm_id]
                            )
                            if deleted_count > 0:
                                st.success("✅ Deleted document successfully!")
                                # Clear confirmation state
                                del st.session_state.delete_confirm_id
                                del st.session_state.delete_confirm_filename
                                # Reset page to 0
                                st.session_state.doc_page = 0
                                # Clear cache to refresh data
                                if "document_manager" in st.session_state:
                                    del st.session_state.document_manager
                                st.rerun()
                            else:
                                st.error("Failed to delete document.")
                        except DocumentManagerError as e:
                            st.error(f"Error deleting document: {str(e)}")
                            logger.error(
                                f"Failed to delete document: {str(e)}", exc_info=True
                            )

                with col2:
                    if st.button("❌ Cancel", key="cancel_delete"):
                        del st.session_state.delete_confirm_id
                        del st.session_state.delete_confirm_filename
                        st.rerun()

    except DocumentManagerError as e:
        st.error(f"Error loading documents: {str(e)}")
        logger.error(f"Failed to load documents: {str(e)}", exc_info=True)
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        logger.error(f"Unexpected error in document list: {str(e)}", exc_info=True)


def render_statistics(doc_manager: DocumentManager) -> None:
    """
    Render document statistics dashboard.

    Args:
        doc_manager: DocumentManager instance
    """
    st.subheader("Document Statistics")

    try:
        stats = doc_manager.get_statistics()

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

    except DocumentManagerError as e:
        st.error(f"Error loading statistics: {str(e)}")
        logger.error(f"Failed to load statistics: {str(e)}", exc_info=True)
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        logger.error(f"Unexpected error in statistics: {str(e)}", exc_info=True)


def render_search_and_filter(doc_manager: DocumentManager) -> None:
    """
    Render search and filter interface.

    Args:
        doc_manager: DocumentManager instance
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
                filtered_docs = doc_manager.get_documents_by_metadata(
                    ticker=ticker, form_type=form_type, filename=filename
                )

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
                                    deleted_count = doc_manager.delete_documents(
                                        st.session_state.bulk_delete_ids
                                    )
                                    st.success(
                                        f"✅ Deleted {deleted_count} documents "
                                        f"successfully!"
                                    )
                                    # Clear state
                                    del st.session_state.bulk_delete_ids
                                    del st.session_state.bulk_delete_count
                                    # Clear cache
                                    if "document_manager" in st.session_state:
                                        del st.session_state.document_manager
                                    st.rerun()
                                except DocumentManagerError as e:
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

            except DocumentManagerError as e:
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
