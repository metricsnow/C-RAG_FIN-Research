"""
Document statistics UI component.

Provides UI for displaying document statistics and analytics.
"""

from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from app.ui.api_client import (
    APIClient,
    APIConnectionError,
    APIError,
)
from app.utils.document_manager import DocumentManager, DocumentManagerError
from app.utils.logger import get_logger

logger = get_logger(__name__)


def compute_statistics(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute statistics from document list (client-side).

    Args:
        documents: List of document dictionaries

    Returns:
        Dictionary with statistics
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
            stats = compute_statistics(all_documents)
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
