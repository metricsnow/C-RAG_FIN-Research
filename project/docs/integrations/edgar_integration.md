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

### Basic Form Types
- **10-K**: Annual reports (comprehensive financial statements)
- **10-Q**: Quarterly reports (quarterly financial statements)
- **8-K**: Current events (significant corporate events)

### Enhanced Form Types (TASK-032)
- **Form 4**: Statement of Changes in Beneficial Ownership (insider trading)
- **Form S-1**: Registration Statement (IPOs and secondary offerings)
- **DEF 14A**: Proxy Statement (voting items, executive compensation, board members)

### Enhanced Features
- **XBRL Financial Statements**: Structured financial data extraction from XBRL files
  - Balance sheet data
  - Income statement data
  - Cash flow statement data
- **Enhanced Metadata**: Structured metadata extraction for all form types
- **Intelligent Parsing**: Automatic form type detection and specialized parsing

## Usage

### Quick Start

Fetch and ingest EDGAR filings from major companies:

```bash
cd project
source venv/bin/activate
python -u scripts/fetch_edgar_data.py
```

This will:
1. Fetch filings from 10 major companies (AAPL, MSFT, GOOGL, AMZN, META, TSLA, NVDA, JPM, V, JNJ)
2. Download up to 5 filings per company (50 total)
3. Convert HTML to text format
4. Save files to `data/documents/edgar_filings/`
5. Ingest into ChromaDB with embeddings
6. Make them searchable in your RAG system

**Example Output:**
```
============================================================
SEC EDGAR Data Fetching and Ingestion
============================================================
Fetching EDGAR filings for 10 companies...
Form types: 10-K, 10-Q, 8-K
Target: 5 filings per company (up to 50 total)

✓ EDGAR fetcher initialized

[1/10] Processing AAPL...
  → Looking up CIK for AAPL... ✓ CIK: 0000320193
  → Fetching filing history... ✓ Found 5 filings
  → Downloading filings...
    [1/5] 10-K (2025-10-31)... ✓ Downloaded (13 KB)
    [2/5] 8-K (2025-10-30)... ✓ Downloaded (3 KB)
    ...
✓ STEP 1 Complete: Fetched 50 filings

STEP 2: Ingesting EDGAR filings into ChromaDB
✓ Processed 50 documents in 27.5s
✓ Generated 511 chunks
✓ Total documents in ChromaDB: 586
```

### Verification

Verify that documents are indexed and searchable:

```bash
python -u scripts/verify_document_indexing.py
```

This will:
1. Verify document count (50-100 range)
2. Test document searchability with sample queries
3. Validate metadata storage
4. Confirm indexing completeness

### Programmatic Usage

#### Basic Usage

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

#### Enhanced Parsing Usage

```python
from app.ingestion import create_edgar_fetcher, create_pipeline

# Create EDGAR fetcher with enhanced parsing enabled (default)
edgar_fetcher = create_edgar_fetcher(
    rate_limit_delay=0.1,
    use_enhanced_parsing=True  # Enable Form 4, S-1, DEF 14A, XBRL parsing
)

# Fetch filings including enhanced form types
tickers = ["AAPL", "MSFT"]
form_types = ["10-K", "10-Q", "8-K", "4", "S-1", "DEF 14A"]

documents = edgar_fetcher.fetch_filings_to_documents(
    tickers=tickers,
    form_types=form_types,
    max_filings_per_company=3
)

# Enhanced metadata is automatically included
for doc in documents:
    if doc.metadata.get("enhanced"):
        print(f"Enhanced form: {doc.metadata['form_type']}")
        # Form 4: Check for insider_name, transaction_count
        # Form S-1: Check for offering_type, risk_factor_count
        # DEF 14A: Check for voting_items, board_member_count
        # XBRL: Check for xbrl_parsed flag
```

#### Form 4 (Insider Trading) Example

```python
from app.ingestion import create_edgar_fetcher

edgar_fetcher = create_edgar_fetcher(use_enhanced_parsing=True)

# Fetch Form 4 filings (insider trading)
documents = edgar_fetcher.fetch_filings_to_documents(
    tickers=["AAPL"],
    form_types=["4"],
    max_filings_per_company=5
)

for doc in documents:
    if doc.metadata.get("form_type") == "4":
        print(f"Insider: {doc.metadata.get('insider_name', 'N/A')}")
        print(f"Position: {doc.metadata.get('insider_position', 'N/A')}")
        print(f"Transactions: {doc.metadata.get('transaction_count', 0)}")
        # Text content includes structured transaction data
```

#### Form S-1 (IPO) Example

```python
# Fetch Form S-1 filings (IPOs)
documents = edgar_fetcher.fetch_filings_to_documents(
    tickers=["NEWCO"],  # New company going public
    form_types=["S-1"],
    max_filings_per_company=1
)

for doc in documents:
    if doc.metadata.get("form_type") == "S-1":
        print(f"Offering Type: {doc.metadata.get('offering_type', 'N/A')}")
        print(f"Offering Amount: {doc.metadata.get('offering_amount', 'N/A')}")
        print(f"Risk Factors: {doc.metadata.get('risk_factor_count', 0)}")
```

#### DEF 14A (Proxy Statement) Example

```python
# Fetch DEF 14A filings (proxy statements)
documents = edgar_fetcher.fetch_filings_to_documents(
    tickers=["AAPL"],
    form_types=["DEF 14A"],
    max_filings_per_company=1
)

for doc in documents:
    if doc.metadata.get("form_type") == "DEF 14A":
        voting_items = doc.metadata.get("voting_items", [])
        print(f"Voting Items: {len(voting_items)}")
        print(f"Board Members: {doc.metadata.get('board_member_count', 0)}")
```

#### XBRL Financial Data Example

```python
# Fetch 10-K/10-Q with XBRL financial statements
documents = edgar_fetcher.fetch_filings_to_documents(
    tickers=["AAPL"],
    form_types=["10-K"],
    max_filings_per_company=1
)

for doc in documents:
    if doc.metadata.get("xbrl_parsed"):
        print("XBRL financial data included")
        # Text content includes structured financial statements
        # Balance sheet, income statement, cash flow data
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

### Basic Metadata

Each EDGAR filing document includes the following base metadata:

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

### Enhanced Metadata (TASK-032)

When enhanced parsing is enabled, additional metadata is extracted based on form type:

#### Form 4 (Insider Trading) Metadata

```python
{
    # ... basic metadata ...
    "enhanced": True,
    "insider_name": "John Doe",
    "insider_position": "Chief Executive Officer",
    "transaction_count": 3,
    "issuer_name": "Apple Inc.",
    "issuer_ticker": "AAPL"
}
```

#### Form S-1 (IPO) Metadata

```python
{
    # ... basic metadata ...
    "enhanced": True,
    "offering_type": "IPO",
    "offering_amount": "1000000000",
    "risk_factor_count": 25
}
```

#### DEF 14A (Proxy Statement) Metadata

```python
{
    # ... basic metadata ...
    "enhanced": True,
    "voting_items": ["Election of Directors", "Ratification of Auditors"],
    "board_member_count": 8,
    "shareholder_proposal_count": 2
}
```

#### XBRL Metadata

```python
{
    # ... basic metadata ...
    "enhanced": True,
    "xbrl_parsed": True,  # or False if fallback mode
    # XBRL financial data is included in text_content
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

- **Company Tickers**: Uses hardcoded ticker-to-CIK mapping (fallback to API if needed)
- **Filing History**: `https://data.sec.gov/submissions/CIK##########.json`
- **Filing Archive**: `https://www.sec.gov/Archives/edgar/data/{CIK}/{accession-number-without-dashes}/{filename}`

**Note**: The SEC EDGAR archive structure uses accession numbers with dashes removed in the URL path. For example:
- Accession number: `0000320193-24-000096`
- URL path: `000032019324000096` (dashes removed)

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

## Status Information

The fetch script provides detailed progress information:

- **Company Progress**: Shows `[1/10]`, `[2/10]`, etc. for each company
- **CIK Lookup**: Status of ticker-to-CIK conversion
- **Filing History**: Number of filings found per company
- **Download Progress**: Individual filing download with file size (KB)
- **Ingestion Progress**: Document processing and chunk generation status
- **Final Statistics**: Total documents, chunks, and ingestion time

All output is unbuffered (`python -u`) to ensure real-time status updates.

## Enhanced Features (TASK-032)

### XBRL Financial Statement Extraction

The enhanced EDGAR integration includes XBRL parsing capabilities:

- **Automatic XBRL Detection**: Automatically downloads and parses XBRL files for 10-K and 10-Q filings
- **Financial Statement Extraction**: Extracts balance sheet, income statement, and cash flow data
- **Structured Data**: Converts XBRL facts to readable text format for RAG ingestion
- **Fallback Mode**: Uses basic XML parsing if Arelle library is unavailable

**XBRL Data Included:**
- Balance Sheet: Assets, Liabilities, Equity
- Income Statement: Revenue, Expenses, Net Income
- Cash Flow: Operating, Investing, Financing Activities

### Enhanced Form Parsers

**Form 4 Parser:**
- Extracts insider trading transactions
- Transaction dates, types, shares, prices
- Insider names and positions
- Shares owned after transactions

**Form S-1 Parser:**
- Extracts IPO offering details
- Company information and risk factors
- Use of proceeds information
- Offering amount and price range

**DEF 14A Parser:**
- Extracts voting items and proposals
- Executive compensation data
- Board member information
- Shareholder proposals

### Configuration

Enhanced parsing can be configured via environment variables:

```bash
# Enable/disable enhanced parsing (default: true)
EDGAR_ENHANCED_PARSING=true

# Configure form types to fetch (comma-separated)
EDGAR_FORM_TYPES=10-K,10-Q,8-K,4,S-1,DEF 14A

# Enable/disable XBRL extraction (default: true)
EDGAR_XBRL_ENABLED=true
```

See [Configuration Documentation](../reference/configuration.md#enhanced-edgar-integration-configuration-task-032) for details.

## Future Enhancements

Potential improvements for future phases:
- Scheduled automatic updates (daily/weekly)
- Support for additional form types (13F, 13D, etc.)
- Forms 3 and 5 insider trading data extraction
- Historical data fetching with date ranges
- Research papers from arXiv/SSRN integration
- Market reports from public sources
- Financial data validation and quality checks

## References

- SEC EDGAR: https://www.sec.gov/edgar/searchedgar/companysearch.html
- SEC API Documentation: https://www.sec.gov/edgar/sec-api-documentation
- Company CIK Lookup: https://www.sec.gov/edgar/searchedgar/companysearch
