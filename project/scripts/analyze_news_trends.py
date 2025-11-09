#!/usr/bin/env python3
"""
Script to analyze news trends and generate trend reports.

Analyzes news articles to identify trending topics, tickers, and patterns
over time periods.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.analysis.news_trends import NewsTrendsAnalyzer, NewsTrendsError
from app.utils.logger import get_logger

logger = get_logger(__name__)


def format_report(report: dict) -> str:
    """
    Format trend report as human-readable text.

    Args:
        report: Trend report dictionary

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 80)
    lines.append("NEWS TREND ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Period: {report.get('period', 'N/A')}")
    lines.append(
        f"Date Range: {report.get('date_from', 'N/A')} to {report.get('date_to', 'N/A')}"
    )
    lines.append(f"Total Articles: {report.get('total_articles', 0)}")
    lines.append("")

    # Trending Tickers
    trending_tickers = report.get("trending_tickers", [])
    if trending_tickers:
        lines.append("-" * 80)
        lines.append("TOP TRENDING TICKERS")
        lines.append("-" * 80)
        for i, ticker_data in enumerate(trending_tickers, 1):
            ticker = ticker_data.get("ticker", "N/A")
            total = ticker_data.get("total_count", 0)
            recent = ticker_data.get("recent_count", 0)
            growth = ticker_data.get("growth_rate", 0) * 100
            lines.append(
                f"{i}. {ticker}: Total={total}, Recent={recent}, "
                f"Growth={growth:.1f}%"
            )
        lines.append("")

    # Trending Topics
    trending_topics = report.get("trending_topics", [])
    if trending_topics:
        lines.append("-" * 80)
        lines.append("TOP TRENDING TOPICS")
        lines.append("-" * 80)
        for i, topic_data in enumerate(trending_topics, 1):
            keyword = topic_data.get("keyword", "N/A")
            total = topic_data.get("total_count", 0)
            recent = topic_data.get("recent_count", 0)
            growth = topic_data.get("growth_rate", 0) * 100
            lines.append(
                f"{i}. {keyword}: Total={total}, Recent={recent}, "
                f"Growth={growth:.1f}%"
            )
        lines.append("")

    # Volume Trends Summary
    volume_trends = report.get("volume_trends")
    if volume_trends is not None and not volume_trends.empty:
        lines.append("-" * 80)
        lines.append("VOLUME TRENDS SUMMARY")
        lines.append("-" * 80)
        total_volume = volume_trends["volume"].sum()
        avg_volume = volume_trends["volume"].mean()
        max_volume = volume_trends["volume"].max()
        max_period = volume_trends.loc[volume_trends["volume"].idxmax(), "period"]
        lines.append(f"Total Volume: {int(total_volume)}")
        lines.append(f"Average Volume: {avg_volume:.1f}")
        lines.append(f"Peak Volume: {int(max_volume)} (Period: {max_period})")
        lines.append("")

    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    """Main function to run news trend analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze news trends and generate trend reports"
    )
    parser.add_argument(
        "--date-from",
        type=str,
        help="Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    )
    parser.add_argument(
        "--date-to",
        type=str,
        help="End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    )
    parser.add_argument(
        "--period",
        type=str,
        choices=["hourly", "daily", "weekly", "monthly"],
        default="daily",
        help="Time period for aggregation (default: daily)",
    )
    parser.add_argument(
        "--top-tickers",
        type=int,
        default=10,
        help="Number of top trending tickers to include (default: 10)",
    )
    parser.add_argument(
        "--top-topics",
        type=int,
        default=10,
        help="Number of top trending topics to include (default: 10)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for JSON report (optional)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Number of days to analyze (from today backwards)",
    )

    args = parser.parse_args()

    # Calculate date range if days specified
    date_from = args.date_from
    date_to = args.date_to

    if args.days:
        date_to = datetime.now().isoformat()
        date_from = (datetime.now() - timedelta(days=args.days)).isoformat()
        logger.info(f"Analyzing last {args.days} days")

    try:
        # Initialize analyzer
        logger.info("Initializing news trends analyzer")
        analyzer = NewsTrendsAnalyzer()

        # Generate trend report
        logger.info("Generating trend report")
        report = analyzer.generate_trend_report(
            date_from=date_from,
            date_to=date_to,
            period=args.period,
            top_tickers=args.top_tickers,
            top_topics=args.top_topics,
        )

        # Output report
        if args.format == "json":
            # Convert DataFrames to dict for JSON serialization
            json_report = {
                "period": report["period"],
                "date_from": report["date_from"],
                "date_to": report["date_to"],
                "total_articles": report["total_articles"],
                "trending_tickers": report["trending_tickers"],
                "trending_topics": report["trending_topics"],
                "volume_trends": (
                    report["volume_trends"].to_dict("records")
                    if not report["volume_trends"].empty
                    else []
                ),
            }

            output_text = json.dumps(json_report, indent=2, default=str)
        else:
            output_text = format_report(report)

        # Write to file or stdout
        if args.output:
            with open(args.output, "w") as f:
                f.write(output_text)
            logger.info(f"Report written to {args.output}")
        else:
            print(output_text)

        logger.info("Trend analysis complete")

    except NewsTrendsError as e:
        logger.error(f"News trends error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error analyzing news trends: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
