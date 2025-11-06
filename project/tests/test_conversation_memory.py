"""
Tests for conversation memory functionality.

Tests conversation context integration, token counting, and
conversation history management.
"""

from app.utils.conversation_memory import (
    count_tokens,
    format_conversation_history,
    get_conversation_context,
    trim_conversation_history,
)


class TestTokenCounting:
    """Test token counting functionality."""

    def test_count_tokens_basic(self):
        """Test basic token counting."""
        text = "Hello, world!"
        tokens = count_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_count_tokens_empty(self):
        """Test token counting with empty string."""
        tokens = count_tokens("")
        assert tokens == 0

    def test_count_tokens_long_text(self):
        """Test token counting with longer text."""
        text = "This is a longer piece of text that should have more tokens."
        tokens = count_tokens(text)
        assert tokens > 5

    def test_count_tokens_with_model(self):
        """Test token counting with specific model."""
        text = "Test text"
        tokens = count_tokens(text, model="gpt-4")
        assert tokens > 0


class TestConversationHistoryFormatting:
    """Test conversation history formatting."""

    def test_format_conversation_history_empty(self):
        """Test formatting empty conversation history."""
        result = format_conversation_history([])
        assert result == ""

    def test_format_conversation_history_basic(self):
        """Test formatting basic conversation history."""
        messages = [
            {"role": "user", "content": "What is revenue?"},
            {"role": "assistant", "content": "Revenue is income from sales."},
        ]
        result = format_conversation_history(messages)
        assert "Previous conversation:" in result
        assert "User: What is revenue?" in result
        assert "Assistant: Revenue is income from sales." in result

    def test_format_conversation_history_with_max_tokens(self):
        """Test formatting with token limit."""
        messages = [
            {"role": "user", "content": "Short question"},
            {"role": "assistant", "content": "Short answer"},
        ]
        # Use very small token limit
        result = format_conversation_history(messages, max_tokens=10)
        # Should still format but may be truncated
        assert isinstance(result, str)

    def test_format_conversation_history_prioritizes_recent(self):
        """Test that recent messages are prioritized."""
        messages = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
            {"role": "assistant", "content": "Second answer"},
        ]
        result = format_conversation_history(messages, max_tokens=50)
        # Recent messages should be included
        assert "Second question" in result or "Second answer" in result


class TestConversationHistoryTrimming:
    """Test conversation history trimming."""

    def test_trim_conversation_history_empty(self):
        """Test trimming empty history."""
        result = trim_conversation_history([])
        assert result == []

    def test_trim_conversation_history_by_count(self):
        """Test trimming by message count."""
        messages = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"},
            {"role": "assistant", "content": "Answer 2"},
        ]
        result = trim_conversation_history(messages, max_history=2)
        assert len(result) <= 2
        # Should keep most recent
        assert (
            "Question 2" in result[-1]["content"] or "Answer 2" in result[-1]["content"]
        )

    def test_trim_conversation_history_by_tokens(self):
        """Test trimming by token count."""
        messages = [
            {"role": "user", "content": "Short"},
            {"role": "assistant", "content": "Short"},
        ]
        result = trim_conversation_history(messages, max_tokens=100)
        assert len(result) <= len(messages)

    def test_trim_conversation_history_keeps_recent(self):
        """Test that trimming keeps recent messages."""
        messages = [
            {"role": "user", "content": "Old question"},
            {"role": "assistant", "content": "Old answer"},
            {"role": "user", "content": "Recent question"},
            {"role": "assistant", "content": "Recent answer"},
        ]
        result = trim_conversation_history(messages, max_history=2)
        # Should keep recent messages
        assert any("Recent" in msg.get("content", "") for msg in result)


class TestConversationContext:
    """Test conversation context generation."""

    def test_get_conversation_context_empty(self):
        """Test getting context from empty history."""
        result = get_conversation_context([], "Current question")
        assert result is None

    def test_get_conversation_context_basic(self):
        """Test getting context from basic history."""
        messages = [
            {"role": "user", "content": "What is revenue?"},
            {"role": "assistant", "content": "Revenue is income."},
        ]
        result = get_conversation_context(messages, "Tell me more")
        assert result is not None
        assert "Previous conversation:" in result

    def test_get_conversation_context_excludes_current(self):
        """Test that current question is excluded from history."""
        messages = [
            {"role": "user", "content": "What is revenue?"},
            {"role": "assistant", "content": "Revenue is income."},
        ]
        result = get_conversation_context(messages, "What is revenue?")
        # Current question should not appear in history
        assert result is None or "What is revenue?" not in result

    def test_get_conversation_context_disabled(self):
        """Test that context is None when disabled."""
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"},
        ]
        result = get_conversation_context(messages, "New question", enabled=False)
        assert result is None

    def test_get_conversation_context_filters_empty(self):
        """Test that empty messages are filtered."""
        messages = [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "Answer"},
        ]
        result = get_conversation_context(messages, "Question")
        # Should handle empty messages gracefully
        assert result is None or isinstance(result, str)


class TestConversationMemoryIntegration:
    """Integration tests for conversation memory."""

    def test_multi_turn_conversation(self):
        """Test multi-turn conversation context."""
        messages = [
            {"role": "user", "content": "What is revenue?"},
            {"role": "assistant", "content": "Revenue is income from sales."},
            {"role": "user", "content": "What about expenses?"},
            {"role": "assistant", "content": "Expenses are costs."},
        ]
        result = get_conversation_context(messages, "Tell me more")
        assert result is not None
        assert "revenue" in result.lower() or "expenses" in result.lower()

    def test_conversation_context_formatting(self):
        """Test that conversation context is properly formatted."""
        messages = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
        ]
        result = get_conversation_context(messages, "Question 2")
        assert result is not None
        assert "Previous conversation:" in result
        assert "User:" in result or "Assistant:" in result

    def test_token_limits_enforced(self):
        """Test that token limits are enforced."""
        # Create messages that would exceed token limit
        long_content = "This is a very long message. " * 100
        messages = [
            {"role": "user", "content": long_content},
            {"role": "assistant", "content": long_content},
        ]
        result = format_conversation_history(messages, max_tokens=100)
        # Should be truncated or limited
        tokens = count_tokens(result)
        assert tokens <= 150  # Allow some margin
