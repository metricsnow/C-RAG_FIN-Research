# IMF and World Bank Data Integration

## Overview

This document describes the integration of IMF Data Portal and World Bank Open Data APIs into the financial research assistant. These integrations provide access to comprehensive global economic data including GDP, inflation, unemployment, trade balance, and other macroeconomic indicators for 188+ countries.

## Features

### World Bank Open Data API

- **Access to 188+ countries**: Comprehensive global economic data
- **Thousands of indicators**: GDP, inflation, unemployment, trade balance, and more
- **Historical data**: Time series data going back decades
- **Country filtering**: Fetch data for specific countries or all countries
- **Year range filtering**: Filter data by start and end year
- **Indicator search**: Search for indicators by keyword

### IMF Data Portal API

- **World Economic Outlook**: Access to WEO database
- **International Financial Statistics**: Comprehensive financial data
- **Global coverage**: Data for 188+ countries
- **Multiple indicators**: GDP growth, inflation, unemployment, and more
- **Historical data**: Time series data with extensive history
- **Country and year filtering**: Filter by countries and date ranges

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# World Bank API Configuration
WORLD_BANK_ENABLED=true
WORLD_BANK_RATE_LIMIT_SECONDS=1.0

# IMF Data Portal API Configuration
IMF_ENABLED=true
IMF_RATE_LIMIT_SECONDS=1.0
```

**Note**: Both World Bank and IMF APIs are free and do not require API keys.

### Configuration Options

- `WORLD_BANK_ENABLED`: Enable/disable World Bank integration (default: `true`)
- `WORLD_BANK_RATE_LIMIT_SECONDS`: Rate limit between requests in seconds (default: `1.0`)
- `IMF_ENABLED`: Enable/disable IMF integration (default: `true`)
- `IMF_RATE_LIMIT_SECONDS`: Rate limit between requests in seconds (default: `1.0`)

## Usage

### Python API

#### World Bank Data

```python
from app.ingestion.world_bank_fetcher import WorldBankFetcher

# Initialize fetcher
fetcher = WorldBankFetcher()

# Fetch single indicator
data = fetcher.fetch_indicator(
    indicator_code="NY.GDP.MKTP.CD",  # GDP (current US$)
    country_codes=["USA", "CHN"],      # Optional: specific countries
    start_year=2020,                    # Optional: start year
    end_year=2023                       # Optional: end year
)

# Fetch multiple indicators
data = fetcher.fetch_multiple_indicators(
    indicator_codes=["NY.GDP.MKTP.CD", "SP.POP.TOTL"],  # GDP and Population
    country_codes=["USA", "CHN"]
)

# Search for indicators
results = fetcher.search_indicators("gdp", limit=20)

# Get available countries
countries = fetcher.get_countries()
```

#### IMF Data

```python
from app.ingestion.imf_fetcher import IMFFetcher

# Initialize fetcher
fetcher = IMFFetcher()

# Fetch single indicator
data = fetcher.fetch_indicator(
    indicator_code="NGDP_RPCH",  # GDP growth rate
    country_codes=["US", "CN"],  # Optional: specific countries
    start_year=2020,              # Optional: start year
    end_year=2023                 # Optional: end year
)

# Fetch multiple indicators
data = fetcher.fetch_multiple_indicators(
    indicator_codes=["NGDP_RPCH", "LUR"],  # GDP growth and Unemployment
    country_codes=["US", "CN"]
)

# Get available indicators
indicators = fetcher.get_available_indicators()

# Get available countries
countries = fetcher.get_countries()
```

### Ingestion Pipeline Integration

#### World Bank Indicators

```python
from app.ingestion.pipeline import create_pipeline

# Create pipeline
pipeline = create_pipeline()

# Process World Bank indicators
chunk_ids = pipeline.process_world_bank_indicators(
    indicator_codes=["NY.GDP.MKTP.CD", "SP.POP.TOTL"],
    country_codes=["USA", "CHN"],
    start_year=2020,
    end_year=2023,
    store_embeddings=True
)
```

#### IMF Indicators

```python
from app.ingestion.pipeline import create_pipeline

# Create pipeline
pipeline = create_pipeline()

# Process IMF indicators
chunk_ids = pipeline.process_imf_indicators(
    indicator_codes=["NGDP_RPCH", "LUR"],
    country_codes=["US", "CN"],
    start_year=2020,
    end_year=2023,
    store_embeddings=True
)
```

### Command-Line Scripts

#### World Bank Data

```bash
# Fetch specific indicators
python scripts/fetch_world_bank_data.py \
    --indicators NY.GDP.MKTP.CD SP.POP.TOTL

# Fetch with country and year filters
python scripts/fetch_world_bank_data.py \
    --indicators NY.GDP.MKTP.CD \
    --countries USA CHN \
    --start-year 2020 \
    --end-year 2023

# Search for indicators
python scripts/fetch_world_bank_data.py --search "gdp"

# List available countries
python scripts/fetch_world_bank_data.py --list-countries
```

#### IMF Data

```bash
# Fetch specific indicators
python scripts/fetch_imf_data.py --indicators NGDP_RPCH LUR

# Fetch with country and year filters
python scripts/fetch_imf_data.py \
    --indicators NGDP_RPCH \
    --countries US CN \
    --start-year 2020 \
    --end-year 2023

# List available indicators
python scripts/fetch_imf_data.py --list-indicators

# List available countries
python scripts/fetch_imf_data.py --list-countries
```

## Common Indicator Codes

### World Bank Indicators

- `NY.GDP.MKTP.CD`: GDP (current US$)
- `SP.POP.TOTL`: Population, total
- `FP.CPI.TOTL.ZG`: Inflation, consumer prices (annual %)
- `SL.UEM.TOTL.ZS`: Unemployment, total (% of total labor force)
- `NE.TRD.GNFS.ZS`: Trade (% of GDP)
- `NY.GDP.PCAP.CD`: GDP per capita (current US$)

### IMF Indicators

- `NGDP_RPCH`: GDP growth rate (annual %)
- `LUR`: Unemployment rate (%)
- `PCPI_PCH`: Consumer price inflation (annual %)
- `NGDPD`: GDP (current prices, US$)
- `BCA`: Current account balance (US$)

## Data Format

Both fetchers return data in a standardized format:

```python
{
    "indicator_code": "NY.GDP.MKTP.CD",
    "data": pd.DataFrame,  # Time series data (years x countries)
    "metadata": {
        "name": "GDP (current US$)",
        "source": "World Bank",
        "topic": "Economic Policy & Debt",
        "unit": "US$",
        "note": "..."
    },
    "country_codes": ["USA", "CHN"],
    "start_year": 2020,
    "end_year": 2023
}
```

## RAG Integration

Data from both sources is automatically formatted for RAG ingestion:

1. **Text Formatting**: Data is converted to human-readable text with metadata
2. **Chunking**: Large datasets are split into manageable chunks
3. **Embedding**: Chunks are embedded using the configured embedding provider
4. **Storage**: Data is stored in ChromaDB with comprehensive metadata

The formatted text includes:
- Indicator name and description
- Data coverage (countries, years, data points)
- Recent data points (latest year, top countries)
- Summary statistics (mean, min, max)

## Error Handling

Both fetchers include comprehensive error handling:

- **API Errors**: Network errors, timeout errors, and API errors are caught and logged
- **Missing Data**: Graceful handling when no data is available for requested indicators
- **Rate Limiting**: Automatic rate limiting to respect API limits
- **Validation**: Input validation for indicator codes, country codes, and date ranges

## Testing

Run the test suite:

```bash
# Test World Bank fetcher
pytest tests/test_world_bank_fetcher.py -v

# Test IMF fetcher
pytest tests/test_imf_fetcher.py -v

# Test with coverage
pytest tests/test_world_bank_fetcher.py tests/test_imf_fetcher.py --cov=app.ingestion.world_bank_fetcher --cov=app.ingestion.imf_fetcher
```

## Dependencies

- `world_bank_data>=1.0.0`: World Bank Open Data API client
- `pandas>=2.0.0`: Data manipulation (already in requirements)
- `requests`: HTTP client for IMF API (already in requirements)

## Limitations

1. **Rate Limiting**: Both APIs have rate limits. Default rate limits are configured, but may need adjustment based on usage.
2. **Data Availability**: Not all indicators are available for all countries or all time periods.
3. **API Changes**: IMF and World Bank may update their APIs. Monitor for breaking changes.
4. **Network Dependency**: Requires internet connection to fetch data.

## Troubleshooting

### World Bank API Issues

- **No data returned**: Check indicator code is correct. Use `search_indicators()` to find correct codes.
- **Rate limit errors**: Increase `WORLD_BANK_RATE_LIMIT_SECONDS` in `.env`.
- **Country code errors**: Use `get_countries()` to get correct ISO country codes.

### IMF API Issues

- **No data returned**: Check indicator code is correct. Use `get_available_indicators()` to find correct codes.
- **Rate limit errors**: Increase `IMF_RATE_LIMIT_SECONDS` in `.env`.
- **Network errors**: Check internet connection and IMF API status.

## References

- [World Bank Open Data API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation)
- [IMF Data Portal API](https://www.imf.org/external/datamapper/api/v1/docs)
- [World Bank Python Library](https://github.com/mwouts/world_bank_data)

## Related Tasks

- **TASK-036**: FRED API Integration (similar economic data integration)
- **TASK-004**: Document Ingestion (pipeline integration)
- **TASK-006**: Embedding Generation (RAG integration)
