"""
Earnings call transcript parser.

Parses earnings call transcripts to extract:
- Speaker information and roles
- Q&A sections
- Management commentary
- Forward guidance statements
"""

import re
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


class TranscriptParserError(Exception):
    """Custom exception for transcript parser errors."""

    pass


class TranscriptParser:
    """
    Earnings call transcript parser.

    Extracts structured information from transcript text including:
    - Speaker identification and role classification
    - Q&A section extraction
    - Management commentary extraction
    - Forward guidance extraction
    """

    # Common management titles
    MANAGEMENT_TITLES = {
        "ceo",
        "chief executive officer",
        "cfo",
        "chief financial officer",
        "coo",
        "chief operating officer",
        "president",
        "cmo",
        "chief marketing officer",
        "cto",
        "chief technology officer",
        "evp",
        "executive vice president",
        "svp",
        "senior vice president",
        "vp",
        "vice president",
        "director",
        "chairman",
        "founder",
    }

    # Common analyst company names
    ANALYST_COMPANIES = {
        "morgan stanley",
        "goldman sachs",
        "jpmorgan",
        "j.p. morgan",
        "bank of america",
        "bofa",
        "credit suisse",
        "deutsche bank",
        "barclays",
        "ubs",
        "wells fargo",
        "citigroup",
        "jefferies",
        "raymond james",
        "piper sandler",
        "cowen",
        "stifel",
        "bernstein",
        "mizuho",
        "nomura",
    }

    def __init__(self):
        """Initialize transcript parser."""
        # Compile regex patterns for efficiency
        self.speaker_pattern = re.compile(
            r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z]\.?)?)\s*[:-]", re.MULTILINE
        )
        self.qa_pattern = re.compile(
            r"(?:question|q&a|questions?\s+and\s+answers?|analyst\s+questions?)",
            re.IGNORECASE,
        )
        self.forward_guidance_pattern = re.compile(
            r"(?:guidance|outlook|forecast|expect|anticipate|project|target|"
            r"guidance\s+for)",
            re.IGNORECASE,
        )

    def parse_speakers(self, transcript_text: str) -> List[Dict[str, Any]]:
        """
        Parse and identify speakers from transcript.

        Args:
            transcript_text: Raw transcript text

        Returns:
            List of speaker dictionaries with name, role, and company
        """
        speakers = []
        seen_speakers = set()

        # Find all speaker mentions
        matches = self.speaker_pattern.finditer(transcript_text)
        for match in matches:
            speaker_name = match.group(1).strip()
            if speaker_name.lower() not in seen_speakers:
                seen_speakers.add(speaker_name.lower())

                # Classify speaker role
                role = self._classify_speaker_role(speaker_name, transcript_text)
                company = self._extract_speaker_company(speaker_name, transcript_text)

                speakers.append(
                    {
                        "name": speaker_name,
                        "role": role,
                        "company": company,
                    }
                )

        logger.debug(f"Identified {len(speakers)} unique speakers")
        return speakers

    def _classify_speaker_role(self, speaker_name: str, transcript_text: str) -> str:
        """
        Classify speaker role (management, analyst, operator, other).

        Args:
            speaker_name: Speaker name
            transcript_text: Full transcript text

        Returns:
            Role classification string
        """
        # Check for operator
        if "operator" in speaker_name.lower():
            return "operator"

        # Check for management titles in context around speaker name
        name_lower = speaker_name.lower()
        for title in self.MANAGEMENT_TITLES:  # noqa: B007
            if title in name_lower:
                return "management"

        # Check for analyst companies
        # Look for speaker name followed by company name
        pattern = re.compile(
            rf"{re.escape(speaker_name)}.*?({'|'.join(self.ANALYST_COMPANIES)})",
            re.IGNORECASE,
        )
        if pattern.search(transcript_text):
            return "analyst"

        # Check if speaker is mentioned with "analyst" or "question"
        analyst_pattern = re.compile(
            rf"{re.escape(speaker_name)}.*?(?:analyst|question)",
            re.IGNORECASE,
        )
        if analyst_pattern.search(transcript_text):
            return "analyst"

        # Default to management if company context suggests it
        # (This is a heuristic - could be improved with NLP)
        return "management"

    def _extract_speaker_company(
        self, speaker_name: str, transcript_text: str
    ) -> Optional[str]:
        """
        Extract company name associated with speaker.

        Args:
            speaker_name: Speaker name
            transcript_text: Full transcript text

        Returns:
            Company name or None
        """
        # Look for company name after speaker name
        pattern = re.compile(
            rf"{re.escape(speaker_name)}.*?((?:{'|'.join(self.ANALYST_COMPANIES)}))",
            re.IGNORECASE,
        )
        match = pattern.search(transcript_text)
        if match:
            return match.group(1).title()

        return None

    def extract_qa_sections(self, transcript_text: str) -> List[Dict[str, Any]]:
        """
        Extract Q&A sections from transcript.

        Args:
            transcript_text: Raw transcript text

        Returns:
            List of Q&A section dictionaries
        """
        qa_sections = []

        # Find Q&A section markers
        qa_markers = self.qa_pattern.finditer(transcript_text)
        qa_start_positions = [m.start() for m in qa_markers]

        if not qa_start_positions:
            logger.debug("No Q&A section markers found")
            return qa_sections

        # Extract Q&A content
        # For simplicity, extract from first Q&A marker to end
        # More sophisticated parsing could identify individual Q&A pairs
        qa_start = qa_start_positions[0]
        qa_text = transcript_text[qa_start:]

        # Split into individual Q&A pairs (simplified)
        # Look for question patterns
        question_pattern = re.compile(
            r"(?:question|q):\s*(.+?)(?=answer|a:|$)", re.IGNORECASE | re.DOTALL
        )
        questions = question_pattern.findall(qa_text)

        for idx, question in enumerate(questions):
            qa_sections.append(
                {
                    "question_number": idx + 1,
                    "question": question.strip(),
                    "answer": "",  # Would need more sophisticated parsing for answers
                }
            )

        logger.debug(f"Extracted {len(qa_sections)} Q&A sections")
        return qa_sections

    def extract_management_commentary(
        self, transcript_text: str, speakers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract management commentary sections.

        Args:
            transcript_text: Raw transcript text
            speakers: List of identified speakers

        Returns:
            List of management commentary dictionaries
        """
        commentary = []

        # Get management speaker names
        management_speakers = [s["name"] for s in speakers if s["role"] == "management"]

        if not management_speakers:
            logger.debug("No management speakers identified")
            return commentary

        # Extract statements by management speakers
        for speaker in management_speakers:
            # Find all statements by this speaker
            pattern = re.compile(
                rf"^{re.escape(speaker)}\s*[:-]\s*(.+?)"
                rf"(?=^{re.escape(speaker)}|^[A-Z][a-z]+|$)",
                re.MULTILINE | re.DOTALL,
            )
            matches = pattern.finditer(transcript_text)

            for match in matches:
                statement = match.group(1).strip()
                if len(statement) > 50:  # Filter out very short statements
                    commentary.append(
                        {
                            "speaker": speaker,
                            "commentary": statement,
                            "length": len(statement),
                        }
                    )

        logger.debug(f"Extracted {len(commentary)} management commentary sections")
        return commentary

    def extract_forward_guidance(self, transcript_text: str) -> List[Dict[str, Any]]:
        """
        Extract forward guidance statements.

        Args:
            transcript_text: Raw transcript text

        Returns:
            List of forward guidance dictionaries
        """
        guidance_statements = []

        # Find sentences containing guidance keywords
        sentences = re.split(r"[.!?]+", transcript_text)
        for sentence in sentences:
            if self.forward_guidance_pattern.search(sentence):
                # Extract numbers and timeframes
                numbers = re.findall(r"\$?[\d,]+\.?\d*", sentence)
                timeframes = re.findall(
                    r"(?:q[1-4]|quarter|year|fiscal|annual|monthly)",
                    sentence,
                    re.IGNORECASE,
                )

                guidance_statements.append(
                    {
                        "statement": sentence.strip(),
                        "numbers": numbers,
                        "timeframes": timeframes,
                    }
                )

        logger.debug(
            f"Extracted {len(guidance_statements)} forward guidance statements"
        )
        return guidance_statements

    def parse_transcript(self, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse complete transcript and extract all structured information.

        Args:
            transcript_data: Transcript data dictionary from fetcher

        Returns:
            Parsed transcript dictionary with all extracted information

        Raises:
            TranscriptParserError: If parsing fails
        """
        try:
            transcript_text = transcript_data.get("transcript", "")
            if not transcript_text:
                raise TranscriptParserError("Empty transcript text")

            logger.info(
                f"Parsing transcript for {transcript_data.get('ticker', 'unknown')}"
            )

            # Parse speakers
            speakers = self.parse_speakers(transcript_text)

            # Extract Q&A sections
            qa_sections = self.extract_qa_sections(transcript_text)

            # Extract management commentary
            management_commentary = self.extract_management_commentary(
                transcript_text, speakers
            )

            # Extract forward guidance
            forward_guidance = self.extract_forward_guidance(transcript_text)

            # Build parsed transcript structure
            parsed_transcript = {
                "ticker": transcript_data.get("ticker"),
                "date": transcript_data.get("date"),
                "quarter": transcript_data.get("quarter"),
                "fiscal_year": transcript_data.get("fiscal_year"),
                "source": transcript_data.get("source"),
                "url": transcript_data.get("url"),
                "speakers": speakers,
                "qa_sections": qa_sections,
                "management_commentary": management_commentary,
                "forward_guidance": forward_guidance,
                "transcript_text": transcript_text,
                "metadata": {
                    "total_speakers": len(speakers),
                    "management_speakers": len(
                        [s for s in speakers if s["role"] == "management"]
                    ),
                    "analyst_speakers": len(
                        [s for s in speakers if s["role"] == "analyst"]
                    ),
                    "qa_count": len(qa_sections),
                    "commentary_count": len(management_commentary),
                    "guidance_count": len(forward_guidance),
                    "transcript_length": len(transcript_text),
                },
            }

            logger.info(
                f"Successfully parsed transcript: "
                f"{parsed_transcript['metadata']['total_speakers']} speakers, "
                f"{parsed_transcript['metadata']['qa_count']} Q&A sections"
            )

            return parsed_transcript

        except Exception as e:
            logger.error(f"Transcript parsing failed: {str(e)}", exc_info=True)
            raise TranscriptParserError(f"Parsing failed: {str(e)}") from e

    def format_transcript_for_rag(self, parsed_transcript: Dict[str, Any]) -> str:
        """
        Format parsed transcript as text for RAG ingestion.

        Args:
            parsed_transcript: Parsed transcript dictionary

        Returns:
            Formatted text string suitable for RAG ingestion
        """
        lines = []

        # Header
        lines.append(f"Earnings Call Transcript: {parsed_transcript['ticker']}")
        lines.append(f"Date: {parsed_transcript.get('date', 'Unknown')}")
        if parsed_transcript.get("quarter"):
            lines.append(f"Quarter: {parsed_transcript['quarter']}")
        if parsed_transcript.get("fiscal_year"):
            lines.append(f"Fiscal Year: {parsed_transcript['fiscal_year']}")
        lines.append("")

        # Speakers
        lines.append("Speakers:")
        for speaker in parsed_transcript.get("speakers", []):
            role_info = f" ({speaker['role']})"
            company_info = f" - {speaker['company']}" if speaker.get("company") else ""
            lines.append(f"  - {speaker['name']}{role_info}{company_info}")
        lines.append("")

        # Management Commentary
        if parsed_transcript.get("management_commentary"):
            lines.append("Management Commentary:")
            for commentary in parsed_transcript["management_commentary"][
                :5
            ]:  # Limit to first 5
                lines.append(
                    f"  {commentary['speaker']}: {commentary['commentary'][:200]}..."
                )
            lines.append("")

        # Forward Guidance
        if parsed_transcript.get("forward_guidance"):
            lines.append("Forward Guidance:")
            for guidance in parsed_transcript["forward_guidance"][
                :5
            ]:  # Limit to first 5
                lines.append(f"  {guidance['statement']}")
            lines.append("")

        # Q&A Sections
        if parsed_transcript.get("qa_sections"):
            lines.append("Q&A Section:")
            for qa in parsed_transcript["qa_sections"][:3]:  # Limit to first 3
                lines.append(f"  Q{qa['question_number']}: {qa['question'][:200]}...")
            lines.append("")

        # Full Transcript
        lines.append("Full Transcript:")
        lines.append(parsed_transcript.get("transcript_text", ""))

        return "\n".join(lines)
