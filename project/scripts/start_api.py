#!/usr/bin/env python3
"""
FastAPI server startup script (TASK-029).

Starts the FastAPI application using Uvicorn ASGI server.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn  # noqa: E402

from app.utils.config import config  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def main() -> None:
    """Start FastAPI server."""
    if not config.api_enabled:
        logger.warning("API server is disabled (API_ENABLED=false)")
        return

    logger.info(f"Starting FastAPI server on {config.api_host}:{config.api_port}")

    try:
        uvicorn.run(
            "app.api.main:app",
            host=config.api_host,
            port=config.api_port,
            reload=False,  # Set to True for development
            log_level=config.log_level.lower(),
            access_log=True,
        )
    except KeyboardInterrupt:
        logger.info("API server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start API server: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
