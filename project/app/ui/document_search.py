"""
Document search and filter UI component.

Provides UI for searching and filtering documents with bulk actions.
"""

from typing import Optional

import pandas as pd
import streamlit as st

from app.ui.api_client import (
    APIClient,
    APIConnectionError,
    APIError,
)
from app.ui.document_helpers import extract_filename, filter_documents
from app.utils.document_manager import DocumentManager, DocumentManagerError
from app.utils.logger import get_logger

logger = get_logger(__name__)


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
                    filtered_docs = filter_documents(
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
