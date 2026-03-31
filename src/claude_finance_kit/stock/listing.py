"""Stock listing data: symbols, groups, industries."""

import pandas as pd

from claude_finance_kit._provider._base import StockProvider


class Listing:
    def __init__(self, symbol: str, provider: StockProvider):
        self._symbol = symbol
        self._provider = provider

    def all_symbols(self, exchange: str | None = None) -> pd.DataFrame:
        return self._provider.all_symbols(exchange)

    def symbols_by_group(self, group: str) -> pd.DataFrame:
        return self._provider.symbols_by_group(group)

    def symbols_by_industries(self) -> pd.DataFrame:
        return self._provider.symbols_by_industries()
