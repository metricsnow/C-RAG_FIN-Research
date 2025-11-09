"""
Helper functions for document management UI.

Provides utility functions used across document management components.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


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


def filter_documents(
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
