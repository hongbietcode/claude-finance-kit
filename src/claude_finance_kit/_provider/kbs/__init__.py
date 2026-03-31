"""KBS (KB Securities) stock data provider."""

import pandas as pd

from claude_finance_kit._provider._base import StockProvider
from claude_finance_kit._provider._registry import registry
from claude_finance_kit._provider.kbs.company import KBSCompany
from claude_finance_kit._provider.kbs.financial import KBSFinancial
from claude_finance_kit._provider.kbs.listing import KBSListing
from claude_finance_kit._provider.kbs.quote import KBSQuote
from claude_finance_kit._provider.kbs.trading import KBSTrading


class KBSStockProvider(StockProvider):
    """Full stock data provider backed by KB Securities (KBS) APIs."""

    def __init__(self) -> None:
        self._quote = KBSQuote()
        self._listing = KBSListing()
        self._company = KBSCompany()
        self._financial = KBSFinancial()
        self._trading = KBSTrading()

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
        return self._trading.price_board(symbols)

    def company_overview(self, symbol: str) -> pd.DataFrame:
        return self._company.company_overview(symbol)

    def shareholders(self, symbol: str) -> pd.DataFrame:
        return self._company.shareholders(symbol)

    def officers(self, symbol: str, **kwargs) -> pd.DataFrame:
        return self._company.officers(symbol, **kwargs)

    def company_news(self, symbol: str, **kwargs) -> pd.DataFrame:
        return self._company.company_news(symbol, **kwargs)

    def company_events(self, symbol: str, **kwargs) -> pd.DataFrame:
        return self._company.company_events(symbol, **kwargs)

    def income_statement(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._financial.income_statement(symbol, period)

    def balance_sheet(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._financial.balance_sheet(symbol, period)

    def cash_flow(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._financial.cash_flow(symbol, period)

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._financial.ratio(symbol, period)

    def all_symbols(self, exchange: str | None = None) -> pd.DataFrame:
        return self._listing.all_symbols(exchange)

    def symbols_by_group(self, group: str) -> pd.DataFrame:
        return self._listing.symbols_by_group(group)

    def symbols_by_industries(self) -> pd.DataFrame:
        return self._listing.symbols_by_industries()

    def price_depth(self, symbol: str) -> pd.DataFrame:
        return self._trading.price_depth(symbol)


registry.register_stock("KBS", KBSStockProvider)

__all__ = ["KBSStockProvider"]
