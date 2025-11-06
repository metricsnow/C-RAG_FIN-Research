# Financial News Aggregation Integration

## Overview

The Financial Research Assistant includes comprehensive financial news aggregation capabilities that fetch, parse, and index news articles from major financial news sources. This integration enables the RAG system to answer questions about current market events, company news, and financial developments.

## Features

- **RSS Feed Parsing**: Parse RSS feeds from major financial news sources
- **Web Scraping**: Scrape full article content with respectful rate limiting
- **Multiple Sources**: Support for Reuters, CNBC, Bloomberg, Financial Times, MarketWatch
- **Ticker Detection**: Automatic extraction of ticker symbols mentioned in articles
- **Article Categorization**: Automatic categorization (earnings, markets, analysis, m&a, ipo, general)
- **Metadata Tagging**: Rich metadata including source, date, author, tickers, category
- **Deduplication**: URL-based deduplication to avoid duplicate articles
- **Rate Limiting**: Configurable rate limits to respect source servers
- **Pipeline Integration**: Seamless integration with existing ingestion pipeline

## Supported Sources

### RSS Feed Sources

- **Reuters Finance**: Financial news and market updates
- **CNBC**: Business and financial news
- **MarketWatch**: Market news and analysis
- **Financial Times**: Global financial news (if RSS available)

### Web Scraping Sources

- **Reuters**: Full article content scraping
- **Bloomberg**: Full article content scraping
- **CNBC**: Full article content scraping
- **Financial Times**: Full article content scraping

**Note**: RSS feed URLs may need to be verified and updated. Default URLs in the code are placeholders.

## Usage

### Command-Line Usage

#### Fetch from RSS Feeds

```bash
# Single RSS feed
python scripts/fetch_news.py --feeds https://www.reuters.com/finance/rss

# Multiple RSS feeds
python scripts/fetch_news.py --feeds \
  https://www.reuters.com/finance/rss \
  https://www.cnbc.com/id/100003114/device/rss/rss.html \
  https://www.marketwatch.com/rss/topstories

# RSS feeds only (no full content scraping)
python scripts/fetch_news.py --feeds https://www.reuters.com/finance/rss --no-scraping
```

#### Scrape Direct URLs

```bash
# Single article
python scripts/fetch_news.py --urls https://www.reuters.com/article/example

# Multiple articles
python scripts/fetch_news.py --urls \
  https://www.reuters.com/article/example1 \
  https://www.bloomberg.com/article/example2 \
  https://www.cnbc.com/article/example3
```

#### Combined RSS and Scraping

```bash
# Fetch from RSS and scrape full content
python scripts/fetch_news.py \
  --feeds https://www.reuters.com/finance/rss \
  --urls https://www.bloomberg.com/article/example
```

#### Options

```bash
# Dry run (don't store in ChromaDB)
python scripts/fetch_news.py --feeds https://www.reuters.com/finance/rss --no-store

# Disable full content scraping for RSS articles
python scripts/fetch_news.py --feeds https://www.reuters.com/finance/rss --no-scraping

# Use different ChromaDB collection
python scripts/fetch_news.py --feeds https://www.reuters.com/finance/rss --collection news
```

### Programmatic Usage

#### Basic Usage

```python
from app.ingestion.pipeline import IngestionPipeline

# Create pipeline
pipeline = IngestionPipeline()

# Process news from RSS feeds
chunk_ids = pipeline.process_news(
    feed_urls=["https://www.reuters.com/finance/rss"],
    enhance_with_scraping=True,  # Scrape full content for RSS articles
    store_embeddings=True
)

print(f"Processed {len(chunk_ids)} chunks from news articles")
```

#### Process Direct URLs

```python
# Process news from direct article URLs
chunk_ids = pipeline.process_news(
    article_urls=[
        "https://www.reuters.com/article/example1",
        "https://www.bloomberg.com/article/example2"
    ],
    store_embeddings=True
)
```

#### Using News Fetcher Directly

```python
from app.ingestion.news_fetcher import NewsFetcher

# Create news fetcher
fetcher = NewsFetcher(
    use_rss=True,
    use_scraping=True,
    rss_rate_limit=1.0,
    scraping_rate_limit=2.0,
    scrape_full_content=True
)

# Fetch news articles
articles = fetcher.fetch_news(
    feed_urls=["https://www.reuters.com/finance/rss"],
    article_urls=None,
    enhance_with_scraping=True
)

# Convert to LangChain Documents
documents = fetcher.to_documents(articles)

# Process through pipeline
pipeline = IngestionPipeline()
chunk_ids = pipeline.process_document_objects(documents, store_embeddings=True)
```

## Configuration

News aggregation is configured via environment variables in `.env`:

```bash
# Enable/disable news aggregation
NEWS_ENABLED=true

# Enable RSS feed parsing
NEWS_USE_RSS=true

# Enable web scraping
NEWS_USE_SCRAPING=true

# Rate limit for RSS feed requests (seconds)
NEWS_RSS_RATE_LIMIT_SECONDS=1.0

# Rate limit for web scraping requests (seconds)
NEWS_SCRAPING_RATE_LIMIT_SECONDS=2.0

# Scrape full article content for RSS articles
NEWS_SCRAPE_FULL_CONTENT=true
```

### Configuration Options

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `NEWS_ENABLED` | boolean | `true` | Enable/disable news aggregation |
| `NEWS_USE_RSS` | boolean | `true` | Enable RSS feed parsing |
| `NEWS_USE_SCRAPING` | boolean | `true` | Enable web scraping |
| `NEWS_RSS_RATE_LIMIT_SECONDS` | float | `1.0` | Rate limit between RSS requests (0.1-60.0) |
| `NEWS_SCRAPING_RATE_LIMIT_SECONDS` | float | `2.0` | Rate limit between scraping requests (0.1-60.0) |
| `NEWS_SCRAPE_FULL_CONTENT` | boolean | `true` | Scrape full content for RSS articles |

## Article Metadata

News articles are stored with rich metadata:

```python
{
    "source": "reuters",              # News source
    "url": "https://...",             # Article URL
    "date": "2025-01-27T12:00:00",   # Publication date
    "author": "Author Name",          # Article author
    "tickers": "AAPL, MSFT",          # Comma-separated ticker symbols
    "category": "earnings",           # Article category
    "type": "news_article",           # Document type
    "feed_title": "Reuters Finance",  # RSS feed title (if from RSS)
}
```

### Article Categories

Articles are automatically categorized based on content:

- **earnings**: Earnings reports, quarterly results
- **markets**: Market updates, trading activity
- **analysis**: Financial analysis, forecasts
- **m&a**: Mergers, acquisitions, deals
- **ipo**: IPOs, listings, public offerings
- **general**: General financial news

### Ticker Detection

Ticker symbols are automatically extracted from article titles and content:

- Pattern: 1-5 uppercase letters (e.g., AAPL, MSFT, GOOGL)
- Filters out common words (THE, AND, FOR, etc.)
- Stored as comma-separated list in metadata

## Architecture

### Components

1. **RSS Parser** (`app/ingestion/rss_parser.py`):
   - Parses RSS feeds using feedparser library
   - Extracts title, content, date, author
   - Automatic source detection
   - Rate limiting

2. **News Scraper** (`app/ingestion/news_scraper.py`):
   - Web scraping with BeautifulSoup
   - Source-specific content selectors
   - Respectful scraping with rate limiting
   - Error handling

3. **News Fetcher** (`app/ingestion/news_fetcher.py`):
   - Combines RSS parsing and web scraping
   - Ticker symbol extraction
   - Article categorization
   - URL-based deduplication
   - Converts to LangChain Documents

4. **Pipeline Integration** (`app/ingestion/pipeline.py`):
   - `process_news()` method for news ingestion
   - Full workflow: fetch → parse → chunk → embed → store
   - Error handling and metrics tracking

### Data Flow

```
RSS Feeds / URLs
    ↓
News Fetcher
    ↓
RSS Parser / News Scraper
    ↓
Article Extraction
    ↓
Ticker Detection & Categorization
    ↓
LangChain Documents
    ↓
Ingestion Pipeline
    ↓
Chunking → Embedding → ChromaDB
```

## Best Practices

### Rate Limiting

- **RSS Feeds**: Default 1 second between requests (configurable)
- **Web Scraping**: Default 2 seconds between requests (configurable)
- **Respectful Scraping**: Always use rate limiting to avoid being blocked
- **User Agents**: Proper user agents are set automatically

### RSS Feed URLs

- Verify RSS feed URLs before use (default URLs are placeholders)
- Some sources may require authentication
- RSS feed structures may vary by source

### Web Scraping Considerations

- **Website Changes**: Selectors may need updates if website structures change
- **Rate Limiting**: Critical to avoid being blocked
- **Error Handling**: Scraping failures are handled gracefully
- **Fallback**: RSS feeds provide fallback if scraping fails

### Deduplication

- Articles are deduplicated by URL
- Same article from different sources will be stored separately
- Consider content-based deduplication for future enhancement

## Troubleshooting

### No Articles Fetched

**Problem**: RSS feed parsing returns no articles

**Solutions**:
1. Verify RSS feed URL is correct and accessible
2. Check network connectivity
3. Verify feed format (some feeds may be malformed)
4. Check logs for parsing errors

### Scraping Failures

**Problem**: Web scraping fails for certain articles

**Solutions**:
1. Check if website structure has changed
2. Verify article URL is accessible
3. Check rate limiting (may be blocked)
4. Review error logs for specific issues
5. Use RSS feeds as fallback

### Rate Limiting Issues

**Problem**: Getting blocked by news sources

**Solutions**:
1. Increase rate limit delays:
   ```bash
   NEWS_RSS_RATE_LIMIT_SECONDS=2.0
   NEWS_SCRAPING_RATE_LIMIT_SECONDS=5.0
   ```
2. Reduce concurrent requests
3. Use RSS feeds instead of scraping when possible

### Missing Tickers

**Problem**: Ticker symbols not detected in articles

**Solutions**:
1. Ticker detection uses regex pattern (1-5 uppercase letters)
2. Common words are filtered out
3. Tickers must be mentioned in title or content
4. Check article content for ticker mentions

## Examples

### Example 1: Daily News Collection

```bash
# Collect daily news from multiple sources
python scripts/fetch_news.py \
  --feeds \
    https://www.reuters.com/finance/rss \
    https://www.cnbc.com/id/100003114/device/rss/rss.html \
    https://www.marketwatch.com/rss/topstories
```

### Example 2: Company-Specific News

```python
from app.ingestion.pipeline import IngestionPipeline

pipeline = IngestionPipeline()

# Fetch news and filter for specific ticker in queries
chunk_ids = pipeline.process_news(
    feed_urls=["https://www.reuters.com/finance/rss"],
    enhance_with_scraping=True
)

# Query for specific ticker news
# The RAG system will find articles mentioning the ticker via metadata
```

### Example 3: Scheduled News Updates

```bash
# Add to crontab for daily news updates
0 9 * * * cd /path/to/project && source venv/bin/activate && python scripts/fetch_news.py --feeds https://www.reuters.com/finance/rss
```

## Integration with Other Features

### Sentiment Analysis (TASK-039) ✅

**Status**: Complete - Sentiment analysis is automatically applied to news articles during ingestion.

**Features**:
- Automatic sentiment scoring using FinBERT, TextBlob, and VADER
- Sentiment scores stored as metadata (`sentiment`, `sentiment_score`, `sentiment_model`)
- Model-specific scores available (`sentiment_finbert`, `sentiment_vader`, `sentiment_textblob`)
- Forward guidance extraction from news articles
- Risk factor identification in news content

**Metadata Added**:
- `sentiment`: Overall sentiment (positive/negative/neutral)
- `sentiment_score`: Overall sentiment score (-1.0 to 1.0)
- `sentiment_model`: Model used (finbert/vader/textblob)
- `forward_guidance_count`: Number of forward guidance statements
- `has_forward_guidance`: Boolean flag
- `risk_factors_count`: Number of risk factors identified
- `has_risk_factors`: Boolean flag

**Usage**: Sentiment analysis is automatically applied - no additional configuration needed. See [Sentiment Analysis Integration](sentiment_analysis.md) for details.

### Query Interface

News articles are queryable through the existing RAG system:

```python
# Query about recent news
"What are the latest earnings reports for tech companies?"

# Query about specific ticker news
"What news is there about AAPL?"

# Query about market trends
"What are analysts saying about the current market?"
```

The RAG system will retrieve relevant news articles based on semantic similarity and metadata filtering.

## Future Enhancements

The following enhancements are planned as separate tasks:

- **TASK-046**: News Article Summarization
- **TASK-047**: News Trend Analysis
- **TASK-048**: Automated News Monitoring
- **TASK-049**: News Alert System

See individual task files for details.

## Related Documentation

- [Configuration Reference](reference/configuration.md#news-aggregation-configuration-task-034)
- [API Documentation](reference/api.md) (for programmatic access)
- [Ingestion Pipeline](../README.md#data-collection)

---

**Last Updated**: 2025-01-27
**Task**: TASK-034
**Status**: Complete
