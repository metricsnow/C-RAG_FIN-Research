"""
Unit tests for transcript parser module.
"""

import pytest

from app.ingestion.transcript_parser import TranscriptParser, TranscriptParserError


class TestTranscriptParser:
    """Test cases for TranscriptParser."""

    def test_init(self):
        """Test parser initialization."""
        parser = TranscriptParser()
        assert parser is not None

    def test_parse_speakers_basic(self):
        """Test basic speaker parsing."""
        parser = TranscriptParser()
        transcript = "John Smith: Welcome to the call.\nJane Doe: Thank you."
        speakers = parser.parse_speakers(transcript)

        assert len(speakers) >= 2
        speaker_names = [s["name"] for s in speakers]
        assert "John Smith" in speaker_names
        assert "Jane Doe" in speaker_names

    def test_parse_speakers_management(self):
        """Test management speaker identification."""
        parser = TranscriptParser()
        # Use format that matches the regex pattern: "Name: text" or "Name - text"
        # The pattern expects "Name:" format, not "Name, Title:"
        transcript = "Tim Cook: Good morning everyone. I am the CEO of Apple."
        speakers = parser.parse_speakers(transcript)

        management_speakers = [s for s in speakers if s["role"] == "management"]
        assert len(management_speakers) > 0

    def test_parse_speakers_operator(self):
        """Test operator speaker identification."""
        parser = TranscriptParser()
        transcript = "Operator: Thank you for joining."
        speakers = parser.parse_speakers(transcript)

        operators = [s for s in speakers if s["role"] == "operator"]
        assert len(operators) > 0

    def test_extract_qa_sections(self):
        """Test Q&A section extraction."""
        parser = TranscriptParser()
        transcript = (
            "Q&A Session\nQuestion: What is the outlook?\nAnswer: We expect growth."
        )
        qa_sections = parser.extract_qa_sections(transcript)

        assert len(qa_sections) > 0
        assert qa_sections[0]["question_number"] == 1

    def test_extract_qa_sections_no_qa(self):
        """Test Q&A extraction when no Q&A section exists."""
        parser = TranscriptParser()
        transcript = "This is a regular transcript without Q&A."
        qa_sections = parser.extract_qa_sections(transcript)

        # Should handle gracefully
        assert isinstance(qa_sections, list)

    def test_extract_management_commentary(self):
        """Test management commentary extraction."""
        parser = TranscriptParser()
        # Use format that matches the regex pattern and provides enough content
        transcript = (
            "Tim Cook: We are pleased with our results this quarter. "
            "Our revenue has grown significantly and we are optimistic "
            "about the future."
        )
        speakers = parser.parse_speakers(transcript)
        commentary = parser.extract_management_commentary(transcript, speakers)

        assert len(commentary) > 0
        assert commentary[0]["speaker"] in [s["name"] for s in speakers]

    def test_extract_forward_guidance(self):
        """Test forward guidance extraction."""
        parser = TranscriptParser()
        transcript = "We expect revenue to grow 10% in Q2 2025."
        guidance = parser.extract_forward_guidance(transcript)

        assert len(guidance) > 0
        assert (
            "guidance" in guidance[0]["statement"].lower()
            or "expect" in guidance[0]["statement"].lower()
        )

    def test_parse_transcript_complete(self):
        """Test complete transcript parsing."""
        parser = TranscriptParser()
        transcript_data = {
            "ticker": "AAPL",
            "date": "2025-01-15",
            "quarter": "Q1 2025",
            "fiscal_year": "2025",
            "source": "tikr",
            "url": "https://example.com",
            "transcript": (
                "Tim Cook, CEO: Welcome. We had a great quarter.\n"
                "Q&A Session\nQuestion: What's next?"
            ),
        }

        parsed = parser.parse_transcript(transcript_data)

        assert parsed["ticker"] == "AAPL"
        assert parsed["date"] == "2025-01-15"
        assert "speakers" in parsed
        assert "qa_sections" in parsed
        assert "metadata" in parsed

    def test_parse_transcript_empty(self):
        """Test parsing empty transcript."""
        parser = TranscriptParser()
        transcript_data = {"ticker": "AAPL", "transcript": ""}

        with pytest.raises(TranscriptParserError):
            parser.parse_transcript(transcript_data)

    def test_format_transcript_for_rag(self):
        """Test transcript formatting for RAG."""
        parser = TranscriptParser()
        parsed_transcript = {
            "ticker": "AAPL",
            "date": "2025-01-15",
            "quarter": "Q1 2025",
            "fiscal_year": "2025",
            "source": "tikr",
            "url": "https://example.com",
            "speakers": [{"name": "Tim Cook", "role": "management", "company": None}],
            "qa_sections": [
                {"question_number": 1, "question": "What's next?", "answer": ""}
            ],
            "management_commentary": [
                {"speaker": "Tim Cook", "commentary": "Great quarter", "length": 12}
            ],
            "forward_guidance": [
                {"statement": "We expect growth", "numbers": [], "timeframes": []}
            ],
            "transcript_text": "Full transcript text here",
        }

        formatted = parser.format_transcript_for_rag(parsed_transcript)

        assert "AAPL" in formatted
        assert "Q1 2025" in formatted
        assert "Tim Cook" in formatted
        assert "Full transcript text here" in formatted

    def test_classify_speaker_role_management(self):
        """Test speaker role classification for management."""
        parser = TranscriptParser()
        transcript = "Tim Cook, CEO of Apple: Welcome."
        role = parser._classify_speaker_role("Tim Cook", transcript)

        assert role == "management"

    def test_classify_speaker_role_operator(self):
        """Test speaker role classification for operator."""
        parser = TranscriptParser()
        transcript = "Operator: Thank you."
        role = parser._classify_speaker_role("Operator", transcript)

        assert role == "operator"

    def test_extract_speaker_company(self):
        """Test company extraction for speaker."""
        parser = TranscriptParser()
        transcript = "John Smith from Morgan Stanley: Question?"
        company = parser._extract_speaker_company("John Smith", transcript)

        assert company is not None
        assert "Morgan" in company or "Stanley" in company
