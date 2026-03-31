"""TVS (Thien Viet Securities) Vietnamese stock data provider."""

import pandas as pd

from claude_finance_kit._provider._base import StockProvider
from claude_finance_kit._provider._registry import registry
from claude_finance_kit._provider.tvs.company import TVSCompany


class TVSStockProvider(StockProvider):
    """Vietnamese stock data provider backed by TVS API.

    Supports: company_overview only.
    """

    def __init__(self) -> None:
        self._company = TVSCompany()

    def history(self, symbol, start, end=None, interval="1D"):
        raise NotImplementedError("TVS does not support history().")

    def intraday(self, symbol):
        raise NotImplementedError("TVS does not support intraday().")

    def price_board(self, symbols):
        raise NotImplementedError("TVS does not support price_board().")

    def company_overview(self, symbol: str) -> pd.DataFrame:
        return self._company.company_overview(symbol)

    def shareholders(self, symbol):
        raise NotImplementedError("TVS does not support shareholders().")

    def income_statement(self, symbol, period="quarter"):
        raise NotImplementedError("TVS does not support income_statement().")

    def balance_sheet(self, symbol, period="quarter"):
        raise NotImplementedError("TVS does not support balance_sheet().")

    def cash_flow(self, symbol, period="quarter"):
        raise NotImplementedError("TVS does not support cash_flow().")

    def ratio(self, symbol, period="quarter"):
        raise NotImplementedError("TVS does not support ratio().")

    def all_symbols(self, exchange=None):
        raise NotImplementedError("TVS does not support all_symbols().")

    def symbols_by_group(self, group):
        raise NotImplementedError("TVS does not support symbols_by_group().")

    def symbols_by_industries(self):
        raise NotImplementedError("TVS does not support symbols_by_industries().")

    def price_depth(self, symbol):
        raise NotImplementedError("TVS does not support price_depth().")


registry.register_stock("TVS", TVSStockProvider)

__all__ = ["TVSStockProvider"]
