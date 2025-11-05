"""
Logging configuration module.

Provides centralized logging configuration for the application with
support for environment-based log levels and structured logging.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from app.utils.config import config


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
    log_file_max_bytes: int = 10 * 1024 * 1024,  # 10MB
    log_file_backup_count: int = 5,
) -> logging.Logger:
    """
    Set up application-wide logging configuration.

    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            If None, uses config.LOG_LEVEL
        log_file: Optional path to log file. If None, logs only to console
        log_file_max_bytes: Maximum log file size before rotation (default: 10MB)
        log_file_backup_count: Number of backup log files to keep (default: 5)

    Returns:
        Configured root logger
    """
    # Get log level from config if not provided
    if log_level is None:
        log_level = config.LOG_LEVEL

    # Convert string to logging level constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler (always add)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file is not None:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=log_file_max_bytes,
            backupCount=log_file_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__ from the calling module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Initialize logging on module import if config.LOG_FILE is set
# Otherwise, logging will be initialized to console only
_log_file_path: Optional[Path] = None
if config.LOG_FILE:
    _log_file_path = Path(config.LOG_FILE)

setup_logging(
    log_file=_log_file_path,
    log_file_max_bytes=config.LOG_FILE_MAX_BYTES,
    log_file_backup_count=config.LOG_FILE_BACKUP_COUNT,
)
