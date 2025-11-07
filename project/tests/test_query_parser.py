"""
Tests for query parser module.
"""

import pytest

from app.rag.query_parser import QueryParseError, QueryParser


class TestQueryParser:
    """Test cases for QueryParser."""

    def test_init(self):
        """Test parser initialization."""
        parser = QueryParser()
        assert parser is not None

    def test_parse_simple_query(self):
        """Test parsing a simple query without filters."""
        parser = QueryParser()
        result = parser.parse("What is revenue?", extract_filters=False)

        assert result["query_text"] == "What is revenue?"
        assert result["boolean_operators"] == []
        assert result["filters"] == {}
        assert "revenue" in result["query_terms"]

    def test_parse_with_date_filter(self):
        """Test parsing query with date filter."""
        parser = QueryParser()
        result = parser.parse("What was revenue from 2023-01-01?", extract_filters=True)

        assert "revenue" in result["query_text"].lower()
        assert "date_from" in result["filters"]
        # Date is returned in ISO format, check it starts with the date
        assert result["filters"]["date_from"].startswith("2023-01-01")

    def test_parse_with_date_range(self):
        """Test parsing query with date range."""
        parser = QueryParser()
        result = parser.parse(
            "Revenue between 2023-01-01 and 2023-12-31", extract_filters=True
        )

        assert "date_from" in result["filters"]
        assert "date_to" in result["filters"]
        # Dates are returned in ISO format, check they start with the date
        assert result["filters"]["date_from"].startswith("2023-01-01")
        assert result["filters"]["date_to"].startswith("2023-12-31")

    def test_parse_with_ticker_filter(self):
        """Test parsing query with ticker filter."""
        parser = QueryParser()
        result = parser.parse("ticker: AAPL revenue", extract_filters=True)

        assert "ticker" in result["filters"]
        assert result["filters"]["ticker"] == "AAPL"
        assert "revenue" in result["query_text"].lower()

    def test_parse_with_form_type_filter(self):
        """Test parsing query with form type filter."""
        parser = QueryParser()
        result = parser.parse("form: 10-K revenue", extract_filters=True)

        assert "form_type" in result["filters"]
        assert result["filters"]["form_type"] == "10-K"
        assert "revenue" in result["query_text"].lower()

    def test_parse_with_boolean_and(self):
        """Test parsing query with AND operator."""
        parser = QueryParser()
        result = parser.parse("revenue AND profit", extract_filters=False)

        assert "AND" in result["boolean_operators"]
        assert "revenue" in result["query_terms"]
        assert "profit" in result["query_terms"]

    def test_parse_with_boolean_or(self):
        """Test parsing query with OR operator."""
        parser = QueryParser()
        result = parser.parse("Apple OR Microsoft", extract_filters=False)

        assert "OR" in result["boolean_operators"]
        assert "apple" in result["query_terms"] or "microsoft" in result["query_terms"]

    def test_parse_with_boolean_not(self):
        """Test parsing query with NOT operator."""
        parser = QueryParser()
        result = parser.parse("revenue NOT loss", extract_filters=False)

        assert "NOT" in result["boolean_operators"]
        assert "revenue" in result["query_terms"]

    def test_parse_empty_query(self):
        """Test parsing empty query raises error."""
        parser = QueryParser()
        with pytest.raises(QueryParseError):
            parser.parse("", extract_filters=False)

    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only query raises error."""
        parser = QueryParser()
        with pytest.raises(QueryParseError):
            parser.parse("   ", extract_filters=False)

    def test_parse_complex_query(self):
        """Test parsing complex query with multiple filters."""
        parser = QueryParser()
        result = parser.parse(
            "ticker: AAPL form: 10-K revenue from 2023-01-01", extract_filters=True
        )

        assert "ticker" in result["filters"]
        assert result["filters"]["ticker"] == "AAPL"
        assert "form_type" in result["filters"]
        assert result["filters"]["form_type"] == "10-K"
        assert "date_from" in result["filters"]
        assert "revenue" in result["query_text"].lower()

    def test_extract_terms_removes_stop_words(self):
        """Test that stop words are removed from query terms."""
        parser = QueryParser()
        result = parser.parse(
            "What is the revenue of the company?", extract_filters=False
        )

        # Stop words like "what", "is", "the", "of" should be removed
        # Note: "what" might be kept if it's 4+ chars, but "is", "the",
        # "of" should be removed
        assert "is" not in result["query_terms"]
        assert "the" not in result["query_terms"]
        assert "of" not in result["query_terms"]
        assert "revenue" in result["query_terms"]
        assert "company" in result["query_terms"]

    def test_parse_date_formats(self):
        """Test parsing different date formats."""
        parser = QueryParser()

        # ISO format
        result1 = parser.parse("Revenue from 2023-01-01", extract_filters=True)
        assert "date_from" in result1["filters"]

        # US format
        result2 = parser.parse("Revenue from 01/01/2023", extract_filters=True)
        assert "date_from" in result2["filters"]

        # Text format
        result3 = parser.parse("Revenue from January 1, 2023", extract_filters=True)
        assert "date_from" in result3["filters"]
