"""
Social media sentiment fetcher for Reddit and Twitter/X.

Fetches posts and tweets from social media platforms and extracts
sentiment data for financial analysis.
"""

import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Optional dependencies - graceful degradation if not available
try:
    import praw

    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    logger.warning("praw library not available. Reddit fetching will be disabled.")

try:
    import tweepy

    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    logger.warning("tweepy library not available. Twitter/X fetching will be disabled.")

# Try to import sentiment analyzer
try:
    from app.ingestion.sentiment_analyzer import SentimentAnalyzer

    SENTIMENT_ANALYZER_AVAILABLE = True
except ImportError:
    SENTIMENT_ANALYZER_AVAILABLE = False
    logger.warning(
        "SentimentAnalyzer not available. Sentiment analysis will be disabled."
    )


class SocialMediaFetcherError(Exception):
    """Custom exception for social media fetcher errors."""

    pass


class SocialMediaFetcher:
    """
    Social media sentiment fetcher.

    Fetches posts from Reddit and tweets from Twitter/X,
    extracts financial sentiment, and converts to documents.
    """

    # Ticker symbol pattern (1-5 uppercase letters)
    TICKER_PATTERN = re.compile(r"\b([A-Z]{1,5})\b")

    # Common words to filter (avoid false positives)
    COMMON_WORDS = {
        "THE",
        "AND",
        "FOR",
        "ARE",
        "BUT",
        "NOT",
        "YOU",
        "ALL",
        "CAN",
        "HER",
        "WAS",
        "ONE",
        "OUR",
        "OUT",
        "DAY",
        "GET",
        "HAS",
        "HIM",
        "HIS",
        "HOW",
        "ITS",
        "MAY",
        "NEW",
        "NOW",
        "OLD",
        "SEE",
        "TWO",
        "WHO",
        "WAY",
        "USE",
    }

    def __init__(
        self,
        reddit_enabled: bool = True,
        twitter_enabled: bool = True,
        sentiment_enabled: bool = True,
        rate_limit_delay: float = 1.0,
    ):
        """
        Initialize social media fetcher.

        Args:
            reddit_enabled: Whether to enable Reddit fetching (default: True)
            twitter_enabled: Whether to enable Twitter/X fetching (default: True)
            sentiment_enabled: Whether to analyze sentiment (default: True)
            rate_limit_delay: Delay between requests in seconds (default: 1.0)
        """
        self.reddit_enabled = reddit_enabled and PRAW_AVAILABLE
        self.twitter_enabled = twitter_enabled and TWEEPY_AVAILABLE
        self.sentiment_enabled = sentiment_enabled and SENTIMENT_ANALYZER_AVAILABLE
        self.rate_limit_delay = rate_limit_delay

        # Initialize Reddit client (if enabled and credentials available)
        self.reddit_client = None
        if self.reddit_enabled:
            try:
                # Reddit credentials should be in environment variables
                # REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
                # Optional: REDDIT_USERNAME, REDDIT_PASSWORD, REDDIT_REFRESH_TOKEN
                import os

                client_id = os.getenv("REDDIT_CLIENT_ID")
                client_secret = os.getenv("REDDIT_CLIENT_SECRET")
                user_agent = os.getenv("REDDIT_USER_AGENT", "FinancialResearch/1.0")

                if client_id and client_secret:
                    self.reddit_client = praw.Reddit(
                        client_id=client_id,
                        client_secret=client_secret,
                        user_agent=user_agent,
                        username=os.getenv("REDDIT_USERNAME"),
                        password=os.getenv("REDDIT_PASSWORD"),
                        refresh_token=os.getenv("REDDIT_REFRESH_TOKEN"),
                    )
                    logger.info("Reddit client initialized successfully")
                else:
                    logger.warning(
                        "Reddit credentials not found. Reddit fetching disabled."
                    )
                    self.reddit_enabled = False
            except Exception as e:
                logger.warning(f"Failed to initialize Reddit client: {str(e)}")
                self.reddit_enabled = False

        # Initialize Twitter client (if enabled and credentials available)
        self.twitter_client = None
        if self.twitter_enabled:
            try:
                # Twitter credentials should be in environment variables
                # TWITTER_BEARER_TOKEN (for API v2)
                # Or: TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
                #     TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
                import os

                bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
                consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
                consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
                access_token = os.getenv("TWITTER_ACCESS_TOKEN")
                access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

                if bearer_token:
                    # Use Bearer Token (simplest for API v2)
                    self.twitter_client = tweepy.Client(bearer_token=bearer_token)
                    logger.info("Twitter client initialized with Bearer Token")
                elif (
                    consumer_key
                    and consumer_secret
                    and access_token
                    and access_token_secret
                ):
                    # Use OAuth 1.0a
                    self.twitter_client = tweepy.Client(
                        consumer_key=consumer_key,
                        consumer_secret=consumer_secret,
                        access_token=access_token,
                        access_token_secret=access_token_secret,
                    )
                    logger.info("Twitter client initialized with OAuth 1.0a")
                else:
                    logger.warning(
                        "Twitter credentials not found. Twitter fetching disabled."
                    )
                    self.twitter_enabled = False
            except Exception as e:
                logger.warning(f"Failed to initialize Twitter client: {str(e)}")
                self.twitter_enabled = False

        # Initialize sentiment analyzer (if enabled)
        self.sentiment_analyzer = None
        if self.sentiment_enabled:
            try:
                self.sentiment_analyzer = SentimentAnalyzer()
                logger.info("Sentiment analyzer initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize sentiment analyzer: {str(e)}")
                self.sentiment_enabled = False

    def _extract_tickers(self, text: str) -> List[str]:
        """
        Extract ticker symbols from text.

        Args:
            text: Text to extract tickers from

        Returns:
            List of unique ticker symbols found
        """
        if not text:
            return []

        # Find all potential tickers
        matches = self.TICKER_PATTERN.findall(text.upper())
        # Filter out common words
        tickers = [
            ticker
            for ticker in set(matches)
            if ticker not in self.COMMON_WORDS and len(ticker) >= 1
        ]
        return sorted(tickers)

    def _analyze_sentiment(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis results or None if analysis fails
        """
        if not self.sentiment_enabled or not self.sentiment_analyzer:
            return None

        try:
            sentiment_result = self.sentiment_analyzer.analyze(text)
            return sentiment_result
        except Exception as e:
            logger.warning(f"Failed to analyze sentiment: {str(e)}")
            return None

    def fetch_reddit_posts(
        self,
        subreddits: Optional[List[str]] = None,
        query: Optional[str] = None,
        limit: int = 25,
        sort: str = "hot",
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from Reddit.

        Args:
            subreddits: List of subreddit names (e.g., ["stocks", "investing"])
            query: Search query (optional)
            limit: Maximum number of posts to fetch (default: 25)
            sort: Sort order ("hot", "new", "top", "rising") (default: "hot")

        Returns:
            List of post dictionaries with metadata

        Raises:
            SocialMediaFetcherError: If fetching fails
        """
        if not self.reddit_enabled or not self.reddit_client:
            logger.warning("Reddit fetching is disabled or client not initialized")
            return []

        if subreddits is None:
            subreddits = ["stocks", "investing", "SecurityAnalysis", "wallstreetbets"]

        posts = []
        try:
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit_client.subreddit(subreddit_name)

                    # Get posts based on sort order
                    if sort == "hot":
                        submissions = subreddit.hot(limit=limit)
                    elif sort == "new":
                        submissions = subreddit.new(limit=limit)
                    elif sort == "top":
                        submissions = subreddit.top(limit=limit, time_filter="day")
                    elif sort == "rising":
                        submissions = subreddit.rising(limit=limit)
                    else:
                        submissions = subreddit.hot(limit=limit)

                    for submission in submissions:
                        # Filter by query if provided
                        if query and query.lower() not in submission.title.lower():
                            continue

                        post_data = {
                            "id": submission.id,
                            "title": submission.title,
                            "content": submission.selftext or "",
                            "url": f"https://reddit.com{submission.permalink}",
                            "author": (
                                str(submission.author)
                                if submission.author
                                else "Unknown"
                            ),
                            "score": submission.score,
                            "num_comments": submission.num_comments,
                            "created_utc": datetime.fromtimestamp(
                                submission.created_utc
                            ),
                            "subreddit": subreddit_name,
                            "source": "reddit",
                            "type": "social_media_post",
                        }

                        # Extract tickers
                        full_text = f"{submission.title} {submission.selftext}"
                        post_data["tickers"] = self._extract_tickers(full_text)

                        # Analyze sentiment
                        if self.sentiment_enabled:
                            sentiment = self._analyze_sentiment(full_text)
                            if sentiment:
                                post_data["sentiment"] = sentiment

                        posts.append(post_data)

                    # Rate limiting
                    time.sleep(self.rate_limit_delay)

                except Exception as e:
                    logger.warning(
                        f"Failed to fetch from subreddit {subreddit_name}: {str(e)}"
                    )
                    continue

            logger.info(f"Fetched {len(posts)} Reddit posts")
            return posts

        except Exception as e:
            logger.error(f"Failed to fetch Reddit posts: {str(e)}", exc_info=True)
            raise SocialMediaFetcherError(
                f"Failed to fetch Reddit posts: {str(e)}"
            ) from e

    def fetch_twitter_tweets(
        self,
        query: str,
        max_results: int = 25,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch tweets from Twitter/X.

        Args:
            query: Search query (e.g., "$AAPL earnings")
            max_results: Maximum number of tweets to fetch (default: 25)
            start_time: Start time for search (optional)
            end_time: End time for search (optional)

        Returns:
            List of tweet dictionaries with metadata

        Raises:
            SocialMediaFetcherError: If fetching fails
        """
        if not self.twitter_enabled or not self.twitter_client:
            logger.warning("Twitter fetching is disabled or client not initialized")
            return []

        tweets = []
        try:
            # Convert datetime to ISO format if provided
            start_time_str = start_time.isoformat() if start_time else None
            end_time_str = end_time.isoformat() if end_time else None

            # Search recent tweets (last 7 days)
            response = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),  # API limit is 100
                start_time=start_time_str,
                end_time=end_time_str,
                tweet_fields=["created_at", "author_id", "public_metrics", "text"],
            )

            if not response.data:
                logger.info(f"No tweets found for query: {query}")
                return []

            # Get user information for author names
            user_ids = list(
                {tweet.author_id for tweet in response.data if tweet.author_id}
            )
            users = {}
            if user_ids:
                try:
                    user_response = self.twitter_client.get_users(ids=user_ids)
                    if user_response.data:
                        users = {user.id: user.username for user in user_response.data}
                except Exception as e:
                    logger.warning(f"Failed to fetch user information: {str(e)}")

            for tweet in response.data:
                tweet_data = {
                    "id": tweet.id,
                    "text": tweet.text,
                    "url": f"https://twitter.com/i/web/status/{tweet.id}",
                    "author": users.get(tweet.author_id, "Unknown"),
                    "author_id": tweet.author_id,
                    "created_at": tweet.created_at,
                    "retweet_count": (
                        tweet.public_metrics.get("retweet_count", 0)
                        if tweet.public_metrics
                        else 0
                    ),
                    "like_count": (
                        tweet.public_metrics.get("like_count", 0)
                        if tweet.public_metrics
                        else 0
                    ),
                    "reply_count": (
                        tweet.public_metrics.get("reply_count", 0)
                        if tweet.public_metrics
                        else 0
                    ),
                    "source": "twitter",
                    "type": "social_media_post",
                }

                # Extract tickers
                tweet_data["tickers"] = self._extract_tickers(tweet.text)

                # Analyze sentiment
                if self.sentiment_enabled:
                    sentiment = self._analyze_sentiment(tweet.text)
                    if sentiment:
                        tweet_data["sentiment"] = sentiment

                tweets.append(tweet_data)

            # Rate limiting
            time.sleep(self.rate_limit_delay)

            logger.info(f"Fetched {len(tweets)} Twitter tweets")
            return tweets

        except Exception as e:
            logger.error(f"Failed to fetch Twitter tweets: {str(e)}", exc_info=True)
            raise SocialMediaFetcherError(
                f"Failed to fetch Twitter tweets: {str(e)}"
            ) from e

    def to_documents(self, posts: List[Dict[str, Any]]) -> List[Document]:
        """
        Convert social media posts to LangChain Document objects.

        Args:
            posts: List of post dictionaries

        Returns:
            List of Document objects
        """
        documents = []
        for post in posts:
            # Create document content
            if post["source"] == "reddit":
                content = f"Title: {post['title']}\n\n{post.get('content', '')}"
            else:  # twitter
                content = post["text"]

            # Create metadata
            metadata = {
                "source": post["source"],
                "type": post["type"],
                "url": post["url"],
                "author": post.get("author", "Unknown"),
                "created_at": (
                    post.get("created_at", datetime.now()).isoformat()
                    if isinstance(post.get("created_at"), datetime)
                    else str(post.get("created_at", ""))
                ),
            }

            # Add tickers if available
            if post.get("tickers"):
                metadata["tickers"] = ", ".join(post["tickers"])

            # Add sentiment if available
            if post.get("sentiment"):
                sentiment = post["sentiment"]
                if isinstance(sentiment, dict):
                    metadata["sentiment_score"] = str(
                        sentiment.get("overall_score", "")
                    )
                    metadata["sentiment_label"] = sentiment.get("overall_label", "")

            # Add platform-specific metadata
            if post["source"] == "reddit":
                metadata["subreddit"] = post.get("subreddit", "")
                metadata["score"] = str(post.get("score", 0))
                metadata["num_comments"] = str(post.get("num_comments", 0))
            elif post["source"] == "twitter":
                metadata["retweet_count"] = str(post.get("retweet_count", 0))
                metadata["like_count"] = str(post.get("like_count", 0))
                metadata["reply_count"] = str(post.get("reply_count", 0))

            document = Document(page_content=content, metadata=metadata)
            documents.append(document)

        return documents
