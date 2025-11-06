"""
Form S-1 (IPO Registration Statement) parser for SEC EDGAR filings.

Extracts IPO filing information including offering details, company information,
use of proceeds, and risk factors.
"""

import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from app.utils.logger import get_logger

logger = get_logger(__name__)


class FormS1ParserError(Exception):
    """Custom exception for Form S-1 parser errors."""

    pass


class FormS1Parser:
    """
    Parser for SEC Form S-1 (Registration Statement).

    Form S-1 is filed for initial public offerings (IPOs) and contains
    comprehensive company information, offering details, and risk factors.
    """

    def __init__(self):
        """Initialize Form S-1 parser."""
        self.logger = logger

    def parse(
        self, html_content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse Form S-1 HTML content and extract IPO data.

        Args:
            html_content: HTML content of Form S-1 filing
            metadata: Optional metadata dictionary (ticker, CIK, filing date, etc.)

        Returns:
            Dictionary containing parsed Form S-1 data

        Raises:
            FormS1ParserError: If parsing fails
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract sections
            company_info = self._extract_company_info(soup)
            offering_info = self._extract_offering_info(soup)
            use_of_proceeds = self._extract_use_of_proceeds(soup)
            risk_factors = self._extract_risk_factors(soup)

            # Convert to text format
            text_content = self._convert_to_text(
                company_info, offering_info, use_of_proceeds, risk_factors
            )

            # Build enhanced metadata
            enhanced_metadata = {
                **(metadata or {}),
                "form_type": "S-1",
                "offering_type": offering_info.get("type", ""),
                "offering_amount": offering_info.get("amount", ""),
                "risk_factor_count": len(risk_factors),
                "enhanced": True,
            }

            result = {
                "form_type": "S-1",
                "company_info": company_info,
                "offering_info": offering_info,
                "use_of_proceeds": use_of_proceeds,
                "risk_factors": risk_factors,
                "text_content": text_content,
                "metadata": enhanced_metadata,
            }

            self.logger.info(f"Parsed Form S-1: {company_info.get('name', 'Unknown')}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to parse Form S-1: {str(e)}", exc_info=True)
            raise FormS1ParserError(f"Failed to parse Form S-1: {str(e)}") from e

    def _extract_company_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract company information from Form S-1."""
        info = {"name": "", "ticker": "", "cik": "", "industry": "", "state": ""}

        text = soup.get_text()

        # Company name
        name_patterns = [
            r"Registrant.*?Name[:\s]+([^\n]+)",
            r"Company.*?Name[:\s]+([^\n]+)",
            r"<registrantName>([^<]+)</registrantName>",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info["name"] = match.group(1).strip()
                break

        # Ticker (if proposed)
        ticker_match = re.search(r"Ticker.*?Symbol[:\s]+([A-Z]+)", text, re.IGNORECASE)
        if ticker_match:
            info["ticker"] = ticker_match.group(1).strip()

        # CIK
        cik_match = re.search(r"CIK[:\s]+(\d+)", text, re.IGNORECASE)
        if cik_match:
            info["cik"] = cik_match.group(1).strip().zfill(10)

        return info

    def _extract_offering_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract offering details from Form S-1."""
        info = {
            "type": "",
            "amount": "",
            "shares": "",
            "price_range": "",
            "underwriters": [],
        }

        text = soup.get_text()

        # Offering type
        if re.search(r"Initial.*?Public.*?Offering", text, re.IGNORECASE):
            info["type"] = "IPO"
        elif re.search(r"Secondary.*?Offering", text, re.IGNORECASE):
            info["type"] = "Secondary Offering"

        # Offering amount
        amount_match = re.search(
            r"Offering.*?Amount[:\s]+\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion|M|B)?",
            text,
            re.IGNORECASE,
        )
        if amount_match:
            info["amount"] = amount_match.group(1)

        # Number of shares
        shares_match = re.search(r"(\d+(?:,\d+)*)\s*shares", text, re.IGNORECASE)
        if shares_match:
            info["shares"] = shares_match.group(1)

        # Price range
        price_match = re.search(
            r"Price.*?Range[:\s]+\$?(\d+\.?\d*)\s*-\s*\$?(\d+\.?\d*)",
            text,
            re.IGNORECASE,
        )
        if price_match:
            info["price_range"] = f"${price_match.group(1)} - ${price_match.group(2)}"

        return info

    def _extract_use_of_proceeds(self, soup: BeautifulSoup) -> str:
        """Extract use of proceeds section."""
        text = soup.get_text()

        # Look for "Use of Proceeds" section
        use_pattern = re.compile(
            r"Use\s+of\s+Proceeds.*?(?=Risk\s+Factors|Item\s+\d+|$)",
            re.IGNORECASE | re.DOTALL,
        )
        match = use_pattern.search(text)
        if match:
            return match.group(0).strip()[:2000]  # Limit length

        return ""

    def _extract_risk_factors(self, soup: BeautifulSoup) -> List[str]:
        """Extract risk factors from Form S-1."""
        risk_factors = []
        text = soup.get_text()

        # Look for "Risk Factors" section
        risk_pattern = re.compile(
            r"Risk\s+Factors.*?(?=Use\s+of\s+Proceeds|Item\s+\d+|$)",
            re.IGNORECASE | re.DOTALL,
        )
        match = risk_pattern.search(text)
        if match:
            risk_section = match.group(0)

            # Extract individual risk factors (numbered or bulleted)
            factor_pattern = re.compile(
                r"(?:^\d+\.|^[-•])\s*(.+?)(?=^\d+\.|^[-•]|$)",
                re.MULTILINE | re.DOTALL,
            )
            factors = factor_pattern.findall(risk_section)
            risk_factors = [f.strip()[:500] for f in factors if f.strip()]

        return risk_factors

    def _convert_to_text(
        self,
        company_info: Dict[str, str],
        offering_info: Dict[str, Any],
        use_of_proceeds: str,
        risk_factors: List[str],
    ) -> str:
        """Convert parsed Form S-1 data to readable text format."""
        lines = []

        lines.append("FORM S-1 - REGISTRATION STATEMENT")
        lines.append("=" * 60)

        # Company information
        lines.append("\nCOMPANY INFORMATION:")
        if company_info.get("name"):
            lines.append(f"  Name: {company_info['name']}")
        if company_info.get("ticker"):
            lines.append(f"  Proposed Ticker: {company_info['ticker']}")
        if company_info.get("cik"):
            lines.append(f"  CIK: {company_info['cik']}")

        # Offering information
        lines.append("\nOFFERING INFORMATION:")
        if offering_info.get("type"):
            lines.append(f"  Type: {offering_info['type']}")
        if offering_info.get("amount"):
            lines.append(f"  Amount: ${offering_info['amount']}")
        if offering_info.get("shares"):
            lines.append(f"  Shares: {offering_info['shares']}")
        if offering_info.get("price_range"):
            lines.append(f"  Price Range: {offering_info['price_range']}")

        # Use of proceeds
        if use_of_proceeds:
            lines.append("\nUSE OF PROCEEDS:")
            lines.append(use_of_proceeds[:1000])  # Limit length

        # Risk factors
        if risk_factors:
            lines.append(f"\nRISK FACTORS ({len(risk_factors)} total):")
            for idx, risk in enumerate(risk_factors[:10], 1):  # Limit to 10
                lines.append(f"\n  {idx}. {risk}")

        return "\n".join(lines)


def create_forms1_parser() -> FormS1Parser:
    """
    Create a Form S-1 parser instance.

    Returns:
        FormS1Parser instance
    """
    return FormS1Parser()
