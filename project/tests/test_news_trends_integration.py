"""
Integration tests for news trends analysis.

Tests news trend analysis with real ChromaDB data and full workflow.
"""

import pytest
from datetime import datetime, timedelta
from langchain_core.documents import Document

from app.analysis.news_trends import NewsTrendsAnalyzer, NewsTrendsError
from app.vector_db.chroma_store import ChromaStore


@pytest.fixture
def test_trends_store(embedding_generator):
    """Create a ChromaDB store for trend analysis testing."""
    import uuid

    collection_name = f"test_trends_{uuid.uuid4().hex[:8]}"
    store = ChromaStore(collection_name=collection_name)
    yield store
    # Cleanup
    try:
        store.delete_collection()
    except Exception:
        pass


@pytest.fixture
def sample_news_articles_for_trends(embedding_generator):
    """Create sample news articles with dates and tickers for trend testing."""
    base_date = datetime(2024, 1, 1, 12, 0, 0)
    articles = []

    # Create articles over 30 days with varying tickers and topics
    for i in range(30):
        date = base_date + timedelta(days=i, hours=i % 24)
        
        # Vary tickers: AAPL more frequent in first half, MSFT in second half
        if i < 15:
            tickers = "AAPL, MSFT" if i % 3 == 0 else "AAPL"
            content = f"Apple Inc reported strong earnings growth revenue profit. "
        else:
            tickers = "MSFT, GOOGL" if i % 3 == 0 else "MSFT"
            content = f"Microsoft Corporation announced cloud services revenue growth. "

        content += f"Financial markets reacted positively to the news. Stock prices increased."

        metadata = {
            "type": "news_article",
            "title": f"Financial News Article {i}",
            "source": "reuters" if i % 2 == 0 else "bloomberg",
            "url": f"https://example.com/news_{i}",
            "author": "Financial Reporter",
            "date": date.isoformat(),
            "tickers": tickers,
            "category": "markets" if i % 2 == 0 else "earnings",
        }

        doc = Document(page_content=content, metadata=metadata)
        articles.append(doc)

    return articles


@pytest.fixture
def populated_trends_store(
    test_trends_store, sample_news_articles_for_trends, embedding_generator
):
    """Create a ChromaDB store populated with test news articles."""
    # Generate embeddings
    texts = [doc.page_content for doc in sample_news_articles_for_trends]
    embeddings = embedding_generator.embed_documents(texts)

    # Add to ChromaDB
    test_trends_store.add_documents(sample_news_articles_for_trends, embeddings)

    return test_trends_store


@pytest.mark.integration
class TestNewsTrendsIntegration:
    """Integration tests for news trends analysis with real ChromaDB data."""

    def test_get_news_articles_from_chromadb(
        self, populated_trends_store
    ):
        """Test retrieving news articles from real ChromaDB."""
        analyzer = NewsTrendsAnalyzer(chroma_store=populated_trends_store)

        articles = analyzer.get_news_articles()

        assert len(articles) == 30, "Should retrieve all 30 test articles"
        assert all("id" in a for a in articles), "All articles should have IDs"
        assert all("date" in a for a in articles), "All articles should have dates"
        assert all("tickers" in a for a in articles), "All articles should have tickers"
        assert all(
            a["metadata"].get("type") == "news_article" for a in articles
        ), "All articles should be news_article type"

    def test_get_news_articles_with_date_filter(
        self, populated_trends_store
    ):
        """Test retrieving news articles with date range filter."""
        analyzer = NewsTrendsAnalyzer(chroma_store=populated_trends_store)

        # Filter to first 10 days (inclusive)
        date_from = datetime(2024, 1, 1).isoformat()
        date_to = datetime(2024, 1, 10, 23, 59, 59).isoformat()

        articles = analyzer.get_news_articles(date_from=date_from, date_to=date_to)

        # Should retrieve articles from days 0-9 (10 days, but some may be filtered by time)
        assert len(articles) >= 9, "Should retrieve at least 9 articles in date range"
        assert len(articles) <= 10, "Should retrieve at most 10 articles in date range"
        assert all(
            date_from <= a["date_str"] <= date_to
            for a in articles
            if a.get("date_str")
        ), "All articles should be within date range"

    def test_analyze_ticker_trends_integration(
        self, populated_trends_store
    ):
        """Test ticker trend analysis with real data."""
        analyzer = NewsTrendsAnalyzer(chroma_store=populated_trends_store)

        # Get articles
        articles = analyzer.get_news_articles()

        # Analyze trends
        trends = analyzer.analyze_ticker_trends(
            articles, period="daily", top_n=5
        )

        assert isinstance(trends, type(analyzer.analyze_ticker_trends([], period="daily"))), "Should return DataFrame"
        assert len(trends) > 0, "Should have trend data"
        assert "period" in trends.columns, "Should have period column"
        assert "ticker" in trends.columns, "Should have ticker column"
        assert "count" in trends.columns, "Should have count column"
        assert "growth_rate" in trends.columns, "Should have growth_rate column"

        # Verify AAPL appears (more frequent in first half)
        tickers = trends["ticker"].unique()
        assert "AAPL" in tickers, "AAPL should appear in trends"

    def test_analyze_topic_trends_integration(
        self, populated_trends_store
    ):
        """Test topic trend analysis with real data."""
        analyzer = NewsTrendsAnalyzer(chroma_store=populated_trends_store)

        # Get articles
        articles = analyzer.get_news_articles()

        # Analyze trends
        trends = analyzer.analyze_topic_trends(
            articles, period="daily", top_n=5
        )

        assert isinstance(trends, type(analyzer.analyze_topic_trends([], period="daily"))), "Should return DataFrame"
        assert len(trends) > 0, "Should have trend data"
        assert "period" in trends.columns, "Should have period column"
        assert "keyword" in trends.columns, "Should have keyword column"
        assert "count" in trends.columns, "Should have count column"

        # Verify financial keywords appear
        keywords = trends["keyword"].unique()
        assert any(
            kw in ["revenue", "growth", "financial", "markets", "earnings"]
            for kw in keywords
        ), "Should contain financial keywords"

    def test_analyze_volume_trends_integration(
        self, populated_trends_store
    ):
        """Test volume trend analysis with real data."""
        analyzer = NewsTrendsAnalyzer(chroma_store=populated_trends_store)

        # Get articles
        articles = analyzer.get_news_articles()

        # Analyze volume trends
        trends = analyzer.analyze_volume_trends(articles, period="daily")

        assert isinstance(trends, type(analyzer.analyze_volume_trends([], period="daily"))), "Should return DataFrame"
        assert len(trends) > 0, "Should have volume trend data"
        assert "period" in trends.columns, "Should have period column"
        assert "volume" in trends.columns, "Should have volume column"
        assert "growth_rate" in trends.columns, "Should have growth_rate column"

        # Verify total volume matches article count
        total_volume = trends["volume"].sum()
        assert total_volume == len(articles), "Total volume should match article count"

    def test_get_trending_tickers_integration(
        self, populated_trends_store
    ):
        """Test getting trending tickers with real data."""
        analyzer = NewsTrendsAnalyzer(chroma_store=populated_trends_store)

        # Get articles
        articles = analyzer.get_news_articles()

        # Get trending tickers
        trending = analyzer.get_trending_tickers(
            articles, period="daily", top_n=5
        )

        assert isinstance(trending, list), "Should return list"
        assert len(trending) > 0, "Should have trending tickers"
        assert all("ticker" in t for t in trending), "All items should have ticker"
        assert all("total_count" in t for t in trending), "All items should have total_count"
        assert all("recent_count" in t for t in trending), "All items should have recent_count"
        assert all("growth_rate" in t for t in trending), "All items should have growth_rate"

        # Verify AAPL and MSFT appear
        tickers = [t["ticker"] for t in trending]
        assert "AAPL" in tickers or "MSFT" in tickers, "Should include test tickers"

    def test_get_trending_topics_integration(
        self, populated_trends_store
    ):
        """Test getting trending topics with real data."""
        analyzer = NewsTrendsAnalyzer(chroma_store=populated_trends_store)

        # Get articles
        articles = analyzer.get_news_articles()

        # Get trending topics
        trending = analyzer.get_trending_topics(
            articles, period="daily", top_n=5
        )

        assert isinstance(trending, list), "Should return list"
        assert len(trending) > 0, "Should have trending topics"
        assert all("keyword" in t for t in trending), "All items should have keyword"
        assert all("total_count" in t for t in trending), "All items should have total_count"
        assert all("recent_count" in t for t in trending), "All items should have recent_count"
        assert all("growth_rate" in t for t in trending), "All items should have growth_rate"

    def test_generate_trend_report_integration(
        self, populated_trends_store
    ):
        """Test generating complete trend report with real data."""
        analyzer = NewsTrendsAnalyzer(chroma_store=populated_trends_store)

        # Generate report
        date_from = datetime(2024, 1, 1).isoformat()
        date_to = datetime(2024, 1, 31).isoformat()

        report = analyzer.generate_trend_report(
            date_from=date_from,
            date_to=date_to,
            period="daily",
            top_tickers=5,
            top_topics=5,
        )

        assert "period" in report, "Report should have period"
        assert "date_from" in report, "Report should have date_from"
        assert "date_to" in report, "Report should have date_to"
        assert "total_articles" in report, "Report should have total_articles"
        assert "ticker_trends" in report, "Report should have ticker_trends"
        assert "topic_trends" in report, "Report should have topic_trends"
        assert "volume_trends" in report, "Report should have volume_trends"
        assert "trending_tickers" in report, "Report should have trending_tickers"
        assert "trending_topics" in report, "Report should have trending_topics"

        assert report["total_articles"] == 30, "Should analyze all 30 articles"
        assert len(report["trending_tickers"]) > 0, "Should have trending tickers"
        assert len(report["trending_topics"]) > 0, "Should have trending topics"

    def test_trend_analysis_different_periods_integration(
        self, populated_trends_store
    ):
        """Test trend analysis with different time periods."""
        analyzer = NewsTrendsAnalyzer(chroma_store=populated_trends_store)

        articles = analyzer.get_news_articles()

        for period in ["hourly", "daily", "weekly", "monthly"]:
            # Test ticker trends
            ticker_trends = analyzer.analyze_ticker_trends(
                articles, period=period, top_n=5
            )
            assert isinstance(ticker_trends, type(analyzer.analyze_ticker_trends([], period="daily"))), f"Should return DataFrame for {period}"

            # Test topic trends
            topic_trends = analyzer.analyze_topic_trends(
                articles, period=period, top_n=5
            )
            assert isinstance(topic_trends, type(analyzer.analyze_topic_trends([], period="daily"))), f"Should return DataFrame for {period}"

            # Test volume trends
            volume_trends = analyzer.analyze_volume_trends(articles, period=period)
            assert isinstance(volume_trends, type(analyzer.analyze_volume_trends([], period="daily"))), f"Should return DataFrame for {period}"

    def test_trend_analysis_with_empty_store(self, test_trends_store):
        """Test trend analysis with empty ChromaDB store."""
        analyzer = NewsTrendsAnalyzer(chroma_store=test_trends_store)

        articles = analyzer.get_news_articles()

        assert len(articles) == 0, "Should return empty list for empty store"

        # All analysis methods should handle empty data gracefully
        ticker_trends = analyzer.analyze_ticker_trends(articles, period="daily")
        assert len(ticker_trends) == 0, "Should return empty DataFrame"

        topic_trends = analyzer.analyze_topic_trends(articles, period="daily")
        assert len(topic_trends) == 0, "Should return empty DataFrame"

        volume_trends = analyzer.analyze_volume_trends(articles, period="daily")
        assert len(volume_trends) == 0, "Should return empty DataFrame"

        trending_tickers = analyzer.get_trending_tickers(articles, period="daily")
        assert trending_tickers == [], "Should return empty list"

        trending_topics = analyzer.get_trending_topics(articles, period="daily")
        assert trending_topics == [], "Should return empty list"

    def test_trend_analysis_date_filtering_integration(
        self, populated_trends_store
    ):
        """Test trend analysis with date filtering."""
        analyzer = NewsTrendsAnalyzer(chroma_store=populated_trends_store)

        # Get articles for first week (inclusive)
        date_from = datetime(2024, 1, 1).isoformat()
        date_to = datetime(2024, 1, 7, 23, 59, 59).isoformat()

        articles = analyzer.get_news_articles(date_from=date_from, date_to=date_to)

        # Should retrieve articles from days 0-6 (7 days, but some may be filtered by time)
        assert len(articles) >= 6, "Should retrieve at least 6 articles for first week"
        assert len(articles) <= 7, "Should retrieve at most 7 articles for first week"

        # Analyze trends for this period
        trends = analyzer.analyze_ticker_trends(articles, period="daily", top_n=5)

        assert len(trends) > 0, "Should have trend data for filtered period"

        # Verify all trends are within date range
        if len(trends) > 0 and "period" in trends.columns:
            # Period should be within date range
            periods = trends["period"].unique()
            for period in periods:
                if isinstance(period, datetime):
                    assert date_from <= period.isoformat() <= date_to, "Period should be within date range"

    def test_trend_report_completeness_integration(
        self, populated_trends_store
    ):
        """Test that trend report contains all required components."""
        analyzer = NewsTrendsAnalyzer(chroma_store=populated_trends_store)

        report = analyzer.generate_trend_report(
            period="daily", top_tickers=10, top_topics=10
        )

        # Verify all components are present and have data
        assert report["total_articles"] > 0, "Should have articles"
        assert isinstance(report["ticker_trends"], type(analyzer.analyze_ticker_trends([], period="daily"))), "Should have ticker_trends DataFrame"
        assert isinstance(report["topic_trends"], type(analyzer.analyze_topic_trends([], period="daily"))), "Should have topic_trends DataFrame"
        assert isinstance(report["volume_trends"], type(analyzer.analyze_volume_trends([], period="daily"))), "Should have volume_trends DataFrame"
        assert isinstance(report["trending_tickers"], list), "Should have trending_tickers list"
        assert isinstance(report["trending_topics"], list), "Should have trending_topics list"

        # Verify trending lists have expected structure
        if report["trending_tickers"]:
            ticker = report["trending_tickers"][0]
            assert "ticker" in ticker, "Trending ticker should have ticker field"
            assert "total_count" in ticker, "Trending ticker should have total_count"
            assert "recent_count" in ticker, "Trending ticker should have recent_count"
            assert "growth_rate" in ticker, "Trending ticker should have growth_rate"

        if report["trending_topics"]:
            topic = report["trending_topics"][0]
            assert "keyword" in topic, "Trending topic should have keyword field"
            assert "total_count" in topic, "Trending topic should have total_count"
            assert "recent_count" in topic, "Trending topic should have recent_count"
            assert "growth_rate" in topic, "Trending topic should have growth_rate"

