"""
Stock data normalization module.

Converts yfinance stock data into text format suitable for vector storage
and RAG queries. Handles various data types and formats them consistently.
"""

from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


class StockDataNormalizerError(Exception):
    """Custom exception for stock data normalization errors."""

    pass


class StockDataNormalizer:
    """
    Normalizes stock data from yfinance into text format.

    Converts various data types (info dict, DataFrames, Series) into
    searchable text representations suitable for vector storage.
    """

    @staticmethod
    def normalize_ticker_info(info: Dict[str, Any], ticker_symbol: str) -> str:
        """
        Normalize ticker info dictionary to text format.

        Args:
            info: Dictionary from yfinance ticker.info
            ticker_symbol: Stock ticker symbol

        Returns:
            Formatted text string with key information
        """
        lines = [
            f"Stock Information for {ticker_symbol} ({info.get('longName', 'N/A')})"
        ]

        # Company Information
        if "sector" in info or "industry" in info:
            lines.append("\nCompany Profile:")
            if "sector" in info:
                lines.append(f"  Sector: {info.get('sector', 'N/A')}")
            if "industry" in info:
                lines.append(f"  Industry: {info.get('industry', 'N/A')}")
            if "longBusinessSummary" in info:
                summary = str(info.get("longBusinessSummary", ""))[:500]
                lines.append(f"  Business Summary: {summary}...")

        # Financial Metrics
        lines.append("\nFinancial Metrics:")
        metrics = {
            "marketCap": ("Market Cap", lambda x: f"${x:,.0f}" if x else "N/A"),
            "currentPrice": ("Current Price", lambda x: f"${x:.2f}" if x else "N/A"),
            "previousClose": ("Previous Close", lambda x: f"${x:.2f}" if x else "N/A"),
            "open": ("Open", lambda x: f"${x:.2f}" if x else "N/A"),
            "dayLow": ("Day Low", lambda x: f"${x:.2f}" if x else "N/A"),
            "dayHigh": ("Day High", lambda x: f"${x:.2f}" if x else "N/A"),
            "volume": ("Volume", lambda x: f"{x:,.0f}" if x else "N/A"),
            "averageVolume": ("Average Volume", lambda x: f"{x:,.0f}" if x else "N/A"),
            "trailingPE": ("Trailing P/E", lambda x: f"{x:.2f}" if x else "N/A"),
            "forwardPE": ("Forward P/E", lambda x: f"{x:.2f}" if x else "N/A"),
            "priceToBook": ("Price to Book", lambda x: f"{x:.2f}" if x else "N/A"),
            "dividendYield": ("Dividend Yield", lambda x: f"{x:.2%}" if x else "N/A"),
            "profitMargins": ("Profit Margin", lambda x: f"{x:.2%}" if x else "N/A"),
            "revenueGrowth": ("Revenue Growth", lambda x: f"{x:.2%}" if x else "N/A"),
            "earningsGrowth": ("Earnings Growth", lambda x: f"{x:.2%}" if x else "N/A"),
            "52WeekHigh": ("52 Week High", lambda x: f"${x:.2f}" if x else "N/A"),
            "52WeekLow": ("52 Week Low", lambda x: f"${x:.2f}" if x else "N/A"),
        }

        for key, (label, formatter) in metrics.items():
            value = info.get(key)
            if value is not None:
                try:
                    formatted_value = formatter(value)
                    lines.append(f"  {label}: {formatted_value}")
                except (TypeError, ValueError):
                    lines.append(f"  {label}: {value}")

        # Financial Statements Summary
        if "totalRevenue" in info or "totalCash" in info:
            lines.append("\nFinancial Position:")
            if "totalRevenue" in info:
                revenue = info.get("totalRevenue")
                if revenue:
                    lines.append(f"  Total Revenue: ${revenue:,.0f}")
            if "totalCash" in info:
                cash = info.get("totalCash")
                if cash:
                    lines.append(f"  Total Cash: ${cash:,.0f}")
            if "totalDebt" in info:
                debt = info.get("totalDebt")
                if debt:
                    lines.append(f"  Total Debt: ${debt:,.0f}")

        return "\n".join(lines)

    @staticmethod
    def normalize_historical_prices(
        history: pd.DataFrame, ticker_symbol: str, max_rows: int = 100
    ) -> str:
        """
        Normalize historical price DataFrame to text format.

        Args:
            history: DataFrame with OHLCV data
            ticker_symbol: Stock ticker symbol
            max_rows: Maximum number of rows to include in summary

        Returns:
            Formatted text string with price history
        """
        if history.empty:
            return f"No historical price data available for {ticker_symbol}"

        lines = [f"Historical Price Data for {ticker_symbol}"]
        lines.append(f"Period: {history.index[0]} to {history.index[-1]}")
        lines.append(f"Total Trading Days: {len(history)}")

        # Summary Statistics
        if "Close" in history.columns:
            close_prices = history["Close"]
            lines.append("\nPrice Summary:")
            lines.append(f"  Current Price: ${close_prices.iloc[-1]:.2f}")
            lines.append(f"  Highest Price: ${close_prices.max():.2f}")
            lines.append(f"  Lowest Price: ${close_prices.min():.2f}")
            lines.append(f"  Average Price: ${close_prices.mean():.2f}")

        if "Volume" in history.columns:
            volumes = history["Volume"]
            lines.append("\nVolume Summary:")
            lines.append(f"  Average Volume: {volumes.mean():,.0f}")
            lines.append(f"  Highest Volume: {volumes.max():,.0f}")

        # Recent Price Data (last N rows)
        lines.append("\nRecent Price History:")
        recent = history.tail(min(max_rows, len(history)))
        for date, row in recent.iterrows():
            date_str = (
                date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date)
            )
            close = row.get("Close", "N/A")
            volume = row.get("Volume", "N/A")
            if isinstance(close, (int, float)):
                close_str = f"${close:.2f}"
            else:
                close_str = str(close)
            if isinstance(volume, (int, float)):
                volume_str = f"{volume:,.0f}"
            else:
                volume_str = str(volume)
            lines.append(f"  {date_str}: Close={close_str}, Volume={volume_str}")

        return "\n".join(lines)

    @staticmethod
    def normalize_dividends(dividends: pd.Series, ticker_symbol: str) -> str:
        """
        Normalize dividend Series to text format.

        Args:
            dividends: Series with dividend dates and amounts
            ticker_symbol: Stock ticker symbol

        Returns:
            Formatted text string with dividend history
        """
        if dividends.empty:
            return f"No dividend history available for {ticker_symbol}"

        lines = [f"Dividend History for {ticker_symbol}"]
        lines.append(f"Total Dividend Payments: {len(dividends)}")

        if len(dividends) > 0:
            total_dividends = dividends.sum()
            avg_dividend = dividends.mean()
            lines.append(f"Total Dividends Paid: ${total_dividends:.2f}")
            lines.append(f"Average Dividend per Payment: ${avg_dividend:.2f}")

        # Recent dividends
        lines.append("\nRecent Dividend Payments:")
        recent = dividends.tail(min(20, len(dividends)))
        for date, amount in recent.items():
            date_str = (
                date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date)
            )
            lines.append(f"  {date_str}: ${amount:.2f}")

        return "\n".join(lines)

    @staticmethod
    def normalize_earnings(earnings: pd.DataFrame, ticker_symbol: str) -> str:
        """
        Normalize earnings DataFrame to text format.

        Args:
            earnings: DataFrame with earnings data
            ticker_symbol: Stock ticker symbol

        Returns:
            Formatted text string with earnings information
        """
        if earnings.empty:
            return f"No earnings data available for {ticker_symbol}"

        lines = [f"Earnings Data for {ticker_symbol}"]

        # Format earnings data
        for index, row in earnings.iterrows():
            period = str(index)
            if "Revenue" in earnings.columns:
                revenue = row.get("Revenue", "N/A")
                if isinstance(revenue, (int, float)):
                    revenue_str = f"${revenue:,.0f}"
                else:
                    revenue_str = str(revenue)
                lines.append(f"  {period}: Revenue={revenue_str}")
            if "Earnings" in earnings.columns:
                earnings_val = row.get("Earnings", "N/A")
                if isinstance(earnings_val, (int, float)):
                    earnings_str = f"${earnings_val:,.0f}"
                else:
                    earnings_str = str(earnings_val)
                lines.append(f"  {period}: Earnings={earnings_str}")

        return "\n".join(lines)

    @staticmethod
    def normalize_recommendations(
        recommendations: pd.DataFrame, ticker_symbol: str
    ) -> str:
        """
        Normalize recommendations DataFrame to text format.

        Args:
            recommendations: DataFrame with analyst recommendations
            ticker_symbol: Stock ticker symbol

        Returns:
            Formatted text string with recommendations
        """
        if recommendations.empty:
            return f"No analyst recommendations available for {ticker_symbol}"

        lines = [f"Analyst Recommendations for {ticker_symbol}"]
        lines.append(f"Total Recommendations: {len(recommendations)}")

        # Count recommendations by action
        if "To Grade" in recommendations.columns:
            grade_counts = recommendations["To Grade"].value_counts()
            lines.append("\nRecommendation Summary:")
            for grade, count in grade_counts.items():
                lines.append(f"  {grade}: {count}")

        # Recent recommendations
        lines.append("\nRecent Recommendations:")
        recent = recommendations.tail(min(10, len(recommendations)))
        for date, row in recent.iterrows():
            date_str = (
                date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date)
            )
            firm = row.get("Firm", "N/A")
            to_grade = row.get("To Grade", "N/A")
            from_grade = row.get("From Grade", "N/A")
            action = row.get("Action", "N/A")
            lines.append(
                f"  {date_str}: {firm} - {action} from {from_grade} to {to_grade}"
            )

        return "\n".join(lines)

    @staticmethod
    def normalize_all_data(
        data: Dict[str, Any], ticker_symbol: str
    ) -> List[Dict[str, Any]]:
        """
        Normalize all stock data into a list of text documents.

        Args:
            data: Dictionary containing all fetched data (from fetch_all_data)
            ticker_symbol: Stock ticker symbol

        Returns:
            List of dictionaries, each containing:
            - text: Normalized text content
            - metadata: Metadata for vector storage
        """
        documents = []
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Normalize ticker info
        if "info" in data:
            try:
                info_text = StockDataNormalizer.normalize_ticker_info(
                    data["info"], ticker_symbol
                )
                documents.append(
                    {
                        "text": info_text,
                        "metadata": {
                            "ticker": ticker_symbol,
                            "data_type": "info",
                            "date": current_date,
                            "source": "yfinance",
                            "update_frequency": "daily",
                        },
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Failed to normalize info for {ticker_symbol}: {str(e)}"
                )

        # Normalize historical prices
        if "history" in data and not data["history"].empty:
            try:
                history_text = StockDataNormalizer.normalize_historical_prices(
                    data["history"], ticker_symbol
                )
                documents.append(
                    {
                        "text": history_text,
                        "metadata": {
                            "ticker": ticker_symbol,
                            "data_type": "price",
                            "date": current_date,
                            "source": "yfinance",
                            "update_frequency": "daily",
                        },
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Failed to normalize history for {ticker_symbol}: {str(e)}"
                )

        # Normalize dividends
        if "dividends" in data and not data["dividends"].empty:
            try:
                dividends_text = StockDataNormalizer.normalize_dividends(
                    data["dividends"], ticker_symbol
                )
                documents.append(
                    {
                        "text": dividends_text,
                        "metadata": {
                            "ticker": ticker_symbol,
                            "data_type": "dividends",
                            "date": current_date,
                            "source": "yfinance",
                            "update_frequency": "quarterly",
                        },
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Failed to normalize dividends for {ticker_symbol}: {str(e)}"
                )

        # Normalize earnings
        if "earnings" in data and not data["earnings"].empty:
            try:
                earnings_text = StockDataNormalizer.normalize_earnings(
                    data["earnings"], ticker_symbol
                )
                documents.append(
                    {
                        "text": earnings_text,
                        "metadata": {
                            "ticker": ticker_symbol,
                            "data_type": "earnings",
                            "date": current_date,
                            "source": "yfinance",
                            "update_frequency": "quarterly",
                        },
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Failed to normalize earnings for {ticker_symbol}: {str(e)}"
                )

        # Normalize recommendations
        if "recommendations" in data and not data["recommendations"].empty:
            try:
                recommendations_text = StockDataNormalizer.normalize_recommendations(
                    data["recommendations"], ticker_symbol
                )
                documents.append(
                    {
                        "text": recommendations_text,
                        "metadata": {
                            "ticker": ticker_symbol,
                            "data_type": "recommendations",
                            "date": current_date,
                            "source": "yfinance",
                            "update_frequency": "daily",
                        },
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Failed to normalize recommendations for {ticker_symbol}: {str(e)}"
                )

        logger.info(f"Normalized {len(documents)} documents for {ticker_symbol}")
        return documents
