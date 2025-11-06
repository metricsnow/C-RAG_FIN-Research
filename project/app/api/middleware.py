"""
API middleware for rate limiting and request logging.
"""

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Rate limiting storage (in-memory, per API key/IP)
# Format: {identifier: [timestamp1, timestamp2, ...]}
_rate_limit_storage: defaultdict[str, list[float]] = defaultdict(list)


def _cleanup_old_requests(identifier: str, window_seconds: int = 60) -> None:
    """
    Clean up old request timestamps outside the rate limit window.

    Args:
        identifier: Rate limit identifier (API key or IP)
        window_seconds: Time window in seconds (default: 60 for per-minute limit)
    """
    current_time = time.time()
    cutoff_time = current_time - window_seconds

    # Remove timestamps older than the window
    _rate_limit_storage[identifier] = [
        ts for ts in _rate_limit_storage[identifier] if ts > cutoff_time
    ]


def _check_rate_limit(identifier: str, limit: int) -> tuple[bool, int]:
    """
    Check if request is within rate limit.

    Args:
        identifier: Rate limit identifier (API key or IP)
        limit: Maximum requests per minute

    Returns:
        Tuple of (is_allowed, remaining_requests)
    """
    _cleanup_old_requests(identifier)
    current_requests = len(_rate_limit_storage[identifier])

    if current_requests >= limit:
        return False, 0

    # Add current request timestamp
    _rate_limit_storage[identifier].append(time.time())
    remaining = limit - current_requests - 1

    return True, remaining


def _get_rate_limit_identifier(request: Request) -> str:
    """
    Get rate limit identifier from request (API key or IP).

    Args:
        request: FastAPI request object

    Returns:
        Rate limit identifier string
    """
    # Try to get API key from header first
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key}"

    # Fall back to client IP
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for API requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """
        Process request with rate limiting.

        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler

        Returns:
            Response with rate limit headers
        """
        # Skip rate limiting for health and docs endpoints
        if request.url.path in ["/api/v1/health", "/docs", "/openapi.json", "/"]:
            return await call_next(request)

        # Get rate limit identifier
        identifier = _get_rate_limit_identifier(request)
        limit = config.api_rate_limit_per_minute

        # Check rate limit
        is_allowed, remaining = _check_rate_limit(identifier, limit)

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {identifier}: " f"{limit} requests per minute"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded: {limit} requests per minute",
                    "retry_after": 60,
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60",
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware for API requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """
        Process request with logging.

        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler

        Returns:
            Response with process time header
        """
        start_time = time.time()

        # Log request
        logger.info(
            f"API Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        response = await call_next(request)

        # Calculate process time
        process_time = time.time() - start_time

        # Add process time header
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        # Log response
        logger.info(
            f"API Response: {request.method} {request.url.path} "
            f"status={response.status_code} time={process_time:.4f}s"
        )

        return response
