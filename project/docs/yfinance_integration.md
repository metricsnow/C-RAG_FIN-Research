# yfinance Stock Data Integration (TASK-030)

## Overview

The system includes comprehensive yfinance integration for fetching and indexing stock market data from Yahoo Finance. This enables querying of real-time and historical stock information through the RAG system.

## Features

### Data Types Supported

1. **Company Information**
   - Company name, sector, industry
   - Business summary and profile
   - Market capitalization
   - Current and previous close prices
   - Trading volume

2. **Financial Metrics**
   - Price-to-Earnings (P/E) ratio (trailing and forward)
   - Price-to-Book (P/B) ratio
   - Dividend yield
   - Profit margins
   - Revenue and earnings growth
   - 52-week high/low prices

3. **Historical Price Data (OHLCV)**
   - Open, High, Low, Close prices
   - Volume data
   - Configurable period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
   - Configurable interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

4. **Dividend Information**
   - Dividend history
   - Payment dates
   - Dividend amounts
   - Total dividends paid

5. **Earnings Data**
   - Quarterly earnings
   - Annual earnings
   - Revenue data
   - Earnings trends

6. **Analyst Recommendations**
   - Recent analyst ratings
   - Price targets
   - Upgrade/downgrade actions
   - Firm names and dates

## Installation

yfinance is automatically installed when you install project dependencies:

```bash
pip install -r requirements.txt
```

Or install directly:
```bash
pip install yfinance pandas
```

## Configuration

See [Configuration Documentation](configuration.md#yfinance-configuration-task-030) for complete configuration options.

Key configuration variables:
- `YFINANCE_ENABLED`: Enable/disable integration (default: `true`)
- `YFINANCE_RATE_LIMIT_SECONDS`: Rate limit between API calls (default: `1.0`)
- `YFINANCE_HISTORY_PERIOD`: Default period for historical data (default: `1y`)
- `YFINANCE_HISTORY_INTERVAL`: Default interval for historical data (default: `1d`)

## Usage

### Command-Line Script

Fetch stock data using the provided script:

```bash
# Single ticker
python scripts/fetch_stock_data.py AAPL

# Multiple tickers
python scripts/fetch_stock_data.py AAPL MSFT GOOGL AMZN

# Skip historical data (faster)
python scripts/fetch_stock_data.py AAPL --no-history

# Dry run (don't store in ChromaDB)
python scripts/fetch_stock_data.py AAPL --no-store

# Custom collection
python scripts/fetch_stock_data.py AAPL --collection stock_data
```

### Programmatic Usage

#### Single Ticker

```python
from app.ingestion.pipeline import IngestionPipeline

# Create pipeline
pipeline = IngestionPipeline()

# Process single ticker
chunk_ids = pipeline.process_stock_data(
    ticker_symbol="AAPL",
    include_history=True,  # Include historical price data
    store_embeddings=True  # Store in ChromaDB
)

print(f"Stored {len(chunk_ids)} chunks for AAPL")
```

#### Multiple Tickers

```python
from app.ingestion.pipeline import IngestionPipeline

pipeline = IngestionPipeline()

# Process multiple tickers
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
chunk_ids = pipeline.process_stock_tickers(
    ticker_symbols=tickers,
    include_history=True,
    store_embeddings=True
)

print(f"Stored {len(chunk_ids)} total chunks for {len(tickers)} tickers")
```

#### Direct Fetcher Usage

For more control, use the fetcher directly:

```python
from app.ingestion.yfinance_fetcher import YFinanceFetcher
from app.ingestion.stock_data_normalizer import StockDataNormalizer

# Create fetcher and normalizer
fetcher = YFinanceFetcher(rate_limit_seconds=1.0)
normalizer = StockDataNormalizer()

# Fetch data
ticker = "AAPL"
data = fetcher.fetch_all_data(ticker, include_history=True)

# Normalize to documents
documents = normalizer.normalize_all_data(data, ticker)

# Process documents (use with pipeline)
from app.ingestion.pipeline import IngestionPipeline
pipeline = IngestionPipeline()

from langchain_core.documents import Document
langchain_docs = [
    Document(page_content=doc["text"], metadata=doc["metadata"])
    for doc in documents
]

chunk_ids = pipeline.process_document_objects(langchain_docs)
```

## Data Normalization

All stock data is automatically normalized to text format suitable for vector storage and RAG queries:

- **Structured Format**: Data formatted as readable text with clear sections
- **Metadata Tagging**: Each document tagged with:
  - `ticker`: Stock ticker symbol
  - `data_type`: Type of data (info, price, dividends, earnings, recommendations)
  - `date`: Date of data fetch
  - `source`: Data source (yfinance)
  - `update_frequency`: Recommended update frequency (daily, quarterly)

## Querying Stock Data

Once stock data is indexed, you can query it through the RAG system:

```python
from app.rag.chain import create_rag_chain

chain = create_rag_chain()

# Query stock information
response = chain.invoke({
    "question": "What is Apple's current P/E ratio?",
    "conversation_history": []
})

print(response["answer"])
print(response["sources"])
```

Example queries:
- "What is Apple's market capitalization?"
- "Show me Microsoft's dividend history"
- "What are the analyst recommendations for Google?"
- "What was Tesla's stock price last month?"
- "Compare the P/E ratios of AAPL and MSFT"

## Rate Limiting

yfinance uses Yahoo Finance's unofficial API, which has no official rate limits. However, aggressive requests may result in temporary IP bans. The integration includes built-in rate limiting:

- **Default**: 1 second between API calls
- **Configurable**: Adjust via `YFINANCE_RATE_LIMIT_SECONDS`
- **Automatic**: Rate limiting applied automatically to all API calls

For batch processing many tickers, consider:
- Increasing rate limit to 2-3 seconds for safety
- Processing in smaller batches
- Using `--no-history` flag to reduce API calls

## Error Handling

The integration includes comprehensive error handling:

- **Missing Data**: Gracefully handles missing data (e.g., no dividends)
- **API Failures**: Continues processing other tickers if one fails
- **Invalid Tickers**: Raises clear error messages for invalid ticker symbols
- **Network Issues**: Retries and error logging for network problems

## Metadata and Filtering

Stock data documents include rich metadata for filtering:

```python
# Query with metadata filtering
from app.vector_db import ChromaStore

store = ChromaStore(collection_name="documents")

# Filter by ticker
results = store.query_by_text(
    query_text="Apple financial metrics",
    n_results=5,
    where={"ticker": "AAPL"}
)

# Filter by data type
results = store.query_by_text(
    query_text="dividend information",
    n_results=5,
    where={"data_type": "dividends"}
)

# Filter by ticker and data type
results = store.query_by_text(
    query_text="earnings data",
    n_results=5,
    where={"ticker": "AAPL", "data_type": "earnings"}
)
```

## Best Practices

1. **Update Frequency**:
   - Company info and metrics: Daily
   - Historical prices: Daily or weekly
   - Dividends: Quarterly (after dividend announcements)
   - Earnings: Quarterly (after earnings releases)
   - Recommendations: Daily or weekly

2. **Batch Processing**:
   - Process multiple tickers in batches
   - Use rate limiting to avoid API issues
   - Monitor for errors and retry failed tickers

3. **Storage Considerations**:
   - Historical data can generate many chunks
   - Consider using `--no-history` for initial indexing
   - Use metadata filtering to query specific data types

4. **Query Optimization**:
   - Use metadata filters to narrow search scope
   - Combine with other data sources (SEC filings) for comprehensive answers
   - Leverage RAG optimizations (hybrid search, reranking) for better results

## Troubleshooting

### yfinance Not Working

1. **Check Configuration**:
   ```bash
   # Verify yfinance is enabled
   echo $YFINANCE_ENABLED  # Should be 'true'
   ```

2. **Check Installation**:
   ```bash
   pip list | grep yfinance
   ```

3. **Test Directly**:
   ```python
   import yfinance as yf
   ticker = yf.Ticker("AAPL")
   info = ticker.info
   print(info)
   ```

### Rate Limiting Issues

If you encounter rate limiting:
- Increase `YFINANCE_RATE_LIMIT_SECONDS` to 2-3 seconds
- Process tickers in smaller batches
- Add delays between batches

### Missing Data

Some tickers may not have all data types:
- Not all stocks pay dividends
- Some stocks may not have analyst recommendations
- Historical data may be limited for new listings

The system handles missing data gracefully and continues processing.

## API Reference

### YFinanceFetcher

Main class for fetching stock data from Yahoo Finance.

**Methods**:
- `fetch_ticker_info(ticker_symbol)`: Fetch company information and financial metrics
- `fetch_historical_prices(ticker_symbol, period, interval, start, end)`: Fetch OHLCV data
- `fetch_dividends(ticker_symbol)`: Fetch dividend history
- `fetch_earnings(ticker_symbol)`: Fetch earnings data
- `fetch_recommendations(ticker_symbol)`: Fetch analyst recommendations
- `fetch_all_data(ticker_symbol, include_history)`: Fetch all available data

### StockDataNormalizer

Class for normalizing stock data to text format.

**Methods**:
- `normalize_ticker_info(info, ticker_symbol)`: Normalize company info
- `normalize_historical_prices(history, ticker_symbol, max_rows)`: Normalize price data
- `normalize_dividends(dividends, ticker_symbol)`: Normalize dividend data
- `normalize_earnings(earnings, ticker_symbol)`: Normalize earnings data
- `normalize_recommendations(recommendations, ticker_symbol)`: Normalize recommendations
- `normalize_all_data(data, ticker_symbol)`: Normalize all data types

### IngestionPipeline

Extended pipeline with stock data processing methods.

**Methods**:
- `process_stock_data(ticker_symbol, include_history, store_embeddings)`: Process single ticker
- `process_stock_tickers(ticker_symbols, include_history, store_embeddings)`: Process multiple tickers

## Testing

Comprehensive unit tests are available:

```bash
# Run all yfinance tests
pytest tests/test_yfinance.py -v

# Run specific test class
pytest tests/test_yfinance.py::TestYFinanceFetcher -v

# Run with coverage
pytest tests/test_yfinance.py --cov=app.ingestion.yfinance_fetcher --cov=app.ingestion.stock_data_normalizer
```

## See Also

- [Configuration Documentation](configuration.md#yfinance-configuration-task-030)
- [Main README](../README.md#stock-data-integration-task-030)
- [SEC EDGAR Integration](edgar_integration.md) - Similar integration for SEC filings
