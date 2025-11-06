"""
Conversation export utility module.

Provides functions to export conversation history to various formats:
JSON, Markdown, and plain text.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.utils.logger import get_logger

logger = get_logger(__name__)


def export_to_json(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> str:
    """
    Export conversation history to JSON format.

    Args:
        messages: List of message dictionaries with 'role', 'content',
            and optionally 'sources'
        model: Model name used for the conversation (optional)
        conversation_id: Unique conversation identifier (optional,
            generated if not provided)

    Returns:
        JSON string representation of the conversation
    """
    if conversation_id is None:
        conversation_id = str(uuid4())

    # Format messages for export
    export_messages = []
    for msg in messages:
        export_msg = {
            "role": msg.get("role", "unknown"),
            "content": msg.get("content", ""),
        }

        # Add timestamp if available
        if "timestamp" in msg:
            export_msg["timestamp"] = msg["timestamp"]

        # Add sources for assistant messages
        if msg.get("role") == "assistant" and "sources" in msg:
            export_msg["sources"] = msg["sources"]

        export_messages.append(export_msg)

    # Create export structure
    export_data = {
        "conversation_id": conversation_id,
        "created_at": datetime.now().isoformat(),
        "messages": export_messages,
        "metadata": {
            "model": model or "unknown",
            "total_messages": len(messages),
            "user_messages": sum(1 for m in messages if m.get("role") == "user"),
            "assistant_messages": sum(
                1 for m in messages if m.get("role") == "assistant"
            ),
        },
    }

    return json.dumps(export_data, indent=2, ensure_ascii=False)


def export_to_markdown(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> str:
    """
    Export conversation history to Markdown format.

    Args:
        messages: List of message dictionaries with 'role', 'content',
            and optionally 'sources'
        model: Model name used for the conversation (optional)
        conversation_id: Unique conversation identifier (optional)

    Returns:
        Markdown string representation of the conversation
    """
    if conversation_id is None:
        conversation_id = str(uuid4())

    # Header
    lines = ["# Conversation Export"]
    lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Model:** {model or 'unknown'}")
    lines.append(f"**Conversation ID:** {conversation_id}")
    lines.append("")
    lines.append("## Messages")
    lines.append("")

    # Format messages
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        # Add timestamp if available
        timestamp_str = ""
        if "timestamp" in msg:
            timestamp_str = f" *({msg['timestamp']})*"

        # Format based on role
        if role == "user":
            lines.append(f"### User{timestamp_str}")
            lines.append("")
            lines.append(content)
        elif role == "assistant":
            lines.append(f"### Assistant{timestamp_str}")
            lines.append("")
            lines.append(content)

            # Add sources if available
            if "sources" in msg and msg["sources"]:
                sources = msg["sources"]
                source_names = []
                for source in sources:
                    filename = source.get("filename") or source.get("source", "unknown")
                    # Extract just the filename if it's a path
                    if isinstance(filename, str) and "/" in filename:
                        filename = Path(filename).name
                    source_names.append(filename)

                if source_names:
                    lines.append("")
                    if len(source_names) == 1:
                        lines.append(f"**Source:** {source_names[0]}")
                    else:
                        lines.append(f"**Sources:** {', '.join(source_names)}")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def export_to_txt(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> str:
    """
    Export conversation history to plain text format.

    Args:
        messages: List of message dictionaries with 'role', 'content',
            and optionally 'sources'
        model: Model name used for the conversation (optional)
        conversation_id: Unique conversation identifier (optional)

    Returns:
        Plain text string representation of the conversation
    """
    if conversation_id is None:
        conversation_id = str(uuid4())

    # Header
    lines = ["Conversation Export"]
    lines.append("=" * 50)
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Model: {model or 'unknown'}")
    lines.append(f"Conversation ID: {conversation_id}")
    lines.append("=" * 50)
    lines.append("")

    # Format messages
    for idx, msg in enumerate(messages, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        # Add timestamp if available
        timestamp_str = ""
        if "timestamp" in msg:
            timestamp_str = f" ({msg['timestamp']})"

        # Format based on role
        lines.append(f"[{idx}] {role.upper()}{timestamp_str}")
        lines.append("-" * 50)
        lines.append(content)

        # Add sources if available
        if role == "assistant" and "sources" in msg and msg["sources"]:
            sources = msg["sources"]
            source_names = []
            for source in sources:
                filename = source.get("filename") or source.get("source", "unknown")
                # Extract just the filename if it's a path
                if isinstance(filename, str) and "/" in filename:
                    filename = Path(filename).name
                source_names.append(filename)

            if source_names:
                lines.append("")
                if len(source_names) == 1:
                    lines.append(f"Source: {source_names[0]}")
                else:
                    lines.append(f"Sources: {', '.join(source_names)}")

        lines.append("")
        lines.append("")

    return "\n".join(lines)


def generate_export_filename(
    format_type: str, conversation_id: Optional[str] = None
) -> str:
    """
    Generate a filename for the exported conversation.

    Args:
        format_type: Export format ('json', 'markdown', 'txt')
        conversation_id: Unique conversation identifier (optional)

    Returns:
        Filename string with timestamp and format extension
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_id_short = (
        conversation_id[:8] if conversation_id else "conversation"
    )  # Use first 8 chars of UUID

    format_extensions = {
        "json": "json",
        "markdown": "md",
        "txt": "txt",
    }

    extension = format_extensions.get(format_type.lower(), "txt")
    return f"conversation_{conv_id_short}_{timestamp}.{extension}"


def export_conversation(
    messages: List[Dict[str, Any]],
    format_type: str,
    model: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> tuple[str, str]:
    """
    Export conversation history to specified format.

    Args:
        messages: List of message dictionaries
        format_type: Export format ('json', 'markdown', 'txt')
        model: Model name used for the conversation (optional)
        conversation_id: Unique conversation identifier (optional)

    Returns:
        Tuple of (exported_content, filename)
    """
    if not messages:
        raise ValueError("Cannot export empty conversation")

    format_type_lower = format_type.lower()

    if format_type_lower == "json":
        content = export_to_json(messages, model, conversation_id)
    elif format_type_lower in ["markdown", "md"]:
        content = export_to_markdown(messages, model, conversation_id)
    elif format_type_lower in ["txt", "text"]:
        content = export_to_txt(messages, model, conversation_id)
    else:
        raise ValueError(
            f"Unsupported format type: {format_type}. "
            f"Supported formats: json, markdown, txt"
        )

    filename = generate_export_filename(format_type_lower, conversation_id)

    return content, filename
