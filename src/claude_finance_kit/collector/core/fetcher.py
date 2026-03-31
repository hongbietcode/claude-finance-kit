"""Abstract base class and default fetcher for pipeline data retrieval."""

import abc
import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class Fetcher(abc.ABC):
    """Abstract fetcher that defines the fetch interface."""

    @abc.abstractmethod
    def fetch(self, ticker: str, **kwargs: Any) -> Any:
        """Fetch raw data for a ticker symbol.

        Args:
            ticker: Stock symbol.
            **kwargs: Additional parameters for the fetch call.

        Returns:
            Raw data (typically a DataFrame or dict of DataFrames).
        """
        raise NotImplementedError


class StockFetcher(Fetcher, abc.ABC):
    """Base fetcher that wraps claude_finance_kit.stock.Stock provider calls.

    Subclasses implement _call() to specify which Stock method to invoke.
    Handles errors with logging; re-raises for the scheduler to catch.
    """

    def _call(self, ticker: str, **kwargs: Any) -> Any:
        raise NotImplementedError

    def fetch(self, ticker: str, **kwargs: Any) -> Any:
        try:
            result = self._call(ticker, **kwargs)
            if isinstance(result, pd.DataFrame):
                logger.debug("Fetched %d rows for %s", len(result), ticker)
            return result
        except Exception as exc:
            logger.error("Error fetching data for %s: %s", ticker, exc)
            raise
