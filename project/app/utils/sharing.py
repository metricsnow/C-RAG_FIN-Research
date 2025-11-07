"""
Sharing utility module.

Provides functions for generating shareable links and link shortening.
"""

import base64
import json
from typing import Any, Dict, Optional
from uuid import uuid4

from app.utils.logger import get_logger

logger = get_logger(__name__)


def encode_conversation_data(messages: list[Dict[str, Any]]) -> str:
    """
    Encode conversation data to base64 for URL sharing.

    Args:
        messages: List of message dictionaries

    Returns:
        Base64-encoded string of conversation data
    """
    try:
        # Convert messages to JSON string
        json_str = json.dumps(messages, ensure_ascii=False)
        # Encode to base64
        encoded = base64.urlsafe_b64encode(json_str.encode("utf-8")).decode("utf-8")
        return encoded
    except Exception as e:
        logger.error(f"Failed to encode conversation data: {e}")
        raise ValueError(f"Failed to encode conversation data: {e}")


def decode_conversation_data(encoded_data: str) -> list[Dict[str, Any]]:
    """
    Decode base64-encoded conversation data.

    Args:
        encoded_data: Base64-encoded string of conversation data

    Returns:
        List of message dictionaries

    Raises:
        ValueError: If decoding fails
    """
    try:
        # Decode from base64
        json_str = base64.urlsafe_b64decode(encoded_data.encode("utf-8")).decode(
            "utf-8"
        )
        # Parse JSON
        messages = json.loads(json_str)
        return messages
    except Exception as e:
        logger.error(f"Failed to decode conversation data: {e}")
        raise ValueError(f"Failed to decode conversation data: {e}")


def generate_shareable_link(
    messages: list[Dict[str, Any]],
    base_url: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> str:
    """
    Generate a shareable link for a conversation.

    Args:
        messages: List of message dictionaries
        base_url: Base URL for the application (default: localhost)
        conversation_id: Optional conversation identifier

    Returns:
        Shareable URL string
    """
    if base_url is None:
        base_url = "http://localhost:8501"

    # Encode conversation data
    encoded_data = encode_conversation_data(messages)

    # Build URL
    url = f"{base_url}/?share={encoded_data}"

    if conversation_id:
        url += f"&id={conversation_id[:8]}"

    return url


def shorten_link(
    long_url: str, service: str = "tinyurl", api_key: Optional[str] = None
) -> str:
    """
    Shorten a URL using a link shortening service.

    Args:
        long_url: The URL to shorten
        service: Shortening service ('tinyurl', 'bitly', 'custom')
        api_key: Optional API key for services that require authentication

    Returns:
        Shortened URL string

    Note:
        This is a placeholder implementation. For production use,
        integrate with actual shortening services like:
        - TinyURL API
        - Bitly API
        - Custom shortening service
    """
    if service == "tinyurl":
        # TinyURL simple API (no key required)
        try:
            import requests

            response = requests.get(
                f"http://tinyurl.com/api-create.php?url={long_url}", timeout=5
            )
            if response.status_code == 200:
                return response.text.strip()
        except Exception as e:
            logger.warning(f"Failed to shorten URL with TinyURL: {e}")

    elif service == "bitly":
        # Bitly API (requires API key)
        if not api_key:
            logger.warning("Bitly API key not provided, returning original URL")
            return long_url

        try:
            import requests

            headers = {"Authorization": f"Bearer {api_key}"}
            data = {"long_url": long_url}
            response = requests.post(
                "https://api-ssl.bitly.com/v4/shorten",
                headers=headers,
                json=data,
                timeout=5,
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("link", long_url)
        except Exception as e:
            logger.warning(f"Failed to shorten URL with Bitly: {e}")

    # Fallback: return original URL
    logger.info("Link shortening not available, returning original URL")
    return long_url


def create_shareable_conversation(
    messages: list[Dict[str, Any]],
    base_url: Optional[str] = None,
    shorten: bool = False,
    service: str = "tinyurl",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a shareable conversation with link and metadata.

    Args:
        messages: List of message dictionaries
        base_url: Base URL for the application
        shorten: Whether to shorten the link
        service: Link shortening service to use
        api_key: Optional API key for shortening service

    Returns:
        Dictionary containing:
        - 'link': Shareable URL
        - 'short_link': Shortened URL (if shortening successful)
        - 'conversation_id': Conversation identifier
        - 'encoded_data': Base64-encoded conversation data
    """
    conversation_id = str(uuid4())

    # Generate shareable link
    link = generate_shareable_link(messages, base_url, conversation_id)

    result = {
        "link": link,
        "conversation_id": conversation_id,
        "encoded_data": encode_conversation_data(messages),
    }

    # Shorten link if requested
    if shorten:
        try:
            short_link = shorten_link(link, service, api_key)
            result["short_link"] = short_link
        except Exception as e:
            logger.warning(f"Failed to shorten link: {e}")
            result["short_link"] = link

    return result
