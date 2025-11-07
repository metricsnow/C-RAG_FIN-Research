"""
Advanced query parser for Boolean operators and filtering.

Supports parsing queries with AND, OR, NOT operators and extracting
filter specifications from natural language queries.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from app.utils.logger import get_logger

logger = get_logger(__name__)


class QueryParseError(Exception):
    """Custom exception for query parsing errors."""

    pass


class QueryParser:
    """
    Parser for advanced queries with Boolean operators and filters.

    Supports:
    - Boolean operators: AND, OR, NOT
    - Date range filtering
    - Document type filtering
    - Metadata-based filtering
    - Source-specific filtering
    """

    # Boolean operator patterns (case-insensitive)
    AND_PATTERN = re.compile(r"\b(?:AND|&)\b", re.IGNORECASE)
    OR_PATTERN = re.compile(r"\b(?:OR|\|)\b", re.IGNORECASE)
    NOT_PATTERN = re.compile(r"\b(?:NOT|!)\b", re.IGNORECASE)

    # Date patterns
    DATE_PATTERN = re.compile(
        r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b|"
        r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b|"
        r"\b(\w+)\s+(\d{1,2}),\s+(\d{4})\b"
    )

    # Filter patterns
    FILTER_PATTERN = re.compile(
        r"\b(?:from|since|after|before|until|between|type|source|"
        r"ticker|form)\s*[:=]?\s*([^\s,]+)",
        re.IGNORECASE,
    )

    def __init__(self):
        """Initialize query parser."""
        logger.debug("Initializing query parser")

    def parse(self, query: str, extract_filters: bool = True) -> Dict[str, Any]:
        """
        Parse a query string into components.

        Args:
            query: Natural language query string
            extract_filters: Whether to extract filter specifications

        Returns:
            Dictionary with keys:
                - query_text: Cleaned query text without filters
                - boolean_operators: List of Boolean operators found
                - filters: Extracted filter specifications
                - query_terms: List of query terms

        Raises:
            QueryParseError: If parsing fails
        """
        if not query or not query.strip():
            raise QueryParseError("Query cannot be empty")

        logger.debug(f"Parsing query: '{query[:50]}...'")

        try:
            # Extract filters if requested
            filters = {}
            cleaned_query = query
            if extract_filters:
                filters, cleaned_query = self._extract_filters(query)

            # Detect Boolean operators
            boolean_operators = self._detect_boolean_operators(cleaned_query)

            # Extract query terms
            query_terms = self._extract_terms(cleaned_query)

            result = {
                "query_text": cleaned_query.strip(),
                "boolean_operators": boolean_operators,
                "filters": filters,
                "query_terms": query_terms,
                "original_query": query,
            }

            logger.debug(
                f"Parsed query: operators={boolean_operators}, "
                f"filters={filters}, terms={len(query_terms)}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to parse query: {str(e)}", exc_info=True)
            raise QueryParseError(f"Failed to parse query: {str(e)}") from e

    def _extract_filters(self, query: str) -> Tuple[Dict[str, Any], str]:
        """
        Extract filter specifications from query.

        Args:
            query: Original query string

        Returns:
            Tuple of (filters_dict, cleaned_query)
        """
        filters: Dict[str, Any] = {}
        cleaned_query = query

        # Extract date range filters
        date_filters, cleaned_query = self._extract_date_filters(cleaned_query)
        if date_filters:
            filters.update(date_filters)

        # Extract document type filters
        type_filters, cleaned_query = self._extract_type_filters(cleaned_query)
        if type_filters:
            filters.update(type_filters)

        # Extract source/ticker filters
        source_filters, cleaned_query = self._extract_source_filters(cleaned_query)
        if source_filters:
            filters.update(source_filters)

        # Extract form type filters
        form_filters, cleaned_query = self._extract_form_filters(cleaned_query)
        if form_filters:
            filters.update(form_filters)

        return filters, cleaned_query

    def _extract_date_filters(self, query: str) -> Tuple[Dict[str, Any], str]:
        """Extract date range filters from query."""
        filters: Dict[str, Any] = {}
        cleaned_query = query

        # Pattern for date ranges
        date_range_pattern = re.compile(
            r"\b(?:from|since|after|before|until|between)\s+"
            r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\w+\s+\d{1,2},\s+\d{4})"
            r"(?:\s+(?:and|to)\s+"
            r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\w+\s+\d{1,2},\s+\d{4}))?",
            re.IGNORECASE,
        )

        matches = date_range_pattern.finditer(query)
        for match in matches:
            prefix = match.group(0).lower()
            date1_str = match.group(1)
            date2_str = match.group(2) if match.group(2) else None

            try:
                date1 = self._parse_date(date1_str)
                date2 = self._parse_date(date2_str) if date2_str else None

                if "from" in prefix or "since" in prefix or "after" in prefix:
                    filters["date_from"] = date1.strftime("%Y-%m-%d")
                elif "before" in prefix or "until" in prefix:
                    filters["date_to"] = date1.strftime("%Y-%m-%d")
                elif "between" in prefix and date2:
                    filters["date_from"] = date1.strftime("%Y-%m-%d")
                    filters["date_to"] = date2.strftime("%Y-%m-%d")

                # Remove from query
                cleaned_query = cleaned_query.replace(match.group(0), "")

            except (ValueError, AttributeError):
                logger.warning(f"Could not parse date: {date1_str}")
                continue

        return filters, cleaned_query

    def _extract_type_filters(self, query: str) -> Tuple[Dict[str, Any], str]:
        """Extract document type filters from query."""
        filters: Dict[str, Any] = {}
        cleaned_query = query

        # Pattern for document type
        type_pattern = re.compile(r"\btype\s*[:=]?\s*(\w+(?:-\w+)?)", re.IGNORECASE)

        matches = type_pattern.finditer(query)
        for match in matches:
            doc_type = match.group(1).lower()
            filters["document_type"] = doc_type
            cleaned_query = cleaned_query.replace(match.group(0), "")

        return filters, cleaned_query

    def _extract_source_filters(self, query: str) -> Tuple[Dict[str, Any], str]:
        """Extract source/ticker filters from query."""
        filters: Dict[str, Any] = {}
        cleaned_query = query

        # Pattern for ticker/source
        ticker_pattern = re.compile(
            r"\b(?:ticker|source)\s*[:=]?\s*([A-Z]{1,5})", re.IGNORECASE
        )

        matches = ticker_pattern.finditer(query)
        for match in matches:
            ticker = match.group(1).upper()
            filters["ticker"] = ticker
            cleaned_query = cleaned_query.replace(match.group(0), "")

        return filters, cleaned_query

    def _extract_form_filters(self, query: str) -> Tuple[Dict[str, Any], str]:
        """Extract form type filters from query."""
        filters: Dict[str, Any] = {}
        cleaned_query = query

        # Pattern for form type (10-K, 10-Q, etc.)
        form_pattern = re.compile(r"\bform\s*[:=]?\s*(\d+[-\w]*)", re.IGNORECASE)

        matches = form_pattern.finditer(query)
        for match in matches:
            form_type = match.group(1).upper()
            filters["form_type"] = form_type
            cleaned_query = cleaned_query.replace(match.group(0), "")

        return filters, cleaned_query

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string into datetime object."""
        if not date_str:
            raise ValueError("Date string cannot be empty")

        # Try different date formats
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%B %d, %Y",
            "%b %d, %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        raise ValueError(f"Could not parse date: {date_str}")

    def _detect_boolean_operators(self, query: str) -> List[str]:
        """Detect Boolean operators in query."""
        operators = []

        if self.AND_PATTERN.search(query):
            operators.append("AND")
        if self.OR_PATTERN.search(query):
            operators.append("OR")
        if self.NOT_PATTERN.search(query):
            operators.append("NOT")

        return operators

    def _extract_terms(self, query: str) -> List[str]:
        """Extract query terms (words) from query."""
        # Remove Boolean operators and special characters
        cleaned = self.AND_PATTERN.sub(" ", query)
        cleaned = self.OR_PATTERN.sub(" ", cleaned)
        cleaned = self.NOT_PATTERN.sub(" ", cleaned)

        # Extract words
        words = re.findall(r"\b\w+\b", cleaned.lower())
        # Filter out common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "not",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
            "what",
            "which",
            "who",
            "when",
            "where",
            "why",
            "how",
        }
        terms = [w for w in words if w not in stop_words and len(w) > 2]

        return terms
