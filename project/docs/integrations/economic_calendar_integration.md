# Economic Calendar Integration (TASK-035)

## Overview

The system includes comprehensive economic calendar integration for fetching and indexing macroeconomic indicators and events from Trading Economics API. This enables querying of economic data, indicators, and events through the RAG system for macroeconomic analysis.

## Features

### Data Types Supported

1. **Economic Indicators**
   - GDP Growth Rate
   - Inflation Rate (CPI, PPI)
   - Unemployment Rate
   - Interest Rates
   - Trade Balance
   - Consumer Confidence
   - Manufacturing PMI
   - Retail Sales
   - And many more economic indicators

2. **Event Information**
   - Event name and description
   - Country/region
   - Date and time
   - Actual value (when released)
   - Forecast value (consensus estimate)
   - Previous value
   - Importance level (High, Medium, Low)
   - Category (GDP, Inflation, Employment, etc.)

3. **Filtering Capabilities**
   - Filter by date range
   - Filter by country/region
   - Filter by importance level
   - Automatic date range defaults (today to 30 days ahead)

## Installation

The economic calendar integration uses the Trading Economics API. You need to:

1. **Register for API Key**:
   - Visit https://tradingeconomics.com/api
   - Sign up for a free account
   - Obtain your API key

2. **Configure API Key**:
   ```bash
   # Add to .env file
   TRADING_ECONOMICS_API_KEY=your_api_key_here
   ```

3. **Dependencies**:
   The integration uses `requests` library which is already included in requirements.txt.

## Configuration

See [Configuration Documentation](../reference/configuration.md#economic-calendar-configuration-task-035) for complete configuration options.

Key configuration variables:
- `ECONOMIC_CALENDAR_ENABLED`: Enable/disable integration (default: `true`)
- `ECONOMIC_CALENDAR_RATE_LIMIT_SECONDS`: Rate limit between API calls (default: `1.0`)
- `TRADING_ECONOMICS_API_KEY`: Trading Economics API key (required)
- `ECONOMIC_CALENDAR_USE_TRADING_ECONOMICS`: Use Trading Economics API (default: `true`)

## Usage

### Command-Line Script

Fetch economic calendar events using the provided script:

```bash
# Default (today to 30 days ahead)
python scripts/fetch_economic_calendar.py

# Specific date range
python scripts/fetch_economic_calendar.py --start-date 2025-01-27 --end-date 2025-01-31

# Filter by country
python scripts/fetch_economic_calendar.py --country "united states"

# Filter by importance
python scripts/fetch_economic_calendar.py --importance High

# Combined filters
python scripts/fetch_economic_calendar.py \
  --start-date 2025-01-27 \
  --end-date 2025-01-31 \
  --country "united states" \
  --importance High

# Dry run (don't store in ChromaDB)
python scripts/fetch_economic_calendar.py --no-store

# Custom collection
python scripts/fetch_economic_calendar.py --collection economic_data
```

### Programmatic Usage

#### Basic Usage

```python
from app.ingestion.pipeline import create_pipeline

# Create pipeline
pipeline = create_pipeline()

# Process economic calendar (default: today to 30 days ahead)
chunk_ids = pipeline.process_economic_calendar(
    store_embeddings=True  # Store in ChromaDB
)

print(f"Stored {len(chunk_ids)} economic calendar chunks")
```

#### With Date Range

```python
from app.ingestion.pipeline import create_pipeline

pipeline = create_pipeline()

# Process specific date range
chunk_ids = pipeline.process_economic_calendar(
    start_date="2025-01-27",
    end_date="2025-01-31",
    store_embeddings=True
)

print(f"Stored {len(chunk_ids)} chunks for date range")
```

#### With Filters

```python
from app.ingestion.pipeline import create_pipeline

pipeline = create_pipeline()

# Process with country and importance filters
chunk_ids = pipeline.process_economic_calendar(
    start_date="2025-01-27",
    end_date="2025-01-31",
    country="united states",
    importance="High",
    store_embeddings=True
)

print(f"Stored {len(chunk_ids)} high-importance US economic events")
```

#### Direct Fetcher Usage

For more control, use the fetcher directly:

```python
from app.ingestion.economic_calendar_fetcher import EconomicCalendarFetcher

# Create fetcher
fetcher = EconomicCalendarFetcher(
    api_key="your_api_key",
    rate_limit_delay=1.0
)

# Fetch events
events = fetcher.fetch_calendar(
    start_date="2025-01-27",
    end_date="2025-01-31",
    country="united states",
    importance="High"
)

# Format for RAG
for event in events:
    formatted_text = fetcher.format_event_for_rag(event)
    metadata = fetcher.get_event_metadata(event)
    print(f"Event: {formatted_text}")
    print(f"Metadata: {metadata}")
```

## Data Format

Economic calendar events are automatically formatted for RAG ingestion:

### Event Format

```
Economic Event: GDP Growth Rate
Country: United States
Date: 2025-01-27T10:00:00
Time: 10:00
Category: GDP
Importance: High
Actual: 2.5%
Forecast: 2.3%
Previous: 2.1%
```

### Metadata Structure

Each event includes rich metadata:

```python
{
    "source": "economic_calendar",
    "event_name": "GDP Growth Rate",
    "country": "United States",
    "date": "2025-01-27T10:00:00",
    "time": "10:00",
    "category": "GDP",
    "importance": "High",
    "actual": "2.5%",
    "forecast": "2.3%",
    "previous": "2.1%",
    "api_source": "trading_economics"
}
```

## Querying Economic Data

Once economic calendar events are indexed, you can query them through the RAG system:

```python
from app.rag.chain import create_rag_chain

chain = create_rag_chain()

# Query economic data
response = chain.invoke({
    "question": "What was the US GDP growth rate last quarter?",
    "conversation_history": []
})

print(response["answer"])
print(response["sources"])
```

Example queries:
- "What is the current US inflation rate?"
- "Show me high-importance economic events for this week"
- "What was the unemployment rate in the United States last month?"
- "What economic indicators are scheduled for release this week?"
- "Compare inflation rates between US and China"
- "What was the forecast vs actual for GDP growth?"

## Rate Limiting

Trading Economics API has rate limits based on your subscription tier:

- **Free Tier**: Limited requests per day
- **Paid Tiers**: Higher rate limits

The integration includes built-in rate limiting:
- **Default**: 1 second between API calls
- **Configurable**: Adjust via `ECONOMIC_CALENDAR_RATE_LIMIT_SECONDS`
- **Automatic**: Rate limiting applied automatically to all API calls

For batch processing, consider:
- Increasing rate limit to 2-3 seconds for safety
- Processing in smaller date ranges
- Using importance filters to reduce data volume

## Error Handling

The integration includes comprehensive error handling:

- **Missing API Key**: Clear warning messages if API key is not configured
- **API Failures**: Graceful error handling with detailed logging
- **Empty Responses**: Handles empty calendar responses gracefully
- **Network Issues**: Retries and error logging for network problems
- **Invalid Parameters**: Validates date formats and parameters

## Metadata and Filtering

Economic calendar documents include rich metadata for filtering:

```python
# Query with metadata filtering
from app.vector_db import ChromaStore

store = ChromaStore(collection_name="documents")

# Filter by country
results = store.query_by_text(
    query_text="US economic indicators",
    n_results=5,
    where={"country": "United States"}
)

# Filter by importance
results = store.query_by_text(
    query_text="high importance events",
    n_results=5,
    where={"importance": "High"}
)

# Filter by category
results = store.query_by_text(
    query_text="GDP data",
    n_results=5,
    where={"category": "GDP"}
)

# Combined filters
results = store.query_by_text(
    query_text="US inflation",
    n_results=5,
    where={"country": "United States", "category": "Inflation"}
)
```

## Best Practices

1. **Update Frequency**:
   - Economic calendar events: Daily (before market open)
   - Historical events: As needed for analysis
   - High-importance events: Monitor daily

2. **Data Volume**:
   - Use date range filters to limit data volume
   - Filter by importance to focus on key events
   - Consider country filters for specific regions

3. **Storage Considerations**:
   - Economic events generate relatively few chunks
   - Events are time-sensitive (consider expiration)
   - Use metadata filtering to query specific time periods

4. **Query Optimization**:
   - Use metadata filters to narrow search scope
   - Combine with other data sources (news, stock data) for comprehensive answers
   - Leverage RAG optimizations (hybrid search, reranking) for better results

5. **API Key Management**:
   - Store API key in `.env` file (never commit to git)
   - Use free tier for development and testing
   - Consider paid tier for production with higher rate limits

## Troubleshooting

### API Key Issues

1. **Check Configuration**:
   ```bash
   # Verify API key is set
   echo $TRADING_ECONOMICS_API_KEY
   ```

2. **Check .env File**:
   ```bash
   # Ensure .env file exists and contains API key
   grep TRADING_ECONOMICS_API_KEY .env
   ```

3. **Test API Key**:
   ```python
   from app.ingestion.economic_calendar_fetcher import EconomicCalendarFetcher

   fetcher = EconomicCalendarFetcher(api_key="your_key")
   events = fetcher.fetch_calendar()
   print(f"Fetched {len(events)} events")
   ```

### Rate Limiting Issues

If you encounter rate limiting:
- Increase `ECONOMIC_CALENDAR_RATE_LIMIT_SECONDS` to 2-3 seconds
- Process smaller date ranges
- Use importance filters to reduce API calls
- Consider upgrading to a paid API tier

### Empty Results

If you get no events:
- Check date range (ensure dates are valid)
- Verify country name format (e.g., "united states" not "USA")
- Check API key validity
- Verify events exist for the specified date range

### Configuration Issues

1. **Check Integration Enabled**:
   ```bash
   echo $ECONOMIC_CALENDAR_ENABLED  # Should be 'true'
   ```

2. **Check API Source**:
   ```bash
   echo $ECONOMIC_CALENDAR_USE_TRADING_ECONOMICS  # Should be 'true'
   ```

## API Reference

### EconomicCalendarFetcher

Main class for fetching economic calendar data from Trading Economics API.

**Methods**:
- `fetch_calendar(start_date, end_date, country, importance)`: Fetch economic calendar events
- `fetch_calendar_by_date_range(start_date, end_date, country)`: Fetch events for date range
- `format_event_for_rag(event)`: Format event for RAG ingestion
- `get_event_metadata(event)`: Extract metadata from event

**Parameters**:
- `start_date`: Start date (YYYY-MM-DD format, optional, defaults to today)
- `end_date`: End date (YYYY-MM-DD format, optional, defaults to 30 days from start)
- `country`: Country filter (e.g., "united states", optional)
- `importance`: Importance filter ("High", "Medium", "Low", optional)

### IngestionPipeline

Extended pipeline with economic calendar processing methods.

**Methods**:
- `process_economic_calendar(start_date, end_date, country, importance, store_embeddings)`: Process economic calendar events

## Testing

Comprehensive unit tests are available:

```bash
# Run all economic calendar tests
pytest tests/test_economic_calendar_fetcher.py -v

# Run specific test class
pytest tests/test_economic_calendar_fetcher.py::TestEconomicCalendarFetcher -v

# Run with coverage
pytest tests/test_economic_calendar_fetcher.py --cov=app.ingestion.economic_calendar_fetcher
```

## Trading Economics API

### API Details

- **Base URL**: `https://api.tradingeconomics.com/calendar`
- **Authentication**: API key via query parameter `c`
- **Format**: JSON response (list of events)
- **Free Tier**: Available (rate limited)
- **Documentation**: https://tradingeconomics.com/api

### API Parameters

- `c`: API key (required)
- `d1`: Start date (YYYY-MM-DD, optional)
- `d2`: End date (YYYY-MM-DD, optional)
- `countries`: Country filter (optional)
- `importance`: Importance filter (High/Medium/Low, optional)

### Response Format

```json
[
  {
    "Event": "GDP Growth Rate",
    "Country": "United States",
    "Date": "2025-01-27T10:00:00",
    "Time": "10:00",
    "Actual": "2.5%",
    "Forecast": "2.3%",
    "Previous": "2.1%",
    "Importance": "High",
    "Category": "GDP"
  }
]
```

## See Also

- [Configuration Documentation](../reference/configuration.md#economic-calendar-configuration-task-035)
- [Main README](../../README.md#economic-calendar-integration-task-035)
- [yfinance Integration](yfinance_integration.md) - Similar integration for stock data
- [News Aggregation](news_aggregation.md) - Similar integration for financial news
