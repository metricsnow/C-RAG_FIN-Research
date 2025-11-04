# SEC EDGAR Data Integration

## Overview

The Financial Research Assistant includes automated integration with the SEC EDGAR (Electronic Data Gathering, Analysis, and Retrieval) system for fetching free financial filings. This allows the RAG system to automatically collect and index public SEC filings without manual intervention.

## Features

- **Free Public API**: Uses SEC's free public EDGAR API (no API keys required)
- **Automated Fetching**: Script to fetch filings from multiple companies
- **Rate Limiting**: Respects SEC guidelines (10 requests per second)
- **Rich Metadata**: Includes ticker, CIK, form type, filing date, and accession number
- **Direct Integration**: Automatically ingests into ChromaDB via ingestion pipeline

## Supported Form Types

- **10-K**: Annual reports (comprehensive financial statements)
- **10-Q**: Quarterly reports (quarterly financial statements)
- **8-K**: Current events (significant corporate events)

## Usage

### Quick Start

Fetch and ingest EDGAR filings from major companies:

```bash
cd project
source venv/bin/activate
PYTHONPATH=/Users/marcus/Public_Git/Project1/project python scripts/fetch_edgar_data.py
```

This will:
1. Fetch filings from 10 major companies (AAPL, MSFT, GOOGL, etc.)
2. Download up to 5 filings per company
3. Convert to text format
4. Ingest into ChromaDB
5. Make them searchable in your RAG system

### Programmatic Usage

```python
from app.ingestion import create_edgar_fetcher, create_pipeline

# Create EDGAR fetcher
edgar_fetcher = create_edgar_fetcher(rate_limit_delay=0.1)

# Fetch filings for specific companies
tickers = ["AAPL", "MSFT", "GOOGL"]
form_types = ["10-K", "10-Q", "8-K"]

documents = edgar_fetcher.fetch_filings_to_documents(
    tickers=tickers,
    form_types=form_types,
    max_filings_per_company=5
)

# Ingest into ChromaDB
pipeline = create_pipeline(collection_name="documents")
chunk_ids = pipeline.process_document_objects(documents)

print(f"Ingested {len(chunk_ids)} chunks from {len(documents)} filings")
```

### Customizing Fetch Parameters

```python
# Fetch specific form types only
documents = edgar_fetcher.fetch_filings_to_documents(
    tickers=["TSLA", "NVDA"],
    form_types=["10-K"],  # Only annual reports
    max_filings_per_company=3
)

# Save to files before ingestion
edgar_fetcher.save_filings_to_files(
    documents,
    output_dir=Path("data/documents/edgar_filings")
)
```

## API Reference

### EdgarFetcher Class

**Methods:**

- `get_company_cik(ticker: str) -> Optional[str]`
  - Get company CIK (Central Index Key) from ticker symbol
  - Returns 10-digit zero-padded CIK string

- `get_filing_history(cik: str) -> Dict[str, Any]`
  - Get complete filing history for a company
  - Returns filing history dictionary

- `get_recent_filings(cik: str, form_types: Optional[List[str]], max_filings: int) -> List[Dict[str, Any]]`
  - Get recent filings filtered by form type
  - Returns list of filing dictionaries sorted by date

- `download_filing_text(cik: str, accession_number: str, form_type: str) -> str`
  - Download filing text content
  - Returns extracted text content

- `fetch_filings_to_documents(tickers: List[str], form_types: Optional[List[str]], max_filings_per_company: int) -> List[Document]`
  - Fetch multiple filings and convert to LangChain Document objects
  - Returns list of Document objects ready for ingestion

- `save_filings_to_files(documents: List[Document], output_dir: Path) -> List[Path]`
  - Save Document objects to text files
  - Returns list of saved file paths

## Metadata Structure

Each EDGAR filing document includes the following metadata:

```python
{
    "source": "SEC EDGAR - AAPL",
    "filename": "AAPL_10-K_2024-01-01.txt",
    "type": "edgar_filing",
    "ticker": "AAPL",
    "cik": "0000320193",
    "form_type": "10-K",
    "filing_date": "2024-01-01",
    "accession_number": "0000950170-24-001234",
    "date": "2025-01-27T10:30:00"  # Ingestion timestamp
}
```

## Rate Limiting

The SEC EDGAR API has rate limits:
- **Maximum**: 10 requests per second
- **Default delay**: 0.1 seconds between requests
- **User-Agent**: Required (set automatically)

The fetcher automatically respects these limits with configurable delays.

## Data Sources

### SEC EDGAR API Endpoints

- **Company Tickers**: `https://data.sec.gov/files/company_tickers.json`
- **Filing History**: `https://data.sec.gov/submissions/CIK##########.json`
- **Filing Text**: `https://data.sec.gov/files/data/{CIK}/{accession-number}/{form-type}-{accession}.txt`

### Documentation

- SEC EDGAR API Documentation: https://www.sec.gov/edgar/sec-api-documentation
- SEC Developer Resources: https://www.sec.gov/about/developer-resources

## Troubleshooting

### Common Issues

1. **Rate Limit Errors**
   - Increase `rate_limit_delay` parameter (default: 0.1 seconds)
   - Reduce number of companies or filings per company

2. **CIK Lookup Failures**
   - Verify ticker symbol is correct
   - Check SEC company tickers JSON is accessible

3. **Filing Download Failures**
   - Some filings may not have text versions (only HTML)
   - HTML versions are automatically converted to text
   - Very old filings may not be available

4. **Network Timeouts**
   - SEC servers may be slow during peak hours
   - Increase timeout values in requests

### Error Handling

The fetcher includes comprehensive error handling:
- Continues processing other companies if one fails
- Logs warnings for individual filing failures
- Returns partial results if some filings fail

## Integration with Ingestion Pipeline

The EDGAR fetcher integrates seamlessly with the existing ingestion pipeline:

1. **Fetch**: EDGAR fetcher downloads filings
2. **Convert**: Filings converted to LangChain Document objects
3. **Process**: `process_document_objects()` method processes documents
4. **Chunk**: Documents chunked with metadata
5. **Embed**: Embeddings generated for chunks
6. **Store**: Chunks stored in ChromaDB with metadata

## Future Enhancements

Potential improvements for Phase 2:
- Scheduled automatic updates (daily/weekly)
- Support for additional form types (13F, 13D, etc.)
- Insider trading data extraction (Forms 3, 4, 5)
- XBRL data parsing for structured financial data
- Historical data fetching with date ranges

## References

- SEC EDGAR: https://www.sec.gov/edgar/searchedgar/companysearch.html
- SEC API Documentation: https://www.sec.gov/edgar/sec-api-documentation
- Company CIK Lookup: https://www.sec.gov/edgar/searchedgar/companysearch

