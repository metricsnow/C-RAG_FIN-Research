# News Trend Analysis Integration

## Overview

The News Trend Analysis module provides comprehensive trend analysis capabilities for financial news articles, enabling identification of trending topics, tickers, and patterns over time. This integration helps identify emerging market themes, track ticker popularity, and analyze news volume trends.

**Status**: Complete (TASK-047) ✅

## Features

- **Ticker Trend Analysis**: Identify trending tickers based on frequency and growth
- **Topic/Keyword Analysis**: Detect trending topics and keywords from news articles
- **Volume Trend Analysis**: Track news volume over time periods
- **Time Series Aggregation**: Support for hourly, daily, weekly, and monthly periods
- **Trend Metrics**: Calculate growth rates and momentum indicators
- **Comprehensive Reports**: Generate detailed trend reports with multiple metrics
- **Date Range Filtering**: Analyze trends for specific time periods
- **Configurable Analysis**: Customize top N results, minimum mentions, and word length

## Usage

### Command-Line Usage

#### Generate Trend Report

```bash
# Generate daily trend report for last 7 days
python scripts/analyze_news_trends.py --days 7

# Generate weekly trend report for specific date range
python scripts/analyze_news_trends.py \
  --date-from 2024-01-01 \
  --date-to 2024-01-31 \
  --period weekly

# Generate report with top 20 tickers and topics
python scripts/analyze_news_trends.py \
  --days 30 \
  --top-tickers 20 \
  --top-topics 20 \
  --period daily

# Output to JSON file
python scripts/analyze_news_trends.py \
  --days 7 \
  --format json \
  --output trends_report.json
```

#### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--date-from` | Start date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) | None |
| `--date-to` | End date (ISO format) | None |
| `--days` | Number of days to analyze (from today backwards) | None |
| `--period` | Time period: `hourly`, `daily`, `weekly`, `monthly` | `daily` |
| `--top-tickers` | Number of top trending tickers to include | `10` |
| `--top-topics` | Number of top trending topics to include | `10` |
| `--format` | Output format: `text` or `json` | `text` |
| `--output` | Output file path (optional) | stdout |

### Python API Usage

#### Basic Trend Analysis

```python
from app.analysis.news_trends import NewsTrendsAnalyzer

# Initialize analyzer
analyzer = NewsTrendsAnalyzer()

# Get news articles
articles = analyzer.get_news_articles(
    date_from="2024-01-01",
    date_to="2024-01-31"
)

# Analyze ticker trends
ticker_trends = analyzer.analyze_ticker_trends(
    articles,
    period="daily",
    top_n=10
)

# Analyze topic trends
topic_trends = analyzer.analyze_topic_trends(
    articles,
    period="daily",
    top_n=10
)

# Analyze volume trends
volume_trends = analyzer.analyze_volume_trends(
    articles,
    period="daily"
)
```

#### Get Trending Tickers and Topics

```python
# Get top trending tickers
trending_tickers = analyzer.get_trending_tickers(
    articles,
    period="daily",
    top_n=10,
    min_mentions=2
)

# Get top trending topics
trending_topics = analyzer.get_trending_topics(
    articles,
    period="daily",
    top_n=10,
    min_mentions=3
)

# Print results
for ticker_data in trending_tickers:
    print(f"{ticker_data['ticker']}: "
          f"Total={ticker_data['total_count']}, "
          f"Recent={ticker_data['recent_count']}, "
          f"Growth={ticker_data['growth_rate']:.1%}")
```

#### Generate Comprehensive Trend Report

```python
# Generate complete trend report
report = analyzer.generate_trend_report(
    date_from="2024-01-01",
    date_to="2024-01-31",
    period="daily",
    top_tickers=10,
    top_topics=10
)

# Access report components
print(f"Total Articles: {report['total_articles']}")
print(f"Trending Tickers: {len(report['trending_tickers'])}")
print(f"Trending Topics: {len(report['trending_topics'])}")

# Access DataFrames
ticker_trends_df = report['ticker_trends']
topic_trends_df = report['topic_trends']
volume_trends_df = report['volume_trends']
```

#### Custom ChromaDB Collection

```python
from app.vector_db.chroma_store import ChromaStore

# Use custom collection
custom_store = ChromaStore(collection_name="news_collection")
analyzer = NewsTrendsAnalyzer(chroma_store=custom_store)

# Analyze trends from custom collection
articles = analyzer.get_news_articles()
trends = analyzer.analyze_ticker_trends(articles, period="daily")
```

## Configuration

News trend analysis is configured via environment variables in `.env`:

```bash
# Enable/disable news trend analysis
NEWS_TRENDS_ENABLED=true

# Default time period for trend analysis
NEWS_TRENDS_DEFAULT_PERIOD=daily  # Options: hourly, daily, weekly, monthly

# Default number of top results (applies to both tickers and topics)
NEWS_TRENDS_DEFAULT_TOP_N=10

# Minimum word length for keyword extraction
NEWS_TRENDS_MIN_WORD_LENGTH=4
```

### Configuration Options

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `NEWS_TRENDS_ENABLED` | boolean | `true` | Enable/disable news trend analysis |
| `NEWS_TRENDS_DEFAULT_PERIOD` | string | `daily` | Default time period (`hourly`, `daily`, `weekly`, `monthly`) |
| `NEWS_TRENDS_DEFAULT_TOP_N` | integer | `10` | Default number of top trending items (1-100) |
| `NEWS_TRENDS_MIN_WORD_LENGTH` | integer | `4` | Minimum word length for keywords (2-20) |

**Note**: The `min_mentions` parameter is configurable per API call or script invocation, not via environment variables.

## Architecture

### Components

1. **NewsTrendsAnalyzer** (`app/analysis/news_trends.py`):
   - Main trend analysis class
   - Retrieves news articles from ChromaDB
   - Performs ticker, topic, and volume trend analysis
   - Generates comprehensive trend reports

2. **Trend Analysis Script** (`scripts/analyze_news_trends.py`):
   - Command-line interface for trend analysis
   - Supports text and JSON output formats
   - Date range filtering and period selection

### Data Flow

```
ChromaDB News Articles
    ↓
NewsTrendsAnalyzer.get_news_articles()
    ↓
Article Retrieval with Date Filtering
    ↓
Ticker Trend Analysis
Topic Trend Analysis
Volume Trend Analysis
    ↓
Time Series Aggregation (hourly/daily/weekly/monthly)
    ↓
Trend Metrics Calculation (growth rate, momentum)
    ↓
Trend Report Generation
```

## Trend Analysis Methods

### Ticker Trend Analysis

Analyzes ticker symbol mentions over time:

- **Frequency Analysis**: Counts ticker mentions per time period
- **Growth Rate**: Calculates period-over-period change
- **Momentum**: Rolling average of growth rate
- **Top Tickers**: Identifies most frequently mentioned tickers

**Example Output**:
```
Period: 2024-01-15
Ticker: AAPL
Count: 25
Growth Rate: 15.3%
Momentum: 12.1%
```

### Topic/Keyword Analysis

Analyzes trending topics and keywords:

- **Keyword Extraction**: Extracts keywords from article titles and content
- **Stop Word Filtering**: Filters common words (the, and, for, etc.)
- **Frequency Tracking**: Counts keyword mentions per time period
- **Growth Metrics**: Calculates growth rate and momentum
- **Top Topics**: Identifies most frequently mentioned topics

**Example Output**:
```
Period: 2024-01-15
Keyword: earnings
Count: 18
Growth Rate: 22.5%
Momentum: 18.3%
```

### Volume Trend Analysis

Analyzes news article volume over time:

- **Volume Counting**: Counts articles per time period
- **Growth Rate**: Calculates period-over-period volume change
- **Peak Detection**: Identifies peak activity periods

**Example Output**:
```
Period: 2024-01-15
Volume: 45
Growth Rate: 8.2%
```

## Time Periods

### Supported Periods

- **Hourly**: Aggregates trends by hour
- **Daily**: Aggregates trends by day (default)
- **Weekly**: Aggregates trends by week
- **Monthly**: Aggregates trends by month

### Period Selection

Choose the appropriate period based on analysis needs:

- **Hourly**: Real-time monitoring, intraday analysis
- **Daily**: Daily market analysis, short-term trends
- **Weekly**: Weekly market summaries, medium-term trends
- **Monthly**: Monthly reports, long-term trends

## Trend Metrics

### Growth Rate

Calculates period-over-period percentage change:

```
Growth Rate = (Current Period - Previous Period) / Previous Period
```

### Momentum

Rolling average of growth rate over multiple periods:

```
Momentum = Average(Growth Rate over last N periods)
```

Default window: 3 periods

## Report Format

### Text Report

Human-readable text format with sections:

- **Header**: Period, date range, total articles
- **Top Trending Tickers**: List of trending tickers with metrics
- **Top Trending Topics**: List of trending topics with metrics
- **Volume Trends Summary**: Total, average, and peak volume

### JSON Report

Structured JSON format for programmatic access:

```json
{
  "period": "daily",
  "date_from": "2024-01-01",
  "date_to": "2024-01-31",
  "total_articles": 150,
  "trending_tickers": [
    {
      "ticker": "AAPL",
      "total_count": 45,
      "recent_count": 12,
      "growth_rate": 0.153
    }
  ],
  "trending_topics": [
    {
      "keyword": "earnings",
      "total_count": 38,
      "recent_count": 10,
      "growth_rate": 0.225
    }
  ],
  "volume_trends": [
    {
      "period": "2024-01-15",
      "volume": 45,
      "growth_rate": 0.082
    }
  ]
}
```

## Best Practices

### Date Range Selection

- **Short-term Analysis**: Use daily or hourly periods for recent trends
- **Long-term Analysis**: Use weekly or monthly periods for historical trends
- **Date Filtering**: Always specify date ranges for consistent results

### Top N Selection

- **Top Tickers**: Start with 10-20 for overview, increase for detailed analysis
- **Top Topics**: Start with 10-20, adjust based on keyword diversity
- **Performance**: Larger top N values require more processing time

### Minimum Mentions

- **Tickers**: Lower threshold (2-3) for broader coverage
- **Topics**: Higher threshold (3-5) to filter noise
- **Adjustment**: Increase to focus on significant trends only

### Period Selection

- **Real-time Monitoring**: Use hourly periods
- **Daily Analysis**: Use daily periods (most common)
- **Weekly Reports**: Use weekly periods
- **Monthly Reviews**: Use monthly periods

## Integration with News Aggregation

News trend analysis integrates seamlessly with the news aggregation system:

1. **Data Source**: Analyzes articles stored by news aggregation (TASK-034)
2. **Metadata Usage**: Leverages ticker, category, and date metadata
3. **Summarization**: Can analyze summarized articles (TASK-046)
4. **Pipeline**: Works with existing ChromaDB collections

## Use Cases

### Market Sentiment Analysis

Identify trending tickers to gauge market sentiment:

```python
trending = analyzer.get_trending_tickers(articles, period="daily", top_n=20)
# Analyze which companies are getting most attention
```

### Topic Discovery

Discover emerging topics and themes:

```python
topics = analyzer.get_trending_topics(articles, period="weekly", top_n=15)
# Identify new market themes and trends
```

### Volume Monitoring

Monitor news volume trends:

```python
volume = analyzer.analyze_volume_trends(articles, period="daily")
# Track news activity levels over time
```

### Comprehensive Reporting

Generate complete trend reports for analysis:

```python
report = analyzer.generate_trend_report(
    date_from="2024-01-01",
    date_to="2024-01-31",
    period="daily"
)
# Use for market analysis, reporting, and insights
```

## Performance Considerations

### Large Datasets

- **Date Filtering**: Always use date ranges to limit data processing
- **Top N Limits**: Use reasonable top N values (10-50) for performance
- **Period Selection**: Daily/weekly periods are more efficient than hourly

### Caching

- **Report Caching**: Cache trend reports for frequently accessed periods
- **Data Refresh**: Refresh data periodically for real-time analysis

### Optimization

- **Batch Processing**: Process multiple date ranges in batches
- **Parallel Analysis**: Run different period analyses in parallel if needed

## Error Handling

The trend analysis module includes comprehensive error handling:

- **Empty Data**: Gracefully handles empty article lists
- **Date Parsing**: Handles various date formats and missing dates
- **ChromaDB Errors**: Proper error messages for database issues
- **Missing Metadata**: Handles missing ticker, date, or category metadata

## Testing

Comprehensive test coverage:

- **Unit Tests**: 25 tests covering core functionality
- **Integration Tests**: 12 tests with real ChromaDB data
- **Test Files**: `tests/test_news_trends.py`, `tests/test_news_trends_integration.py`

Run tests:
```bash
# Unit tests
pytest tests/test_news_trends.py -v

# Integration tests
pytest tests/test_news_trends_integration.py -v

# All tests
pytest tests/test_news_trends.py tests/test_news_trends_integration.py -v
```

## Future Enhancements

The following enhancements are planned:

- **TASK-048**: Automated News Monitoring (for real-time trend updates)
- **TASK-049**: News Alert System (for trend-based alerts)
- **Real-time Updates**: Continuous trend monitoring
- **Visualization**: Charts and graphs for trend visualization
- **ML-based Prediction**: Machine learning for trend prediction
- **Export Formats**: CSV, Excel export options

## API Endpoints

The news trend analysis feature includes RESTful API endpoints for programmatic access:

### Get Trending Tickers

```http
GET /api/v1/trends/tickers
```

**Query Parameters**:
- `period` (optional): Time period (`hourly`, `daily`, `weekly`, `monthly`) - defaults to config
- `top_n` (optional): Number of top tickers (1-100) - defaults to config
- `date_from` (optional): Start date (ISO format)
- `date_to` (optional): End date (ISO format)
- `min_mentions` (optional): Minimum mentions threshold (default: 2)

**Response**:
```json
[
  {
    "ticker": "AAPL",
    "total_count": 45,
    "recent_count": 12,
    "growth_rate": 0.153
  }
]
```

### Get Trending Topics

```http
GET /api/v1/trends/topics
```

**Query Parameters**:
- `period` (optional): Time period - defaults to config
- `top_n` (optional): Number of top topics (1-100) - defaults to config
- `date_from` (optional): Start date (ISO format)
- `date_to` (optional): End date (ISO format)
- `min_mentions` (optional): Minimum mentions threshold (default: 3)

**Response**:
```json
[
  {
    "keyword": "earnings",
    "total_count": 38,
    "recent_count": 10,
    "growth_rate": 0.225
  }
]
```

### Get Trend Report

```http
GET /api/v1/trends/report
```

**Query Parameters**:
- `period` (optional): Time period - defaults to config
- `top_tickers` (optional): Number of top tickers (1-100) - defaults to config
- `top_topics` (optional): Number of top topics (1-100) - defaults to config
- `date_from` (optional): Start date (ISO format)
- `date_to` (optional): End date (ISO format)

**Response**:
```json
{
  "period": "daily",
  "date_from": "2024-01-01",
  "date_to": "2024-01-31",
  "total_articles": 150,
  "trending_tickers": [...],
  "trending_topics": [...],
  "volume_trends": [...]
}
```

**Authentication**: All endpoints require API key authentication (see API documentation).

**Example Usage**:
```bash
# Get trending tickers
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/trends/tickers?period=daily&top_n=10"

# Get trend report
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/trends/report?date_from=2024-01-01&date_to=2024-01-31"
```

## Related Documentation

- [News Aggregation Integration](news_aggregation.md) - News article collection
- [Configuration Reference](../reference/configuration.md#news-trend-analysis-configuration-task-047) - Configuration options
- [FastAPI Documentation](../../README.md#api-documentation) - Complete API reference

## Examples

### Example 1: Daily Trend Report

```bash
python scripts/analyze_news_trends.py --days 7 --period daily
```

Output:
```
================================================================================
NEWS TREND ANALYSIS REPORT
================================================================================

Period: daily
Date Range: 2024-01-25 to 2024-01-31
Total Articles: 45

--------------------------------------------------------------------------------
TOP TRENDING TICKERS
--------------------------------------------------------------------------------
1. AAPL: Total=25, Recent=8, Growth=15.3%
2. MSFT: Total=18, Recent=6, Growth=12.1%
3. GOOGL: Total=15, Recent=5, Growth=8.5%
...
```

### Example 2: Weekly Analysis

```python
from app.analysis.news_trends import NewsTrendsAnalyzer

analyzer = NewsTrendsAnalyzer()
articles = analyzer.get_news_articles(date_from="2024-01-01", date_to="2024-01-31")

# Weekly ticker trends
weekly_trends = analyzer.analyze_ticker_trends(articles, period="weekly", top_n=10)

# Get top trending tickers
trending = analyzer.get_trending_tickers(articles, period="weekly", top_n=10)
for ticker_data in trending:
    print(f"{ticker_data['ticker']}: {ticker_data['total_count']} mentions")
```

### Example 3: Topic Discovery

```python
analyzer = NewsTrendsAnalyzer()
articles = analyzer.get_news_articles()

# Discover trending topics
topics = analyzer.get_trending_topics(
    articles,
    period="daily",
    top_n=15,
    min_mentions=3
)

print("Top Trending Topics:")
for topic in topics:
    print(f"  {topic['keyword']}: {topic['total_count']} mentions "
          f"(Growth: {topic['growth_rate']:.1%})")
```

---

**Last Updated**: 2025-01-27
**Task**: TASK-047 (News Trend Analysis)
**Status**: Complete ✅
