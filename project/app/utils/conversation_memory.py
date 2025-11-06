"""
Conversation memory utility module.

Provides utilities for managing conversation history, token counting,
and context window management for RAG queries.
"""

from typing import Any, Dict, List, Optional

import tiktoken

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Default encoding for token counting (cl100k_base is used by GPT-3.5/GPT-4)
# For Ollama models, we'll use a reasonable approximation
_DEFAULT_ENCODING = "cl100k_base"


def count_tokens(text: str, model: Optional[str] = None) -> int:
    """
    Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for
        model: Model name (optional, for model-specific encoding)

    Returns:
        Number of tokens
    """
    try:
        # Try to get encoding for specific model
        if model:
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # Model not found, use default encoding
                encoding = tiktoken.get_encoding(_DEFAULT_ENCODING)
        else:
            encoding = tiktoken.get_encoding(_DEFAULT_ENCODING)

        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(
            f"Token counting failed: {str(e)}, using character approximation"
        )
        # Fallback: approximate tokens as characters / 4 (rough estimate)
        return len(text) // 4


def format_conversation_history(
    messages: List[Dict[str, Any]], max_tokens: Optional[int] = None
) -> str:
    """
    Format conversation history for inclusion in prompt.

    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        max_tokens: Maximum tokens to include (optional)

    Returns:
        Formatted conversation history string
    """
    if not messages:
        return ""

    # Use config defaults if not specified
    if max_tokens is None:
        max_tokens = config.conversation_max_tokens

    # Format messages
    formatted_messages = []
    total_tokens = 0

    # Process messages in reverse order (most recent first)
    # and prioritize recent messages
    for message in reversed(messages):
        role = message.get("role", "user")
        content = message.get("content", "")

        if not content:
            continue

        # Format message
        formatted_msg = f"- {role.capitalize()}: {content}"
        msg_tokens = count_tokens(formatted_msg)

        # Check if adding this message would exceed token limit
        if total_tokens + msg_tokens > max_tokens:
            logger.debug(
                f"Conversation history truncated at {total_tokens} tokens "
                f"(limit: {max_tokens})"
            )
            break

        formatted_messages.insert(
            0, formatted_msg
        )  # Insert at beginning (oldest first)
        total_tokens += msg_tokens

    if not formatted_messages:
        return ""

    return "Previous conversation:\n" + "\n".join(formatted_messages)


def trim_conversation_history(
    messages: List[Dict[str, Any]],
    max_history: Optional[int] = None,
    max_tokens: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Trim conversation history to fit within limits.

    Prioritizes recent messages over older ones.

    Args:
        messages: List of message dictionaries
        max_history: Maximum number of messages to keep (optional)
        max_tokens: Maximum tokens to keep (optional)

    Returns:
        Trimmed list of messages
    """
    if not messages:
        return []

    # Use config defaults if not specified
    if max_history is None:
        max_history = config.conversation_max_history
    if max_tokens is None:
        max_tokens = config.conversation_max_tokens

    # First, limit by message count (keep most recent)
    trimmed = messages[-max_history:] if len(messages) > max_history else messages

    # Then, limit by tokens (keep most recent that fit)
    if max_tokens:
        result = []
        total_tokens = 0

        for message in reversed(trimmed):
            content = message.get("content", "")
            if not content:
                continue

            msg_tokens = count_tokens(content)
            if total_tokens + msg_tokens > max_tokens:
                break

            result.insert(0, message)
            total_tokens += msg_tokens

        return result

    return trimmed


def get_conversation_context(
    messages: List[Dict[str, Any]],
    current_question: str,
    enabled: Optional[bool] = None,
) -> Optional[str]:
    """
    Get formatted conversation context for RAG query.

    Args:
        messages: List of previous conversation messages
        current_question: Current question being asked
        enabled: Whether conversation memory is enabled (optional)

    Returns:
        Formatted conversation context string, or None if disabled/empty
    """
    # Use config default if not specified
    if enabled is None:
        enabled = config.conversation_enabled

    if not enabled:
        return None

    if not messages:
        return None

    # Exclude the current question from history (it will be added separately)
    # Filter out messages that match the current question
    history_messages = [
        msg
        for msg in messages
        if msg.get("role") != "user"
        or msg.get("content", "").strip() != current_question.strip()
    ]

    if not history_messages:
        return None

    # Trim and format conversation history
    trimmed = trim_conversation_history(history_messages)
    formatted = format_conversation_history(trimmed)

    return formatted if formatted else None
