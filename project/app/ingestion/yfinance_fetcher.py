"""
yfinance stock data fetching module.

Fetches stock market data and financial metrics from Yahoo Finance using yfinance.
Supports rate limiting and error handling for robust data fetching.
"""

import time
from typing import Any, Dict, Optional

import pandas as pd
import yfinance as yf

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class YFinanceFetcherError(Exception):
    """Custom exception for yfinance fetching errors."""

    pass


class YFinanceFetcher:
    """
    Fetches stock data from Yahoo Finance using yfinance library.

    Supports fetching:
    - Current price and market data
    - Historical price data (OHLCV)
    - Financial metrics (P/E, P/B, market cap, etc.)
    - Dividend information
    - Earnings data
    - Analyst recommendations
    - Company information
    """

    def __init__(self, rate_limit_seconds: Optional[float] = None):
        """
        Initialize yfinance fetcher.

        Args:
            rate_limit_seconds: Rate limit between API calls in seconds.
                If None, uses config.yfinance_rate_limit_seconds
        """
        self.rate_limit_seconds = (
            rate_limit_seconds or config.yfinance_rate_limit_seconds
        )
        self._last_request_time: Optional[float] = None

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between API calls."""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit_seconds:
                sleep_time = self.rate_limit_seconds - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        self._last_request_time = time.time()

    def fetch_ticker_info(self, ticker_symbol: str) -> Dict[str, Any]:
        """
        Fetch comprehensive stock information for a ticker.

        Args:
            ticker_symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            Dictionary containing stock information including:
            - Basic info (name, sector, industry)
            - Financial metrics (market cap, P/E, P/B, etc.)
            - Company profile
            - Current price and volume

        Raises:
            YFinanceFetcherError: If fetching fails
        """
        logger.info(f"Fetching ticker info for {ticker_symbol}")
        self._apply_rate_limit()

        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info

            if not info or len(info) == 0:
                raise YFinanceFetcherError(
                    f"No information available for ticker {ticker_symbol}"
                )

            logger.debug(f"Successfully fetched info for {ticker_symbol}")
            return info

        except Exception as e:
            logger.error(
                f"Failed to fetch ticker info for {ticker_symbol}: {str(e)}",
                exc_info=True,
            )
            raise YFinanceFetcherError(
                f"Failed to fetch ticker info for {ticker_symbol}: {str(e)}"
            ) from e

    def fetch_historical_prices(
        self,
        ticker_symbol: str,
        period: Optional[str] = None,
        interval: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch historical price data (OHLCV) for a ticker.

        Args:
            ticker_symbol: Stock ticker symbol
            period: Period for historical data
                (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
                If None, uses config.yfinance_history_period
            interval: Interval for historical data
                (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
                If None, uses config.yfinance_history_interval
            start: Start date (YYYY-MM-DD format). Overrides period if provided
            end: End date (YYYY-MM-DD format). Overrides period if provided

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume,
            Dividends, Stock Splits

        Raises:
            YFinanceFetcherError: If fetching fails
        """
        logger.info(
            f"Fetching historical prices for {ticker_symbol}: "
            f"period={period or config.yfinance_history_period}, "
            f"interval={interval or config.yfinance_history_interval}"
        )
        self._apply_rate_limit()

        try:
            ticker = yf.Ticker(ticker_symbol)

            # Use period/interval or start/end
            if start and end:
                history = ticker.history(
                    start=start,
                    end=end,
                    interval=interval or config.yfinance_history_interval,
                )
            else:
                history = ticker.history(
                    period=period or config.yfinance_history_period,
                    interval=interval or config.yfinance_history_interval,
                )

            if history.empty:
                raise YFinanceFetcherError(
                    f"No historical data available for ticker {ticker_symbol}"
                )

            logger.debug(
                f"Successfully fetched {len(history)} rows of historical data "
                f"for {ticker_symbol}"
            )
            return history

        except Exception as e:
            logger.error(
                f"Failed to fetch historical prices for {ticker_symbol}: {str(e)}",
                exc_info=True,
            )
            raise YFinanceFetcherError(
                f"Failed to fetch historical prices for {ticker_symbol}: {str(e)}"
            ) from e

    def fetch_dividends(self, ticker_symbol: str) -> pd.Series:
        """
        Fetch dividend history for a ticker.

        Args:
            ticker_symbol: Stock ticker symbol

        Returns:
            Series with dividend dates as index and dividend amounts as values

        Raises:
            YFinanceFetcherError: If fetching fails
        """
        logger.info(f"Fetching dividends for {ticker_symbol}")
        self._apply_rate_limit()

        try:
            ticker = yf.Ticker(ticker_symbol)
            dividends = ticker.dividends

            if dividends.empty:
                logger.warning(f"No dividend data available for ticker {ticker_symbol}")
                return pd.Series(dtype=float)

            logger.debug(
                f"Successfully fetched {len(dividends)} dividend records "
                f"for {ticker_symbol}"
            )
            return dividends

        except Exception as e:
            logger.error(
                f"Failed to fetch dividends for {ticker_symbol}: {str(e)}",
                exc_info=True,
            )
            raise YFinanceFetcherError(
                f"Failed to fetch dividends for {ticker_symbol}: {str(e)}"
            ) from e

    def fetch_earnings(self, ticker_symbol: str) -> pd.DataFrame:
        """
        Fetch earnings data for a ticker.

        Args:
            ticker_symbol: Stock ticker symbol

        Returns:
            DataFrame with earnings data (quarterly and yearly)

        Raises:
            YFinanceFetcherError: If fetching fails
        """
        logger.info(f"Fetching earnings for {ticker_symbol}")
        self._apply_rate_limit()

        try:
            ticker = yf.Ticker(ticker_symbol)
            earnings = ticker.earnings

            if earnings.empty:
                logger.warning(f"No earnings data available for ticker {ticker_symbol}")
                return pd.DataFrame()

            logger.debug(
                f"Successfully fetched earnings data for {ticker_symbol}: "
                f"{len(earnings)} records"
            )
            return earnings

        except Exception as e:
            logger.error(
                f"Failed to fetch earnings for {ticker_symbol}: {str(e)}",
                exc_info=True,
            )
            raise YFinanceFetcherError(
                f"Failed to fetch earnings for {ticker_symbol}: {str(e)}"
            ) from e

    def fetch_recommendations(self, ticker_symbol: str) -> pd.DataFrame:
        """
        Fetch analyst recommendations for a ticker.

        Args:
            ticker_symbol: Stock ticker symbol

        Returns:
            DataFrame with analyst recommendations

        Raises:
            YFinanceFetcherError: If fetching fails
        """
        logger.info(f"Fetching recommendations for {ticker_symbol}")
        self._apply_rate_limit()

        try:
            ticker = yf.Ticker(ticker_symbol)
            recommendations = ticker.recommendations

            if recommendations is None or recommendations.empty:
                logger.warning(
                    f"No recommendations data available for ticker {ticker_symbol}"
                )
                return pd.DataFrame()

            logger.debug(
                f"Successfully fetched {len(recommendations)} recommendations "
                f"for {ticker_symbol}"
            )
            return recommendations

        except Exception as e:
            logger.error(
                f"Failed to fetch recommendations for {ticker_symbol}: {str(e)}",
                exc_info=True,
            )
            raise YFinanceFetcherError(
                f"Failed to fetch recommendations for {ticker_symbol}: {str(e)}"
            ) from e

    def fetch_all_data(
        self, ticker_symbol: str, include_history: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch all available data for a ticker.

        Args:
            ticker_symbol: Stock ticker symbol
            include_history: Whether to include historical price data (default: True)

        Returns:
            Dictionary containing all fetched data:
            - info: Company and financial information
            - history: Historical price data (if include_history=True)
            - dividends: Dividend history
            - earnings: Earnings data
            - recommendations: Analyst recommendations

        Raises:
            YFinanceFetcherError: If fetching fails
        """
        logger.info(f"Fetching all data for {ticker_symbol}")
        result: Dict[str, Any] = {}

        try:
            # Fetch basic info
            result["info"] = self.fetch_ticker_info(ticker_symbol)

            # Fetch historical prices if requested
            if include_history:
                result["history"] = self.fetch_historical_prices(ticker_symbol)

            # Fetch dividends
            try:
                result["dividends"] = self.fetch_dividends(ticker_symbol)
            except YFinanceFetcherError as e:
                logger.warning(f"Failed to fetch dividends: {str(e)}")
                result["dividends"] = pd.Series(dtype=float)

            # Fetch earnings
            try:
                result["earnings"] = self.fetch_earnings(ticker_symbol)
            except YFinanceFetcherError as e:
                logger.warning(f"Failed to fetch earnings: {str(e)}")
                result["earnings"] = pd.DataFrame()

            # Fetch recommendations
            try:
                result["recommendations"] = self.fetch_recommendations(ticker_symbol)
            except YFinanceFetcherError as e:
                logger.warning(f"Failed to fetch recommendations: {str(e)}")
                result["recommendations"] = pd.DataFrame()

            logger.info(f"Successfully fetched all data for {ticker_symbol}")
            return result

        except Exception as e:
            logger.error(
                f"Failed to fetch all data for {ticker_symbol}: {str(e)}",
                exc_info=True,
            )
            raise YFinanceFetcherError(
                f"Failed to fetch all data for {ticker_symbol}: {str(e)}"
            ) from e
