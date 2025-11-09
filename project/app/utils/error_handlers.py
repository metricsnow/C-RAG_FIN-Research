"""
Error handling utilities for consistent error management across the codebase.

Provides decorators and helper functions for standardized error handling,
logging, and error tracking.
"""

import functools
from typing import Any, Callable, Optional, Type, TypeVar

from app.utils.logger import get_logger
from app.utils.metrics import track_error, track_success

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def handle_ingestion_errors(
    operation_name: str,
    custom_exception: Optional[Type[Exception]] = None,
    log_level: str = "error",
    track_metrics: bool = True,
    reraise: bool = True,
):
    """
    Decorator for consistent error handling in ingestion operations.

    Handles common exceptions (DocumentIngestionError, EmbeddingError,
    ChromaStoreError) and provides standardized logging and error tracking.

    Args:
        operation_name: Name of the operation for logging
        custom_exception: Custom exception class to raise on generic errors
        log_level: Logging level for errors ('error', 'warning', 'info')
        track_metrics: Whether to track error metrics (default: True)
        reraise: Whether to re-raise exceptions (default: True)

    Returns:
        Decorated function

    Example:
        @handle_ingestion_errors("document processing", IngestionPipelineError)
        def process_documents(self, ...):
            ...
    """
    from app.ingestion.document_loader import DocumentIngestionError
    from app.rag.embedding_factory import EmbeddingError
    from app.vector_db import ChromaStoreError

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = func(*args, **kwargs)
                if track_metrics:
                    track_success(None)  # Pass appropriate metric if available
                return result
            except DocumentIngestionError as e:
                log_message = (
                    f"{operation_name} failed: Document ingestion error - {str(e)}"
                )
                if log_level == "error":
                    logger.error(log_message)
                elif log_level == "warning":
                    logger.warning(log_message)
                else:
                    logger.info(log_message)

                if track_metrics:
                    track_error(None)  # Pass appropriate metric if available

                if reraise:
                    raise
                return None

            except EmbeddingError as e:
                log_message = f"{operation_name} failed: Embedding error - {str(e)}"
                if log_level == "error":
                    logger.error(log_message)
                elif log_level == "warning":
                    logger.warning(log_message)
                else:
                    logger.info(log_message)

                if track_metrics:
                    track_error(None)  # Pass appropriate metric if available

                if reraise:
                    raise
                return None

            except ChromaStoreError as e:
                log_message = (
                    f"{operation_name} failed: ChromaDB storage error - {str(e)}"
                )
                if log_level == "error":
                    logger.error(log_message)
                elif log_level == "warning":
                    logger.warning(log_message)
                else:
                    logger.info(log_message)

                if track_metrics:
                    track_error(None)  # Pass appropriate metric if available

                if reraise:
                    raise
                return None

            except Exception as e:
                log_message = f"{operation_name} failed: Unexpected error - {str(e)}"
                if log_level == "error":
                    logger.error(log_message, exc_info=True)
                elif log_level == "warning":
                    logger.warning(log_message)
                else:
                    logger.info(log_message)

                if track_metrics:
                    track_error(None)  # Pass appropriate metric if available

                if reraise:
                    if custom_exception:
                        raise custom_exception(
                            f"{operation_name} failed: {str(e)}"
                        ) from e
                    raise
                return None

        return wrapper  # type: ignore

    return decorator


def handle_fetcher_errors(
    fetcher_name: str,
    custom_exception: Optional[Type[Exception]] = None,
    log_level: str = "error",
    reraise: bool = True,
):
    """
    Decorator for consistent error handling in data fetcher operations.

    Handles common exceptions from data fetchers and provides standardized logging.

    Args:
        fetcher_name: Name of the fetcher for logging
        custom_exception: Custom exception class to raise on generic errors
        log_level: Logging level for errors ('error', 'warning', 'info')
        reraise: Whether to re-raise exceptions (default: True)

    Returns:
        Decorated function

    Example:
        @handle_fetcher_errors("FRED Fetcher", FREDFetcherError)
        def fetch_series(self, ...):
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if it's already a custom exception (don't wrap it)
                if custom_exception and isinstance(e, custom_exception):
                    log_message = f"{fetcher_name} error: {str(e)}"
                else:
                    log_message = f"{fetcher_name} error: Unexpected error - {str(e)}"

                if log_level == "error":
                    logger.error(log_message, exc_info=True)
                elif log_level == "warning":
                    logger.warning(log_message)
                else:
                    logger.info(log_message)

                if reraise:
                    if custom_exception and not isinstance(e, custom_exception):
                        raise custom_exception(f"{fetcher_name} error: {str(e)}") from e
                    raise
                return None

        return wrapper  # type: ignore

    return decorator


def safe_execute(
    operation: Callable[[], Any],
    operation_name: str,
    default_return: Any = None,
    log_level: str = "error",
    reraise: bool = False,
) -> Any:
    """
    Safely execute an operation with error handling.

    Args:
        operation: Function to execute
        operation_name: Name of operation for logging
        default_return: Value to return on error (if reraise=False)
        log_level: Logging level for errors
        reraise: Whether to re-raise exceptions

    Returns:
        Result of operation or default_return on error

    Example:
        result = safe_execute(
            lambda: risky_operation(),
            "risky operation",
            default_return=[],
        )
    """
    try:
        return operation()
    except Exception as e:
        log_message = f"{operation_name} failed: {str(e)}"
        if log_level == "error":
            logger.error(log_message, exc_info=True)
        elif log_level == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)

        if reraise:
            raise
        return default_return


def log_and_track_error(
    error: Exception,
    operation_name: str,
    metric: Optional[Any] = None,
    log_level: str = "error",
    context: Optional[dict] = None,
) -> None:
    """
    Log error and track metrics consistently.

    Args:
        error: Exception that occurred
        operation_name: Name of operation that failed
        metric: Optional metric to track (from app.utils.metrics)
        log_level: Logging level ('error', 'warning', 'info')
        context: Optional context dictionary for logging
    """
    log_message = f"{operation_name} failed: {str(error)}"
    if context:
        log_message += f" | Context: {context}"

    if log_level == "error":
        logger.error(log_message, exc_info=True)
    elif log_level == "warning":
        logger.warning(log_message)
    else:
        logger.info(log_message)

    if metric:
        track_error(metric)
