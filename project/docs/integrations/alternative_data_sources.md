# Alternative Data Sources Integration

## Overview

The Financial Research Assistant includes comprehensive alternative data sources integration that fetches, analyzes, and indexes data from social media platforms, ESG providers, and alternative data sources. This integration enables the RAG system to answer questions about social sentiment, ESG ratings, hiring signals, supply chain activity, and IPO/secondary offering information.

## Features

### Social Media Sentiment
- **Reddit Integration**: Fetch posts from financial subreddits with sentiment analysis
- **Twitter/X Integration**: Fetch tweets with financial sentiment analysis
- **Ticker Detection**: Automatic extraction of ticker symbols from posts/tweets
- **Sentiment Analysis**: Integration with financial sentiment analyzer
- **Metadata Tagging**: Rich metadata including source, author, engagement metrics

### ESG Data
- **MSCI ESG Ratings**: Framework for MSCI ESG ratings integration
- **Sustainalytics Data**: Framework for Sustainalytics ESG data integration
- **CDP Climate Data**: Framework for CDP climate disclosure integration
- **Multi-Provider Support**: Fetch ESG data from multiple providers simultaneously
- **Rating Metadata**: Store ESG ratings, scores, and risk levels

### Alternative Data
- **LinkedIn Job Postings**: Framework for hiring signal analysis
- **Supply Chain Data**: Framework for port activity and shipping data
- **Form S-1 Filings**: IPO and secondary offering data from SEC EDGAR
- **Ticker Association**: Link alternative data to specific companies

## Supported Data Sources

### Social Media Platforms

#### Reddit
- **Subreddits**: stocks, investing, SecurityAnalysis, wallstreetbets
- **Authentication**: OAuth 2.0 (requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
- **Rate Limiting**: Configurable rate limits (default: 1.0 seconds)
- **Features**: Post fetching, ticker extraction, sentiment analysis

#### Twitter/X
- **Authentication**: Bearer Token or OAuth 1.0a (requires TWITTER_BEARER_TOKEN or OAuth credentials)
- **API Version**: Twitter API v2
- **Rate Limiting**: Configurable rate limits (default: 1.0 seconds)
- **Features**: Tweet search, ticker extraction, sentiment analysis, engagement metrics

### ESG Providers

#### MSCI ESG Ratings
- **Authentication**: API Key (requires MSCI_ESG_API_KEY)
- **Data**: ESG ratings, scores, categories
- **Status**: Framework implemented (requires API subscription)

#### Sustainalytics
- **Authentication**: API Key (requires SUSTAINALYTICS_API_KEY)
- **Data**: ESG ratings, scores, risk levels
- **Status**: Framework implemented (requires API subscription)

#### CDP (Carbon Disclosure Project)
- **Authentication**: API Key (requires CDP_API_KEY)
- **Data**: Climate disclosure scores, performance scores, leadership levels
- **Status**: Framework implemented (requires API subscription)

### Alternative Data Sources

#### LinkedIn Job Postings
- **Authentication**: API Key (requires LINKEDIN_API_KEY)
- **Data**: Job postings, company information, hiring signals
- **Status**: Framework implemented (requires API access)

#### Supply Chain Data
- **Authentication**: API Key (requires SUPPLY_CHAIN_API_KEY)
- **Data**: Port activity, shipping data, cargo information
- **Status**: Framework implemented (requires API subscription)

#### Form S-1 (SEC EDGAR)
- **Authentication**: None required (free public API)
- **Data**: IPO filings, secondary offering documents
- **Status**: Fully implemented (uses existing EDGAR fetcher)

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# Social Media Configuration
SOCIAL_MEDIA_ENABLED=true
SOCIAL_MEDIA_REDDIT_ENABLED=true
SOCIAL_MEDIA_TWITTER_ENABLED=true
SOCIAL_MEDIA_SENTIMENT_ENABLED=true
SOCIAL_MEDIA_RATE_LIMIT=1.0

# Reddit Credentials
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=YourApp/1.0
REDDIT_USERNAME=your_username  # Optional
REDDIT_PASSWORD=your_password  # Optional
REDDIT_REFRESH_TOKEN=your_refresh_token  # Optional

# Twitter/X Credentials
TWITTER_BEARER_TOKEN=your_bearer_token
# OR use OAuth 1.0a:
TWITTER_CONSUMER_KEY=your_consumer_key
TWITTER_CONSUMER_SECRET=your_consumer_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# ESG Configuration
ESG_ENABLED=true
ESG_MSCI_ENABLED=true
ESG_SUSTAINALYTICS_ENABLED=true
ESG_CDP_ENABLED=true
ESG_RATE_LIMIT=1.0

# ESG Provider Credentials
MSCI_ESG_API_KEY=your_api_key
MSCI_ESG_BASE_URL=https://api.msci.com  # Optional
SUSTAINALYTICS_API_KEY=your_api_key
SUSTAINALYTICS_BASE_URL=https://api.sustainalytics.com  # Optional
CDP_API_KEY=your_api_key
CDP_BASE_URL=https://api.cdp.net  # Optional

# Alternative Data Configuration
ALTERNATIVE_DATA_ENABLED=true
ALTERNATIVE_DATA_LINKEDIN_ENABLED=true
ALTERNATIVE_DATA_SUPPLY_CHAIN_ENABLED=true
ALTERNATIVE_DATA_IPO_ENABLED=true
ALTERNATIVE_DATA_RATE_LIMIT=1.0

# Alternative Data Credentials
LINKEDIN_API_KEY=your_api_key
LINKEDIN_BASE_URL=https://api.linkedin.com/v2  # Optional
SUPPLY_CHAIN_API_KEY=your_api_key
SUPPLY_CHAIN_BASE_URL=https://api.supplychain.com  # Optional
```

## Usage

### Programmatic Usage

#### Social Media Sentiment

```python
from app.ingestion.pipeline import IngestionPipeline

# Create pipeline
pipeline = IngestionPipeline()

# Process Reddit posts
chunk_ids = pipeline.process_social_media(
    subreddits=["stocks", "investing", "SecurityAnalysis"],
    limit=25,
    store_embeddings=True
)

# Process Twitter tweets
chunk_ids = pipeline.process_social_media(
    twitter_query="$AAPL earnings",
    limit=25,
    store_embeddings=True
)

# Process both Reddit and Twitter
chunk_ids = pipeline.process_social_media(
    subreddits=["stocks", "investing"],
    twitter_query="$MSFT revenue",
    limit=25
)
```

#### Direct Fetcher Usage (Social Media)

```python
from app.ingestion.social_media_fetcher import SocialMediaFetcher

# Initialize fetcher
fetcher = SocialMediaFetcher(
    reddit_enabled=True,
    twitter_enabled=True,
    sentiment_enabled=True,
    rate_limit_delay=1.0
)

# Fetch Reddit posts
reddit_posts = fetcher.fetch_reddit_posts(
    subreddits=["stocks", "investing"],
    query="AAPL",  # Optional filter
    limit=25,
    sort="hot"  # "hot", "new", "top", "rising"
)

# Fetch Twitter tweets
twitter_tweets = fetcher.fetch_twitter_tweets(
    query="$AAPL earnings",
    max_results=25,
    start_time=None,  # Optional datetime
    end_time=None     # Optional datetime
)

# Convert to documents
documents = fetcher.to_documents(reddit_posts + twitter_tweets)
```

#### ESG Data

```python
from app.ingestion.pipeline import IngestionPipeline

# Create pipeline
pipeline = IngestionPipeline()

# Process ESG data for multiple tickers
chunk_ids = pipeline.process_esg_data(
    tickers=["AAPL", "MSFT", "GOOGL", "AMZN"],
    providers=["msci", "sustainalytics", "cdp"],  # Optional, uses all enabled if None
    store_embeddings=True
)
```

#### Direct Fetcher Usage (ESG)

```python
from app.ingestion.esg_fetcher import ESGFetcher

# Initialize fetcher
fetcher = ESGFetcher(
    msci_enabled=True,
    sustainalytics_enabled=True,
    cdp_enabled=True,
    rate_limit_delay=1.0
)

# Fetch ESG data for a single ticker
msci_rating = fetcher.fetch_msci_esg_rating("AAPL")
sustainalytics_rating = fetcher.fetch_sustainalytics_rating("AAPL")
cdp_data = fetcher.fetch_cdp_data("AAPL")

# Fetch ESG data for multiple tickers
esg_data = fetcher.fetch_esg_data(
    tickers=["AAPL", "MSFT", "GOOGL"],
    providers=["msci", "sustainalytics", "cdp"]
)

# Convert to documents
documents = fetcher.to_documents(esg_data)
```

#### Alternative Data

```python
from app.ingestion.pipeline import IngestionPipeline

# Create pipeline
pipeline = IngestionPipeline()

# Process alternative data
chunk_ids = pipeline.process_alternative_data(
    tickers=["AAPL", "MSFT"],
    linkedin_company="Apple Inc.",  # Optional
    form_s1_limit=10,
    store_embeddings=True
)
```

#### Direct Fetcher Usage (Alternative Data)

```python
from app.ingestion.alternative_data_fetcher import AlternativeDataFetcher

# Initialize fetcher
fetcher = AlternativeDataFetcher(
    linkedin_enabled=True,
    supply_chain_enabled=True,
    ipo_enabled=True,
    rate_limit_delay=1.0
)

# Fetch LinkedIn jobs
linkedin_jobs = fetcher.fetch_linkedin_jobs(
    company="Apple Inc.",
    ticker="AAPL",  # Optional
    limit=25
)

# Fetch supply chain data
supply_chain_data = fetcher.fetch_supply_chain_data(
    ticker="AAPL",
    port=None  # Optional port filter
)

# Fetch Form S-1 filings
form_s1_filings = fetcher.fetch_form_s1_filings(
    ticker="AAPL",
    limit=10
)

# Convert to documents
documents = fetcher.to_documents(linkedin_jobs + supply_chain_data + form_s1_filings)
```

## Data Structure

### Social Media Posts

```python
{
    "id": "post_id",
    "title": "Post Title",  # Reddit only
    "content": "Post content",  # Reddit only
    "text": "Tweet text",  # Twitter only
    "url": "https://reddit.com/...",
    "author": "username",
    "created_at": "2025-01-27T12:00:00",
    "source": "reddit" | "twitter",
    "type": "social_media_post",
    "tickers": ["AAPL", "MSFT"],
    "sentiment": {
        "overall_score": 0.75,
        "overall_label": "positive",
        # ... additional sentiment metrics
    },
    # Reddit-specific
    "subreddit": "stocks",
    "score": 100,
    "num_comments": 50,
    # Twitter-specific
    "retweet_count": 10,
    "like_count": 25,
    "reply_count": 5
}
```

### ESG Data

```python
{
    "provider": "MSCI" | "Sustainalytics" | "CDP",
    "ticker": "AAPL",
    "rating": "AAA",  # MSCI/Sustainalytics
    "score": 85,  # Numeric score
    "category": "Technology",  # MSCI
    "risk_level": "Low",  # Sustainalytics
    "disclosure_score": 90,  # CDP
    "performance_score": 85,  # CDP
    "leadership_level": "A",  # CDP
    "last_updated": "2025-01-27T12:00:00",
    "source": "msci_esg" | "sustainalytics_esg" | "cdp_climate",
    "type": "esg_rating"
}
```

### Alternative Data

#### LinkedIn Job Postings

```python
{
    "id": "job_id",
    "title": "Software Engineer",
    "company": "Apple Inc.",
    "location": "Cupertino, CA",
    "description": "Job description...",
    "posted_date": "2025-01-27T12:00:00",
    "url": "https://linkedin.com/jobs/...",
    "source": "linkedin",
    "type": "job_posting",
    "tickers": ["AAPL"]
}
```

#### Supply Chain Data

```python
{
    "id": "activity_id",
    "port": "Los Angeles",
    "vessel": "Ship Name",
    "cargo": "Electronics",
    "date": "2025-01-27T12:00:00",
    "ticker": "AAPL",
    "source": "supply_chain",
    "type": "supply_chain_activity"
}
```

#### Form S-1 Filings

```python
{
    "accession_number": "0001234567-25-000001",
    "filing_date": "2025-01-27",
    "form_type": "S-1",
    "ticker": "AAPL",
    "cik": "0000320193",
    "content": "Filing content...",
    "url": "https://sec.gov/Archives/edgar/data/...",
    "source": "edgar",
    "type": "form_s1"
}
```

## Document Metadata

All alternative data sources are converted to LangChain Document objects with rich metadata:

### Social Media Documents

```python
{
    "source": "reddit" | "twitter",
    "type": "social_media_post",
    "url": "...",
    "author": "...",
    "created_at": "...",
    "tickers": "AAPL, MSFT",  # Comma-separated
    "sentiment_score": "0.75",
    "sentiment_label": "positive",
    # Reddit-specific
    "subreddit": "stocks",
    "score": "100",
    "num_comments": "50",
    # Twitter-specific
    "retweet_count": "10",
    "like_count": "25",
    "reply_count": "5"
}
```

### ESG Documents

```python
{
    "source": "msci_esg" | "sustainalytics_esg" | "cdp_climate",
    "type": "esg_rating",
    "provider": "MSCI" | "Sustainalytics" | "CDP",
    "ticker": "AAPL",
    "rating": "AAA",
    "score": "85",
    "last_updated": "..."
}
```

### Alternative Data Documents

```python
{
    "source": "linkedin" | "supply_chain" | "edgar",
    "type": "job_posting" | "supply_chain_activity" | "form_s1",
    "date": "...",
    "ticker": "AAPL",  # If applicable
    "company": "Apple Inc.",  # LinkedIn
    "port": "Los Angeles",  # Supply chain
    "accession_number": "...",  # Form S-1
    "cik": "...",  # Form S-1
    "url": "..."  # If available
}
```

## Integration with RAG System

All alternative data sources are automatically integrated with the RAG system:

1. **Fetching**: Data is fetched from various sources
2. **Conversion**: Data is converted to LangChain Document objects
3. **Chunking**: Documents are chunked for optimal retrieval
4. **Embedding**: Chunks are embedded using configured embedding provider
5. **Storage**: Chunks are stored in ChromaDB with metadata
6. **Retrieval**: Data is retrieved during RAG queries based on relevance

### Query Examples

```python
# Query about social sentiment
response = rag_system.query("What is the current sentiment about Apple stock on Reddit?")

# Query about ESG ratings
response = rag_system.query("What are the ESG ratings for Microsoft from MSCI and Sustainalytics?")

# Query about hiring signals
response = rag_system.query("What job postings has Apple posted recently on LinkedIn?")

# Query about IPO data
response = rag_system.query("What recent Form S-1 filings are available for tech companies?")
```

## Rate Limiting

All data sources support configurable rate limiting to respect API limits and server resources:

- **Social Media**: Default 1.0 seconds between requests
- **ESG Data**: Default 1.0 seconds between requests
- **Alternative Data**: Default 1.0 seconds between requests

Configure via environment variables:
- `SOCIAL_MEDIA_RATE_LIMIT`
- `ESG_RATE_LIMIT`
- `ALTERNATIVE_DATA_RATE_LIMIT`

## Error Handling

All fetchers implement comprehensive error handling:

- **Graceful Degradation**: Fetchers disable themselves if credentials are missing
- **API Errors**: Network and API errors are caught and logged
- **Rate Limit Handling**: Automatic rate limiting to prevent API throttling
- **Missing Data**: Handles cases where no data is available

## API Requirements

### Required API Keys/Subscriptions

Most data sources require API keys or subscriptions:

- **Reddit**: Free (requires OAuth app registration)
- **Twitter/X**: Requires Twitter Developer account (free tier available)
- **MSCI ESG**: Requires paid subscription
- **Sustainalytics**: Requires paid subscription
- **CDP**: Requires paid subscription
- **LinkedIn**: Requires LinkedIn API access
- **Supply Chain**: Requires paid API subscription
- **Form S-1**: Free (SEC EDGAR public API)

### Getting API Keys

1. **Reddit**: Create OAuth app at https://www.reddit.com/prefs/apps
2. **Twitter/X**: Apply for developer account at https://developer.twitter.com
3. **ESG Providers**: Contact providers for API access and pricing
4. **LinkedIn**: Apply for LinkedIn API access
5. **Supply Chain**: Contact data providers for API access

## Best Practices

1. **Rate Limiting**: Always configure appropriate rate limits to respect API terms
2. **Credential Security**: Store all API keys in `.env` file (never commit to git)
3. **Error Handling**: Implement retry logic for transient failures
4. **Data Validation**: Validate fetched data before processing
5. **Monitoring**: Monitor API usage and costs
6. **Caching**: Consider caching frequently accessed data
7. **Compliance**: Ensure compliance with API terms of service

## Limitations

1. **API Availability**: Some data sources require paid subscriptions
2. **Rate Limits**: API rate limits may restrict data volume
3. **Data Freshness**: Data freshness depends on source update frequency
4. **Coverage**: Not all companies may have data available from all sources
5. **Framework Status**: Some integrations are frameworks requiring API-specific implementation

## Troubleshooting

### Reddit Authentication Issues

- Verify `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` are correct
- Check `REDDIT_USER_AGENT` is properly formatted
- Ensure OAuth app has correct permissions

### Twitter Authentication Issues

- Verify `TWITTER_BEARER_TOKEN` is valid
- Check Twitter Developer account status
- Ensure API v2 access is enabled

### ESG Data Not Available

- Verify API keys are correct and active
- Check subscription status with provider
- Confirm API endpoints are accessible

### No Data Returned

- Check if data sources are enabled in configuration
- Verify API credentials are valid
- Check rate limiting isn't too aggressive
- Review logs for error messages

## Related Documentation

- [News Aggregation Integration](news_aggregation.md)
- [Sentiment Analysis Integration](sentiment_analysis.md)
- [EDGAR Integration](edgar_integration.md)
- [yfinance Integration](yfinance_integration.md)

## Examples

See `scripts/` directory for example scripts:
- `fetch_social_media.py` (example - to be created)
- `fetch_esg_data.py` (example - to be created)
- `fetch_alternative_data.py` (example - to be created)

## Support

For issues or questions:
1. Check logs for error messages
2. Verify configuration and credentials
3. Review API documentation for specific providers
4. Check GitHub issues for known problems
