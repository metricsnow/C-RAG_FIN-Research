"""
Filter builder for ChromaDB where clauses.

Converts user-friendly filter specifications into ChromaDB-compatible
where clause dictionaries.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


class FilterBuilderError(Exception):
    """Custom exception for filter building errors."""

    pass


class FilterBuilder:
    """
    Builder for ChromaDB where clause filters.

    Converts filter specifications into ChromaDB-compatible where clauses
    supporting complex Boolean logic and metadata filtering.
    """

    def __init__(self):
        """Initialize filter builder."""
        logger.debug("Initializing filter builder")

    def build_where_clause(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Build ChromaDB where clause from filter specifications.

        Args:
            filters: Dictionary of filter specifications with keys:
                - date_from: Start date (ISO format string)
                - date_to: End date (ISO format string)
                - document_type: Document type filter
                - ticker: Ticker symbol filter
                - form_type: Form type filter (e.g., "10-K", "10-Q")
                - source: Source identifier filter
                - metadata: Custom metadata filters

        Returns:
            ChromaDB where clause dictionary or None if no filters

        Raises:
            FilterBuilderError: If filter building fails
        """
        if not filters:
            return None

        logger.debug(f"Building where clause from filters: {filters}")

        try:
            where_conditions: List[Dict[str, Any]] = []

            # Date range filter
            date_filter = self._build_date_filter(filters)
            if date_filter:
                where_conditions.append(date_filter)

            # Document type filter
            if "document_type" in filters:
                where_conditions.append({"type": filters["document_type"]})

            # Ticker filter
            if "ticker" in filters:
                where_conditions.append({"ticker": filters["ticker"]})

            # Form type filter
            if "form_type" in filters:
                where_conditions.append({"form_type": filters["form_type"]})

            # Source filter
            if "source" in filters:
                where_conditions.append({"source": filters["source"]})

            # Custom metadata filters
            if "metadata" in filters and isinstance(filters["metadata"], dict):
                for key, value in filters["metadata"].items():
                    where_conditions.append({key: value})

            # Combine conditions
            if not where_conditions:
                return None

            if len(where_conditions) == 1:
                where_clause = where_conditions[0]
            else:
                # Use $and to combine multiple conditions
                where_clause = {"$and": where_conditions}

            logger.debug(f"Built where clause: {where_clause}")
            return where_clause

        except Exception as e:
            logger.error(f"Failed to build where clause: {str(e)}", exc_info=True)
            raise FilterBuilderError(f"Failed to build where clause: {str(e)}") from e

    def _build_date_filter(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build date range filter."""
        date_from = filters.get("date_from")
        date_to = filters.get("date_to")

        if not date_from and not date_to:
            return None

        date_conditions: List[Dict[str, Any]] = []

        # Parse dates if strings
        if date_from:
            if isinstance(date_from, str):
                try:
                    date_from_dt = datetime.fromisoformat(
                        date_from.replace("Z", "+00:00")
                    )
                except ValueError:
                    logger.warning(f"Could not parse date_from: {date_from}")
                    date_from_dt = None
            else:
                date_from_dt = date_from

            if date_from_dt:
                # ChromaDB uses date strings in metadata
                date_conditions.append(
                    {"date": {"$gte": date_from_dt.strftime("%Y-%m-%d")}}
                )

        if date_to:
            if isinstance(date_to, str):
                try:
                    date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
                except ValueError:
                    logger.warning(f"Could not parse date_to: {date_to}")
                    date_to_dt = None
            else:
                date_to_dt = date_to

            if date_to_dt:
                date_conditions.append(
                    {"date": {"$lte": date_to_dt.strftime("%Y-%m-%d")}}
                )

        if not date_conditions:
            return None

        if len(date_conditions) == 1:
            return date_conditions[0]
        else:
            return {"$and": date_conditions}

    def build_where_document_clause(
        self, document_filters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Build ChromaDB where_document clause for document content filtering.

        Args:
            document_filters: Dictionary with keys:
                - contains: String that must be contained in document
                - not_contains: String that must not be contained

        Returns:
            ChromaDB where_document clause or None
        """
        if not document_filters:
            return None

        logger.debug(f"Building where_document clause: {document_filters}")

        try:
            if "contains" in document_filters:
                return {"$contains": document_filters["contains"]}
            elif "not_contains" in document_filters:
                # ChromaDB doesn't directly support $not_contains
                # This would need to be handled at application level
                logger.warning("$not_contains not directly supported by ChromaDB")
                return None

            return None

        except Exception as e:
            logger.error(
                f"Failed to build where_document clause: {str(e)}",
                exc_info=True,
            )
            raise FilterBuilderError(
                f"Failed to build where_document clause: {str(e)}"
            ) from e
