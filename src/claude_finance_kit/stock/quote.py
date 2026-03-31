"""Stock quote data: history, intraday, price board."""

import pandas as pd

from claude_finance_kit._provider._base import StockProvider


class Quote:
    def __init__(self, symbol: str, provider: StockProvider):
        self._symbol = symbol
        self._provider = provider

    def history(
        self,
        start: str,
        end: str | None = None,
        interval: str = "1D",
    ) -> pd.DataFrame:
        return self._provider.history(self._symbol, start, end, interval)

    def intraday(self) -> pd.DataFrame:
        return self._provider.intraday(self._symbol)

    def price_board(self, symbols: list[str] | None = None) -> pd.DataFrame:
        target = symbols if symbols else [self._symbol]
        return self._provider.price_board(target)
