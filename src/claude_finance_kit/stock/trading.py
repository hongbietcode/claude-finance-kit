"""Stock trading data: price depth."""

import pandas as pd

from claude_finance_kit._provider._base import StockProvider


class Trading:
    def __init__(self, symbol: str, provider: StockProvider):
        self._symbol = symbol
        self._provider = provider

    def price_depth(self) -> pd.DataFrame:
        return self._provider.price_depth(self._symbol)
