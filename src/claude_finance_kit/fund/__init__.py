"""User-facing mutual fund API."""

import pandas as pd

from claude_finance_kit._provider import fmarket  # noqa: F401 — trigger provider registration
from claude_finance_kit._provider._registry import registry


class Fund:
    """High-level mutual fund interface delegating to a FundProvider."""

    def __init__(self, source: str = "FMARKET") -> None:
        self._provider = registry.get_fund(source)()

    def listing(self, fund_type: str = "STOCK") -> pd.DataFrame:
        """List funds by type: '', 'BALANCED', 'BOND', 'STOCK'."""
        return self._provider.listing(fund_type)

    def fund_filter(self, symbol: str) -> pd.DataFrame:
        """Search funds by short name."""
        return self._provider.fund_filter(symbol)

    def top_holding(self, fund_id: str) -> pd.DataFrame:
        """Top holdings for a fund by fund_id."""
        return self._provider.top_holding(fund_id)

    def industry_holding(self, fund_id: str) -> pd.DataFrame:
        """Industry allocation for a fund by fund_id."""
        return self._provider.industry_holding(fund_id)

    def nav_report(self, fund_id: str) -> pd.DataFrame:
        """Full NAV history for a fund by fund_id."""
        return self._provider.nav_report(fund_id)

    def asset_holding(self, fund_id: str) -> pd.DataFrame:
        """Asset allocation breakdown for a fund by fund_id."""
        return self._provider.asset_holding(fund_id)
