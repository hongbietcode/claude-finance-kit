"""OHLCV daily batch fetch task using claude_finance_kit.stock.Stock."""

import logging
from typing import Any

from claude_finance_kit.collector.core.exporter import CSVExporter
from claude_finance_kit.collector.core.fetcher import StockFetcher
from claude_finance_kit.collector.core.scheduler import Scheduler
from claude_finance_kit.collector.core.transformer import DeduplicatingTransformer
from claude_finance_kit.collector.core.validator import DataFrameValidator

logger = logging.getLogger(__name__)

_DEFAULT_START = "2024-01-01"
_DEFAULT_END = "2025-03-19"


class OHLCVFetcher(StockFetcher):
    """Fetches OHLCV daily history for a ticker via Stock.quote.history().

    Accepted kwargs:
        start (str): Start date in YYYY-MM-DD format.
        end (str): End date in YYYY-MM-DD format.
        interval (str): Bar interval, e.g. "1D".
    """

    def _call(self, ticker: str, **kwargs: Any) -> Any:
        from claude_finance_kit.stock import Stock

        start = kwargs.get("start", _DEFAULT_START)
        end = kwargs.get("end", _DEFAULT_END)
        interval = kwargs.get("interval", "1D")
        stock = Stock(ticker)
        return stock.quote.history(start=start, end=end, interval=interval)


class OHLCVValidator(DataFrameValidator):
    """Validates that the OHLCV DataFrame contains required price columns."""

    required_columns = ["time", "open", "high", "low", "close", "volume"]


class OHLCVTransformer(DeduplicatingTransformer):
    """Normalises and deduplicates OHLCV data on the 'time' column."""

    dedup_subset = ["time"]


class OHLCVTask:
    """High-level OHLCV batch task.

    Usage:
        task = OHLCVTask(base_path="./data/ohlcv")
        task.run(["ACB", "VCB", "HPG"], start="2024-01-01", end="2024-12-31")
    """

    def __init__(
        self,
        base_path: str = "./data/ohlcv",
        retry_attempts: int = 3,
        max_workers: int = 3,
        request_delay: float = 0.5,
        rate_limit_wait: float = 35.0,
    ) -> None:
        self._fetcher = OHLCVFetcher()
        self._validator = OHLCVValidator()
        self._transformer = OHLCVTransformer()
        self._exporter = CSVExporter(base_path=base_path)
        self._scheduler = Scheduler(
            fetcher=self._fetcher,
            validator=self._validator,
            transformer=self._transformer,
            exporter=self._exporter,
            retry_attempts=retry_attempts,
            max_workers=max_workers,
            request_delay=request_delay,
            rate_limit_wait=rate_limit_wait,
        )

    def run(self, tickers: list[str], **fetch_kwargs: Any) -> dict[str, Any]:
        """Run the OHLCV pipeline for a list of tickers.

        Args:
            tickers: Stock symbols to process.
            **fetch_kwargs: Forwarded to OHLCVFetcher (start, end, interval).

        Returns:
            Scheduler summary dict.
        """
        return self._scheduler.run(tickers, fetcher_kwargs=fetch_kwargs or None)


def run_task(tickers: list[str], **kwargs: Any) -> dict[str, Any]:
    """Convenience function to run the OHLCV task.

    Args:
        tickers: Stock symbols to process.
        **kwargs: start, end, interval forwarded to the fetcher.

    Returns:
        Scheduler summary dict.
    """
    task = OHLCVTask()
    return task.run(tickers, **kwargs)
