"""
DEF 14A (Proxy Statement) parser for SEC EDGAR filings.

Extracts proxy statement information including voting items, executive compensation,
board member information, and shareholder proposals.
"""

import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from app.utils.logger import get_logger

logger = get_logger(__name__)


class Def14AParserError(Exception):
    """Custom exception for DEF 14A parser errors."""

    pass


class Def14AParser:
    """
    Parser for SEC DEF 14A (Proxy Statement).

    DEF 14A contains information about matters to be voted on at shareholder meetings,
    executive compensation, board composition, and other corporate governance matters.
    """

    def __init__(self):
        """Initialize DEF 14A parser."""
        self.logger = logger

    def parse(
        self, html_content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse DEF 14A HTML content and extract proxy statement data.

        Args:
            html_content: HTML content of DEF 14A filing
            metadata: Optional metadata dictionary (ticker, CIK, filing date, etc.)

        Returns:
            Dictionary containing parsed DEF 14A data

        Raises:
            Def14AParserError: If parsing fails
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract sections
            company_info = self._extract_company_info(soup)
            voting_items = self._extract_voting_items(soup)
            executive_compensation = self._extract_executive_compensation(soup)
            board_members = self._extract_board_members(soup)
            shareholder_proposals = self._extract_shareholder_proposals(soup)

            # Convert to text format
            text_content = self._convert_to_text(
                company_info,
                voting_items,
                executive_compensation,
                board_members,
                shareholder_proposals,
            )

            # Build enhanced metadata
            enhanced_metadata = {
                **(metadata or {}),
                "form_type": "DEF 14A",
                "voting_items": [
                    item.get("description", "")[:100] for item in voting_items
                ],
                "board_member_count": len(board_members),
                "shareholder_proposal_count": len(shareholder_proposals),
                "enhanced": True,
            }

            result = {
                "form_type": "DEF 14A",
                "company_info": company_info,
                "voting_items": voting_items,
                "executive_compensation": executive_compensation,
                "board_members": board_members,
                "shareholder_proposals": shareholder_proposals,
                "text_content": text_content,
                "metadata": enhanced_metadata,
            }

            self.logger.info(
                f"Parsed DEF 14A: {len(voting_items)} voting items, "
                f"{len(board_members)} board members"
            )
            return result

        except Exception as e:
            self.logger.error(f"Failed to parse DEF 14A: {str(e)}", exc_info=True)
            raise Def14AParserError(f"Failed to parse DEF 14A: {str(e)}") from e

    def _extract_company_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract company information from DEF 14A."""
        info = {"name": "", "ticker": "", "cik": "", "meeting_date": ""}

        text = soup.get_text()

        # Company name
        name_match = re.search(
            r"Registrant.*?Name[:\s]+([^\n]+)|Company.*?Name[:\s]+([^\n]+)",
            text,
            re.IGNORECASE,
        )
        if name_match:
            info["name"] = (name_match.group(1) or name_match.group(2)).strip()

        # Ticker
        ticker_match = re.search(r"Ticker.*?Symbol[:\s]+([A-Z]+)", text, re.IGNORECASE)
        if ticker_match:
            info["ticker"] = ticker_match.group(1).strip()

        # CIK
        cik_match = re.search(r"CIK[:\s]+(\d+)", text, re.IGNORECASE)
        if cik_match:
            info["cik"] = cik_match.group(1).strip().zfill(10)

        # Meeting date
        meeting_match = re.search(
            r"Meeting.*?Date[:\s]+([^\n]+)|Annual.*?Meeting[:\s]+([^\n]+)",
            text,
            re.IGNORECASE,
        )
        if meeting_match:
            info["meeting_date"] = (
                meeting_match.group(1) or meeting_match.group(2)
            ).strip()

        return info

    def _extract_voting_items(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract voting items/proposals from DEF 14A."""
        voting_items = []
        text = soup.get_text()

        # Look for proposal sections
        proposal_pattern = re.compile(
            r"Proposal\s+(\d+)[:\s]+(.+?)(?=Proposal\s+\d+|Recommendation|$)",
            re.IGNORECASE | re.DOTALL,
        )

        matches = proposal_pattern.finditer(text)
        for match in matches:
            proposal_num = match.group(1)
            proposal_text = match.group(2).strip()

            # Extract recommendation
            rec_match = re.search(
                r"Recommendation[:\s]+([^\n]+)", proposal_text, re.IGNORECASE
            )
            recommendation = rec_match.group(1).strip() if rec_match else ""

            voting_items.append(
                {
                    "proposal_number": proposal_num,
                    "description": proposal_text[:500],  # Limit length
                    "recommendation": recommendation,
                }
            )

        return voting_items

    def _extract_executive_compensation(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract executive compensation information."""
        compensation = {
            "ceo_total": "",
            "cfo_total": "",
            "named_executives": [],
        }

        text = soup.get_text()

        # Look for compensation tables
        comp_section = re.search(
            r"Executive.*?Compensation.*?(?=Director.*?Compensation|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if comp_section:
            comp_text = comp_section.group(0)

            # Extract CEO compensation
            ceo_match = re.search(
                r"CEO.*?Total[:\s]+\$?([\d,]+(?:\.\d+)?)",
                comp_text,
                re.IGNORECASE,
            )
            if ceo_match:
                compensation["ceo_total"] = ceo_match.group(1)

            # Extract CFO compensation
            cfo_match = re.search(
                r"CFO.*?Total[:\s]+\$?([\d,]+(?:\.\d+)?)",
                comp_text,
                re.IGNORECASE,
            )
            if cfo_match:
                compensation["cfo_total"] = cfo_match.group(1)

        return compensation

    def _extract_board_members(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract board member information."""
        board_members = []
        text = soup.get_text()

        # Look for director information
        director_section = re.search(
            r"Director.*?Information.*?(?=Executive.*?Compensation|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if director_section:
            # Extract director names and positions
            director_pattern = re.compile(
                r"([A-Z][a-z]+\s+[A-Z][a-z]+).*?(?:Director|Chairman|Independent)",
                re.IGNORECASE,
            )

            matches = director_pattern.finditer(director_section.group(0))
            for match in matches:
                name = match.group(1).strip()
                if name and len(name.split()) >= 2:  # Valid name
                    board_members.append({"name": name, "position": "Director"})

        return board_members[:20]  # Limit to 20

    def _extract_shareholder_proposals(self, soup: BeautifulSoup) -> List[str]:
        """Extract shareholder proposals."""
        proposals = []
        text = soup.get_text()

        # Look for shareholder proposal section
        shareholder_section = re.search(
            r"Shareholder.*?Proposal.*?(?=Other.*?Business|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if shareholder_section:
            # Extract individual proposals
            proposal_pattern = re.compile(
                r"Proposal\s+\d+[:\s]+(.+?)(?=Proposal\s+\d+|$)",
                re.IGNORECASE | re.DOTALL,
            )

            matches = proposal_pattern.finditer(shareholder_section.group(0))
            for match in matches:
                proposal_text = match.group(1).strip()[:500]  # Limit length
                if proposal_text:
                    proposals.append(proposal_text)

        return proposals

    def _convert_to_text(
        self,
        company_info: Dict[str, str],
        voting_items: List[Dict[str, Any]],
        executive_compensation: Dict[str, Any],
        board_members: List[Dict[str, str]],
        shareholder_proposals: List[str],
    ) -> str:
        """Convert parsed DEF 14A data to readable text format."""
        lines = []

        lines.append("DEF 14A - PROXY STATEMENT")
        lines.append("=" * 60)

        # Company information
        lines.append("\nCOMPANY INFORMATION:")
        if company_info.get("name"):
            lines.append(f"  Name: {company_info['name']}")
        if company_info.get("ticker"):
            lines.append(f"  Ticker: {company_info['ticker']}")
        if company_info.get("meeting_date"):
            lines.append(f"  Meeting Date: {company_info['meeting_date']}")

        # Voting items
        if voting_items:
            lines.append(f"\nVOTING ITEMS ({len(voting_items)} total):")
            for item in voting_items:
                lines.append(
                    f"\n  Proposal {item.get('proposal_number', 'N/A')}: "
                    f"{item.get('description', '')[:200]}"
                )
                if item.get("recommendation"):
                    lines.append(f"    Recommendation: {item['recommendation']}")

        # Executive compensation
        if executive_compensation.get("ceo_total") or executive_compensation.get(
            "cfo_total"
        ):
            lines.append("\nEXECUTIVE COMPENSATION:")
            if executive_compensation.get("ceo_total"):
                lines.append(
                    f"  CEO Total Compensation: ${executive_compensation['ceo_total']}"
                )
            if executive_compensation.get("cfo_total"):
                lines.append(
                    f"  CFO Total Compensation: ${executive_compensation['cfo_total']}"
                )

        # Board members
        if board_members:
            lines.append(f"\nBOARD MEMBERS ({len(board_members)} total):")
            for member in board_members[:10]:  # Limit display
                lines.append(f"  - {member.get('name', 'N/A')}")

        # Shareholder proposals
        if shareholder_proposals:
            lines.append(
                f"\nSHAREHOLDER PROPOSALS ({len(shareholder_proposals)} total):"
            )
            for idx, proposal in enumerate(
                shareholder_proposals[:5], 1
            ):  # Limit display
                lines.append(f"  {idx}. {proposal[:200]}")

        return "\n".join(lines)


def create_def14a_parser() -> Def14AParser:
    """
    Create a DEF 14A parser instance.

    Returns:
        Def14AParser instance
    """
    return Def14AParser()
