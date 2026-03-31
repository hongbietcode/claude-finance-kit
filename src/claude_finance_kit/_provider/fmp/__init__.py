"""FMP (Financial Modeling Prep) global stock data provider."""

import pandas as pd

from claude_finance_kit._provider._base import StockProvider
from claude_finance_kit._provider._registry import registry
from claude_finance_kit._provider.fmp.company import FMPCompany
from claude_finance_kit._provider.fmp.financial import FMPFinancial
from claude_finance_kit._provider.fmp.quote import FMPQuote


class FMPStockProvider(StockProvider):
    """Global stock data provider backed by Financial Modeling Prep API.

    Requires FMP_TOKEN or FMP_API_KEY environment variable, or pass
    api_key via Stock("AAPL", source="FMP", api_key="...").
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key
        self._quote = FMPQuote(api_key=api_key)
        self._company = FMPCompany(api_key=api_key)
        self._financial = FMPFinancial(api_key=api_key)

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
        raise NotImplementedError("FMP does not support price_board().")

    def company_overview(self, symbol: str) -> pd.DataFrame:
        return self._company.company_overview(symbol)

    def shareholders(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("FMP does not support shareholders().")

    def officers(self, symbol: str, **kwargs) -> pd.DataFrame:
        return self._company.officers(symbol)

    def income_statement(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._financial.income_statement(symbol, period)

    def balance_sheet(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._financial.balance_sheet(symbol, period)

    def cash_flow(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._financial.cash_flow(symbol, period)

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._financial.ratio(symbol, period)

    def all_symbols(self, exchange: str | None = None) -> pd.DataFrame:
        raise NotImplementedError("FMP does not support all_symbols().")

    def symbols_by_group(self, group: str) -> pd.DataFrame:
        raise NotImplementedError("FMP does not support symbols_by_group().")

    def symbols_by_industries(self) -> pd.DataFrame:
        raise NotImplementedError("FMP does not support symbols_by_industries().")

    def price_depth(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("FMP does not support price_depth().")


registry.register_stock("FMP", FMPStockProvider)

__all__ = ["FMPStockProvider"]
