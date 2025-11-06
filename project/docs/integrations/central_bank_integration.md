# Central Bank Data Integration

## Overview

This document describes the integration of central bank communications into the financial research assistant. This integration provides access to FOMC (Federal Reserve) statements, meeting minutes, press conference transcripts, and forward guidance extraction for comprehensive monetary policy analysis.

## Features

### FOMC Data Sources

- **FOMC Statements**: Federal Reserve monetary policy statements after FOMC meetings
- **Meeting Minutes**: Detailed minutes from FOMC meetings (released 3 weeks after meetings)
- **Press Conference Transcripts**: Transcripts from FOMC press conferences with the Chair
- **Forward Guidance Extraction**: Automatic extraction of forward guidance statements
- **Interest Rate Decisions**: Information about interest rate changes and policy decisions

### Data Processing

- **Web Scraping**: Automated scraping of Federal Reserve website
- **Metadata Extraction**: Bank, date, type, URL, and title extraction
- **Forward Guidance Detection**: Automatic identification of forward guidance statements
- **RAG Formatting**: Optimized formatting for RAG system ingestion
- **Chunking and Embedding**: Automatic chunking and embedding for vector storage

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Central Bank Data Configuration
CENTRAL_BANK_ENABLED=true
CENTRAL_BANK_RATE_LIMIT_SECONDS=2.0
CENTRAL_BANK_USE_WEB_SCRAPING=true
```

### Configuration Options

- `CENTRAL_BANK_ENABLED`: Enable/disable central bank integration (default: `true`)
- `CENTRAL_BANK_RATE_LIMIT_SECONDS`: Rate limit between web scraping requests in seconds (default: `2.0`)
- `CENTRAL_BANK_USE_WEB_SCRAPING`: Enable web scraping for central bank data (default: `true`)

**Note**: Central bank data is fetched via web scraping from the Federal Reserve website. No API key is required, but rate limiting is important to respect the website's resources.

## Usage

### Python API

#### Direct Fetcher Usage

```python
from app.ingestion.central_bank_fetcher import CentralBankFetcher

# Initialize fetcher
fetcher = CentralBankFetcher()

# Fetch FOMC statements
statements = fetcher.fetch_fomc_statements(
    start_date="2025-01-01",  # Optional: start date (YYYY-MM-DD)
    end_date="2025-01-31",    # Optional: end date (YYYY-MM-DD)
    limit=10                   # Optional: maximum number to fetch
)

# Fetch FOMC meeting minutes
minutes = fetcher.fetch_fomc_minutes(
    start_date="2025-01-01",
    limit=5
)

# Fetch press conference transcripts
transcripts = fetcher.fetch_fomc_press_conferences(
    start_date="2025-01-01",
    limit=5
)

# Extract forward guidance from content
content = "The Committee will maintain accommodative policy..."
guidance = fetcher.extract_forward_guidance(content)

# Convert to Document objects for RAG
documents = fetcher.to_documents(statements)
```

#### Pipeline Integration

```python
from app.ingestion.pipeline import create_pipeline

# Create pipeline
pipeline = create_pipeline()

# Process all central bank communications
ids = pipeline.process_central_bank(
    comm_types=["fomc_statement", "fomc_minutes", "fomc_press_conference"],
    start_date="2025-01-01",
    end_date="2025-01-31",
    limit=10,
    store_embeddings=True
)

# Process only statements
ids = pipeline.process_central_bank(
    comm_types=["fomc_statement"],
    limit=5
)
```

### Command Line Usage

#### Fetch and Display (No Storage)

```bash
# Fetch all communication types
python scripts/fetch_central_bank_data.py --types all

# Fetch specific types
python scripts/fetch_central_bank_data.py --types fomc_statement fomc_minutes

# Fetch with date range
python scripts/fetch_central_bank_data.py --types fomc_statement \
    --start-date 2025-01-01 --end-date 2025-01-31

# Fetch with limit
python scripts/fetch_central_bank_data.py --types fomc_statement --limit 5
```

#### Fetch and Store in ChromaDB

```bash
# Fetch and store all types
python scripts/fetch_central_bank_data.py --types all --store

# Fetch and store specific types
python scripts/fetch_central_bank_data.py --types fomc_statement fomc_minutes --store
```

## Data Format

### Communication Dictionary Structure

```python
{
    "type": "fomc_statement",  # or "fomc_minutes", "fomc_press_conference"
    "bank": "Federal Reserve",
    "date": "2025-01-27",      # Date in MM/DD/YYYY format
    "url": "https://www.federalreserve.gov/...",
    "title": "FOMC Statement - January 27, 2025",
    "content": "Full text content of the communication"
}
```

### Document Metadata

When converted to Document objects, the following metadata is included:

```python
{
    "source": "central_bank",
    "type": "fomc_statement",
    "bank": "Federal Reserve",
    "date": "2025-01-27",
    "url": "https://...",
    "title": "FOMC Statement - January 27, 2025",
    "has_forward_guidance": True,
    "forward_guidance_count": 3
}
```

## Forward Guidance Extraction

The fetcher automatically extracts forward guidance statements using keyword matching. Keywords include:

- "forward guidance"
- "policy path"
- "future policy"
- "policy outlook"
- "monetary policy stance"
- "accommodative"
- "restrictive"
- "neutral"
- "policy normalization"
- "policy tightening"
- "policy easing"

Forward guidance statements are included in the formatted RAG text and counted in metadata.

## RAG Query Examples

Once central bank communications are ingested, you can query them through the RAG system:

```python
from app.rag.chain import RAGQuerySystem

rag = RAGQuerySystem()

# Query about FOMC policy
response = rag.query("What did the FOMC say about interest rates in January 2025?")

# Query about forward guidance
response = rag.query("What forward guidance did the Fed provide about future policy?")

# Query about specific meeting
response = rag.query("What were the key points from the January 2025 FOMC meeting?")
```

## Error Handling

The fetcher includes comprehensive error handling:

- **Network Errors**: Handles connection failures and timeouts gracefully
- **HTML Parsing Errors**: Handles malformed HTML and missing content
- **Rate Limiting**: Automatic rate limiting to respect website resources
- **Missing Data**: Gracefully handles missing or unavailable communications

## Limitations

1. **Web Scraping Dependency**: Relies on Federal Reserve website structure, which may change
2. **Rate Limiting**: Must respect website rate limits (default: 2 seconds between requests)
3. **Historical Data**: Limited by what's available on the Federal Reserve website
4. **Website Changes**: May require updates if Federal Reserve website structure changes

## Troubleshooting

### No Communications Fetched

- Check that `CENTRAL_BANK_ENABLED=true` in `.env`
- Verify internet connection
- Check if Federal Reserve website is accessible
- Review logs for specific error messages

### Web Scraping Fails

- Verify `CENTRAL_BANK_USE_WEB_SCRAPING=true`
- Check if website structure has changed
- Increase rate limit if getting blocked: `CENTRAL_BANK_RATE_LIMIT_SECONDS=3.0`

### Forward Guidance Not Detected

- Forward guidance detection uses keyword matching
- Some statements may not contain standard forward guidance language
- Check the `forward_guidance_count` in metadata to verify detection

## Future Enhancements

Potential future enhancements:

- Support for other central banks (ECB, BOJ, BOE, etc.)
- Dot plot data extraction
- Interest rate decision parsing
- Historical data API integration
- Real-time monitoring of new communications

## Related Documentation

- [Pipeline Integration](reference/configuration.md)
- [RAG System](reference/configuration.md)
- [Document Ingestion](reference/configuration.md)
