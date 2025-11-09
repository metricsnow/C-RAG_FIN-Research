# Financial News Aggregation Integration

## Overview

The Financial Research Assistant includes comprehensive financial news aggregation capabilities that fetch, parse, and index news articles from major financial news sources. This integration enables the RAG system to answer questions about current market events, company news, and financial developments.

## Features

- **RSS Feed Parsing**: Parse RSS feeds from major financial news sources
- **Web Scraping**: Scrape full article content with respectful rate limiting
- **Multiple Sources**: Support for Reuters, CNBC, Bloomberg, Financial Times, MarketWatch
- **Ticker Detection**: Automatic extraction of ticker symbols mentioned in articles
- **Article Categorization**: Automatic categorization (earnings, markets, analysis, m&a, ipo, general)
- **Article Summarization**: Automatic LLM-based summarization of news articles (TASK-046) ✅
- **News Trend Analysis**: Trend analysis for tickers, topics, and volume patterns (TASK-047) ✅
- **Automated News Monitoring**: Continuous monitoring and automatic ingestion of new articles (TASK-048) ✅
- **Metadata Tagging**: Rich metadata including source, date, author, tickers, category, summary
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

#### Automated News Monitoring

```bash
# Start monitoring service with default configuration
python scripts/start_news_monitor.py

# Start with custom feeds and interval
python scripts/start_news_monitor.py \
  --feeds https://www.reuters.com/finance/rss \
  --interval 15

# Start with filters (only monitor specific tickers/keywords)
python scripts/start_news_monitor.py \
  --feeds https://www.reuters.com/finance/rss \
  --filter-tickers AAPL MSFT GOOGL \
  --filter-keywords earnings revenue

# Disable full content scraping
python scripts/start_news_monitor.py \
  --feeds https://www.reuters.com/finance/rss \
  --no-scraping

# Use different ChromaDB collection
python scripts/start_news_monitor.py \
  --feeds https://www.reuters.com/finance/rss \
  --collection news
```

**Note**: The monitoring service runs continuously in the background. Press Ctrl+C to stop.

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

# News Summarization (TASK-046) ✅
NEWS_SUMMARIZATION_ENABLED=true
NEWS_SUMMARIZATION_TARGET_WORDS=150
NEWS_SUMMARIZATION_MIN_WORDS=50
NEWS_SUMMARIZATION_MAX_WORDS=200
NEWS_SUMMARIZATION_LLM_PROVIDER=  # Optional: 'ollama' or 'openai' (uses LLM_PROVIDER if empty)
NEWS_SUMMARIZATION_LLM_MODEL=     # Optional: model name (uses default for provider if empty)
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
| `NEWS_SUMMARIZATION_ENABLED` | boolean | `true` | Enable automatic article summarization |
| `NEWS_SUMMARIZATION_TARGET_WORDS` | int | `150` | Target summary length in words (50-300) |
| `NEWS_SUMMARIZATION_MIN_WORDS` | int | `50` | Minimum summary length in words (20-200) |
| `NEWS_SUMMARIZATION_MAX_WORDS` | int | `200` | Maximum summary length in words (100-500) |
| `NEWS_SUMMARIZATION_LLM_PROVIDER` | string | `""` | LLM provider ('ollama' or 'openai'). Empty uses `LLM_PROVIDER` |
| `NEWS_SUMMARIZATION_LLM_MODEL` | string | `""` | LLM model name. Empty uses default for provider |

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
    "summary": "Article summary...", # LLM-generated summary (if summarization enabled)
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
   - Integrates with News Summarizer for automatic summarization

4. **News Summarizer** (`app/ingestion/news_summarizer.py`) (TASK-046) ✅:
   - LLM-based article summarization
   - Support for Ollama and OpenAI providers
   - Configurable summary length (50-200 words)
   - Financial domain prompt engineering
   - Batch summarization support
   - Error handling and graceful degradation

5. **Pipeline Integration** (`app/ingestion/pipeline.py`):
   - `process_news()` method for news ingestion
   - Full workflow: fetch → parse → summarize → chunk → embed → store
   - Error handling and metrics tracking
   - Automatic summarization integration

6. **News Monitor** (`app/services/news_monitor.py`) (TASK-048) ✅:
   - Automated background service for continuous news monitoring
   - Scheduled RSS feed polling using APScheduler
   - Automatic article detection and ingestion
   - URL-based deduplication (in-memory and ChromaDB)
   - Configurable filtering (tickers, keywords, categories)
   - Service lifecycle management (start/stop/pause/resume)
   - Health monitoring and statistics tracking
   - Error recovery and retry logic

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
News Summarizer (if enabled) ← LLM-based summarization
    ↓
LangChain Documents (with summary in metadata)
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

### Automated Monitoring

- **Polling Intervals**: Default 30 minutes (configurable 5-1440 minutes)
- **Deduplication**: In-memory cache + ChromaDB lookup for robust deduplication
- **Filtering**: Apply filters before ingestion to reduce processing overhead
- **Error Handling**: Errors are logged but don't stop the service
- **Resource Usage**: Monitor CPU and memory usage for long-running services
- **Service Management**: Use start/stop/pause/resume for service control

## Configuration

### Environment Variables

#### News Monitoring Configuration (TASK-048)

```bash
# Enable automated news monitoring
NEWS_MONITOR_ENABLED=true

# Polling interval in minutes (5-1440, default: 30)
NEWS_MONITOR_POLL_INTERVAL_MINUTES=30

# RSS feed URLs (comma-separated)
NEWS_MONITOR_FEEDS=https://www.reuters.com/finance/rss,https://www.cnbc.com/id/100003114/device/rss/rss.html

# Enable full content scraping (default: true)
NEWS_MONITOR_ENABLE_SCRAPING=true

# Filter by ticker symbols (comma-separated, optional)
NEWS_MONITOR_FILTER_TICKERS=AAPL,MSFT,GOOGL

# Filter by keywords (comma-separated, optional)
NEWS_MONITOR_FILTER_KEYWORDS=earnings,revenue,profit

# Filter by categories (comma-separated, optional)
NEWS_MONITOR_FILTER_CATEGORIES=earnings,markets
```

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

### Monitoring Service Issues

**Problem**: Monitoring service fails to start or stops unexpectedly

**Solutions**:
1. Verify `NEWS_MONITOR_ENABLED=true` in configuration
2. Check that feed URLs are valid and accessible
3. Verify ChromaDB is accessible and collection exists
4. Check logs for specific error messages
5. Ensure APScheduler is installed: `pip install apscheduler>=3.10.0`

**Problem**: No articles being ingested by monitoring service

**Solutions**:
1. Check that feeds are returning articles (test manually)
2. Verify deduplication isn't filtering all articles
3. Check filter criteria aren't too restrictive
4. Review monitoring statistics: `monitor.get_stats()`
5. Check health status: `monitor.health_check()`
6. Review error logs for specific issues
7. Use RSS feeds as fallback
8. Verify service is not paused: `monitor.is_paused`

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

## News Summarization (TASK-046) ✅

**Status**: Complete - Automatic LLM-based summarization of news articles is now available.

### Features

- **Automatic Summarization**: Articles are automatically summarized during ingestion
- **LLM-Based**: Uses Ollama or OpenAI for high-quality summaries
- **Financial Domain**: Prompt engineering optimized for financial news
- **Configurable Length**: Target 50-200 words (default 150)
- **Metadata Storage**: Summaries stored in document metadata for quick access
- **Batch Processing**: Script available to summarize existing articles

### Usage

Summarization is automatically enabled by default. To disable:

```bash
NEWS_SUMMARIZATION_ENABLED=false
```

### Batch Summarization

To summarize existing articles in ChromaDB:

```bash
# Summarize all articles without summaries
python scripts/summarize_news.py

# Limit to first 10 articles
python scripts/summarize_news.py --limit 10

# Dry run (don't update ChromaDB)
python scripts/summarize_news.py --dry-run

# Use different collection
python scripts/summarize_news.py --collection news
```

### Configuration

```bash
# Enable/disable summarization
NEWS_SUMMARIZATION_ENABLED=true

# Summary length configuration
NEWS_SUMMARIZATION_TARGET_WORDS=150  # Target length
NEWS_SUMMARIZATION_MIN_WORDS=50      # Minimum length
NEWS_SUMMARIZATION_MAX_WORDS=200     # Maximum length

# Optional: Use specific LLM provider/model
NEWS_SUMMARIZATION_LLM_PROVIDER=ollama  # or 'openai'
NEWS_SUMMARIZATION_LLM_MODEL=llama3.2   # Optional model name
```

### Summary Quality

- **Focus**: Key financial information (tickers, numbers, events)
- **Length**: 50-200 words (configurable)
- **Format**: Concise, informative summaries
- **Error Handling**: Pipeline continues even if summarization fails

### Benefits

- **Quick Overviews**: Users can quickly understand article content
- **Improved Search**: Summaries enhance search relevance
- **Metadata Access**: Summaries available in document metadata
- **Optional Feature**: Can be disabled if not needed

## News Trend Analysis (TASK-047) ✅

**Status**: Complete - News trend analysis is now available for identifying trending topics, tickers, and patterns.

### Features

- **Ticker Trend Analysis**: Identify trending tickers based on frequency and growth
- **Topic/Keyword Analysis**: Detect trending topics and keywords from news articles
- **Volume Trend Analysis**: Track news volume over time periods
- **Time Series Aggregation**: Support for hourly, daily, weekly, and monthly periods
- **Comprehensive Reports**: Generate detailed trend reports with multiple metrics

### Quick Start

```bash
# Generate daily trend report for last 7 days
python scripts/analyze_news_trends.py --days 7
```

For detailed documentation, see [News Trend Analysis Integration](news_trend_analysis.md).

## Automated News Monitoring (TASK-048) ✅

**Status**: Complete - Automated news monitoring service is now available for continuous background monitoring and automatic ingestion of new articles.

### Features

- **Continuous Monitoring**: Background service that continuously monitors RSS feeds
- **Automatic Ingestion**: Automatically detects and ingests new articles
- **Configurable Polling**: Polling intervals from 5 minutes to 24 hours
- **Deduplication**: In-memory cache + ChromaDB lookup for robust deduplication
- **Filtering**: Configurable filters for tickers, keywords, and categories
- **Service Management**: Start/stop/pause/resume capabilities
- **Health Monitoring**: Health checks and statistics tracking
- **Error Recovery**: Graceful error handling with retry logic
- **Signal Handling**: Graceful shutdown on SIGINT/SIGTERM
- **Statistics Tracking**: Comprehensive metrics for monitoring and debugging

### Quick Start

```bash
# Start monitoring with default configuration
python scripts/start_news_monitor.py

# Start with custom feeds and interval
python scripts/start_news_monitor.py \
  --feeds https://www.reuters.com/finance/rss \
  --interval 15

# Start with filters (only monitor specific tickers/keywords)
python scripts/start_news_monitor.py \
  --feeds https://www.reuters.com/finance/rss \
  --filter-tickers AAPL MSFT GOOGL \
  --filter-keywords earnings revenue

# Disable full content scraping
python scripts/start_news_monitor.py \
  --feeds https://www.reuters.com/finance/rss \
  --no-scraping

# Use different ChromaDB collection
python scripts/start_news_monitor.py \
  --feeds https://www.reuters.com/finance/rss \
  --collection news
```

**Note**: The monitoring service runs continuously in the background. Press Ctrl+C to stop gracefully.

### Programmatic Usage

```python
from app.services.news_monitor import NewsMonitor, NewsMonitorError

# Create monitor instance
monitor = NewsMonitor(
    feed_urls=[
        "https://www.reuters.com/finance/rss",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html"
    ],
    poll_interval_minutes=30,
    collection_name="documents",
    enable_scraping=True,
    filter_tickers=["AAPL", "MSFT"],  # Optional
    filter_keywords=["earnings", "revenue"],  # Optional
    filter_categories=["earnings", "markets"]  # Optional
)

# Start monitoring service
try:
    monitor.start()
    print("Monitoring service started")

    # Service runs in background
    # You can check status, pause, resume, etc.

    # Get statistics
    stats = monitor.get_stats()
    print(f"Total polls: {stats['total_polls']}")
    print(f"Articles ingested: {stats['total_articles_ingested']}")

    # Health check
    health = monitor.health_check()
    print(f"Service running: {health['service_running']}")

    # Pause monitoring (scheduler continues, polls skipped)
    monitor.pause()

    # Resume monitoring
    monitor.resume()

    # Stop monitoring
    monitor.stop()

except NewsMonitorError as e:
    print(f"Error: {e}")
```

### Service Management

The monitoring service provides full lifecycle management:

```python
# Start service
monitor.start()  # Performs initial poll immediately

# Pause monitoring (scheduler continues, but polls are skipped)
monitor.pause()

# Resume monitoring
monitor.resume()

# Stop service (shuts down scheduler)
monitor.stop()
```

### Statistics and Monitoring

The service tracks comprehensive statistics:

```python
stats = monitor.get_stats()

# Available statistics:
# - total_polls: Number of feed polls completed
# - total_articles_processed: Total articles processed
# - total_articles_ingested: Total articles successfully ingested
# - total_errors: Number of errors encountered
# - last_poll_time: Timestamp of last poll
# - last_poll_success: Whether last poll was successful
# - start_time: Service start timestamp
# - uptime_seconds: Service uptime in seconds
# - is_running: Whether service is running
# - is_paused: Whether service is paused
# - feed_count: Number of feeds being monitored
# - processed_urls_count: Number of URLs in deduplication cache
```

### Health Checks

Monitor service health:

```python
health = monitor.health_check()

# Returns dictionary with:
# - service_running: Whether service is running
# - scheduler_running: Whether scheduler is active
# - pipeline_available: Whether ingestion pipeline is available
# - chroma_store_available: Whether ChromaDB store is available
# - feeds_configured: Whether feeds are configured
```

### Configuration

Configure via environment variables in `.env`:

```bash
# Enable automated news monitoring
NEWS_MONITOR_ENABLED=true

# Polling interval in minutes (5-1440, default: 30)
NEWS_MONITOR_POLL_INTERVAL_MINUTES=30

# RSS feed URLs (comma-separated)
NEWS_MONITOR_FEEDS=https://www.reuters.com/finance/rss,https://www.cnbc.com/id/100003114/device/rss/rss.html

# Enable full content scraping (default: true)
NEWS_MONITOR_ENABLE_SCRAPING=true

# Filter by ticker symbols (comma-separated, optional)
NEWS_MONITOR_FILTER_TICKERS=AAPL,MSFT,GOOGL

# Filter by keywords (comma-separated, optional)
NEWS_MONITOR_FILTER_KEYWORDS=earnings,revenue,profit

# Filter by categories (comma-separated, optional)
NEWS_MONITOR_FILTER_CATEGORIES=earnings,markets
```

### Architecture

The monitoring service uses:

- **APScheduler**: Reliable background task scheduling with interval triggers
- **IngestionPipeline**: Existing pipeline for article processing
- **ChromaStore**: For deduplication checks against existing articles
- **Thread-safe Design**: Proper state management for concurrent operations

### Deduplication Strategy

The service uses a two-tier deduplication approach:

1. **In-Memory Cache**: Fast lookup of recently processed URLs
2. **ChromaDB Lookup**: Persistent check against all stored articles

This ensures:
- Fast processing of new articles
- No duplicate ingestion
- Robust handling of service restarts

### Filtering

Apply filters before ingestion to reduce processing overhead:

- **Ticker Filter**: Only process articles mentioning specified tickers
- **Keyword Filter**: Only process articles containing specified keywords
- **Category Filter**: Only process articles in specified categories

Filters use AND logic - all specified filters must match.

### Error Handling

The service includes comprehensive error handling:

- **Feed Errors**: Individual feed failures don't stop the service
- **Ingestion Errors**: Article ingestion failures are logged but don't stop polling
- **Recovery**: Service continues running after errors
- **Statistics**: Error counts tracked in statistics

### Best Practices

1. **Polling Intervals**:
   - Default 30 minutes is reasonable for most use cases
   - Shorter intervals (5-15 min) for time-sensitive news
   - Longer intervals (60+ min) to reduce resource usage

2. **Filtering**:
   - Use filters to reduce processing overhead
   - Start broad, then narrow based on needs
   - Monitor statistics to optimize filter criteria

3. **Resource Management**:
   - Monitor CPU and memory usage for long-running services
   - Consider running as a systemd service for production
   - Use pause/resume for maintenance windows

4. **Deduplication**:
   - In-memory cache grows over time (cleared on restart)
   - ChromaDB lookup ensures no duplicates across restarts
   - Monitor `processed_urls_count` in statistics

### Troubleshooting

See the [Troubleshooting](#troubleshooting) section below for common issues and solutions.

## Future Enhancements

The following enhancements are planned as separate tasks:

- **TASK-049**: News Alert System

See individual task files for details.

## Related Documentation

- [Configuration Reference](reference/configuration.md#news-aggregation-configuration-task-034)
- [News Trend Analysis Integration](news_trend_analysis.md) - Trend analysis for news articles (TASK-047) ✅
- [API Documentation](reference/api.md) (for programmatic access)
- [Ingestion Pipeline](../README.md#data-collection)

---

**Last Updated**: 2025-01-27
**Tasks**: TASK-034 (News Aggregation) ✅, TASK-046 (News Summarization) ✅, TASK-047 (News Trend Analysis) ✅, TASK-048 (Automated News Monitoring) ✅
**Status**: Complete
