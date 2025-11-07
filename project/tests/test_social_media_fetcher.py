"""
Tests for social media fetcher (Reddit and Twitter/X).

Tests social media sentiment fetching functionality.
"""

import os
from unittest.mock import MagicMock, patch

from app.ingestion.social_media_fetcher import SocialMediaFetcher


class TestSocialMediaFetcher:
    """Test suite for SocialMediaFetcher."""

    def test_init_without_credentials(self):
        """Test initialization without API credentials."""
        fetcher = SocialMediaFetcher(
            reddit_enabled=False, twitter_enabled=False, sentiment_enabled=False
        )
        assert not fetcher.reddit_enabled
        assert not fetcher.twitter_enabled
        assert not fetcher.sentiment_enabled

    def test_extract_tickers(self):
        """Test ticker extraction from text."""
        fetcher = SocialMediaFetcher(
            reddit_enabled=False, twitter_enabled=False, sentiment_enabled=False
        )
        text = "I think AAPL and MSFT are great investments"
        tickers = fetcher._extract_tickers(text)
        assert "AAPL" in tickers
        assert "MSFT" in tickers
        assert "THE" not in tickers  # Common word filtered

    def test_extract_tickers_empty(self):
        """Test ticker extraction with empty text."""
        fetcher = SocialMediaFetcher(
            reddit_enabled=False, twitter_enabled=False, sentiment_enabled=False
        )
        tickers = fetcher._extract_tickers("")
        assert tickers == []

    @patch.dict(
        os.environ,
        {"REDDIT_CLIENT_ID": "test_id", "REDDIT_CLIENT_SECRET": "test_secret"},
    )
    @patch("app.ingestion.social_media_fetcher.praw")
    def test_reddit_client_initialization(self, mock_praw):
        """Test Reddit client initialization with credentials."""
        mock_reddit = MagicMock()
        mock_praw.Reddit.return_value = mock_reddit

        SocialMediaFetcher(reddit_enabled=True, twitter_enabled=False)
        # Client should be initialized if credentials are available
        # Note: Actual initialization depends on environment variables

    @patch.dict(os.environ, {"TWITTER_BEARER_TOKEN": "test_token"})
    @patch("app.ingestion.social_media_fetcher.tweepy")
    def test_twitter_client_initialization(self, mock_tweepy):
        """Test Twitter client initialization with Bearer Token."""
        mock_client = MagicMock()
        mock_tweepy.Client.return_value = mock_client

        SocialMediaFetcher(reddit_enabled=False, twitter_enabled=True)
        # Client should be initialized if credentials are available
        # Note: Actual initialization depends on environment variables

    def test_fetch_reddit_posts_disabled(self):
        """Test Reddit fetching when disabled."""
        fetcher = SocialMediaFetcher(reddit_enabled=False, twitter_enabled=False)
        posts = fetcher.fetch_reddit_posts()
        assert posts == []

    def test_fetch_twitter_tweets_disabled(self):
        """Test Twitter fetching when disabled."""
        fetcher = SocialMediaFetcher(reddit_enabled=False, twitter_enabled=False)
        tweets = fetcher.fetch_twitter_tweets(query="test")
        assert tweets == []

    def test_to_documents_reddit(self):
        """Test conversion of Reddit posts to documents."""
        fetcher = SocialMediaFetcher(reddit_enabled=False, twitter_enabled=False)
        posts = [
            {
                "id": "test123",
                "title": "Test Post",
                "content": "This is a test post about AAPL",
                "url": "https://reddit.com/test",
                "author": "testuser",
                "score": 10,
                "num_comments": 5,
                "created_utc": "2025-01-27T12:00:00",
                "subreddit": "stocks",
                "source": "reddit",
                "type": "social_media_post",
                "tickers": ["AAPL"],
            }
        ]
        documents = fetcher.to_documents(posts)
        assert len(documents) == 1
        assert "AAPL" in documents[0].page_content
        assert documents[0].metadata["source"] == "reddit"
        assert documents[0].metadata["tickers"] == "AAPL"

    def test_to_documents_twitter(self):
        """Test conversion of Twitter tweets to documents."""
        fetcher = SocialMediaFetcher(reddit_enabled=False, twitter_enabled=False)
        tweets = [
            {
                "id": "test456",
                "text": "Great earnings from MSFT!",
                "url": "https://twitter.com/test",
                "author": "testuser",
                "created_at": "2025-01-27T12:00:00",
                "retweet_count": 5,
                "like_count": 10,
                "reply_count": 2,
                "source": "twitter",
                "type": "social_media_post",
                "tickers": ["MSFT"],
            }
        ]
        documents = fetcher.to_documents(tweets)
        assert len(documents) == 1
        assert "MSFT" in documents[0].page_content
        assert documents[0].metadata["source"] == "twitter"
        assert documents[0].metadata["tickers"] == "MSFT"

    def test_to_documents_with_sentiment(self):
        """Test document conversion with sentiment analysis."""
        fetcher = SocialMediaFetcher(reddit_enabled=False, twitter_enabled=False)
        posts = [
            {
                "id": "test789",
                "title": "Test",
                "content": "Test content",
                "url": "https://test.com",
                "author": "testuser",
                "source": "reddit",
                "type": "social_media_post",
                "tickers": [],
                "sentiment": {
                    "overall_score": 0.75,
                    "overall_label": "positive",
                },
            }
        ]
        documents = fetcher.to_documents(posts)
        assert len(documents) == 1
        assert "sentiment_score" in documents[0].metadata
        assert documents[0].metadata["sentiment_label"] == "positive"
