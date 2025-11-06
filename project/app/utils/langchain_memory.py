"""
LangChain memory integration module.

Provides LangChain-compatible memory components for conversation management.
This module creates a ConversationBufferMemory-like interface that integrates
with LangChain's message system and the existing RAG chain.
"""

from typing import Any, Dict, List, Optional

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

from app.utils.config import config
from app.utils.conversation_memory import count_tokens, trim_conversation_history
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StreamlitChatMessageHistory(BaseChatMessageHistory):
    """
    LangChain-compatible chat message history using Streamlit session state.

    This class provides a LangChain-compatible interface for managing
    conversation history while using Streamlit's session state for storage.
    """

    def __init__(self, messages: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize chat message history.

        Args:
            messages: Optional list of message dictionaries from Streamlit
                session state. If None, starts with empty history.
        """
        self._messages: List[BaseMessage] = []
        if messages:
            self._load_from_dicts(messages)

    def _load_from_dicts(self, messages: List[Dict[str, Any]]) -> None:
        """
        Load messages from Streamlit message dictionaries.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
        """
        self._messages = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                self._messages.append(HumanMessage(content=content))
            elif role == "assistant":
                self._messages.append(AIMessage(content=content))
            elif role == "system":
                self._messages.append(SystemMessage(content=content))

    def add_user_message(self, message: str) -> None:
        """
        Add a user message to the history.

        Args:
            message: User message content
        """
        self._messages.append(HumanMessage(content=message))
        logger.debug(f"Added user message: {message[:50]}...")

    def add_ai_message(self, message: str) -> None:
        """
        Add an AI message to the history.

        Args:
            message: AI message content
        """
        self._messages.append(AIMessage(content=message))
        logger.debug(f"Added AI message: {message[:50]}...")

    def add_message(self, message: BaseMessage) -> None:
        """
        Add a message to the history.

        Args:
            message: LangChain message object
        """
        self._messages.append(message)
        logger.debug(f"Added message: {type(message).__name__}")

    def clear(self) -> None:
        """Clear all messages from history."""
        self._messages = []
        logger.debug("Cleared message history")

    @property
    def messages(self) -> List[BaseMessage]:
        """
        Get all messages in the history.

        Returns:
            List of LangChain message objects
        """
        return self._messages

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Convert messages to Streamlit-compatible dictionary list.

        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        result = []
        for msg in self._messages:
            if isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                result.append({"role": "system", "content": msg.content})
        return result


class ConversationBufferMemory:
    """
    LangChain-compatible conversation buffer memory.

    Manages conversation history with token-aware trimming and context
    window management. Provides a ConversationBufferMemory-like interface
    that integrates with LangChain's message system.
    """

    def __init__(
        self,
        chat_memory: Optional[StreamlitChatMessageHistory] = None,
        max_token_limit: Optional[int] = None,
        max_history: Optional[int] = None,
        return_messages: bool = True,
    ):
        """
        Initialize conversation buffer memory.

        Args:
            chat_memory: Chat message history instance. If None, creates new.
            max_token_limit: Maximum tokens to keep in memory (optional)
            max_history: Maximum number of messages to keep (optional)
            return_messages: Whether to return LangChain messages (default: True)
        """
        if chat_memory is None:
            chat_memory = StreamlitChatMessageHistory()
        self.chat_memory = chat_memory

        # Use config defaults if not specified
        self.max_token_limit = (
            max_token_limit
            if max_token_limit is not None
            else config.conversation_max_tokens
        )
        self.max_history = (
            max_history if max_history is not None else config.conversation_max_history
        )
        self.return_messages = return_messages

        logger.debug(
            f"Initialized ConversationBufferMemory: "
            f"max_tokens={self.max_token_limit}, max_history={self.max_history}"
        )

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """
        Save user input and AI output to memory.

        Args:
            inputs: Dictionary with user input (typically {'input': '...'})
            outputs: Dictionary with AI output (typically {'output': '...'})
        """
        # Extract user input
        user_input = inputs.get("input", "")
        if not user_input:
            # Try alternative keys
            user_input = inputs.get("question", "") or inputs.get("query", "")

        # Extract AI output
        ai_output = outputs.get("output", "")
        if not ai_output:
            # Try alternative keys
            ai_output = outputs.get("answer", "") or outputs.get("response", "")

        if user_input:
            self.chat_memory.add_user_message(user_input)
        if ai_output:
            self.chat_memory.add_ai_message(ai_output)

        # Trim if necessary
        self._trim_memory()

        logger.debug(
            f"Saved context: user_input={user_input[:50]}..., "
            f"ai_output={ai_output[:50]}..."
        )

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load memory variables for use in prompts.

        Args:
            inputs: Input dictionary (not used, but required by interface)

        Returns:
            Dictionary with 'history' key containing formatted conversation history
        """
        messages = self.chat_memory.messages

        if not messages:
            return {"history": ""}

        # Convert to dict format for trimming
        message_dicts = self.chat_memory.to_dict_list()

        # Trim conversation history
        trimmed = trim_conversation_history(
            message_dicts,
            max_history=self.max_history,
            max_tokens=self.max_token_limit,
        )

        # Format for prompt
        if self.return_messages:
            # Return LangChain messages
            history_messages = []
            for msg_dict in trimmed:
                role = msg_dict.get("role", "")
                content = msg_dict.get("content", "")
                if role == "user":
                    history_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    history_messages.append(AIMessage(content=content))
            return {"history": history_messages}
        else:
            # Return formatted string
            history_str = self._format_history_string(trimmed)
            return {"history": history_str}

    def _format_history_string(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format conversation history as string for prompt inclusion.

        Args:
            messages: List of message dictionaries

        Returns:
            Formatted history string
        """
        if not messages:
            return ""

        formatted_parts = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted_parts.append(f"{role.capitalize()}: {content}")

        return "\n".join(formatted_parts)

    def _trim_memory(self) -> None:
        """Trim memory if it exceeds limits."""
        messages = self.chat_memory.to_dict_list()
        if not messages:
            return

        # Check if trimming is needed
        total_tokens = sum(count_tokens(msg.get("content", "")) for msg in messages)

        if total_tokens > self.max_token_limit or len(messages) > self.max_history:
            # Trim messages
            trimmed = trim_conversation_history(
                messages,
                max_history=self.max_history,
                max_tokens=self.max_token_limit,
            )

            # Rebuild chat memory with trimmed messages
            self.chat_memory.clear()
            for msg in trimmed:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    self.chat_memory.add_user_message(content)
                elif role == "assistant":
                    self.chat_memory.add_ai_message(content)

            logger.debug(f"Trimmed memory: {len(messages)} -> {len(trimmed)} messages")

    def clear(self) -> None:
        """Clear all memory."""
        self.chat_memory.clear()
        logger.debug("Cleared conversation memory")

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary with memory statistics (message_count, token_count, etc.)
        """
        messages = self.chat_memory.messages
        message_dicts = self.chat_memory.to_dict_list()

        total_tokens = sum(
            count_tokens(msg.get("content", "")) for msg in message_dicts
        )

        return {
            "message_count": len(messages),
            "token_count": total_tokens,
            "max_tokens": self.max_token_limit,
            "max_history": self.max_history,
            "user_messages": sum(1 for m in message_dicts if m.get("role") == "user"),
            "assistant_messages": sum(
                1 for m in message_dicts if m.get("role") == "assistant"
            ),
        }

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Convert memory to Streamlit-compatible dictionary list.

        Returns:
            List of message dictionaries
        """
        return self.chat_memory.to_dict_list()
