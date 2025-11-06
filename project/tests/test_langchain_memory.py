"""
Unit tests for LangChain memory integration.

Tests ConversationBufferMemory and StreamlitChatMessageHistory functionality.
"""

from app.utils.langchain_memory import (
    ConversationBufferMemory,
    StreamlitChatMessageHistory,
)


class TestStreamlitChatMessageHistory:
    """Test StreamlitChatMessageHistory class."""

    def test_init_empty(self):
        """Test initialization with empty history."""
        history = StreamlitChatMessageHistory()
        assert len(history.messages) == 0

    def test_init_with_messages(self):
        """Test initialization with existing messages."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        history = StreamlitChatMessageHistory(messages=messages)
        assert len(history.messages) == 2

    def test_add_user_message(self):
        """Test adding user message."""
        history = StreamlitChatMessageHistory()
        history.add_user_message("Test message")
        assert len(history.messages) == 1
        assert history.messages[0].content == "Test message"

    def test_add_ai_message(self):
        """Test adding AI message."""
        history = StreamlitChatMessageHistory()
        history.add_ai_message("AI response")
        assert len(history.messages) == 1
        assert history.messages[0].content == "AI response"

    def test_clear(self):
        """Test clearing messages."""
        history = StreamlitChatMessageHistory()
        history.add_user_message("Test")
        history.add_ai_message("Response")
        assert len(history.messages) == 2
        history.clear()
        assert len(history.messages) == 0

    def test_to_dict_list(self):
        """Test conversion to dictionary list."""
        history = StreamlitChatMessageHistory()
        history.add_user_message("Hello")
        history.add_ai_message("Hi")
        dict_list = history.to_dict_list()
        assert len(dict_list) == 2
        assert dict_list[0]["role"] == "user"
        assert dict_list[0]["content"] == "Hello"
        assert dict_list[1]["role"] == "assistant"
        assert dict_list[1]["content"] == "Hi"


class TestConversationBufferMemory:
    """Test ConversationBufferMemory class."""

    def test_init_default(self):
        """Test initialization with defaults."""
        memory = ConversationBufferMemory()
        assert memory.max_token_limit > 0
        assert memory.max_history > 0

    def test_init_custom(self):
        """Test initialization with custom parameters."""
        memory = ConversationBufferMemory(max_token_limit=1000, max_history=5)
        assert memory.max_token_limit == 1000
        assert memory.max_history == 5

    def test_save_context(self):
        """Test saving context."""
        memory = ConversationBufferMemory()
        memory.save_context(inputs={"input": "Hello"}, outputs={"output": "Hi there!"})
        assert len(memory.chat_memory.messages) == 2

    def test_load_memory_variables_string(self):
        """Test loading memory variables as string."""
        memory = ConversationBufferMemory(return_messages=False)
        memory.save_context(inputs={"input": "Hello"}, outputs={"output": "Hi there!"})
        vars = memory.load_memory_variables({})
        assert "history" in vars
        assert isinstance(vars["history"], str)
        assert "Hello" in vars["history"]
        assert "Hi there!" in vars["history"]

    def test_load_memory_variables_messages(self):
        """Test loading memory variables as messages."""
        memory = ConversationBufferMemory(return_messages=True)
        memory.save_context(inputs={"input": "Hello"}, outputs={"output": "Hi there!"})
        vars = memory.load_memory_variables({})
        assert "history" in vars
        assert isinstance(vars["history"], list)

    def test_clear(self):
        """Test clearing memory."""
        memory = ConversationBufferMemory()
        memory.save_context(inputs={"input": "Hello"}, outputs={"output": "Hi there!"})
        assert len(memory.chat_memory.messages) == 2
        memory.clear()
        assert len(memory.chat_memory.messages) == 0

    def test_get_memory_stats(self):
        """Test getting memory statistics."""
        memory = ConversationBufferMemory()
        memory.save_context(inputs={"input": "Hello"}, outputs={"output": "Hi there!"})
        stats = memory.get_memory_stats()
        assert "message_count" in stats
        assert "token_count" in stats
        assert "max_tokens" in stats
        assert "max_history" in stats
        assert stats["message_count"] == 2
        assert stats["user_messages"] == 1
        assert stats["assistant_messages"] == 1

    def test_to_dict_list(self):
        """Test conversion to dictionary list."""
        memory = ConversationBufferMemory()
        memory.save_context(inputs={"input": "Hello"}, outputs={"output": "Hi there!"})
        dict_list = memory.to_dict_list()
        assert len(dict_list) == 2
        assert dict_list[0]["role"] == "user"
        assert dict_list[1]["role"] == "assistant"

    def test_trim_memory_by_tokens(self):
        """Test memory trimming when token limit exceeded."""
        memory = ConversationBufferMemory(max_token_limit=50, max_history=100)
        # Add many messages that exceed token limit
        for i in range(10):
            memory.save_context(
                inputs={"input": f"Question {i} " * 10},
                outputs={"output": f"Answer {i} " * 10},
            )
        # Memory should be trimmed
        stats = memory.get_memory_stats()
        assert (
            stats["token_count"] <= memory.max_token_limit * 1.1
        )  # Allow small margin

    def test_trim_memory_by_history(self):
        """Test memory trimming when history limit exceeded."""
        memory = ConversationBufferMemory(max_token_limit=10000, max_history=3)
        # Add more messages than max_history
        for i in range(5):
            memory.save_context(
                inputs={"input": f"Question {i}"},
                outputs={"output": f"Answer {i}"},
            )
        # Memory should be trimmed to max_history
        stats = memory.get_memory_stats()
        assert (
            stats["message_count"] <= memory.max_history * 2
        )  # User + assistant pairs


class TestMemoryIntegration:
    """Test memory integration scenarios."""

    def test_memory_with_streamlit_messages(self):
        """Test memory integration with Streamlit message format."""
        streamlit_messages = [
            {"role": "user", "content": "What is AI?"},
            {"role": "assistant", "content": "AI is artificial intelligence."},
            {"role": "user", "content": "Tell me more."},
        ]
        history = StreamlitChatMessageHistory(messages=streamlit_messages)
        memory = ConversationBufferMemory(chat_memory=history)
        vars = memory.load_memory_variables({})
        assert "history" in vars
        # Should contain conversation history
        history_str = (
            vars["history"]
            if isinstance(vars["history"], str)
            else str(vars["history"])
        )
        assert "AI" in history_str or len(vars["history"]) > 0

    def test_memory_persistence(self):
        """Test that memory persists across multiple saves."""
        memory = ConversationBufferMemory()
        memory.save_context(
            inputs={"input": "First question"},
            outputs={"output": "First answer"},
        )
        memory.save_context(
            inputs={"input": "Second question"},
            outputs={"output": "Second answer"},
        )
        assert len(memory.chat_memory.messages) == 4  # 2 user + 2 assistant
        vars = memory.load_memory_variables({})
        history_str = (
            vars["history"]
            if isinstance(vars["history"], str)
            else str(vars["history"])
        )
        assert (
            "First" in history_str
            or "Second" in history_str
            or len(vars["history"]) > 0
        )
