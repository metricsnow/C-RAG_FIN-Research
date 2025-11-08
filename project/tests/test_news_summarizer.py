"""
Unit tests for news summarizer module.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from app.ingestion.news_summarizer import (
    NewsSummarizer,
    NewsSummarizerError,
)


class TestNewsSummarizer:
    """Test cases for NewsSummarizer class."""

    def test_init_disabled(self):
        """Test initializing summarizer with disabled flag."""
        summarizer = NewsSummarizer(enabled=False)
        assert summarizer.enabled is False
        assert summarizer.llm is None

    def test_init_enabled_without_llm(self):
        """Test initializing summarizer with enabled flag but no LLM available."""
        with patch("app.ingestion.news_summarizer.get_llm") as mock_get_llm:
            mock_get_llm.side_effect = Exception("LLM not available")
            with pytest.raises(NewsSummarizerError):
                NewsSummarizer(enabled=True)

    def test_init_enabled_with_llm(self):
        """Test initializing summarizer with enabled flag and LLM."""
        mock_llm = MagicMock()
        with patch("app.ingestion.news_summarizer.get_llm", return_value=mock_llm):
            summarizer = NewsSummarizer(enabled=True)
            assert summarizer.enabled is True
            assert summarizer.llm is not None
            assert summarizer.target_words == 150
            assert summarizer.min_words == 50
            assert summarizer.max_words == 200

    def test_init_custom_params(self):
        """Test initializing summarizer with custom parameters."""
        mock_llm = MagicMock()
        with patch("app.ingestion.news_summarizer.get_llm", return_value=mock_llm):
            summarizer = NewsSummarizer(
                enabled=True,
                target_words=100,
                min_words=30,
                max_words=150,
            )
            assert summarizer.target_words == 100
            assert summarizer.min_words == 30
            assert summarizer.max_words == 150

    def test_summarize_article_disabled(self):
        """Test summarizing article when summarization is disabled."""
        summarizer = NewsSummarizer(enabled=False)
        article = {"title": "Test", "content": "Test content"}
        result = summarizer.summarize_article(article)
        assert result is None

    def test_summarize_article_no_content(self):
        """Test summarizing article with no content."""
        mock_llm = MagicMock()
        with patch("app.ingestion.news_summarizer.get_llm", return_value=mock_llm):
            summarizer = NewsSummarizer(enabled=True)
            article = {"title": "Test", "content": ""}
            result = summarizer.summarize_article(article)
            assert result is None

    def test_summarize_article_success(self):
        """Test successful article summarization."""
        mock_llm = MagicMock()
        mock_response = Mock()
        mock_response.content = "This is a test summary of the article."
        mock_llm.invoke.return_value = mock_response

        with patch("app.ingestion.news_summarizer.get_llm", return_value=mock_llm):
            summarizer = NewsSummarizer(enabled=True)
            article = {
                "title": "Test Article",
                "content": (
                    "This is a long article with lots of content "
                    "about financial news."
                ),
            }
            result = summarizer.summarize_article(article)

            assert result is not None
            assert "test summary" in result.lower()
            mock_llm.invoke.assert_called_once()

    def test_summarize_article_string_response(self):
        """Test handling string response from LLM."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "This is a string summary response."

        with patch("app.ingestion.news_summarizer.get_llm", return_value=mock_llm):
            summarizer = NewsSummarizer(enabled=True)
            article = {
                "title": "Test Article",
                "content": "Test content",
            }
            result = summarizer.summarize_article(article)

            assert result is not None
            assert isinstance(result, str)

    def test_summarize_article_long_content_truncation(self):
        """Test truncation of very long articles."""
        mock_llm = MagicMock()
        mock_response = Mock()
        mock_response.content = "Summary"
        mock_llm.invoke.return_value = mock_response

        with patch("app.ingestion.news_summarizer.get_llm", return_value=mock_llm):
            summarizer = NewsSummarizer(enabled=True)
            # Create article with > 4000 characters
            long_content = "A" * 5000
            article = {
                "title": "Test Article",
                "content": long_content,
            }
            summarizer.summarize_article(article)

            # Verify truncation happened (prompt should contain truncated content)
            call_args = mock_llm.invoke.call_args[0][0]
            assert len(call_args) < 5000  # Should be truncated

    def test_summarize_article_empty_summary(self):
        """Test handling empty summary from LLM."""
        mock_llm = MagicMock()
        mock_response = Mock()
        mock_response.content = ""
        mock_llm.invoke.return_value = mock_response

        with patch("app.ingestion.news_summarizer.get_llm", return_value=mock_llm):
            summarizer = NewsSummarizer(enabled=True)
            article = {
                "title": "Test Article",
                "content": "Test content",
            }
            result = summarizer.summarize_article(article)
            assert result is None

    def test_summarize_article_llm_error(self):
        """Test handling LLM errors gracefully."""
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("LLM error")

        with patch("app.ingestion.news_summarizer.get_llm", return_value=mock_llm):
            summarizer = NewsSummarizer(enabled=True)
            article = {
                "title": "Test Article",
                "content": "Test content",
            }
            # Should return None, not raise exception
            result = summarizer.summarize_article(article)
            assert result is None

    def test_summarize_articles_batch(self):
        """Test batch summarization of multiple articles."""
        mock_llm = MagicMock()
        mock_response = Mock()
        mock_response.content = "Summary"
        mock_llm.invoke.return_value = mock_response

        with patch("app.ingestion.news_summarizer.get_llm", return_value=mock_llm):
            summarizer = NewsSummarizer(enabled=True)
            articles = [
                {"title": "Article 1", "content": "Content 1"},
                {"title": "Article 2", "content": "Content 2"},
                {"title": "Article 3", "content": "Content 3"},
            ]
            result = summarizer.summarize_articles(articles)

            assert len(result) == 3
            assert all("summary" in article for article in result)
            assert mock_llm.invoke.call_count == 3

    def test_summarize_articles_disabled(self):
        """Test batch summarization when disabled."""
        summarizer = NewsSummarizer(enabled=False)
        articles = [
            {"title": "Article 1", "content": "Content 1"},
        ]
        result = summarizer.summarize_articles(articles)

        assert len(result) == 1
        assert "summary" not in result[0]

    def test_summarize_articles_partial_failure(self):
        """Test batch summarization with some failures."""
        mock_llm = MagicMock()
        mock_response = Mock()
        mock_response.content = "Summary"

        # First call succeeds, second fails, third succeeds
        mock_llm.invoke.side_effect = [
            mock_response,
            Exception("LLM error"),
            mock_response,
        ]

        with patch("app.ingestion.news_summarizer.get_llm", return_value=mock_llm):
            summarizer = NewsSummarizer(enabled=True)
            articles = [
                {"title": "Article 1", "content": "Content 1"},
                {"title": "Article 2", "content": "Content 2"},
                {"title": "Article 3", "content": "Content 3"},
            ]
            result = summarizer.summarize_articles(articles)

            # All articles should be returned, but only 2 should have summaries
            assert len(result) == 3
            assert result[0].get("summary") is not None
            assert result[1].get("summary") is None
            assert result[2].get("summary") is not None

    def test_summarize_article_word_count_validation(self):
        """Test word count validation for summaries."""
        mock_llm = MagicMock()

        # Test summary that's too short
        mock_response_short = Mock()
        mock_response_short.content = "Short"
        # Test summary that's too long (200+ words)
        long_summary = "word " * 250
        mock_response_long = Mock()
        mock_response_long.content = long_summary

        with patch("app.ingestion.news_summarizer.get_llm", return_value=mock_llm):
            summarizer = NewsSummarizer(enabled=True, min_words=50, max_words=200)

            # Test short summary
            mock_llm.invoke.return_value = mock_response_short
            article = {"title": "Test", "content": "Test content"}
            result = summarizer.summarize_article(article)
            # Should still return it (with warning logged)
            assert result is not None

            # Test long summary
            mock_llm.invoke.return_value = mock_response_long
            result = summarizer.summarize_article(article)
            # Should be truncated to max_words
            assert result is not None
            word_count = len(result.split())
            assert word_count <= 200
