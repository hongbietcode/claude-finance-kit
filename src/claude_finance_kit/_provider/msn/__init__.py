"""MSN Finance quote provider."""

from claude_finance_kit._provider._base import StockProvider
from claude_finance_kit._provider._registry import registry
from claude_finance_kit._provider.msn.quote import MSNQuote


class MSNStockProvider(StockProvider):
    """Historical quote-only provider backed by MSN Finance."""

    def __init__(self, api_version: str = "20240430") -> None:
        self._quote = MSNQuote(api_version=api_version)

    def history(self, symbol, start, end=None, interval="1D"):
        return self._quote.history(symbol, start, end, interval)

    def intraday(self, symbol):
        raise NotImplementedError("MSN does not support intraday().")

    def price_board(self, symbols):
        raise NotImplementedError("MSN does not support price_board().")

    def company_overview(self, symbol):
        raise NotImplementedError("MSN does not support company_overview().")

    def shareholders(self, symbol):
        raise NotImplementedError("MSN does not support shareholders().")

    def income_statement(self, symbol, period="quarter"):
        raise NotImplementedError("MSN does not support income_statement().")

    def balance_sheet(self, symbol, period="quarter"):
        raise NotImplementedError("MSN does not support balance_sheet().")

    def cash_flow(self, symbol, period="quarter"):
        raise NotImplementedError("MSN does not support cash_flow().")

    def ratio(self, symbol, period="quarter"):
        raise NotImplementedError("MSN does not support ratio().")

    def all_symbols(self, exchange=None):
        raise NotImplementedError("MSN does not provide a complete symbol listing.")

    def symbols_by_group(self, group):
        raise NotImplementedError("MSN does not support symbols_by_group().")

    def symbols_by_industries(self):
        raise NotImplementedError("MSN does not support symbols_by_industries().")

    def price_depth(self, symbol):
        raise NotImplementedError("MSN does not support price_depth().")


registry.register_stock("MSN", MSNStockProvider)

__all__ = ["MSNStockProvider"]
