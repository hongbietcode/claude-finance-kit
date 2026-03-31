"""VDS (Viet Dragon Securities) Vietnamese stock data provider."""

import pandas as pd

from claude_finance_kit._provider._base import StockProvider
from claude_finance_kit._provider._registry import registry
from claude_finance_kit._provider.vds.quote import VDSQuote


class VDSStockProvider(StockProvider):
    """Vietnamese stock data provider backed by VDS API.

    Supports: intraday only.
    """

    def __init__(self) -> None:
        self._quote = VDSQuote()

    def history(self, symbol, start, end=None, interval="1D"):
        raise NotImplementedError("VDS does not support history().")

    def intraday(self, symbol: str) -> pd.DataFrame:
        return self._quote.intraday(symbol)

    def price_board(self, symbols):
        raise NotImplementedError("VDS does not support price_board().")

    def company_overview(self, symbol):
        raise NotImplementedError("VDS does not support company_overview().")

    def shareholders(self, symbol):
        raise NotImplementedError("VDS does not support shareholders().")

    def income_statement(self, symbol, period="quarter"):
        raise NotImplementedError("VDS does not support income_statement().")

    def balance_sheet(self, symbol, period="quarter"):
        raise NotImplementedError("VDS does not support balance_sheet().")

    def cash_flow(self, symbol, period="quarter"):
        raise NotImplementedError("VDS does not support cash_flow().")

    def ratio(self, symbol, period="quarter"):
        raise NotImplementedError("VDS does not support ratio().")

    def all_symbols(self, exchange=None):
        raise NotImplementedError("VDS does not support all_symbols().")

    def symbols_by_group(self, group):
        raise NotImplementedError("VDS does not support symbols_by_group().")

    def symbols_by_industries(self):
        raise NotImplementedError("VDS does not support symbols_by_industries().")

    def price_depth(self, symbol):
        raise NotImplementedError("VDS does not support price_depth().")


registry.register_stock("VDS", VDSStockProvider)

__all__ = ["VDSStockProvider"]
