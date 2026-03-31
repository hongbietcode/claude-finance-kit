"""Stock financial data: balance sheet, income statement, cash flow, ratios."""

import pandas as pd

from claude_finance_kit._provider._base import StockProvider


class Finance:
    def __init__(self, symbol: str, provider: StockProvider):
        self._symbol = symbol
        self._provider = provider

    def balance_sheet(self, period: str = "quarter") -> pd.DataFrame:
        return self._provider.balance_sheet(self._symbol, period)

    def income_statement(self, period: str = "quarter") -> pd.DataFrame:
        return self._provider.income_statement(self._symbol, period)

    def cash_flow(self, period: str = "quarter") -> pd.DataFrame:
        return self._provider.cash_flow(self._symbol, period)

    def ratio(self, period: str = "quarter") -> pd.DataFrame:
        return self._provider.ratio(self._symbol, period)
