"""
Data formatting utilities for RAG ingestion.

Provides common functions for formatting various data types (time series, indicators,
events, etc.) into text suitable for RAG ingestion. These utilities reduce code
duplication across data source fetchers.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


def format_metadata_section(
    title: str,
    metadata: Dict[str, Any],
    fields: List[str],
    field_labels: Optional[Dict[str, str]] = None,
) -> List[str]:
    """
    Format metadata fields into a text section.

    Args:
        title: Section title
        metadata: Metadata dictionary
        fields: List of field names to extract
        field_labels: Optional mapping of field names to display labels

    Returns:
        List of formatted text lines
    """
    if field_labels is None:
        field_labels = {}

    text_parts = [f"{title}:"]
    for field in fields:
        label = field_labels.get(field, field.replace("_", " ").title())
        value = metadata.get(field, "N/A")
        if value and value != "N/A":
            text_parts.append(f"{label}: {value}")

    return text_parts


def format_time_series_for_rag(
    series_id: str,
    metadata: Dict[str, Any],
    data: pd.Series,
    source_name: str = "Time Series",
    metadata_fields: Optional[List[str]] = None,
    include_recent_points: int = 10,
    include_statistics: bool = True,
) -> str:
    """
    Format time series data for RAG ingestion.

    Common pattern used by FRED, World Bank, IMF, and other time series data sources.

    Args:
        series_id: Unique identifier for the series
        metadata: Metadata dictionary with series information
        data: pandas Series with time series data
        source_name: Name of data source (e.g., "FRED", "World Bank")
        metadata_fields: List of metadata fields to include (default: common fields)
        include_recent_points: Number of recent data points to include (default: 10)
        include_statistics: Whether to include summary statistics (default: True)

    Returns:
        Formatted text string for RAG
    """
    if data is None or data.empty:
        return f"{source_name} Series: {series_id}\nNo data available"

    # Default metadata fields if not specified
    if metadata_fields is None:
        metadata_fields = [
            "title",
            "name",
            "description",
            "units",
            "unit",
            "frequency",
            "seasonal_adjustment",
            "observation_start",
            "observation_end",
            "last_updated",
        ]

    # Build formatted text
    text_parts = [f"{source_name} Economic Data Series: {series_id}"]

    # Add metadata fields
    for field in metadata_fields:
        value = metadata.get(field)
        if value:
            label = field.replace("_", " ").title()
            if field in ["observation_start", "observation_end"]:
                if (
                    "observation_start" in metadata_fields
                    and "observation_end" in metadata_fields
                ):
                    start = metadata.get("observation_start", "N/A")
                    end = metadata.get("observation_end", "N/A")
                    text_parts.append(f"Observation Period: {start} to {end}")
                    # Skip individual fields if we've combined them
                    if field == "observation_start":
                        continue
                    elif field == "observation_end":
                        continue
            else:
                text_parts.append(f"{label}: {value}")

    # Add notes if available
    for note_field in ["notes", "note", "description"]:
        if note_field in metadata and metadata[note_field]:
            note = str(metadata[note_field])
            text_parts.append(f"Notes: {note[:500]}")
            break

    # Add recent data points
    if include_recent_points > 0 and not data.empty:
        text_parts.append("\nRecent Data Points:")
        recent_data = data.tail(include_recent_points)
        for date, value in recent_data.items():
            if isinstance(date, pd.Timestamp):
                date_str = date.strftime("%Y-%m-%d")
            else:
                date_str = str(date)
            text_parts.append(f"  {date_str}: {value}")

    # Add summary statistics
    if include_statistics and not data.empty:
        text_parts.append("\nSummary Statistics:")
        text_parts.append(f"  Total Observations: {len(data)}")
        text_parts.append(f"  Latest Value: {data.iloc[-1]}")
        text_parts.append(f"  Mean: {data.mean():.2f}")
        text_parts.append(f"  Min: {data.min():.2f}")
        text_parts.append(f"  Max: {data.max():.2f}")

    return "\n".join(text_parts)


def format_dataframe_for_rag(
    indicator_code: str,
    metadata: Dict[str, Any],
    data: pd.DataFrame,
    source_name: str = "Indicator",
    metadata_fields: Optional[List[str]] = None,
    include_recent_data: bool = True,
    top_countries: int = 10,
    include_statistics: bool = True,
) -> str:
    """
    Format DataFrame (multi-country/time) data for RAG ingestion.

    Common pattern used by World Bank and IMF indicator data.

    Args:
        indicator_code: Unique identifier for the indicator
        metadata: Metadata dictionary with indicator information
        data: pandas DataFrame with indicator data (typically countries x years)
        source_name: Name of data source (e.g., "World Bank", "IMF")
        metadata_fields: List of metadata fields to include
        include_recent_data: Whether to include recent data points (default: True)
        top_countries: Number of top countries to include (default: 10)
        include_statistics: Whether to include summary statistics (default: True)

    Returns:
        Formatted text string for RAG
    """
    if data is None or data.empty:
        return f"{source_name} Indicator: {indicator_code}\nNo data available"

    # Default metadata fields if not specified
    if metadata_fields is None:
        metadata_fields = ["name", "description", "source", "topic", "unit"]

    # Build formatted text
    text_parts = [f"{source_name} Economic Data Indicator: {indicator_code}"]

    # Add metadata fields
    for field in metadata_fields:
        value = metadata.get(field)
        if value:
            label = field.replace("_", " ").title()
            text_parts.append(f"{label}: {value}")

    # Add notes if available
    for note_field in ["notes", "note", "description"]:
        if note_field in metadata and metadata[note_field]:
            note = str(metadata[note_field])
            text_parts.append(f"Note: {note[:500]}")
            break

    # Add data coverage summary
    text_parts.append("\nData Coverage:")
    text_parts.append(f"  Countries: {len(data.columns)}")
    text_parts.append(f"  Years: {len(data.index)}")
    text_parts.append(f"  Total Data Points: {len(data) * len(data.columns)}")

    # Add recent data points (latest year, top countries)
    if include_recent_data and not data.empty:
        text_parts.append("\nRecent Data (Latest Year, Top Countries):")
        latest_year = data.index.max()
        latest_data = data.loc[latest_year].dropna().sort_values(ascending=False)
        for country, value in latest_data.head(top_countries).items():
            text_parts.append(f"  {country}: {value}")

    # Add summary statistics
    if include_statistics and not data.empty:
        text_parts.append("\nSummary Statistics (All Countries, All Years):")
        flattened = data.values.flatten()
        text_parts.append(f"  Mean: {flattened.mean():.2f}")
        text_parts.append(f"  Min: {flattened.min():.2f}")
        text_parts.append(f"  Max: {flattened.max():.2f}")

    return "\n".join(text_parts)


def format_event_for_rag(
    event: Dict[str, Any],
    source_name: str = "Event",
    field_mappings: Optional[Dict[str, str]] = None,
) -> str:
    """
    Format event data for RAG ingestion.

    Common pattern for economic calendar events and similar structured events.

    Args:
        event: Event dictionary with event data
        source_name: Name of event type (e.g., "Economic Event")
        field_mappings: Optional mapping of event keys to display labels

    Returns:
        Formatted text string for RAG
    """
    if field_mappings is None:
        field_mappings = {
            "Event": "Event",
            "event": "Event",
            "Country": "Country",
            "country": "Country",
            "Date": "Date",
            "date": "Date",
            "Time": "Time",
            "time": "Time",
            "Category": "Category",
            "category": "Category",
            "Importance": "Importance",
            "importance": "Importance",
            "Actual": "Actual",
            "actual": "Actual",
            "Forecast": "Forecast",
            "forecast": "Forecast",
            "Previous": "Previous",
            "previous": "Previous",
        }

    # Extract key fields with fallback
    event_name = event.get("Event", event.get("event", "Unknown Event"))
    country = event.get("Country", event.get("country", "Unknown"))
    date = event.get("Date", event.get("date", ""))

    # Build formatted text
    text_parts = [
        f"{source_name}: {event_name}",
        f"Country: {country}",
        f"Date: {date}",
    ]

    # Add optional fields
    optional_fields = [
        "Time",
        "time",
        "Category",
        "category",
        "Importance",
        "importance",
    ]
    for field in optional_fields:
        value = event.get(field)
        if value:
            label = field_mappings.get(field, field.replace("_", " ").title())
            text_parts.append(f"{label}: {value}")

    # Add data fields
    data_fields = ["Actual", "actual", "Forecast", "forecast", "Previous", "previous"]
    for field in data_fields:
        value = event.get(field)
        if value:
            label = field_mappings.get(field, field.replace("_", " ").title())
            text_parts.append(f"{label}: {value}")

    return "\n".join(text_parts)


def format_generic_data_for_rag(
    data_id: str,
    metadata: Dict[str, Any],
    content: Optional[str] = None,
    source_name: str = "Data",
    metadata_fields: Optional[List[str]] = None,
) -> str:
    """
    Format generic data for RAG ingestion.

    Flexible formatter for various data types that don't fit specific patterns.

    Args:
        data_id: Unique identifier for the data
        metadata: Metadata dictionary
        content: Optional content text to include
        source_name: Name of data source
        metadata_fields: List of metadata fields to include (if None, includes all)

    Returns:
        Formatted text string for RAG
    """
    text_parts = [f"{source_name}: {data_id}"]

    # Add metadata fields
    if metadata_fields:
        for field in metadata_fields:
            value = metadata.get(field)
            if value:
                label = field.replace("_", " ").title()
                text_parts.append(f"{label}: {value}")
    else:
        # Include all metadata fields
        for field, value in metadata.items():
            if value and not isinstance(value, (dict, list)):
                label = field.replace("_", " ").title()
                text_parts.append(f"{label}: {value}")

    # Add content if provided
    if content:
        text_parts.append("")
        text_parts.append("Content:")
        text_parts.append(content)

    return "\n".join(text_parts)
