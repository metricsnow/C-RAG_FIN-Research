"""
News trend analysis module.

Analyzes news articles to identify trending topics, tickers, and patterns
over time, providing insights into market sentiment and emerging themes.
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.utils.logger import get_logger
from app.vector_db.chroma_store import ChromaStore, ChromaStoreError

logger = get_logger(__name__)


class NewsTrendsError(Exception):
    """Custom exception for news trends analysis errors."""

    pass


class NewsTrendsAnalyzer:
    """
    News trend analysis analyzer.

    Analyzes news articles to identify trending topics, tickers, and patterns
    over time periods (hourly, daily, weekly, monthly).
    """

    # Common stop words to filter from keyword analysis
    STOP_WORDS = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "they",
        "them",
        "their",
        "there",
        "then",
        "than",
    }

    def __init__(
        self,
        chroma_store: Optional[ChromaStore] = None,
        collection_name: str = "documents",
    ):
        """
        Initialize news trends analyzer.

        Args:
            chroma_store: Optional ChromaStore instance.
                If None, creates a new instance.
            collection_name: Name of ChromaDB collection (default: "documents")
        """
        if chroma_store is None:
            self.chroma_store = ChromaStore(collection_name=collection_name)
        else:
            self.chroma_store = chroma_store

        logger.debug("Initialized NewsTrendsAnalyzer")

    def get_news_articles(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve news articles from ChromaDB.

        Args:
            date_from: Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
            date_to: End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
            limit: Optional limit on number of articles to retrieve

        Returns:
            List of article dictionaries with metadata

        Raises:
            NewsTrendsError: If retrieval fails
        """
        logger.debug(
            f"Retrieving news articles: date_from={date_from}, "
            f"date_to={date_to}, limit={limit}"
        )

        try:
            # Build where filter for news articles
            where_filter: Dict[str, Any] = {"type": "news_article"}

            # Get all news articles matching filter
            collection = self.chroma_store.collection
            if collection is None:
                raise NewsTrendsError("Collection is not initialized")

            # Use get() with where filter to retrieve all matching articles
            # Note: ChromaDB doesn't support complex date range queries directly,
            # so we'll filter by date after retrieval
            results = collection.get(
                where=where_filter,
                include=["metadatas", "documents"],
            )

            # Convert to list of article dictionaries
            articles = []
            for i, doc_id in enumerate(results.get("ids", [])):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                document_text = results["documents"][i] if results["documents"] else ""

                # Parse date if available
                date_str = metadata.get("date", "")
                try:
                    if date_str:
                        # Try parsing ISO format
                        if "T" in date_str:
                            article_date = datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            )
                        else:
                            # Try date-only format
                            article_date = datetime.fromisoformat(date_str)
                    else:
                        article_date = None
                except (ValueError, AttributeError):
                    logger.warning(f"Could not parse date: {date_str}")
                    article_date = None

                # Apply date filters if provided
                if date_from and article_date:
                    try:
                        date_from_dt = datetime.fromisoformat(
                            date_from.replace("Z", "+00:00")
                        )
                        if article_date < date_from_dt:
                            continue
                    except (ValueError, AttributeError):
                        pass

                if date_to and article_date:
                    try:
                        date_to_dt = datetime.fromisoformat(
                            date_to.replace("Z", "+00:00")
                        )
                        if article_date > date_to_dt:
                            continue
                    except (ValueError, AttributeError):
                        pass

                article = {
                    "id": doc_id,
                    "title": metadata.get("title", ""),
                    "content": document_text,
                    "date": article_date,
                    "date_str": date_str,
                    "source": metadata.get("source", ""),
                    "url": metadata.get("url", ""),
                    "author": metadata.get("author", ""),
                    "tickers": self._parse_tickers(metadata.get("tickers", "")),
                    "category": metadata.get("category", "general"),
                    "summary": metadata.get("summary", ""),
                    "metadata": metadata,
                }
                articles.append(article)

            # Sort by date (newest first)
            articles.sort(key=lambda x: x["date"] or datetime.min, reverse=True)

            # Apply limit if specified
            if limit:
                articles = articles[:limit]

            logger.info(f"Retrieved {len(articles)} news articles")
            return articles

        except ChromaStoreError as e:
            logger.error(f"ChromaDB error retrieving news articles: {str(e)}")
            raise NewsTrendsError(f"Failed to retrieve news articles: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error retrieving news articles: {str(e)}", exc_info=True)
            raise NewsTrendsError(f"Failed to retrieve news articles: {str(e)}") from e

    def _parse_tickers(self, tickers_str: str) -> List[str]:
        """
        Parse ticker symbols from comma-separated string.

        Args:
            tickers_str: Comma-separated ticker symbols

        Returns:
            List of ticker symbols
        """
        if not tickers_str:
            return []

        # Split by comma and clean up
        tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]
        return tickers

    def analyze_ticker_trends(
        self,
        articles: List[Dict[str, Any]],
        period: str = "daily",
        top_n: int = 10,
    ) -> pd.DataFrame:
        """
        Analyze trending tickers over time periods.

        Args:
            articles: List of article dictionaries
            period: Time period for aggregation ('hourly', 'daily', 'weekly', 'monthly')
            top_n: Number of top trending tickers to return

        Returns:
            DataFrame with columns: period, ticker, count, growth_rate, momentum
        """
        logger.debug(f"Analyzing ticker trends: period={period}, top_n={top_n}")

        if not articles:
            logger.warning("No articles provided for ticker trend analysis")
            return pd.DataFrame(
                columns=["period", "ticker", "count", "growth_rate", "momentum"]
            )

        # Create DataFrame from articles
        data = []
        for article in articles:
            if not article.get("date"):
                continue

            date = article["date"]
            tickers = article.get("tickers", [])

            for ticker in tickers:
                data.append({"date": date, "ticker": ticker})

        if not data:
            logger.warning("No ticker data found in articles")
            return pd.DataFrame(
                columns=["period", "ticker", "count", "growth_rate", "momentum"]
            )

        df = pd.DataFrame(data)

        # Set date as index and resample by period
        df.set_index("date", inplace=True)

        # Resample based on period
        period_map = {
            "hourly": "h",
            "daily": "D",
            "weekly": "W",
            "monthly": "ME",
        }
        freq = period_map.get(period.lower(), "D")

        # Count ticker mentions per period
        ticker_counts = (
            df.groupby([pd.Grouper(freq=freq), "ticker"])
            .size()
            .reset_index(name="count")
        )
        ticker_counts.columns = ["period", "ticker", "count"]

        # Calculate growth rate (period-over-period change)
        ticker_counts["growth_rate"] = (
            ticker_counts.groupby("ticker")["count"]
            .pct_change()
            .fillna(0)
            .replace([np.inf, -np.inf], 0)
        )

        # Calculate momentum (rolling average of growth rate)
        ticker_counts["momentum"] = (
            ticker_counts.groupby("ticker")["growth_rate"]
            .rolling(window=3, min_periods=1)
            .mean()
            .reset_index(level=0, drop=True)
        )

        # Get top N tickers by total count
        total_counts = (
            ticker_counts.groupby("ticker")["count"].sum().sort_values(ascending=False)
        )
        top_tickers = total_counts.head(top_n).index.tolist()

        # Filter to top tickers
        result = ticker_counts[ticker_counts["ticker"].isin(top_tickers)].copy()

        # Sort by period and count
        result = result.sort_values(["period", "count"], ascending=[True, False])

        logger.info(
            f"Analyzed ticker trends: {len(result)} records, "
            f"top {len(top_tickers)} tickers"
        )

        return result

    def analyze_topic_trends(
        self,
        articles: List[Dict[str, Any]],
        period: str = "daily",
        top_n: int = 10,
        min_word_length: int = 4,
    ) -> pd.DataFrame:
        """
        Analyze trending topics/keywords over time periods.

        Args:
            articles: List of article dictionaries
            period: Time period for aggregation ('hourly', 'daily', 'weekly', 'monthly')
            top_n: Number of top trending topics to return
            min_word_length: Minimum word length for keyword extraction

        Returns:
            DataFrame with columns: period, keyword, count, growth_rate, momentum
        """
        logger.debug(
            f"Analyzing topic trends: period={period}, top_n={top_n}, "
            f"min_word_length={min_word_length}"
        )

        if not articles:
            logger.warning("No articles provided for topic trend analysis")
            return pd.DataFrame(
                columns=["period", "keyword", "count", "growth_rate", "momentum"]
            )

        # Extract keywords from articles
        data = []
        for article in articles:
            if not article.get("date"):
                continue

            date = article["date"]
            # Combine title and content for keyword extraction
            text = f"{article.get('title', '')} {article.get('content', '')}"
            keywords = self._extract_keywords(text, min_word_length)

            for keyword in keywords:
                data.append({"date": date, "keyword": keyword})

        if not data:
            logger.warning("No keyword data extracted from articles")
            return pd.DataFrame(
                columns=["period", "keyword", "count", "growth_rate", "momentum"]
            )

        df = pd.DataFrame(data)

        # Set date as index and resample by period
        df.set_index("date", inplace=True)

        # Resample based on period
        period_map = {
            "hourly": "h",
            "daily": "D",
            "weekly": "W",
            "monthly": "ME",
        }
        freq = period_map.get(period.lower(), "D")

        # Count keyword mentions per period
        keyword_counts = (
            df.groupby([pd.Grouper(freq=freq), "keyword"])
            .size()
            .reset_index(name="count")
        )
        keyword_counts.columns = ["period", "keyword", "count"]

        # Calculate growth rate (period-over-period change)
        keyword_counts["growth_rate"] = (
            keyword_counts.groupby("keyword")["count"]
            .pct_change()
            .fillna(0)
            .replace([np.inf, -np.inf], 0)
        )

        # Calculate momentum (rolling average of growth rate)
        keyword_counts["momentum"] = (
            keyword_counts.groupby("keyword")["growth_rate"]
            .rolling(window=3, min_periods=1)
            .mean()
            .reset_index(level=0, drop=True)
        )

        # Get top N keywords by total count
        total_counts = (
            keyword_counts.groupby("keyword")["count"]
            .sum()
            .sort_values(ascending=False)
        )
        top_keywords = total_counts.head(top_n).index.tolist()

        # Filter to top keywords
        result = keyword_counts[keyword_counts["keyword"].isin(top_keywords)].copy()

        # Sort by period and count
        result = result.sort_values(["period", "count"], ascending=[True, False])

        logger.info(
            f"Analyzed topic trends: {len(result)} records, "
            f"top {len(top_keywords)} keywords"
        )

        return result

    def _extract_keywords(self, text: str, min_word_length: int = 4) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text: Text to extract keywords from
            min_word_length: Minimum word length

        Returns:
            List of keywords
        """
        if not text:
            return []

        # Convert to lowercase and split into words
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

        # Filter by length and stop words
        keywords = [
            word
            for word in words
            if len(word) >= min_word_length and word not in self.STOP_WORDS
        ]

        # Count frequency and return most common
        word_counts = Counter(keywords)
        # Return top keywords (appearing at least twice)
        top_keywords = [
            word for word, count in word_counts.most_common(20) if count >= 2
        ]

        return top_keywords

    def analyze_volume_trends(
        self,
        articles: List[Dict[str, Any]],
        period: str = "daily",
    ) -> pd.DataFrame:
        """
        Analyze news volume trends over time.

        Args:
            articles: List of article dictionaries
            period: Time period for aggregation ('hourly', 'daily', 'weekly', 'monthly')

        Returns:
            DataFrame with columns: period, volume, growth_rate
        """
        logger.debug(f"Analyzing volume trends: period={period}")

        if not articles:
            logger.warning("No articles provided for volume trend analysis")
            return pd.DataFrame(columns=["period", "volume", "growth_rate"])

        # Create DataFrame with dates
        data = []
        for article in articles:
            if article.get("date"):
                data.append({"date": article["date"]})

        if not data:
            logger.warning("No date data found in articles")
            return pd.DataFrame(columns=["period", "volume", "growth_rate"])

        df = pd.DataFrame(data)

        # Set date as index and resample by period
        df.set_index("date", inplace=True)

        # Resample based on period
        period_map = {
            "hourly": "h",
            "daily": "D",
            "weekly": "W",
            "monthly": "ME",
        }
        freq = period_map.get(period.lower(), "D")

        # Count articles per period
        volume = df.resample(freq).size().reset_index(name="volume")
        volume.columns = ["period", "volume"]

        # Calculate growth rate
        volume["growth_rate"] = (
            volume["volume"].pct_change().fillna(0).replace([np.inf, -np.inf], 0)
        )

        logger.info(f"Analyzed volume trends: {len(volume)} periods")

        return volume

    def get_trending_tickers(
        self,
        articles: List[Dict[str, Any]],
        period: str = "daily",
        top_n: int = 10,
        min_mentions: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Get top trending tickers based on frequency and growth.

        Args:
            articles: List of article dictionaries
            period: Time period for analysis ('hourly', 'daily', 'weekly', 'monthly')
            top_n: Number of top tickers to return
            min_mentions: Minimum number of mentions to include

        Returns:
            List of dictionaries with ticker, total_count, recent_count, growth_rate
        """
        logger.debug(
            f"Getting trending tickers: period={period}, top_n={top_n}, "
            f"min_mentions={min_mentions}"
        )

        if not articles:
            return []

        # Analyze ticker trends
        ticker_trends = self.analyze_ticker_trends(articles, period=period, top_n=top_n)

        if ticker_trends.empty:
            return []

        # Get most recent period data
        if "period" in ticker_trends.columns:
            recent_period = ticker_trends["period"].max()
            recent_data = ticker_trends[ticker_trends["period"] == recent_period]

            # Calculate total and recent counts
            total_counts = ticker_trends.groupby("ticker")["count"].sum()
            recent_counts = recent_data.groupby("ticker")["count"].sum()

            # Get average growth rate
            avg_growth = ticker_trends.groupby("ticker")["growth_rate"].mean()

            # Combine into results
            trending = []
            for ticker in total_counts.index:
                total = int(total_counts[ticker])
                if total < min_mentions:
                    continue

                recent = int(recent_counts.get(ticker, 0))
                growth = float(avg_growth.get(ticker, 0))

                trending.append(
                    {
                        "ticker": ticker,
                        "total_count": total,
                        "recent_count": recent,
                        "growth_rate": growth,
                    }
                )

            # Sort by recent count and growth rate
            trending.sort(
                key=lambda x: (x["recent_count"], x["growth_rate"]), reverse=True
            )

            return trending[:top_n]

        return []

    def get_trending_topics(
        self,
        articles: List[Dict[str, Any]],
        period: str = "daily",
        top_n: int = 10,
        min_mentions: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Get top trending topics/keywords based on frequency and growth.

        Args:
            articles: List of article dictionaries
            period: Time period for analysis ('hourly', 'daily', 'weekly', 'monthly')
            top_n: Number of top topics to return
            min_mentions: Minimum number of mentions to include

        Returns:
            List of dictionaries with keyword, total_count, recent_count, growth_rate
        """
        logger.debug(
            f"Getting trending topics: period={period}, top_n={top_n}, "
            f"min_mentions={min_mentions}"
        )

        if not articles:
            return []

        # Analyze topic trends
        topic_trends = self.analyze_topic_trends(articles, period=period, top_n=top_n)

        if topic_trends.empty:
            return []

        # Get most recent period data
        if "period" in topic_trends.columns:
            recent_period = topic_trends["period"].max()
            recent_data = topic_trends[topic_trends["period"] == recent_period]

            # Calculate total and recent counts
            total_counts = topic_trends.groupby("keyword")["count"].sum()
            recent_counts = recent_data.groupby("keyword")["count"].sum()

            # Get average growth rate
            avg_growth = topic_trends.groupby("keyword")["growth_rate"].mean()

            # Combine into results
            trending = []
            for keyword in total_counts.index:
                total = int(total_counts[keyword])
                if total < min_mentions:
                    continue

                recent = int(recent_counts.get(keyword, 0))
                growth = float(avg_growth.get(keyword, 0))

                trending.append(
                    {
                        "keyword": keyword,
                        "total_count": total,
                        "recent_count": recent,
                        "growth_rate": growth,
                    }
                )

            # Sort by recent count and growth rate
            trending.sort(
                key=lambda x: (x["recent_count"], x["growth_rate"]), reverse=True
            )

            return trending[:top_n]

        return []

    def generate_trend_report(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        period: str = "daily",
        top_tickers: int = 10,
        top_topics: int = 10,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive trend report.

        Args:
            date_from: Start date in ISO format
            date_to: End date in ISO format
            period: Time period for analysis ('hourly', 'daily', 'weekly', 'monthly')
            top_tickers: Number of top tickers to include
            top_topics: Number of top topics to include

        Returns:
            Dictionary with trend analysis results
        """
        logger.info(
            f"Generating trend report: date_from={date_from}, date_to={date_to}, "
            f"period={period}"
        )

        # Retrieve articles
        articles = self.get_news_articles(date_from=date_from, date_to=date_to)

        if not articles:
            logger.warning("No articles found for trend report")
            return {
                "period": period,
                "date_from": date_from,
                "date_to": date_to,
                "total_articles": 0,
                "ticker_trends": pd.DataFrame(),
                "topic_trends": pd.DataFrame(),
                "volume_trends": pd.DataFrame(),
                "trending_tickers": [],
                "trending_topics": [],
            }

        # Analyze trends
        ticker_trends = self.analyze_ticker_trends(
            articles, period=period, top_n=top_tickers
        )
        topic_trends = self.analyze_topic_trends(
            articles, period=period, top_n=top_topics
        )
        volume_trends = self.analyze_volume_trends(articles, period=period)
        trending_tickers = self.get_trending_tickers(
            articles, period=period, top_n=top_tickers
        )
        trending_topics = self.get_trending_topics(
            articles, period=period, top_n=top_topics
        )

        # Build report
        report = {
            "period": period,
            "date_from": date_from,
            "date_to": date_to,
            "total_articles": len(articles),
            "ticker_trends": ticker_trends,
            "topic_trends": topic_trends,
            "volume_trends": volume_trends,
            "trending_tickers": trending_tickers,
            "trending_topics": trending_topics,
        }

        logger.info(f"Generated trend report: {len(articles)} articles analyzed")

        return report
