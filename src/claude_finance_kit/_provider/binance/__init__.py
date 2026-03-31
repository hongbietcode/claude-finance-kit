"""Binance crypto data provider (public API, no key required)."""

import pandas as pd

from claude_finance_kit._provider._base import StockProvider
from claude_finance_kit._provider._registry import registry
from claude_finance_kit._provider.binance.quote import BinanceQuote


class BinanceStockProvider(StockProvider):
    """Crypto data provider backed by Binance public API.

    No API key required. Symbols use Binance format: BTCUSDT, ETHUSDT, etc.
    Supports: history, intraday, price_depth.
    """

    def __init__(self) -> None:
        self._quote = BinanceQuote()

    def history(self, symbol, start, end=None, interval="1D"):
        return self._quote.history(symbol, start, end, interval)

    def intraday(self, symbol):
        return self._quote.intraday(symbol)

    def price_board(self, symbols):
        raise NotImplementedError("Binance does not support price_board().")

    def company_overview(self, symbol):
        raise NotImplementedError("Binance does not support company_overview().")

    def shareholders(self, symbol):
        raise NotImplementedError("Binance does not support shareholders().")

    def income_statement(self, symbol, period="quarter"):
        raise NotImplementedError("Binance does not support income_statement().")

    def balance_sheet(self, symbol, period="quarter"):
        raise NotImplementedError("Binance does not support balance_sheet().")

    def cash_flow(self, symbol, period="quarter"):
        raise NotImplementedError("Binance does not support cash_flow().")

    def ratio(self, symbol, period="quarter"):
        raise NotImplementedError("Binance does not support ratio().")

    def all_symbols(self, exchange=None):
        raise NotImplementedError("Binance does not support all_symbols().")

    def symbols_by_group(self, group):
        raise NotImplementedError("Binance does not support symbols_by_group().")

    def symbols_by_industries(self):
        raise NotImplementedError("Binance does not support symbols_by_industries().")

    def price_depth(self, symbol):
        return self._quote.price_depth(symbol)


registry.register_stock("BINANCE", BinanceStockProvider)

__all__ = ["BinanceStockProvider"]
