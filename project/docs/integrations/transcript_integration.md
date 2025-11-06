# Earnings Call Transcripts Integration (TASK-033)

## Overview

The Financial Research Assistant integrates earnings call transcript data sources to provide access to management commentary, forward guidance, and Q&A sessions from earnings calls. The system uses the **API Ninjas Earnings Call Transcript API** as the primary source, with web scraping as an optional fallback (disabled by default).

## Implementation Status

**Status**: ✅ Complete (2025-01-27)
**Primary Source**: API Ninjas Earnings Call Transcript API
**Fallback**: Web scraping (Seeking Alpha, Yahoo Finance) - disabled by default

## API Ninjas Integration

### Overview

API Ninjas provides a free-tier API for accessing earnings call transcripts from over 8,000 companies with data dating back to 2000.

### Configuration

Add the following to your `.env` file:

```bash
# API Ninjas API Key (required for transcript fetching)
API_NINJAS_API_KEY=your-api-key-here

# Transcript Configuration
TRANSCRIPT_USE_API_NINJAS=true           # Use API Ninjas (recommended, default: true)
TRANSCRIPT_USE_WEB_SCRAPING=false       # Enable web scraping fallback (not recommended, default: false)
TRANSCRIPT_RATE_LIMIT_SECONDS=1.0       # Rate limit between requests
```

### Getting an API Key

1. Visit https://api-ninjas.com
2. Sign up for a free account
3. Navigate to API Keys section
4. Copy your API key
5. Add it to your `.env` file as `API_NINJAS_API_KEY`

### API Details

- **Base URL**: `https://api.api-ninjas.com/v1/earningscalltranscript`
- **Authentication**: X-Api-Key header
- **Method**: GET
- **Parameters**:
  - `ticker` (required): Stock ticker symbol (e.g., "AAPL")
  - `date` (optional): Transcript date in YYYY-MM-DD format
- **Response Format**: JSON array of transcript objects
- **Rate Limits**: Free tier has rate limits (configurable via `TRANSCRIPT_RATE_LIMIT_SECONDS`)

### Example API Request

```python
import requests

headers = {"X-Api-Key": "your-api-key-here"}
params = {"ticker": "AAPL", "date": "2025-01-15"}
response = requests.get(
    "https://api.api-ninjas.com/v1/earningscalltranscript",
    headers=headers,
    params=params
)
transcripts = response.json()
```

### Response Structure

```json
[
  {
    "ticker": "AAPL",
    "date": "2025-01-15",
    "transcript": "Full transcript text...",
    "quarter": "Q1 2025",
    "fiscal_year": "2025",
    "url": "https://example.com/transcript"
  }
]
```

## Usage

### Python API

```python
from app.ingestion.transcript_fetcher import TranscriptFetcher

# Initialize fetcher (uses config from .env)
fetcher = TranscriptFetcher()

# Fetch latest transcript for a ticker
transcript = fetcher.fetch_transcript("AAPL")

# Fetch transcript for specific date
transcript = fetcher.fetch_transcript("AAPL", date="2025-01-15")

# Fetch multiple transcripts for date range
transcripts = fetcher.fetch_transcripts_by_date_range(
    "AAPL",
    start_date="2025-01-01",
    end_date="2025-01-31"
)
```

### Command Line Script

```bash
# Fetch and ingest transcripts
python scripts/fetch_transcripts.py --ticker AAPL --date 2025-01-15
```

## Transcript Parsing

The system includes a comprehensive transcript parser that extracts:

- **Speakers**: Identifies management, analysts, and operators
- **Q&A Sections**: Extracts question and answer pairs
- **Management Commentary**: Extracts statements from management
- **Forward Guidance**: Identifies forward-looking statements

### Example Parsing

```python
from app.ingestion.transcript_parser import TranscriptParser

parser = TranscriptParser()
parsed = parser.parse_transcript(transcript_data)

# Access parsed information
speakers = parsed["speakers"]
qa_sections = parsed["qa_sections"]
management_commentary = parsed["management_commentary"]
forward_guidance = parsed["forward_guidance"]
```

## Integration with RAG System

Transcripts are automatically integrated with the RAG system for querying:

```python
# Query about earnings calls
query = "What did Apple's CEO say about iPhone sales in Q1 2025?"
results = rag_chain.query(query)
```

The system will:
1. Retrieve relevant transcript chunks
2. Include speaker information in context
3. Provide citations to specific transcripts
4. Support queries about forward guidance and management commentary

## Fallback Options

### Web Scraping (Not Recommended)

Web scraping is available as a fallback but is **disabled by default** due to:
- Potential Terms of Service violations
- Unreliable parsing
- Legal risks

To enable web scraping fallback (not recommended):

```bash
TRANSCRIPT_USE_WEB_SCRAPING=true
```

**Note**: Web scraping should only be used if API Ninjas is unavailable and you understand the risks.

## Error Handling

The system handles various error scenarios:

- **Missing API Key**: Logs warning, returns None
- **Invalid API Key**: Raises `TranscriptFetcherError` with clear message
- **Rate Limit Exceeded**: Raises `TranscriptFetcherError` with rate limit info
- **Transcript Not Found**: Returns None, logs warning
- **API Unavailable**: Falls back to web scraping (if enabled)

## Testing

Unit tests are available in `tests/test_transcript_fetcher.py`:

```bash
# Run transcript fetcher tests
pytest tests/test_transcript_fetcher.py -v

# Run transcript parser tests
pytest tests/test_transcript_parser.py -v
```

## Best Practices

1. **Always use API Ninjas**: It's free, reliable, and ToS compliant
2. **Respect Rate Limits**: Configure `TRANSCRIPT_RATE_LIMIT_SECONDS` appropriately
3. **Cache Results**: Consider caching transcripts to reduce API calls
4. **Handle Errors Gracefully**: Implement retry logic for transient failures
5. **Monitor API Usage**: Track API calls to stay within free tier limits

## Troubleshooting

### API Key Issues

**Problem**: "API Ninjas API key not configured"
**Solution**: Add `API_NINJAS_API_KEY` to your `.env` file

**Problem**: "API Ninjas API key is invalid"
**Solution**: Verify your API key at https://api-ninjas.com and ensure it's correctly set in `.env`

### Rate Limiting

**Problem**: "API Ninjas rate limit exceeded"
**Solution**:
- Increase `TRANSCRIPT_RATE_LIMIT_SECONDS` in `.env`
- Reduce frequency of transcript fetching
- Consider upgrading API Ninjas plan if needed

### No Transcripts Found

**Problem**: Transcript not found for ticker/date
**Solution**:
- Verify ticker symbol is correct
- Check if transcript exists for that date
- Try fetching without date to get latest transcript

## Related Documentation

- [API Integration Audit](../reference/api_integration_audit.md)
- [Configuration Reference](../reference/configuration.md)
- [Testing Guide](../reference/testing.md)

## References

- [API Ninjas Documentation](https://api-ninjas.com/api/earningscalltranscript)
- [API Ninjas Registration](https://api-ninjas.com)
- Task Documentation: `dev/tasks/TASK-033.md`

---

**Last Updated**: 2025-01-27
**Maintained By**: Development Team
