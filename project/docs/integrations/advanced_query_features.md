# Advanced Query Features

## Overview

The Advanced Query Features module provides powerful query capabilities for the RAG system, including Boolean operators, date range filtering, document type filtering, metadata-based filtering, and source-specific filtering.

## Features

### Boolean Operators

Support for Boolean operators in queries:
- **AND** or `&`: Require all terms to match
- **OR** or `|`: Match any term
- **NOT** or `!`: Exclude terms

**Examples:**
```
"revenue AND profit"
"Apple OR Microsoft"
"revenue NOT loss"
```

### Filtering Capabilities

#### Date Range Filtering

Filter documents by date range:
- `from 2023-01-01` or `since 2023-01-01` - Filter from date
- `before 2023-12-31` or `until 2023-12-31` - Filter to date
- `between 2023-01-01 and 2023-12-31` - Date range

**Supported Date Formats:**
- ISO format: `2023-01-01`
- US format: `01/01/2023`
- Text format: `January 1, 2023`

#### Document Type Filtering

Filter by document type:
- `type: edgar_filing` - SEC EDGAR filings
- `type: news` - News articles
- `type: transcript` - Earnings call transcripts
- `type: economic_data` - Economic data

#### Ticker Filtering

Filter by ticker symbol:
- `ticker: AAPL` or `ticker=AAPL` - Filter by ticker

#### Form Type Filtering

Filter by SEC form type:
- `form: 10-K` or `form=10-K` - Annual reports
- `form: 10-Q` - Quarterly reports
- `form: 8-K` - Current reports
- `form: DEF 14A` - Proxy statements

#### Source Filtering

Filter by source identifier:
- `source: data/documents/AAPL_10-K_2023.txt`

## Usage

### Python API

```python
from app.rag.chain import create_rag_system

# Create RAG system
rag_system = create_rag_system()

# Query with filters
result = rag_system.query(
    question="What was Apple's revenue in 2023?",
    filters={
        "ticker": "AAPL",
        "form_type": "10-K",
        "date_from": "2023-01-01",
        "date_to": "2023-12-31"
    },
    enable_query_parsing=True
)

# Access parsed query information
if "parsed_query" in result:
    print(f"Query text: {result['parsed_query']['query_text']}")
    print(f"Boolean operators: {result['parsed_query']['boolean_operators']}")
    print(f"Filters: {result['parsed_query']['filters']}")
```

### REST API

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "question": "What was Apple'\''s revenue in 2023?",
    "filters": {
      "ticker": "AAPL",
      "form_type": "10-K",
      "date_from": "2023-01-01",
      "date_to": "2023-12-31"
    },
    "enable_query_parsing": true
  }'
```

### Streamlit UI

1. Open the Advanced Query Builder (expandable section)
2. Enter your query in the text area
3. Optionally set filters:
   - Date From/To
   - Ticker
   - Form Type
   - Document Type
4. Enable/disable query parsing
5. Click "Query with Filters"

## Query Syntax Examples

### Simple Query with Date Filter
```
What was revenue from 2023-01-01?
```

### Query with Ticker and Form Type
```
ticker: AAPL form: 10-K revenue AND profit
```

### Complex Query with Multiple Filters
```
ticker: AAPL form: 10-K revenue from 2023-01-01 to 2023-12-31
```

### Boolean Operators
```
Apple OR Microsoft revenue AND profit NOT loss
```

## Implementation Details

### Query Parser

The `QueryParser` class (`app/rag/query_parser.py`) handles:
- Boolean operator detection
- Filter extraction from natural language
- Query term extraction
- Stop word removal

### Filter Builder

The `FilterBuilder` class (`app/rag/filter_builder.py`) converts filter specifications into ChromaDB where clauses:
- Date range filters using `$gte` and `$lte`
- Metadata filters
- Combined filters using `$and`

### Integration

The advanced query features are integrated into:
- `RAGQuerySystem.query()` method
- FastAPI query endpoint (`/query`)
- Streamlit UI query builder

## Testing

Comprehensive tests are available:
- `tests/test_query_parser.py` - Query parser tests
- `tests/test_filter_builder.py` - Filter builder tests

Run tests:
```bash
pytest tests/test_query_parser.py tests/test_filter_builder.py -v
```

## Limitations

1. **Boolean Operators**: Currently detected but not fully implemented in retrieval logic (future enhancement)
2. **Date Parsing**: Limited to common date formats
3. **Filter Combinations**: Complex Boolean logic in filters requires explicit filter specification

## Future Enhancements

- Full Boolean operator implementation in retrieval
- More sophisticated query parsing
- Query validation and error messages
- Query history and saved queries
- Query performance analytics
