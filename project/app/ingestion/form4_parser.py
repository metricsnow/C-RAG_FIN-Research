"""
Form 4 (Insider Trading) parser for SEC EDGAR filings.

Extracts insider trading transaction data from Form 4 filings,
including transaction dates, types, share amounts, prices, and insider information.
"""

import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from app.utils.logger import get_logger

logger = get_logger(__name__)


class Form4ParserError(Exception):
    """Custom exception for Form 4 parser errors."""

    pass


class Form4Parser:
    """
    Parser for SEC Form 4 (Statement of Changes in Beneficial Ownership).

    Form 4 is filed when insiders (officers, directors, 10%+ shareholders)
    buy or sell company stock.
    """

    def __init__(self):
        """Initialize Form 4 parser."""
        self.logger = logger

    def parse(
        self, html_content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse Form 4 HTML content and extract insider trading data.

        Args:
            html_content: HTML content of Form 4 filing
            metadata: Optional metadata dictionary (ticker, CIK, filing date, etc.)

        Returns:
            Dictionary containing parsed Form 4 data:
            {
                "form_type": "4",
                "transactions": [...],
                "insider_name": "...",
                "insider_position": "...",
                "issuer_name": "...",
                "issuer_ticker": "...",
                "text_content": "...",
                "metadata": {...}
            }

        Raises:
            Form4ParserError: If parsing fails
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract basic information
            issuer_info = self._extract_issuer_info(soup)
            insider_info = self._extract_insider_info(soup)
            transactions = self._extract_transactions(soup)

            # Convert to text format for RAG
            text_content = self._convert_to_text(
                issuer_info, insider_info, transactions
            )

            # Build enhanced metadata
            enhanced_metadata = {
                **(metadata or {}),
                "form_type": "4",
                "insider_name": insider_info.get("name", ""),
                "insider_position": insider_info.get("position", ""),
                "transaction_count": len(transactions),
                "enhanced": True,
            }

            result = {
                "form_type": "4",
                "issuer_name": issuer_info.get("name", ""),
                "issuer_ticker": issuer_info.get("ticker", ""),
                "insider_name": insider_info.get("name", ""),
                "insider_position": insider_info.get("position", ""),
                "transactions": transactions,
                "text_content": text_content,
                "metadata": enhanced_metadata,
            }

            self.logger.info(
                f"Parsed Form 4: {len(transactions)} transactions for "
                f"{insider_info.get('name', 'Unknown')}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Failed to parse Form 4: {str(e)}", exc_info=True)
            raise Form4ParserError(f"Failed to parse Form 4: {str(e)}") from e

    def _extract_issuer_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract issuer (company) information from Form 4."""
        issuer_info = {"name": "", "ticker": "", "cik": ""}

        # Look for issuer name (common patterns in Form 4)
        issuer_name_patterns = [
            r"Issuer.*?Name[:\s]+([^\n]+)",
            r"Company.*?Name[:\s]+([^\n]+)",
            r"<issuerName>([^<]+)</issuerName>",
        ]

        for pattern in issuer_name_patterns:
            match = re.search(pattern, soup.get_text(), re.IGNORECASE)
            if match:
                issuer_info["name"] = match.group(1).strip()
                break

        # Look for ticker symbol
        ticker_patterns = [
            r"Ticker.*?Symbol[:\s]+([A-Z]+)",
            r"<issuerTradingSymbol>([^<]+)</issuerTradingSymbol>",
        ]

        for pattern in ticker_patterns:
            match = re.search(pattern, soup.get_text(), re.IGNORECASE)
            if match:
                issuer_info["ticker"] = match.group(1).strip()
                break

        # Look for CIK
        cik_patterns = [
            r"CIK[:\s]+(\d+)",
            r"<issuerCik>(\d+)</issuerCik>",
        ]

        for pattern in cik_patterns:
            match = re.search(pattern, soup.get_text(), re.IGNORECASE)
            if match:
                issuer_info["cik"] = match.group(1).strip().zfill(10)
                break

        return issuer_info

    def _extract_insider_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract insider (reporting person) information from Form 4."""
        insider_info = {"name": "", "position": "", "relationship": ""}

        # Look for reporting person name
        name_patterns = [
            r"Reporting.*?Person[:\s]+([^\n]+)",
            r"Owner.*?Name[:\s]+([^\n]+)",
            r"<rptOwnerName>([^<]+)</rptOwnerName>",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, soup.get_text(), re.IGNORECASE)
            if match:
                insider_info["name"] = match.group(1).strip()
                break

        # Look for position/relationship
        position_patterns = [
            r"Title[:\s]+([^\n]+)",
            r"Relationship[:\s]+([^\n]+)",
            r"<officerTitle>([^<]+)</officerTitle>",
            r"<directorTitle>([^<]+)</directorTitle>",
        ]

        for pattern in position_patterns:
            match = re.search(pattern, soup.get_text(), re.IGNORECASE)
            if match:
                insider_info["position"] = match.group(1).strip()
                break

        return insider_info

    def _extract_transactions(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract transaction data from Form 4.

        Form 4 transactions include:
        - Transaction date
        - Transaction code (P=Purchase, S=Sale, A=Grant, etc.)
        - Shares acquired/disposed
        - Price per share
        - Shares owned after transaction
        """
        transactions = []

        # Look for transaction tables or structured data
        # Form 4 typically has transaction tables with specific patterns
        text = soup.get_text()

        # Pattern for transaction rows (simplified - real Form 4s have structured XML)
        # This is a basic extraction - real implementation would parse XML structure
        transaction_pattern = re.compile(
            r"(\d{2}/\d{2}/\d{4})"  # Date
            r".*?"
            r"([A-Z])\s*"  # Transaction code
            r".*?"
            r"(\d+(?:,\d+)*)"  # Shares
            r".*?"
            r"(\$?\d+\.?\d*)"  # Price
            r".*?"
            r"(\d+(?:,\d+)*)",  # Shares owned after
            re.IGNORECASE | re.DOTALL,
        )

        matches = transaction_pattern.finditer(text)
        for match in matches:
            try:
                transaction = {
                    "transaction_date": match.group(1),
                    "transaction_code": match.group(2),
                    "transaction_type": self._get_transaction_type(match.group(2)),
                    "shares": self._parse_number(match.group(3)),
                    "price_per_share": self._parse_price(match.group(4)),
                    "shares_owned_after": self._parse_number(match.group(5)),
                }
                transactions.append(transaction)
            except Exception as e:
                self.logger.warning(f"Failed to parse transaction: {str(e)}")
                continue

        # If no transactions found via pattern, try XML structure
        if not transactions:
            transactions = self._extract_transactions_from_xml(soup)

        return transactions

    def _extract_transactions_from_xml(
        self, soup: BeautifulSoup
    ) -> List[Dict[str, Any]]:
        """Extract transactions from XML structure in Form 4."""
        transactions = []

        # Look for XML transaction elements
        transaction_elements = soup.find_all(
            ["nonDerivativeTransaction", "derivativeTransaction"]
        )

        for elem in transaction_elements:
            try:
                transaction = {
                    "transaction_date": self._extract_xml_text(elem, "transactionDate"),
                    "transaction_code": self._extract_xml_text(elem, "transactionCode"),
                    "transaction_type": self._get_transaction_type(
                        self._extract_xml_text(elem, "transactionCode")
                    ),
                    "shares": self._parse_number(
                        self._extract_xml_text(elem, "transactionShares")
                    ),
                    "price_per_share": self._parse_price(
                        self._extract_xml_text(elem, "transactionPricePerShare")
                    ),
                    "shares_owned_after": self._parse_number(
                        self._extract_xml_text(elem, "sharesOwnedFollowingTransaction")
                    ),
                }
                transactions.append(transaction)
            except Exception as e:
                self.logger.warning(f"Failed to parse XML transaction: {str(e)}")
                continue

        return transactions

    def _extract_xml_text(self, element, tag_name: str) -> str:
        """Extract text from XML element by tag name."""
        tag = element.find(tag_name)
        return tag.get_text(strip=True) if tag else ""

    def _get_transaction_type(self, code: str) -> str:
        """Convert transaction code to human-readable type."""
        transaction_types = {
            "P": "Purchase",
            "S": "Sale",
            "A": "Grant",
            "D": "Disposition",
            "F": "Tax Withholding",
            "I": "Exercise",
            "M": "Conversion",
            "W": "Acquisition",
            "X": "Expiration",
            "G": "Gift",
            "C": "Conversion",
        }
        return transaction_types.get(code.upper(), f"Unknown ({code})")

    def _parse_number(self, text: str) -> int:
        """Parse number from text (removes commas, handles formats)."""
        if not text:
            return 0
        # Remove commas and non-digit characters except decimal point
        cleaned = re.sub(r"[^\d.]", "", text)
        try:
            return int(float(cleaned))
        except (ValueError, TypeError):
            return 0

    def _parse_price(self, text: str) -> float:
        """Parse price from text."""
        if not text:
            return 0.0
        # Remove $ and commas
        cleaned = re.sub(r"[^\d.]", "", text)
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    def _convert_to_text(
        self,
        issuer_info: Dict[str, str],
        insider_info: Dict[str, str],
        transactions: List[Dict[str, Any]],
    ) -> str:
        """Convert parsed Form 4 data to readable text format."""
        lines = []

        # Header
        lines.append("FORM 4 - STATEMENT OF CHANGES IN BENEFICIAL OWNERSHIP")
        lines.append("=" * 60)

        # Issuer information
        lines.append("\nISSUER INFORMATION:")
        if issuer_info.get("name"):
            lines.append(f"  Company Name: {issuer_info['name']}")
        if issuer_info.get("ticker"):
            lines.append(f"  Ticker Symbol: {issuer_info['ticker']}")
        if issuer_info.get("cik"):
            lines.append(f"  CIK: {issuer_info['cik']}")

        # Insider information
        lines.append("\nREPORTING PERSON:")
        if insider_info.get("name"):
            lines.append(f"  Name: {insider_info['name']}")
        if insider_info.get("position"):
            lines.append(f"  Position: {insider_info['position']}")

        # Transactions
        lines.append(f"\nTRANSACTIONS ({len(transactions)} total):")
        for idx, trans in enumerate(transactions, 1):
            lines.append(f"\n  Transaction {idx}:")
            lines.append(f"    Date: {trans.get('transaction_date', 'N/A')}")
            lines.append(
                f"    Type: {trans.get('transaction_type', 'N/A')} "
                f"({trans.get('transaction_code', 'N/A')})"
            )
            lines.append(f"    Shares: {trans.get('shares', 0):,}")
            lines.append(
                f"    Price per Share: ${trans.get('price_per_share', 0.0):.2f}"
            )
            lines.append(
                f"    Shares Owned After: {trans.get('shares_owned_after', 0):,}"
            )

        return "\n".join(lines)


def create_form4_parser() -> Form4Parser:
    """
    Create a Form 4 parser instance.

    Returns:
        Form4Parser instance
    """
    return Form4Parser()
