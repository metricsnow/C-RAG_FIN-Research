# FRED API Integration (TASK-036)

## Overview

The system includes comprehensive FRED (Federal Reserve Economic Data) API integration for fetching and indexing economic time series data. This enables querying of 840,000+ time series including interest rates, exchange rates, inflation indicators, employment data, GDP, and monetary indicators through the RAG system.

## Features

### Data Types Supported

1. **Interest Rates**
   - Federal Funds Rate (FEDFUNDS)
   - Treasury yields (10-year, 30-year, etc.)
   - Prime rate
   - Discount rate
   - Commercial paper rates

2. **Exchange Rates**
   - USD/EUR, USD/JPY, USD/GBP
   - Major currency pairs
   - Real effective exchange rates
   - Trade-weighted dollar index

3. **Inflation Indicators**
   - Consumer Price Index (CPI)
   - Producer Price Index (PPI)
   - Core inflation measures
   - Inflation expectations

4. **Employment Data**
   - Unemployment rate (UNRATE)
   - Non-farm payrolls
   - Labor force participation
   - Average hourly earnings

5. **GDP and Economic Growth**
   - Gross Domestic Product (GDP)
   - GDP per capita
   - Real GDP growth
   - GDP components (consumption, investment, government, net exports)

6. **Monetary Indicators**
   - Money supply (M1, M2, M3)
   - Bank reserves
   - Currency in circulation
   - Monetary base

7. **Other Economic Indicators**
   - Consumer confidence
   - Industrial production
   - Retail sales
   - Housing starts
   - And 840,000+ more time series

### Search and Discovery

- **Text Search**: Search for series by keywords (e.g., "unemployment rate", "inflation")
- **Series ID Lookup**: Direct access by FRED series ID (e.g., "GDP", "UNRATE", "FEDFUNDS")
- **Metadata Access**: Rich metadata including title, units, frequency, seasonal adjustment

## Installation

The FRED API integration uses the `fredapi` Python library. You need to:

1. **Register for API Key**:
   - Visit https://fred.stlouisfed.org/docs/api/api_key.html
   - Sign up for a free account
   - Obtain your API key (free tier available)

2. **Configure API Key**:
   ```bash
   # Add to .env file
   FRED_API_KEY=your_api_key_here
   ```

3. **Dependencies**:
   The integration uses `fredapi` library which is included in requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

See [Configuration Documentation](../reference/configuration.md#fred-api-configuration-task-036) for complete configuration options.

Key configuration variables:
- `FRED_ENABLED`: Enable/disable integration (default: `true`)
- `FRED_API_KEY`: FRED API key (required)
- `FRED_RATE_LIMIT_SECONDS`: Rate limit between API calls (default: `0.2`)

## Usage

### Command-Line Script

Fetch FRED time series data using the provided script:

```bash
# Fetch specific series
python scripts/fetch_fred_data.py --series GDP UNRATE FEDFUNDS

# Fetch with date range
python scripts/fetch_fred_data.py --series GDP --start-date 2020-01-01 --end-date 2024-12-31

# Search for series
python scripts/fetch_fred_data.py --search "unemployment rate"

# Dry run (don't store in ChromaDB)
python scripts/fetch_fred_data.py --series GDP --no-store

# Custom collection
python scripts/fetch_fred_data.py --series GDP --collection economic_data
```

### Programmatic Usage

#### Basic Usage

```python
from app.ingestion.pipeline import create_pipeline

# Create pipeline
pipeline = create_pipeline()

# Process FRED series
chunk_ids = pipeline.process_fred_series(
    series_ids=["GDP", "UNRATE", "FEDFUNDS"],
    store_embeddings=True  # Store in ChromaDB
)

print(f"Stored {len(chunk_ids)} FRED series chunks")
```

#### With Date Range

```python
from app.ingestion.pipeline import create_pipeline

pipeline = create_pipeline()

# Process specific date range
chunk_ids = pipeline.process_fred_series(
    series_ids=["GDP"],
    start_date="2020-01-01",
    end_date="2024-12-31",
    store_embeddings=True
)

print(f"Stored {len(chunk_ids)} chunks for date range")
```

#### Search for Series

```python
from app.ingestion.fred_fetcher import FREDFetcher

# Create fetcher
fetcher = FREDFetcher(api_key="your_api_key")

# Search for series
results = fetcher.search_series("unemployment rate", limit=20)

for result in results:
    print(f"{result['series_id']}: {result['title']} ({result['frequency']})")
```

#### Direct Fetcher Usage

For more control, use the fetcher directly:

```python
from app.ingestion.fred_fetcher import FREDFetcher

# Create fetcher
fetcher = FREDFetcher(
    api_key="your_api_key",
    rate_limit_delay=0.2
)

# Fetch single series
series_data = fetcher.fetch_series(
    "GDP",
    start_date="2020-01-01",
    end_date="2024-12-31"
)

# Format for RAG
formatted_text = fetcher.format_series_for_rag(series_data)
metadata = fetcher.get_series_metadata(series_data)

print(f"Formatted text: {formatted_text}")
print(f"Metadata: {metadata}")

# Fetch multiple series
multiple_series = fetcher.fetch_multiple_series(
    ["GDP", "UNRATE", "FEDFUNDS"],
    start_date="2020-01-01",
    end_date="2024-12-31"
)
```

## Data Format

FRED time series are automatically formatted for RAG ingestion:

### Series Format

```
FRED Economic Data Series: GDP
Title: Gross Domestic Product
Units: Billions of Dollars
Frequency: Quarterly
Seasonal Adjustment: Seasonally Adjusted Annual Rate
Observation Period: 2020-01-01 to 2024-12-31
Last Updated: 2024-12-31 12:00:00

Recent Data Points:
  2024-10-01: 28000.0
  2024-07-01: 27800.0
  2024-04-01: 27600.0
  ...

Summary Statistics:
  Total Observations: 20
  Latest Value: 28000.0
  Mean: 26500.0
  Min: 21000.0
  Max: 28000.0
```

### Metadata Structure

Each series includes rich metadata:

```python
{
    "source": "fred",
    "series_id": "GDP",
    "title": "Gross Domestic Product",
    "units": "Billions of Dollars",
    "frequency": "Quarterly",
    "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
    "observation_start": "2020-01-01",
    "observation_end": "2024-12-31",
    "last_updated": "2024-12-31 12:00:00",
    "data_points": 20,
    "start_date": "2020-01-01",
    "end_date": "2024-12-31"
}
```

## Querying Economic Data

Once FRED series are indexed, you can query them through the RAG system:

```python
from app.rag.chain import create_rag_chain

chain = create_rag_chain()

# Query economic data
response = chain.invoke({
    "question": "What is the current US unemployment rate?",
    "conversation_history": []
})

print(response["answer"])
print(response["sources"])
```

Example queries:
- "What is the current US inflation rate?"
- "Show me GDP growth over the last 5 years"
- "What is the Federal Funds Rate?"
- "Compare unemployment rates between 2020 and 2024"
- "What is the current money supply (M2)?"
- "Show me exchange rates for USD/EUR"

## Rate Limiting

FRED API has rate limits based on your subscription tier:

- **Free Tier**: 120 requests per minute
- **Paid Tiers**: Higher rate limits

The integration includes built-in rate limiting:
- **Default**: 0.2 seconds between API calls (300 requests per minute)
- **Configurable**: Adjust via `FRED_RATE_LIMIT_SECONDS`
- **Automatic**: Rate limiting applied automatically to all API calls

For batch processing, consider:
- Adjusting rate limit based on your tier
- Processing series in smaller batches
- Using date range filters to reduce data volume

## Error Handling

The integration includes comprehensive error handling:

- **Missing API Key**: Clear warning messages if API key is not configured
- **API Failures**: Graceful error handling with detailed logging
- **Empty Responses**: Handles empty series responses gracefully
- **Network Issues**: Retries and error logging for network problems
- **Invalid Series IDs**: Validates series IDs and provides helpful error messages

## Metadata and Filtering

FRED series documents include rich metadata for filtering:

```python
# Query with metadata filtering
from app.vector_db import ChromaStore

store = ChromaStore(collection_name="documents")

# Filter by series ID
results = store.query_by_text(
    query_text="GDP data",
    n_results=5,
    where={"series_id": "GDP"}
)

# Filter by frequency
results = store.query_by_text(
    query_text="quarterly economic data",
    n_results=5,
    where={"frequency": "Quarterly"}
)

# Filter by units
results = store.query_by_text(
    query_text="percentage data",
    n_results=5,
    where={"units": "Percent"}
)

# Combined filters
results = store.query_by_text(
    query_text="US economic indicators",
    n_results=5,
    where={"frequency": "Monthly", "units": "Percent"}
)
```

## Best Practices

1. **Update Frequency**:
   - Key indicators: Daily or weekly updates
   - Historical data: As needed for analysis
   - Real-time indicators: Monitor based on release schedule

2. **Data Volume**:
   - Use date range filters to limit data volume
   - Focus on key indicators for your use case
   - Consider frequency (daily vs. monthly vs. quarterly)

3. **Storage Considerations**:
   - Time series can generate many chunks (one per observation period)
   - Use date range filters to control chunk count
   - Consider aggregating data for long time series

4. **Query Optimization**:
   - Use metadata filters to narrow search scope
   - Combine with other data sources (news, stock data) for comprehensive answers
   - Leverage RAG optimizations (hybrid search, reranking) for better results

5. **API Key Management**:
   - Store API key in `.env` file (never commit to git)
   - Use free tier for development and testing
   - Consider paid tier for production with higher rate limits

6. **Series Selection**:
   - Use search functionality to discover relevant series
   - Focus on commonly used indicators (GDP, UNRATE, FEDFUNDS, CPI)
   - Document series IDs for your use case

## Common Series IDs

Here are some commonly used FRED series IDs:

- **GDP**: Gross Domestic Product
- **UNRATE**: Unemployment Rate
- **FEDFUNDS**: Federal Funds Rate
- **CPIAUCSL**: Consumer Price Index for All Urban Consumers
- **PPIACO**: Producer Price Index for All Commodities
- **M2SL**: M2 Money Stock
- **DEXUSEU**: U.S. / Euro Foreign Exchange Rate
- **DEXJPUS**: Japanese Yen to U.S. Dollar Spot Exchange Rate
- **DGS10**: 10-Year Treasury Constant Maturity Rate
- **DGS30**: 30-Year Treasury Constant Maturity Rate

## Troubleshooting

### API Key Issues

1. **Check Configuration**:
   ```bash
   # Verify API key is set
   echo $FRED_API_KEY
   ```

2. **Check .env File**:
   ```bash
   # Ensure .env file exists and contains API key
   grep FRED_API_KEY .env
   ```

3. **Test API Key**:
   ```python
   from app.ingestion.fred_fetcher import FREDFetcher

   fetcher = FREDFetcher(api_key="your_key")
   series_data = fetcher.fetch_series("GDP")
   print(f"Fetched series: {series_data['series_id']}")
   ```

### Rate Limiting Issues

If you encounter rate limiting:
- Increase `FRED_RATE_LIMIT_SECONDS` to 0.5-1.0 seconds
- Process series in smaller batches
- Use date range filters to reduce API calls
- Consider upgrading to a paid API tier

### Empty Results

If you get no data:
- Check series ID validity (use search to find correct IDs)
- Verify date range (ensure dates are valid)
- Check API key validity
- Verify series has data for the specified date range

### Configuration Issues

1. **Check Integration Enabled**:
   ```bash
   echo $FRED_ENABLED  # Should be 'true'
   ```

2. **Check Rate Limit**:
   ```bash
   echo $FRED_RATE_LIMIT_SECONDS  # Should be >= 0.0
   ```

## API Reference

### FREDFetcher

Main class for fetching FRED time series data.

**Methods**:
- `fetch_series(series_id, start_date, end_date, frequency, aggregation_method)`: Fetch a single time series
- `fetch_multiple_series(series_ids, start_date, end_date)`: Fetch multiple time series
- `search_series(search_text, limit)`: Search for series by text
- `format_series_for_rag(series_data)`: Format series data for RAG ingestion
- `get_series_metadata(series_data)`: Extract metadata from series data

**Parameters**:
- `series_id`: FRED series ID (e.g., "GDP", "UNRATE", "FEDFUNDS")
- `start_date`: Start date (YYYY-MM-DD format, optional)
- `end_date`: End date (YYYY-MM-DD format, optional)
- `frequency`: Data frequency ('d'=daily, 'w'=weekly, 'm'=monthly, 'q'=quarterly, 'a'=annual, optional)
- `aggregation_method`: Aggregation method ('avg', 'sum', 'eop', optional)
- `search_text`: Search query text
- `limit`: Maximum number of search results (default: 20)

### IngestionPipeline

Extended pipeline with FRED series processing methods.

**Methods**:
- `process_fred_series(series_ids, start_date, end_date, store_embeddings)`: Process FRED time series

## Testing

Comprehensive unit tests are available:

```bash
# Run all FRED fetcher tests
pytest tests/test_fred_fetcher.py -v

# Run specific test class
pytest tests/test_fred_fetcher.py::TestFREDFetcher -v

# Run with coverage
pytest tests/test_fred_fetcher.py --cov=app.ingestion.fred_fetcher
```

## FRED API

### API Details

- **Base URL**: `https://api.stlouisfed.org/fred/`
- **Authentication**: API key via query parameter `api_key`
- **Format**: JSON response
- **Free Tier**: Available (120 requests per minute)
- **Documentation**: https://fred.stlouisfed.org/docs/api/

### API Endpoints

- **Series Observations**: `/fred/series/observations`
- **Series Info**: `/fred/series`
- **Series Search**: `/fred/series/search`

### Response Format

```json
{
  "realtime_start": "2024-12-31",
  "realtime_end": "2024-12-31",
  "observation_start": "2020-01-01",
  "observation_end": "2024-12-31",
  "units": "Billions of Dollars",
  "output_type": 1,
  "file_type": "json",
  "order_by": "observation_date",
  "sort_order": "asc",
  "count": 20,
  "offset": 0,
  "limit": 100000,
  "observations": [
    {
      "realtime_start": "2024-12-31",
      "realtime_end": "2024-12-31",
      "date": "2020-01-01",
      "value": "21000.0"
    }
  ]
}
```

## See Also

- [Configuration Documentation](../reference/configuration.md#fred-api-configuration-task-036)
- [Main README](../../README.md#fred-api-integration-task-036)
- [Economic Calendar Integration](economic_calendar_integration.md) - Similar integration for economic events
- [yfinance Integration](yfinance_integration.md) - Similar integration for stock data
