"""
Unit tests for news trends analysis module.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

from app.analysis.news_trends import NewsTrendsAnalyzer, NewsTrendsError
from app.vector_db.chroma_store import ChromaStore, ChromaStoreError


@pytest.fixture
def mock_chroma_store():
    """Create a mock ChromaStore instance."""
    store = Mock(spec=ChromaStore)
    store.collection = Mock()
    return store


@pytest.fixture
def sample_articles():
    """Create sample news articles for testing."""
    base_date = datetime(2024, 1, 1, 12, 0, 0)
    articles = []
    for i in range(20):
        date = base_date + timedelta(days=i, hours=i % 24)
        articles.append(
            {
                "id": f"article_{i}",
                "title": f"Article {i}",
                "content": f"Content about AAPL and MSFT {i}",
                "date": date,
                "date_str": date.isoformat(),
                "source": "reuters",
                "url": f"https://example.com/article_{i}",
                "author": "Author",
                "tickers": ["AAPL", "MSFT"] if i % 2 == 0 else ["GOOGL"],
                "category": "markets",
                "summary": f"Summary {i}",
                "metadata": {
                    "type": "news_article",
                    "date": date.isoformat(),
                    "tickers": "AAPL, MSFT" if i % 2 == 0 else "GOOGL",
                },
            }
        )
    return articles


@pytest.fixture
def mock_chromadb_results(sample_articles):
    """Create mock ChromaDB results."""
    ids = [a["id"] for a in sample_articles]
    metadatas = [a["metadata"] for a in sample_articles]
    documents = [a["content"] for a in sample_articles]

    return {
        "ids": ids,
        "metadatas": metadatas,
        "documents": documents,
    }


class TestNewsTrendsAnalyzer:
    """Test cases for NewsTrendsAnalyzer."""

    def test_init_with_chroma_store(self, mock_chroma_store):
        """Test initialization with provided ChromaStore."""
        analyzer = NewsTrendsAnalyzer(chroma_store=mock_chroma_store)
        assert analyzer.chroma_store == mock_chroma_store

    def test_init_without_chroma_store(self):
        """Test initialization without ChromaStore (creates new)."""
        analyzer = NewsTrendsAnalyzer()
        assert analyzer.chroma_store is not None
        assert isinstance(analyzer.chroma_store, ChromaStore)

    def test_get_news_articles_success(self, mock_chroma_store, mock_chromadb_results):
        """Test successful retrieval of news articles."""
        mock_chroma_store.collection.get.return_value = mock_chromadb_results

        analyzer = NewsTrendsAnalyzer(chroma_store=mock_chroma_store)
        articles = analyzer.get_news_articles()

        assert len(articles) == 20
        assert all("id" in a for a in articles)
        assert all("date" in a for a in articles)
        assert all("tickers" in a for a in articles)

    def test_get_news_articles_with_date_filter(
        self, mock_chroma_store, mock_chromadb_results
    ):
        """Test retrieval with date filters."""
        mock_chroma_store.collection.get.return_value = mock_chromadb_results

        analyzer = NewsTrendsAnalyzer(chroma_store=mock_chroma_store)
        date_from = datetime(2024, 1, 5).isoformat()
        date_to = datetime(2024, 1, 15).isoformat()

        articles = analyzer.get_news_articles(date_from=date_from, date_to=date_to)

        # Should filter to articles between dates
        assert all(
            date_from <= a["date_str"] <= date_to for a in articles if a.get("date_str")
        )

    def test_get_news_articles_with_limit(
        self, mock_chroma_store, mock_chromadb_results
    ):
        """Test retrieval with limit."""
        mock_chroma_store.collection.get.return_value = mock_chromadb_results

        analyzer = NewsTrendsAnalyzer(chroma_store=mock_chroma_store)
        articles = analyzer.get_news_articles(limit=5)

        assert len(articles) == 5

    def test_get_news_articles_no_collection(self, mock_chroma_store):
        """Test retrieval when collection is not initialized."""
        mock_chroma_store.collection = None

        analyzer = NewsTrendsAnalyzer(chroma_store=mock_chroma_store)

        with pytest.raises(NewsTrendsError):
            analyzer.get_news_articles()

    def test_get_news_articles_chromadb_error(self, mock_chroma_store):
        """Test handling of ChromaDB errors."""
        mock_chroma_store.collection.get.side_effect = ChromaStoreError("DB error")

        analyzer = NewsTrendsAnalyzer(chroma_store=mock_chroma_store)

        with pytest.raises(NewsTrendsError):
            analyzer.get_news_articles()

    def test_parse_tickers(self):
        """Test ticker parsing."""
        analyzer = NewsTrendsAnalyzer()

        assert analyzer._parse_tickers("AAPL, MSFT, GOOGL") == ["AAPL", "MSFT", "GOOGL"]
        assert analyzer._parse_tickers("AAPL") == ["AAPL"]
        assert analyzer._parse_tickers("") == []
        assert analyzer._parse_tickers("  AAPL  ,  MSFT  ") == ["AAPL", "MSFT"]

    def test_analyze_ticker_trends(self, sample_articles):
        """Test ticker trend analysis."""
        analyzer = NewsTrendsAnalyzer()

        trends = analyzer.analyze_ticker_trends(
            sample_articles, period="daily", top_n=5
        )

        assert isinstance(trends, pd.DataFrame)
        assert "period" in trends.columns
        assert "ticker" in trends.columns
        assert "count" in trends.columns
        assert "growth_rate" in trends.columns
        assert "momentum" in trends.columns

    def test_analyze_ticker_trends_empty(self):
        """Test ticker trend analysis with no articles."""
        analyzer = NewsTrendsAnalyzer()

        trends = analyzer.analyze_ticker_trends([], period="daily")

        assert isinstance(trends, pd.DataFrame)
        assert len(trends) == 0

    def test_analyze_topic_trends(self, sample_articles):
        """Test topic trend analysis."""
        analyzer = NewsTrendsAnalyzer()

        trends = analyzer.analyze_topic_trends(sample_articles, period="daily", top_n=5)

        assert isinstance(trends, pd.DataFrame)
        assert "period" in trends.columns
        assert "keyword" in trends.columns
        assert "count" in trends.columns
        assert "growth_rate" in trends.columns
        assert "momentum" in trends.columns

    def test_analyze_topic_trends_empty(self):
        """Test topic trend analysis with no articles."""
        analyzer = NewsTrendsAnalyzer()

        trends = analyzer.analyze_topic_trends([], period="daily")

        assert isinstance(trends, pd.DataFrame)
        assert len(trends) == 0

    def test_extract_keywords(self):
        """Test keyword extraction."""
        analyzer = NewsTrendsAnalyzer()

        # Use text with repeated words to meet minimum mention requirement
        text = (
            "Apple Inc announced earnings revenue growth profit Apple earnings revenue"
        )
        keywords = analyzer._extract_keywords(text, min_word_length=4)

        assert isinstance(keywords, list)
        # Should filter out short words and stop words
        assert all(len(k) >= 4 for k in keywords)

    def test_extract_keywords_empty(self):
        """Test keyword extraction with empty text."""
        analyzer = NewsTrendsAnalyzer()

        keywords = analyzer._extract_keywords("", min_word_length=4)

        assert keywords == []

    def test_analyze_volume_trends(self, sample_articles):
        """Test volume trend analysis."""
        analyzer = NewsTrendsAnalyzer()

        trends = analyzer.analyze_volume_trends(sample_articles, period="daily")

        assert isinstance(trends, pd.DataFrame)
        assert "period" in trends.columns
        assert "volume" in trends.columns
        assert "growth_rate" in trends.columns

    def test_analyze_volume_trends_empty(self):
        """Test volume trend analysis with no articles."""
        analyzer = NewsTrendsAnalyzer()

        trends = analyzer.analyze_volume_trends([], period="daily")

        assert isinstance(trends, pd.DataFrame)
        assert len(trends) == 0

    def test_get_trending_tickers(self, sample_articles):
        """Test getting trending tickers."""
        analyzer = NewsTrendsAnalyzer()

        trending = analyzer.get_trending_tickers(
            sample_articles, period="daily", top_n=5
        )

        assert isinstance(trending, list)
        assert all("ticker" in t for t in trending)
        assert all("total_count" in t for t in trending)
        assert all("recent_count" in t for t in trending)
        assert all("growth_rate" in t for t in trending)

    def test_get_trending_tickers_empty(self):
        """Test getting trending tickers with no articles."""
        analyzer = NewsTrendsAnalyzer()

        trending = analyzer.get_trending_tickers([], period="daily")

        assert trending == []

    def test_get_trending_topics(self, sample_articles):
        """Test getting trending topics."""
        analyzer = NewsTrendsAnalyzer()

        trending = analyzer.get_trending_topics(
            sample_articles, period="daily", top_n=5
        )

        assert isinstance(trending, list)
        assert all("keyword" in t for t in trending)
        assert all("total_count" in t for t in trending)
        assert all("recent_count" in t for t in trending)
        assert all("growth_rate" in t for t in trending)

    def test_get_trending_topics_empty(self):
        """Test getting trending topics with no articles."""
        analyzer = NewsTrendsAnalyzer()

        trending = analyzer.get_trending_topics([], period="daily")

        assert trending == []

    @patch.object(NewsTrendsAnalyzer, "get_news_articles")
    def test_generate_trend_report(self, mock_get_articles, sample_articles):
        """Test trend report generation."""
        mock_get_articles.return_value = sample_articles

        analyzer = NewsTrendsAnalyzer()

        report = analyzer.generate_trend_report(
            date_from="2024-01-01",
            date_to="2024-01-31",
            period="daily",
            top_tickers=5,
            top_topics=5,
        )

        assert "period" in report
        assert "date_from" in report
        assert "date_to" in report
        assert "total_articles" in report
        assert "ticker_trends" in report
        assert "topic_trends" in report
        assert "volume_trends" in report
        assert "trending_tickers" in report
        assert "trending_topics" in report

        assert report["total_articles"] == len(sample_articles)
        assert isinstance(report["ticker_trends"], pd.DataFrame)
        assert isinstance(report["topic_trends"], pd.DataFrame)
        assert isinstance(report["volume_trends"], pd.DataFrame)

    @patch.object(NewsTrendsAnalyzer, "get_news_articles")
    def test_generate_trend_report_no_articles(self, mock_get_articles):
        """Test trend report generation with no articles."""
        mock_get_articles.return_value = []

        analyzer = NewsTrendsAnalyzer()

        report = analyzer.generate_trend_report()

        assert report["total_articles"] == 0
        assert len(report["trending_tickers"]) == 0
        assert len(report["trending_topics"]) == 0

    def test_analyze_ticker_trends_different_periods(self, sample_articles):
        """Test ticker trend analysis with different periods."""
        analyzer = NewsTrendsAnalyzer()

        for period in ["hourly", "daily", "weekly", "monthly"]:
            trends = analyzer.analyze_ticker_trends(
                sample_articles, period=period, top_n=5
            )
            assert isinstance(trends, pd.DataFrame)

    def test_analyze_topic_trends_different_periods(self, sample_articles):
        """Test topic trend analysis with different periods."""
        analyzer = NewsTrendsAnalyzer()

        for period in ["hourly", "daily", "weekly", "monthly"]:
            trends = analyzer.analyze_topic_trends(
                sample_articles, period=period, top_n=5
            )
            assert isinstance(trends, pd.DataFrame)

    def test_analyze_volume_trends_different_periods(self, sample_articles):
        """Test volume trend analysis with different periods."""
        analyzer = NewsTrendsAnalyzer()

        for period in ["hourly", "daily", "weekly", "monthly"]:
            trends = analyzer.analyze_volume_trends(sample_articles, period=period)
            assert isinstance(trends, pd.DataFrame)
