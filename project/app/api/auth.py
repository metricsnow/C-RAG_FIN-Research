"""
API authentication utilities.
"""

from fastapi import Header, HTTPException, status
from fastapi.security import APIKeyHeader

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)

# API key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(x_api_key: str = Header(None)) -> str:  # noqa: B008
    """
    Verify API key from request header.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        API key if valid

    Raises:
        HTTPException: If API key is invalid or missing (when auth is enabled)
    """
    # If API key is not configured, skip authentication
    if not config.api_key:
        logger.debug("API key authentication disabled (no API_KEY configured)")
        return "anonymous"

    # If API key is configured but not provided, raise error
    if not x_api_key:
        logger.warning("API key missing from request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key matches configured key
    if x_api_key != config.api_key:
        logger.warning(f"Invalid API key provided: {x_api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.debug("API key verified successfully")
    return x_api_key
