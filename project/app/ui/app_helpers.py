"""
Helper functions for main Streamlit app.

Provides utility functions used across the app.
"""

from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from app.vector_db.chroma_store import ChromaStore


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
        except Exception as e:
            from app.utils.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to load tickers: {str(e)}", exc_info=True)
            st.session_state.available_tickers = []

    return st.session_state.available_tickers


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
