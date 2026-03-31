"""MAS (Mirae Asset Securities) Vietnamese stock data provider."""

import pandas as pd

from claude_finance_kit._provider._base import StockProvider
from claude_finance_kit._provider._registry import registry
from claude_finance_kit._provider.mas.financial import MASFinancial
from claude_finance_kit._provider.mas.quote import MASQuote


class MASStockProvider(StockProvider):
    """Vietnamese stock data provider backed by Mirae Asset (MAS) APIs.

    Supports: history, intraday, price_depth, financials.
    Does not support: company, listing.
    """

    def __init__(self) -> None:
        self._quote = MASQuote()
        self._financial = MASFinancial()

    def history(
        self,
        symbol: str,
        start: str,
        end: str | None = None,
        interval: str = "1D",
    ) -> pd.DataFrame:
        return self._quote.history(symbol, start, end, interval)

    def intraday(self, symbol: str) -> pd.DataFrame:
        return self._quote.intraday(symbol)

    def price_board(self, symbols: list[str]) -> pd.DataFrame:
        raise NotImplementedError("MAS does not support price_board().")

    def company_overview(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("MAS does not support company_overview().")

    def shareholders(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("MAS does not support shareholders().")

    def income_statement(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._financial.income_statement(symbol, period)

    def balance_sheet(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._financial.balance_sheet(symbol, period)

    def cash_flow(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._financial.cash_flow(symbol, period)

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._financial.ratio(symbol, period)

    def all_symbols(self, exchange: str | None = None) -> pd.DataFrame:
        raise NotImplementedError("MAS does not support all_symbols().")

    def symbols_by_group(self, group: str) -> pd.DataFrame:
        raise NotImplementedError("MAS does not support symbols_by_group().")

    def symbols_by_industries(self) -> pd.DataFrame:
        raise NotImplementedError("MAS does not support symbols_by_industries().")

    def price_depth(self, symbol: str) -> pd.DataFrame:
        return self._quote.price_depth(symbol)


registry.register_stock("MAS", MASStockProvider)

__all__ = ["MASStockProvider"]
