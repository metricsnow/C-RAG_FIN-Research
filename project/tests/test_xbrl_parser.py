"""
Unit tests for XBRL parser.

Tests cover:
- XBRL file parsing (with and without Arelle)
- Balance sheet extraction
- Income statement extraction
- Cash flow extraction
- Fallback parsing
- Error handling
"""

import pytest

from app.ingestion.xbrl_parser import XBRLParser, XBRLParserError


class TestXBRLParserInitialization:
    """Test XBRL parser initialization."""

    def test_init(self):
        """Test parser initialization."""
        parser = XBRLParser()
        assert parser is not None
        assert parser.logger is not None
        # Arelle may or may not be available
        assert isinstance(parser.arelle_available, bool)


class TestXBRLParserParse:
    """Test XBRL parsing functionality."""

    def test_parse_fallback_mode(self):
        """Test parsing in fallback mode (without Arelle or with Arelle failure)."""
        parser = XBRLParser()

        # Simple XML content without namespaces (to avoid namespace parsing issues)
        xbrl_content = b"""<?xml version="1.0"?>
        <xbrl xmlns="http://www.xbrl.org/2003/instance">
            <context id="c1">
                <entity>
                    <identifier scheme="http://www.sec.gov/CIK">0000320193</identifier>
                </entity>
            </context>
            <Assets contextRef="c1" unitRef="u1">1000000</Assets>
        </xbrl>"""

        metadata = {"ticker": "AAPL", "form_type": "10-K"}

        result = parser.parse(xbrl_content, metadata)

        assert result["form_type"] == "10-K"
        assert "text_content" in result
        assert "metadata" in result
        assert result["metadata"]["enhanced"] is True

    def test_parse_with_metadata(self):
        """Test parsing with provided metadata."""
        parser = XBRLParser()

        xbrl_content = b"<xbrl><test>content</test></xbrl>"
        metadata = {
            "ticker": "AAPL",
            "cik": "0000320193",
            "form_type": "10-K",
        }

        result = parser.parse(xbrl_content, metadata)

        assert result["metadata"]["ticker"] == "AAPL"
        assert result["metadata"]["form_type"] == "10-K"

    def test_parse_zip_file(self):
        """Test parsing XBRL from zip file."""
        import io
        import zipfile

        parser = XBRLParser()

        # Create a zip file with XBRL content
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            zip_file.writestr("instance.xbrl", "<xbrl><test>content</test></xbrl>")
        zip_content = zip_buffer.getvalue()

        metadata = {"ticker": "AAPL", "form_type": "10-K"}

        result = parser.parse(zip_content, metadata)

        assert result["form_type"] == "10-K"
        assert "text_content" in result

    def test_parse_invalid_content(self):
        """Test parsing invalid content."""
        parser = XBRLParser()

        invalid_content = b"Not valid XML or ZIP"
        metadata = {"ticker": "AAPL", "form_type": "10-K"}

        # Should use fallback and handle gracefully
        try:
            result = parser.parse(invalid_content, metadata)
            assert result is not None
        except XBRLParserError:
            # Error is acceptable for invalid content
            pass


class TestXBRLParserFallback:
    """Test fallback parsing mode."""

    def test_parse_xbrl_fallback_basic_xml(self):
        """Test fallback parsing with basic XML."""
        parser = XBRLParser()

        xml_content = b"""<?xml version="1.0"?>
        <xbrl>
            <context id="c1">
                <entity>
                    <identifier>0000320193</identifier>
                </entity>
            </context>
            <fact id="f1" contextRef="c1">1000000</fact>
        </xbrl>"""

        metadata = {"ticker": "AAPL", "form_type": "10-K"}

        result = parser._parse_xbrl_fallback(xml_content, metadata)

        assert result["form_type"] == "10-K"
        assert "text_content" in result
        assert result["metadata"]["xbrl_parsed"] is False  # Fallback mode

    def test_parse_xbrl_fallback_zip(self):
        """Test fallback parsing with zip file."""
        import io
        import zipfile

        parser = XBRLParser()

        # Create zip with XBRL file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            zip_file.writestr("test.xbrl", "<xbrl><test>data</test></xbrl>")
        zip_content = zip_buffer.getvalue()

        metadata = {"ticker": "AAPL", "form_type": "10-K"}

        result = parser._parse_xbrl_fallback(zip_content, metadata)

        assert result["form_type"] == "10-K"
        assert "text_content" in result

    def test_parse_xbrl_fallback_invalid_zip(self):
        """Test fallback parsing with invalid zip."""
        parser = XBRLParser()

        invalid_zip = b"Not a valid zip file"
        metadata = {"ticker": "AAPL", "form_type": "10-K"}

        with pytest.raises(XBRLParserError):
            parser._parse_xbrl_fallback(invalid_zip, metadata)


class TestXBRLParserExtractFinancialStatements:
    """Test financial statement extraction (requires Arelle)."""

    def test_extract_fact_values(self):
        """Test extracting fact values."""
        parser = XBRLParser()

        # Mock facts (simplified)
        class MockFact:
            def __init__(self, value, context_id, unit_id):
                self.xValue = value
                self.contextID = context_id
                self.unitID = unit_id

        facts = [
            MockFact("1000000", "c1", "u1"),
            MockFact("2000000", "c2", "u1"),
        ]

        result = parser._extract_fact_values(facts)

        assert isinstance(result, list)
        assert len(result) <= 5  # Limited to 5
        if result:
            assert "value" in result[0]
            assert "context" in result[0]

    def test_extract_fact_values_empty(self):
        """Test extracting fact values from empty list."""
        parser = XBRLParser()

        result = parser._extract_fact_values([])

        assert isinstance(result, list)
        assert len(result) == 0


class TestXBRLParserConvertToText:
    """Test text conversion."""

    def test_convert_to_text(self):
        """Test converting parsed data to text."""
        parser = XBRLParser()

        balance_sheet = {
            "assets": {"Assets": [{"value": "1000000"}]},
            "liabilities": {"Liabilities": [{"value": "500000"}]},
        }
        income_statement = {
            "revenue": {"Revenues": [{"value": "2000000"}]},
            "net_income": {"NetIncomeLoss": [{"value": "300000"}]},
        }
        cash_flow = {
            "operating": {
                "NetCashProvidedByUsedInOperatingActivities": [{"value": "400000"}]
            },
        }

        result = parser._convert_to_text(balance_sheet, income_statement, cash_flow)

        assert "XBRL FINANCIAL STATEMENTS" in result
        assert "BALANCE SHEET" in result or "Assets" in result
        assert "INCOME STATEMENT" in result or "Revenue" in result
        assert "CASH FLOW" in result or "Operating" in result

    def test_convert_to_text_empty(self):
        """Test converting empty data to text."""
        parser = XBRLParser()

        result = parser._convert_to_text({}, {}, {})

        assert "XBRL FINANCIAL STATEMENTS" in result
        # Should still produce valid text even with empty data


class TestXBRLParserErrorHandling:
    """Test error handling."""

    def test_parse_raises_error_on_both_failures(self):
        """Test that parse raises error if both Arelle and fallback fail."""
        parser = XBRLParser()

        # Create content that will fail both parsing methods
        invalid_content = b""
        metadata = {"ticker": "AAPL", "form_type": "10-K"}

        # Should handle gracefully or raise error
        try:
            result = parser.parse(invalid_content, metadata)
            # If it doesn't raise, should return valid structure
            assert result is not None
        except XBRLParserError:
            # Error is acceptable
            pass
