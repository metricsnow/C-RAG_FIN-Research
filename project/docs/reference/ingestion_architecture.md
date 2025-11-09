# Ingestion Pipeline Architecture

## Overview

The ingestion pipeline uses a modular, processor-based architecture that separates concerns by data source type. This design improves maintainability, testability, and scalability.

## Architecture Design

### Processor-Based Architecture

The ingestion pipeline (`app/ingestion/pipeline.py`) orchestrates data ingestion through specialized processor classes. Each processor handles a specific data source type and inherits from a common `BaseProcessor` class.

```
IngestionPipeline (Orchestrator)
    ├── DocumentProcessor (File-based documents)
    ├── StockProcessor (Stock market data via yfinance)
    ├── TranscriptProcessor (Earnings call transcripts)
    ├── NewsProcessor (Financial news articles)
    ├── EconomicDataProcessor (Economic indicators)
    │   ├── Economic Calendar
    │   ├── FRED Series
    │   ├── World Bank Indicators
    │   ├── IMF Indicators
    │   └── Central Bank Communications
    └── AlternativeDataProcessor (Alternative data sources)
        ├── Social Media (Reddit, Twitter/X)
        ├── ESG Data
        └── Alternative Data (LinkedIn, Supply Chain, Form S-1)
```

### Base Processor

All processors inherit from `BaseProcessor` (`app/ingestion/processors/base_processor.py`), which provides:

- **Common Dependencies**: Document loader, embedding generator, ChromaDB store, sentiment analyzer
- **Shared Processing Logic**: Document chunking, embedding generation, storage
- **Sentiment Enrichment**: Automatic sentiment analysis for documents
- **Error Handling**: Standardized error handling patterns

### Processor Classes

#### DocumentProcessor
- **Purpose**: Process file-based documents (PDF, TXT, Markdown, etc.)
- **Methods**: `process_document()`, `process_documents()`
- **Location**: `app/ingestion/processors/document_processor.py`

#### StockProcessor
- **Purpose**: Process stock market data from yfinance
- **Methods**: `process_stock_data()`, `process_stock_tickers()`
- **Location**: `app/ingestion/processors/stock_processor.py`

#### TranscriptProcessor
- **Purpose**: Process earnings call transcripts
- **Methods**: `process_transcript()`, `process_transcripts()`
- **Location**: `app/ingestion/processors/transcript_processor.py`

#### NewsProcessor
- **Purpose**: Process financial news articles
- **Methods**: `process_news()`
- **Location**: `app/ingestion/processors/news_processor.py`
- **Features**: Integrates with news alert system for automatic notification

#### EconomicDataProcessor
- **Purpose**: Process economic indicators and data
- **Methods**:
  - `process_economic_calendar()` - Economic calendar events
  - `process_fred_series()` - FRED time series
  - `process_world_bank_indicators()` - World Bank indicators
  - `process_imf_indicators()` - IMF indicators
  - `process_central_bank()` - Central bank communications
- **Location**: `app/ingestion/processors/economic_data_processor.py`

#### AlternativeDataProcessor
- **Purpose**: Process alternative data sources
- **Methods**:
  - `process_social_media()` - Reddit and Twitter/X posts
  - `process_esg_data()` - ESG ratings and data
  - `process_alternative_data()` - LinkedIn jobs, supply chain, Form S-1
- **Location**: `app/ingestion/processors/alternative_data_processor.py`

## Data Flow

### Standard Processing Flow

1. **Fetch**: Data source fetcher retrieves raw data
2. **Normalize**: Data is normalized to a standard format
3. **Convert to Documents**: Raw data is converted to LangChain Document objects
4. **Process Documents**: `BaseProcessor.process_documents_to_chunks()` handles:
   - Sentiment enrichment (if enabled)
   - Document chunking
   - Embedding generation
   - ChromaDB storage
5. **Return IDs**: List of chunk IDs stored in ChromaDB

### Example: News Processing

```python
from app.ingestion.pipeline import IngestionPipeline

pipeline = IngestionPipeline()

# NewsProcessor handles the entire flow:
chunk_ids = pipeline.process_news(
    feed_urls=["https://feeds.reuters.com/reuters/businessNews"],
    enhance_with_scraping=True,
    store_embeddings=True
)
```

**Internal Flow:**
1. `NewsProcessor.process_news()` is called
2. `NewsFetcher` fetches articles from RSS feeds
3. Articles are converted to LangChain Documents
4. `BaseProcessor.process_documents_to_chunks()`:
   - Enriches with sentiment analysis
   - Chunks documents
   - Generates embeddings
   - Stores in ChromaDB
5. Returns list of chunk IDs

## Benefits of Processor Architecture

### 1. Modularity
- Each data source has its own processor class
- Easy to understand and maintain
- Clear separation of concerns

### 2. Maintainability
- Changes to one data source don't affect others
- Smaller, focused files (processors are 140-600 lines vs. 2,153 lines in monolithic design)
- Easier to locate and fix bugs

### 3. Testability
- Each processor can be tested independently
- Mock dependencies easily
- Isolated unit tests

### 4. Scalability
- Easy to add new data sources by creating new processor classes
- Inherit from `BaseProcessor` for common functionality
- Minimal code duplication

### 5. Reusability
- Common processing logic in `BaseProcessor`
- Shared utilities in `app/utils/`
- Consistent error handling and metrics

## File Structure

```
app/ingestion/
├── pipeline.py                    # Main orchestrator (869 lines)
├── processors/
│   ├── __init__.py               # Processor exports
│   ├── base_processor.py         # Base class (189 lines)
│   ├── document_processor.py     # Document processing (141 lines)
│   ├── stock_processor.py        # Stock data (207 lines)
│   ├── transcript_processor.py  # Transcripts (234 lines)
│   ├── news_processor.py        # News articles (168 lines)
│   ├── economic_data_processor.py # Economic data (598 lines)
│   └── alternative_data_processor.py # Alternative data (330 lines)
├── document_loader.py            # Document loading and chunking
├── embedding_factory.py         # Embedding generation
└── [other fetchers and normalizers]
```

## Usage Examples

### Processing Documents

```python
from app.ingestion.pipeline import IngestionPipeline
from pathlib import Path

pipeline = IngestionPipeline()

# Single document
chunk_ids = pipeline.process_document(
    Path("document.pdf"),
    store_embeddings=True
)

# Multiple documents
chunk_ids = pipeline.process_documents(
    [Path("doc1.pdf"), Path("doc2.txt")],
    store_embeddings=True
)
```

### Processing Stock Data

```python
# Single ticker
chunk_ids = pipeline.process_stock_data(
    "AAPL",
    include_history=True,
    store_embeddings=True
)

# Multiple tickers
chunk_ids = pipeline.process_stock_tickers(
    ["AAPL", "MSFT", "GOOGL"],
    include_history=True
)
```

### Processing Economic Data

```python
# FRED series
chunk_ids = pipeline.process_fred_series(
    ["GDP", "UNRATE", "FEDFUNDS"],
    start_date="2020-01-01",
    end_date="2024-12-31"
)

# Economic calendar
chunk_ids = pipeline.process_economic_calendar(
    start_date="2024-01-01",
    end_date="2024-12-31",
    country="united states",
    importance="High"
)
```

## Extending the Architecture

### Adding a New Data Source

1. **Create a new processor class**:
```python
from app.ingestion.processors.base_processor import BaseProcessor

class MyDataProcessor(BaseProcessor):
    def __init__(self, document_loader, embedding_generator,
                 chroma_store, my_fetcher, sentiment_analyzer=None):
        super().__init__(document_loader, embedding_generator,
                        chroma_store, sentiment_analyzer)
        self.my_fetcher = my_fetcher

    def process_my_data(self, **kwargs):
        # Fetch data
        data = self.my_fetcher.fetch(**kwargs)

        # Convert to documents
        documents = self.my_fetcher.to_documents(data)

        # Process using base class method
        return self.process_documents_to_chunks(
            documents,
            store_embeddings=True,
            source_name="my_data"
        )
```

2. **Initialize in pipeline.py**:
```python
self.my_data_processor = MyDataProcessor(
    document_loader=self.document_loader,
    embedding_generator=self.embedding_generator,
    chroma_store=self.chroma_store,
    my_fetcher=self.my_fetcher,
    sentiment_analyzer=self.sentiment_analyzer,
)
```

3. **Add delegation method**:
```python
def process_my_data(self, **kwargs):
    return self.my_data_processor.process_my_data(**kwargs)
```

## Migration Notes

The processor architecture was introduced in TASK-050 to improve code maintainability. The public API of `IngestionPipeline` remains unchanged - all existing code continues to work without modification.

### Before (Monolithic)
- Single `pipeline.py` file with 2,153 lines
- All processing methods in one class
- Difficult to maintain and test

### After (Processor-Based)
- Main `pipeline.py` reduced to 869 lines (60% reduction)
- 7 specialized processor classes (1,867 total lines)
- Improved modularity and maintainability

## Related Documentation

- [Configuration Reference](../reference/configuration.md) - Configuration options
- [API Documentation](../reference/api.md) - REST API endpoints
- [Testing Guide](../reference/testing.md) - Testing strategies
