"""
Tests for filter builder module.
"""

from app.rag.filter_builder import FilterBuilder


class TestFilterBuilder:
    """Test cases for FilterBuilder."""

    def test_init(self):
        """Test filter builder initialization."""
        builder = FilterBuilder()
        assert builder is not None

    def test_build_where_clause_no_filters(self):
        """Test building where clause with no filters."""
        builder = FilterBuilder()
        result = builder.build_where_clause({})
        assert result is None

    def test_build_where_clause_ticker(self):
        """Test building where clause with ticker filter."""
        builder = FilterBuilder()
        filters = {"ticker": "AAPL"}
        result = builder.build_where_clause(filters)

        assert result is not None
        assert result["ticker"] == "AAPL"

    def test_build_where_clause_form_type(self):
        """Test building where clause with form type filter."""
        builder = FilterBuilder()
        filters = {"form_type": "10-K"}
        result = builder.build_where_clause(filters)

        assert result is not None
        assert result["form_type"] == "10-K"

    def test_build_where_clause_document_type(self):
        """Test building where clause with document type filter."""
        builder = FilterBuilder()
        filters = {"document_type": "edgar_filing"}
        result = builder.build_where_clause(filters)

        assert result is not None
        assert result["type"] == "edgar_filing"

    def test_build_where_clause_date_from(self):
        """Test building where clause with date from filter."""
        builder = FilterBuilder()
        filters = {"date_from": "2023-01-01"}
        result = builder.build_where_clause(filters)

        assert result is not None
        assert "$and" in result or "date" in result

    def test_build_where_clause_date_to(self):
        """Test building where clause with date to filter."""
        builder = FilterBuilder()
        filters = {"date_to": "2023-12-31"}
        result = builder.build_where_clause(filters)

        assert result is not None
        assert "$and" in result or "date" in result

    def test_build_where_clause_date_range(self):
        """Test building where clause with date range."""
        builder = FilterBuilder()
        filters = {"date_from": "2023-01-01", "date_to": "2023-12-31"}
        result = builder.build_where_clause(filters)

        assert result is not None
        # Should have $and with date conditions
        assert "$and" in result or "date" in result

    def test_build_where_clause_multiple_filters(self):
        """Test building where clause with multiple filters."""
        builder = FilterBuilder()
        filters = {
            "ticker": "AAPL",
            "form_type": "10-K",
            "document_type": "edgar_filing",
        }
        result = builder.build_where_clause(filters)

        assert result is not None
        # Should use $and to combine conditions
        if "$and" in result:
            assert len(result["$and"]) == 3
        else:
            # Or all conditions in single dict
            assert "ticker" in result or "form_type" in result

    def test_build_where_clause_custom_metadata(self):
        """Test building where clause with custom metadata."""
        builder = FilterBuilder()
        filters = {"metadata": {"source": "test_source", "category": "financial"}}
        result = builder.build_where_clause(filters)

        assert result is not None
        # Should include custom metadata fields

    def test_build_where_document_clause_contains(self):
        """Test building where_document clause with contains."""
        builder = FilterBuilder()
        filters = {"contains": "revenue"}
        result = builder.build_where_document_clause(filters)

        assert result is not None
        assert "$contains" in result
        assert result["$contains"] == "revenue"

    def test_build_where_document_clause_empty(self):
        """Test building where_document clause with no filters."""
        builder = FilterBuilder()
        result = builder.build_where_document_clause({})
        assert result is None
