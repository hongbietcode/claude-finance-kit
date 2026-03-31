"""User-facing macro economics API."""

import pandas as pd

from claude_finance_kit._provider import mbk  # noqa: F401 — trigger provider registration
from claude_finance_kit._provider._registry import registry


class Macro:
    """High-level macroeconomic data interface delegating to a MacroProvider."""

    def __init__(self, source: str = "MBK") -> None:
        self._provider = registry.get_macro(source)()

    def gdp(self, start: str | None = None, end: str | None = None, period: str = "quarter") -> pd.DataFrame:
        """GDP data. period: 'quarter' or 'year'."""
        return self._provider.gdp(start, end, period)

    def cpi(self, length: str = "2Y", period: str = "month") -> pd.DataFrame:
        """CPI data. period: 'month' or 'year'."""
        return self._provider.cpi(length, period)

    def interest_rate(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """Interest rate data (daily pivot table)."""
        return self._provider.interest_rate(start, end)

    def exchange_rate(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """Exchange rate data (daily)."""
        return self._provider.exchange_rate(start, end)

    def fdi(self, start: str | None = None, end: str | None = None, period: str = "month") -> pd.DataFrame:
        """Foreign Direct Investment data. period: 'month' or 'year'."""
        return self._provider.fdi(start, end, period)

    def trade_balance(self, start: str | None = None, end: str | None = None, period: str = "month") -> pd.DataFrame:
        """Import/export trade balance data. period: 'month' or 'year'."""
        return self._provider.trade_balance(start, end, period)
