"""
XBRL (eXtensible Business Reporting Language) parser for SEC EDGAR filings.

Extracts structured financial data from XBRL files including balance sheet,
income statement, and cash flow statement data.
"""

import io
import zipfile
from typing import Any, Dict, List, Optional
from zipfile import ZipFile

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import arelle - make it optional for graceful degradation
try:
    from arelle import Cntlr, ModelManager

    ARELLE_AVAILABLE = True
except ImportError:
    ARELLE_AVAILABLE = False
    logger.warning(
        "Arelle library not available. XBRL parsing will be limited. "
        "Install with: pip install arelle"
    )


class XBRLParserError(Exception):
    """Custom exception for XBRL parser errors."""

    pass


class XBRLParser:
    """
    Parser for XBRL financial statements.

    Extracts structured financial data from XBRL instance documents,
    including balance sheet, income statement, and cash flow data.
    """

    def __init__(self):
        """Initialize XBRL parser."""
        self.logger = logger
        self.arelle_available = ARELLE_AVAILABLE

        if self.arelle_available:
            try:
                self.cntlr = Cntlr.Cntlr()
                self.model_manager = ModelManager.initialize(self.cntlr)
            except Exception as e:
                self.logger.warning(f"Failed to initialize Arelle: {str(e)}")
                self.arelle_available = False

    def parse(
        self,
        xbrl_content: bytes,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Parse XBRL content and extract financial statement data.

        Args:
            xbrl_content: XBRL file content (bytes) - can be .xbrl file or .zip archive
            metadata: Optional metadata dictionary (ticker, CIK, filing date, etc.)

        Returns:
            Dictionary containing parsed XBRL data:
            {
                "form_type": "10-K" or "10-Q",
                "balance_sheet": {...},
                "income_statement": {...},
                "cash_flow": {...},
                "text_content": "...",
                "metadata": {...}
            }

        Raises:
            XBRLParserError: If parsing fails
        """
        try:
            if not self.arelle_available:
                # Fallback: extract text from XBRL XML without full parsing
                return self._parse_xbrl_fallback(xbrl_content, metadata)

            # Try to parse with Arelle
            return self._parse_with_arelle(xbrl_content, metadata)

        except Exception as e:
            self.logger.error(f"Failed to parse XBRL: {str(e)}", exc_info=True)
            # Fallback to basic parsing
            try:
                return self._parse_xbrl_fallback(xbrl_content, metadata)
            except Exception as fallback_error:
                raise XBRLParserError(
                    f"Failed to parse XBRL: {str(e)}. "
                    f"Fallback also failed: {str(fallback_error)}"
                ) from fallback_error

    def _parse_with_arelle(
        self, xbrl_content: bytes, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Parse XBRL using Arelle library."""
        try:
            # Determine if content is a zip file or single XBRL file
            is_zip = xbrl_content[:2] == b"PK"  # ZIP file signature

            if is_zip:
                # Extract XBRL instance from zip
                with ZipFile(io.BytesIO(xbrl_content)) as zip_file:
                    # Find XBRL instance file
                    xbrl_files = [f for f in zip_file.namelist() if f.endswith(".xbrl")]
                    if not xbrl_files:
                        raise XBRLParserError("No XBRL file found in archive")
                    xbrl_file = xbrl_files[0]
                    xbrl_data = zip_file.read(xbrl_file)
            else:
                xbrl_data = xbrl_content

            # Save to temporary file for Arelle
            import os
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".xbrl", delete=False
            ) as tmp_file:
                tmp_file.write(xbrl_data)
                tmp_path = tmp_file.name

            try:
                # Load XBRL model with Arelle
                model_xbrl = self.model_manager.load(tmp_path)

                if model_xbrl is None:
                    raise XBRLParserError("Failed to load XBRL model")

                # Extract financial statements
                balance_sheet = self._extract_balance_sheet(model_xbrl)
                income_statement = self._extract_income_statement(model_xbrl)
                cash_flow = self._extract_cash_flow(model_xbrl)

                # Convert to text format
                text_content = self._convert_to_text(
                    balance_sheet, income_statement, cash_flow
                )

                # Build enhanced metadata
                enhanced_metadata = {
                    **(metadata or {}),
                    "form_type": metadata.get("form_type", "XBRL"),
                    "enhanced": True,
                    "xbrl_parsed": True,
                }

                result = {
                    "form_type": metadata.get("form_type", "XBRL"),
                    "balance_sheet": balance_sheet,
                    "income_statement": income_statement,
                    "cash_flow": cash_flow,
                    "text_content": text_content,
                    "metadata": enhanced_metadata,
                }

                self.logger.info("Successfully parsed XBRL with Arelle")
                return result

            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        except Exception as e:
            self.logger.warning(f"Arelle parsing failed: {str(e)}, using fallback")
            raise

    def _extract_balance_sheet(self, model_xbrl) -> Dict[str, Any]:
        """Extract balance sheet data from XBRL model."""
        balance_sheet = {"assets": {}, "liabilities": {}, "equity": {}}

        # Common balance sheet concepts
        asset_concepts = [
            "Assets",
            "AssetsCurrent",
            "AssetsNoncurrent",
            "CashAndCashEquivalentsAtCarryingValue",
            "AccountsReceivableNetCurrent",
            "InventoryNet",
            "PropertyPlantAndEquipmentNet",
        ]

        liability_concepts = [
            "Liabilities",
            "LiabilitiesCurrent",
            "LiabilitiesNoncurrent",
            "AccountsPayableCurrent",
            "LongTermDebt",
        ]

        equity_concepts = [
            "Equity",
            "StockholdersEquity",
            "RetainedEarningsAccumulatedDeficit",
        ]

        # Extract facts for each concept
        for concept in asset_concepts:
            facts = model_xbrl.factsByQname.get(concept, [])
            if facts:
                balance_sheet["assets"][concept] = self._extract_fact_values(facts)

        for concept in liability_concepts:
            facts = model_xbrl.factsByQname.get(concept, [])
            if facts:
                balance_sheet["liabilities"][concept] = self._extract_fact_values(facts)

        for concept in equity_concepts:
            facts = model_xbrl.factsByQname.get(concept, [])
            if facts:
                balance_sheet["equity"][concept] = self._extract_fact_values(facts)

        return balance_sheet

    def _extract_income_statement(self, model_xbrl) -> Dict[str, Any]:
        """Extract income statement data from XBRL model."""
        income_statement = {"revenue": {}, "expenses": {}, "net_income": {}}

        # Common income statement concepts
        revenue_concepts = [
            "Revenues",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet",
        ]

        expense_concepts = [
            "CostOfRevenue",
            "OperatingExpenses",
            "ResearchAndDevelopmentExpense",
            "SellingGeneralAndAdministrativeExpense",
        ]

        net_income_concepts = [
            "NetIncomeLoss",
            "IncomeLossFromContinuingOperations",
        ]

        # Extract facts
        for concept in revenue_concepts:
            facts = model_xbrl.factsByQname.get(concept, [])
            if facts:
                income_statement["revenue"][concept] = self._extract_fact_values(facts)

        for concept in expense_concepts:
            facts = model_xbrl.factsByQname.get(concept, [])
            if facts:
                income_statement["expenses"][concept] = self._extract_fact_values(facts)

        for concept in net_income_concepts:
            facts = model_xbrl.factsByQname.get(concept, [])
            if facts:
                income_statement["net_income"][concept] = self._extract_fact_values(
                    facts
                )

        return income_statement

    def _extract_cash_flow(self, model_xbrl) -> Dict[str, Any]:
        """Extract cash flow statement data from XBRL model."""
        cash_flow = {
            "operating": {},
            "investing": {},
            "financing": {},
            "net_change": {},
        }

        # Common cash flow concepts
        operating_concepts = [
            "NetCashProvidedByUsedInOperatingActivities",
            "CashAndCashEquivalentsPeriodIncreaseDecrease",
        ]

        investing_concepts = [
            "NetCashProvidedByUsedInInvestingActivities",
            "PaymentsToAcquirePropertyPlantAndEquipment",
        ]

        financing_concepts = [
            "NetCashProvidedByUsedInFinancingActivities",
            "ProceedsFromIssuanceOfCommonStock",
        ]

        # Extract facts
        for concept in operating_concepts:
            facts = model_xbrl.factsByQname.get(concept, [])
            if facts:
                cash_flow["operating"][concept] = self._extract_fact_values(facts)

        for concept in investing_concepts:
            facts = model_xbrl.factsByQname.get(concept, [])
            if facts:
                cash_flow["investing"][concept] = self._extract_fact_values(facts)

        for concept in financing_concepts:
            facts = model_xbrl.factsByQname.get(concept, [])
            if facts:
                cash_flow["financing"][concept] = self._extract_fact_values(facts)

        return cash_flow

    def _extract_fact_values(self, facts) -> List[Dict[str, Any]]:
        """Extract values from XBRL facts."""
        values = []
        for fact in facts[:5]:  # Limit to 5 most recent
            try:
                value = {
                    "value": str(fact.xValue) if hasattr(fact, "xValue") else "",
                    "context": (
                        str(fact.contextID) if hasattr(fact, "contextID") else ""
                    ),
                    "unit": str(fact.unitID) if hasattr(fact, "unitID") else "",
                }
                values.append(value)
            except Exception as e:
                self.logger.warning(f"Failed to extract fact value: {str(e)}")
                continue
        return values

    def _parse_xbrl_fallback(
        self, xbrl_content: bytes, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fallback XBRL parsing without Arelle - basic XML text extraction."""
        try:
            import xml.etree.ElementTree as ET

            # Check if content is a zip file (starts with PK signature)
            is_zip = xbrl_content[:2] == b"PK"

            if is_zip:
                # Try to extract from zip
                try:
                    with ZipFile(io.BytesIO(xbrl_content)) as zip_file:
                        xbrl_files = [
                            f for f in zip_file.namelist() if f.endswith(".xbrl")
                        ]
                        if not xbrl_files:
                            raise XBRLParserError("No XBRL file found in archive")
                        xbrl_data = zip_file.read(xbrl_files[0])
                        root = ET.fromstring(xbrl_data)
                except (zipfile.BadZipFile, KeyError) as e:
                    raise XBRLParserError(f"Invalid zip file: {str(e)}") from e
            else:
                # Try to parse as XML directly
                try:
                    root = ET.fromstring(xbrl_content)
                except ET.ParseError as e:
                    # If XML parsing fails (e.g., namespace issues), use regex fallback
                    import re

                    try:
                        text_matches = re.findall(
                            r">([^<]+)<", xbrl_content.decode("utf-8", errors="ignore")
                        )
                        if text_matches:
                            text_content = "\n".join(text_matches[:1000])
                            enhanced_metadata = {
                                **(metadata or {}),
                                "form_type": metadata.get("form_type", "XBRL"),
                                "enhanced": True,
                                "xbrl_parsed": False,
                            }
                            return {
                                "form_type": metadata.get("form_type", "XBRL"),
                                "balance_sheet": {},
                                "income_statement": {},
                                "cash_flow": {},
                                "text_content": text_content
                                or "XBRL content extracted (basic mode)",
                                "metadata": enhanced_metadata,
                            }
                    except Exception:
                        pass
                    raise XBRLParserError(f"Invalid XML content: {str(e)}") from e

            # Extract text content from XML
            text_parts = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_parts.append(elem.text.strip())

            text_content = "\n".join(text_parts[:1000])  # Limit length

            enhanced_metadata = {
                **(metadata or {}),
                "form_type": metadata.get("form_type", "XBRL"),
                "enhanced": True,
                "xbrl_parsed": False,  # Fallback mode
            }

            return {
                "form_type": metadata.get("form_type", "XBRL"),
                "balance_sheet": {},
                "income_statement": {},
                "cash_flow": {},
                "text_content": text_content or "XBRL content extracted (basic mode)",
                "metadata": enhanced_metadata,
            }

        except Exception as e:
            raise XBRLParserError(f"Fallback XBRL parsing failed: {str(e)}") from e

    def _convert_to_text(
        self,
        balance_sheet: Dict[str, Any],
        income_statement: Dict[str, Any],
        cash_flow: Dict[str, Any],
    ) -> str:
        """Convert parsed XBRL data to readable text format."""
        lines = []

        lines.append("XBRL FINANCIAL STATEMENTS")
        lines.append("=" * 60)

        # Balance Sheet
        if balance_sheet.get("assets") or balance_sheet.get("liabilities"):
            lines.append("\nBALANCE SHEET:")
            if balance_sheet.get("assets"):
                lines.append("  Assets:")
                for concept, values in balance_sheet["assets"].items():
                    if values:
                        lines.append(f"    {concept}: {values[0].get('value', 'N/A')}")

            if balance_sheet.get("liabilities"):
                lines.append("  Liabilities:")
                for concept, values in balance_sheet["liabilities"].items():
                    if values:
                        lines.append(f"    {concept}: {values[0].get('value', 'N/A')}")

        # Income Statement
        if income_statement.get("revenue") or income_statement.get("net_income"):
            lines.append("\nINCOME STATEMENT:")
            if income_statement.get("revenue"):
                lines.append("  Revenue:")
                for concept, values in income_statement["revenue"].items():
                    if values:
                        lines.append(f"    {concept}: {values[0].get('value', 'N/A')}")

            if income_statement.get("net_income"):
                lines.append("  Net Income:")
                for concept, values in income_statement["net_income"].items():
                    if values:
                        lines.append(f"    {concept}: {values[0].get('value', 'N/A')}")

        # Cash Flow
        if cash_flow.get("operating") or cash_flow.get("net_change"):
            lines.append("\nCASH FLOW STATEMENT:")
            if cash_flow.get("operating"):
                lines.append("  Operating Activities:")
                for concept, values in cash_flow["operating"].items():
                    if values:
                        lines.append(f"    {concept}: {values[0].get('value', 'N/A')}")

        return "\n".join(lines)


def create_xbrl_parser() -> XBRLParser:
    """
    Create an XBRL parser instance.

    Returns:
        XBRLParser instance
    """
    return XBRLParser()
