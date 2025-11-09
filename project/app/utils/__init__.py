"""
Utility functions and helpers.

Common utilities used across the application.
"""

# Lazy imports to avoid circular dependencies
# Import document_processors last as it depends on app.rag which may import app.utils
from app.utils.error_handlers import (
    handle_fetcher_errors,
    handle_ingestion_errors,
    log_and_track_error,
    safe_execute,
)
from app.utils.formatters import (
    format_dataframe_for_rag,
    format_event_for_rag,
    format_generic_data_for_rag,
    format_metadata_section,
    format_time_series_for_rag,
)

# Document processors import (has circular dependency risk)
# Imported conditionally to avoid circular imports
try:
    from app.utils.document_processors import generate_and_store_embeddings
except ImportError:
    # If circular import occurs, this will be None and can be imported directly
    generate_and_store_embeddings = None  # type: ignore

__all__ = [
    "generate_and_store_embeddings",
    "format_time_series_for_rag",
    "format_dataframe_for_rag",
    "format_event_for_rag",
    "format_generic_data_for_rag",
    "format_metadata_section",
    "handle_ingestion_errors",
    "handle_fetcher_errors",
    "safe_execute",
    "log_and_track_error",
]
