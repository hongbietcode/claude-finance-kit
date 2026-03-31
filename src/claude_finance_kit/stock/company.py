"""Stock company data: overview, shareholders, officers, news, events."""

import pandas as pd

from claude_finance_kit._provider._base import StockProvider


class Company:
    def __init__(self, symbol: str, provider: StockProvider):
        self._symbol = symbol
        self._provider = provider

    def overview(self) -> pd.DataFrame:
        return self._provider.company_overview(self._symbol)

    def shareholders(self) -> pd.DataFrame:
        return self._provider.shareholders(self._symbol)

    def officers(self, **kwargs) -> pd.DataFrame:
        return self._provider.officers(self._symbol, **kwargs)

    def news(self, limit: int = 20, **kwargs) -> pd.DataFrame:
        return self._provider.company_news(self._symbol, limit=limit, **kwargs)

    def events(self, **kwargs) -> pd.DataFrame:
        return self._provider.company_events(self._symbol, **kwargs)
