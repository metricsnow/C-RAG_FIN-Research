"""
News trends API routes (TASK-047).

Provides API endpoints for news trend analysis including trending tickers,
topics, and volume trends.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.auth import verify_api_key
from app.analysis.news_trends import NewsTrendsAnalyzer, NewsTrendsError
from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/trends", tags=["trends"])

# Global analyzer instance (lazy initialization)
_trends_analyzer: NewsTrendsAnalyzer | None = None


def get_trends_analyzer() -> NewsTrendsAnalyzer:
    """
    Get or create news trends analyzer instance.

    Returns:
        NewsTrendsAnalyzer instance
    """
    global _trends_analyzer
    if _trends_analyzer is None:
        logger.info("Initializing news trends analyzer for API")
        _trends_analyzer = NewsTrendsAnalyzer()
    return _trends_analyzer


# Response models
class TrendingTicker(BaseModel):
    """Trending ticker response model."""

    ticker: str = Field(..., description="Ticker symbol")
    total_count: int = Field(..., description="Total mentions across all periods")
    recent_count: int = Field(..., description="Mentions in most recent period")
    growth_rate: float = Field(..., description="Average growth rate")


class TrendingTopic(BaseModel):
    """Trending topic response model."""

    keyword: str = Field(..., description="Trending keyword/topic")
    total_count: int = Field(..., description="Total mentions across all periods")
    recent_count: int = Field(..., description="Mentions in most recent period")
    growth_rate: float = Field(..., description="Average growth rate")


class VolumeTrend(BaseModel):
    """Volume trend response model."""

    period: str = Field(..., description="Time period")
    volume: int = Field(..., description="Number of articles in period")
    growth_rate: float = Field(..., description="Period-over-period growth rate")


class TrendReportResponse(BaseModel):
    """Complete trend report response model."""

    period: str = Field(..., description="Time period used for analysis")
    date_from: Optional[str] = Field(None, description="Start date filter")
    date_to: Optional[str] = Field(None, description="End date filter")
    total_articles: int = Field(..., description="Total articles analyzed")
    trending_tickers: List[TrendingTicker] = Field(
        ..., description="Top trending tickers"
    )
    trending_topics: List[TrendingTopic] = Field(..., description="Top trending topics")
    volume_trends: List[VolumeTrend] = Field(..., description="Volume trends over time")


@router.get(
    "/tickers",
    response_model=List[TrendingTicker],
    status_code=status.HTTP_200_OK,
)
async def get_trending_tickers(
    period: str = Query(
        default=None,
        description="Time period (hourly, daily, weekly, monthly)",
    ),
    top_n: int = Query(
        default=None,
        ge=1,
        le=100,
        description="Number of top tickers to return",
    ),
    date_from: Optional[str] = Query(
        default=None,
        description="Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    ),
    date_to: Optional[str] = Query(
        default=None,
        description="End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    ),
    min_mentions: int = Query(
        default=2,
        ge=1,
        description="Minimum number of mentions to include",
    ),
    analyzer: NewsTrendsAnalyzer = Depends(get_trends_analyzer),  # noqa: B008
    api_key: str = Depends(verify_api_key),  # noqa: B008
) -> List[TrendingTicker]:
    """
    Get top trending tickers based on news article frequency and growth.

    Args:
        period: Time period for aggregation (default: from config)
        top_n: Number of top tickers to return (default: from config)
        date_from: Start date filter (optional)
        date_to: End date filter (optional)
        min_mentions: Minimum mentions to include (default: 2)
        analyzer: News trends analyzer instance (dependency injection)
        api_key: Verified API key (dependency injection)

    Returns:
        List of trending tickers with counts and growth rates

    Raises:
        HTTPException: If analysis fails
    """
    if not config.news_trends_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="News trend analysis is disabled",
        )

    try:
        # Use config defaults if not provided
        period = period or config.news_trends_default_period
        top_n = top_n or config.news_trends_default_top_n

        # Validate period
        valid_periods = ["hourly", "daily", "weekly", "monthly"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid period: {period}. Must be one of {valid_periods}",
            )

        # Get articles
        articles = analyzer.get_news_articles(date_from=date_from, date_to=date_to)

        if not articles:
            return []

        # Get trending tickers
        trending = analyzer.get_trending_tickers(
            articles, period=period, top_n=top_n, min_mentions=min_mentions
        )

        # Convert to response models
        return [TrendingTicker(**t) for t in trending]

    except NewsTrendsError as e:
        logger.error(f"News trends error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze trending tickers: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error getting trending tickers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/topics",
    response_model=List[TrendingTopic],
    status_code=status.HTTP_200_OK,
)
async def get_trending_topics(
    period: str = Query(
        default=None,
        description="Time period (hourly, daily, weekly, monthly)",
    ),
    top_n: int = Query(
        default=None,
        ge=1,
        le=100,
        description="Number of top topics to return",
    ),
    date_from: Optional[str] = Query(
        default=None,
        description="Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    ),
    date_to: Optional[str] = Query(
        default=None,
        description="End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    ),
    min_mentions: int = Query(
        default=3,
        ge=1,
        description="Minimum number of mentions to include",
    ),
    analyzer: NewsTrendsAnalyzer = Depends(get_trends_analyzer),  # noqa: B008
    api_key: str = Depends(verify_api_key),  # noqa: B008
) -> List[TrendingTopic]:
    """
    Get top trending topics/keywords based on news article frequency and growth.

    Args:
        period: Time period for aggregation (default: from config)
        top_n: Number of top topics to return (default: from config)
        date_from: Start date filter (optional)
        date_to: End date filter (optional)
        min_mentions: Minimum mentions to include (default: 3)
        analyzer: News trends analyzer instance (dependency injection)
        api_key: Verified API key (dependency injection)

    Returns:
        List of trending topics with counts and growth rates

    Raises:
        HTTPException: If analysis fails
    """
    if not config.news_trends_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="News trend analysis is disabled",
        )

    try:
        # Use config defaults if not provided
        period = period or config.news_trends_default_period
        top_n = top_n or config.news_trends_default_top_n

        # Validate period
        valid_periods = ["hourly", "daily", "weekly", "monthly"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid period: {period}. Must be one of {valid_periods}",
            )

        # Get articles
        articles = analyzer.get_news_articles(date_from=date_from, date_to=date_to)

        if not articles:
            return []

        # Get trending topics
        trending = analyzer.get_trending_topics(
            articles, period=period, top_n=top_n, min_mentions=min_mentions
        )

        # Convert to response models
        return [TrendingTopic(**t) for t in trending]

    except NewsTrendsError as e:
        logger.error(f"News trends error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze trending topics: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error getting trending topics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/report",
    response_model=TrendReportResponse,
    status_code=status.HTTP_200_OK,
)
async def get_trend_report(
    period: str = Query(
        default=None,
        description="Time period (hourly, daily, weekly, monthly)",
    ),
    top_tickers: int = Query(
        default=None,
        ge=1,
        le=100,
        description="Number of top tickers to include",
    ),
    top_topics: int = Query(
        default=None,
        ge=1,
        le=100,
        description="Number of top topics to include",
    ),
    date_from: Optional[str] = Query(
        default=None,
        description="Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    ),
    date_to: Optional[str] = Query(
        default=None,
        description="End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    ),
    analyzer: NewsTrendsAnalyzer = Depends(get_trends_analyzer),  # noqa: B008
    api_key: str = Depends(verify_api_key),  # noqa: B008
) -> TrendReportResponse:
    """
    Generate comprehensive trend report with tickers, topics, and volume trends.

    Args:
        period: Time period for aggregation (default: from config)
        top_tickers: Number of top tickers to include (default: from config)
        top_topics: Number of top topics to include (default: from config)
        date_from: Start date filter (optional)
        date_to: End date filter (optional)
        analyzer: News trends analyzer instance (dependency injection)
        api_key: Verified API key (dependency injection)

    Returns:
        Complete trend report with all analysis results

    Raises:
        HTTPException: If analysis fails
    """
    if not config.news_trends_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="News trend analysis is disabled",
        )

    try:
        # Use config defaults if not provided
        period = period or config.news_trends_default_period
        top_tickers = top_tickers or config.news_trends_default_top_n
        top_topics = top_topics or config.news_trends_default_top_n

        # Validate period
        valid_periods = ["hourly", "daily", "weekly", "monthly"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid period: {period}. Must be one of {valid_periods}",
            )

        # Generate report
        report = analyzer.generate_trend_report(
            date_from=date_from,
            date_to=date_to,
            period=period,
            top_tickers=top_tickers,
            top_topics=top_topics,
        )

        # Convert DataFrames to lists for JSON serialization
        volume_trends = []
        if not report["volume_trends"].empty:
            for _, row in report["volume_trends"].iterrows():
                volume_trends.append(
                    VolumeTrend(
                        period=str(row["period"]),
                        volume=int(row["volume"]),
                        growth_rate=float(row["growth_rate"]),
                    )
                )

        # Convert to response model
        return TrendReportResponse(
            period=report["period"],
            date_from=report["date_from"],
            date_to=report["date_to"],
            total_articles=report["total_articles"],
            trending_tickers=[TrendingTicker(**t) for t in report["trending_tickers"]],
            trending_topics=[TrendingTopic(**t) for t in report["trending_topics"]],
            volume_trends=volume_trends,
        )

    except NewsTrendsError as e:
        logger.error(f"News trends error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate trend report: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error generating trend report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e

