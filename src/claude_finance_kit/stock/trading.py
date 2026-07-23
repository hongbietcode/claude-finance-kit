"""Stock trading data: price depth."""

import pandas as pd

from claude_finance_kit._provider._base import StockProvider


class Trading:
    def __init__(self, symbol: str, provider: StockProvider):
        self._symbol = symbol
        self._provider = provider

    def price_depth(self) -> pd.DataFrame:
        return self._provider.price_depth(self._symbol)

    def trades(
        self,
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        return self._provider.trades(self._symbol, start, end, limit)

    def order_book(
        self,
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        return self._provider.order_book(self._symbol, start, end, limit)

    def foreign_flow(
        self,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        return self._provider.foreign_flow(self._symbol, start, end)

    def filings(self, limit: int = 40) -> pd.DataFrame:
        return self._provider.filings(self._symbol, limit)
