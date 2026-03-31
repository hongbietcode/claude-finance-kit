"""Abstract base classes for all provider types."""

from abc import ABC, abstractmethod

import pandas as pd


class StockProvider(ABC):
    """Full stock data provider: quote, company, finance, listing, trading."""

    @abstractmethod
    def history(
        self,
        symbol: str,
        start: str,
        end: str | None = None,
        interval: str = "1D",
    ) -> pd.DataFrame: ...

    @abstractmethod
    def intraday(self, symbol: str) -> pd.DataFrame: ...

    @abstractmethod
    def price_board(self, symbols: list[str]) -> pd.DataFrame: ...

    @abstractmethod
    def company_overview(self, symbol: str) -> pd.DataFrame: ...

    @abstractmethod
    def shareholders(self, symbol: str) -> pd.DataFrame: ...

    def officers(self, symbol: str, **kwargs) -> pd.DataFrame:
        raise NotImplementedError(f"{type(self).__name__} does not support officers().")

    def company_news(self, symbol: str, **kwargs) -> pd.DataFrame:
        raise NotImplementedError(f"{type(self).__name__} does not support company_news().")

    def company_events(self, symbol: str, **kwargs) -> pd.DataFrame:
        raise NotImplementedError(f"{type(self).__name__} does not support company_events().")

    @abstractmethod
    def income_statement(self, symbol: str, period: str = "quarter") -> pd.DataFrame: ...

    @abstractmethod
    def balance_sheet(self, symbol: str, period: str = "quarter") -> pd.DataFrame: ...

    @abstractmethod
    def cash_flow(self, symbol: str, period: str = "quarter") -> pd.DataFrame: ...

    @abstractmethod
    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame: ...

    @abstractmethod
    def all_symbols(self, exchange: str | None = None) -> pd.DataFrame: ...

    @abstractmethod
    def symbols_by_group(self, group: str) -> pd.DataFrame: ...

    @abstractmethod
    def symbols_by_industries(self) -> pd.DataFrame: ...

    @abstractmethod
    def price_depth(self, symbol: str) -> pd.DataFrame: ...


class MarketProvider(ABC):
    """Market-level data: P/E, P/B, top movers."""

    @abstractmethod
    def pe(self, index: str, duration: str = "5Y") -> pd.DataFrame: ...

    @abstractmethod
    def pb(self, index: str, duration: str = "5Y") -> pd.DataFrame: ...

    @abstractmethod
    def top_gainer(self, index: str, limit: int = 10) -> pd.DataFrame: ...

    @abstractmethod
    def top_loser(self, index: str, limit: int = 10) -> pd.DataFrame: ...

    def top_liquidity(self, index: str, limit: int = 10) -> pd.DataFrame:
        raise NotImplementedError("top_liquidity() not implemented by this provider")


class MacroProvider(ABC):
    """Macroeconomic data provider."""

    @abstractmethod
    def gdp(self, start: str | None = None, end: str | None = None, period: str = "quarter") -> pd.DataFrame: ...

    @abstractmethod
    def cpi(self, length: str = "2Y", period: str = "month") -> pd.DataFrame: ...

    @abstractmethod
    def interest_rate(self, start: str | None = None, end: str | None = None) -> pd.DataFrame: ...

    def exchange_rate(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        raise NotImplementedError("exchange_rate() not implemented by this provider")

    def fdi(self, start: str | None = None, end: str | None = None, period: str = "month") -> pd.DataFrame:
        raise NotImplementedError("fdi() not implemented by this provider")

    def trade_balance(self, start: str | None = None, end: str | None = None, period: str = "month") -> pd.DataFrame:
        raise NotImplementedError("trade_balance() not implemented by this provider")


class FundProvider(ABC):
    """Mutual fund data provider."""

    @abstractmethod
    def listing(self, fund_type: str = "STOCK") -> pd.DataFrame: ...

    @abstractmethod
    def fund_filter(self, symbol: str) -> pd.DataFrame: ...

    @abstractmethod
    def top_holding(self, fund_id: str) -> pd.DataFrame: ...

    @abstractmethod
    def industry_holding(self, fund_id: str) -> pd.DataFrame: ...

    @abstractmethod
    def nav_report(self, fund_id: str) -> pd.DataFrame: ...

    def asset_holding(self, fund_id: str) -> pd.DataFrame:
        raise NotImplementedError("asset_holding() not implemented by this provider")


class CommodityProvider(ABC):
    """Commodity price data provider."""

    @abstractmethod
    def gold(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame: ...

    @abstractmethod
    def oil(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame: ...

    @abstractmethod
    def steel(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame: ...

    def gas(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        raise NotImplementedError("gas() not implemented by this provider")

    def fertilizer(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        raise NotImplementedError("fertilizer() not implemented by this provider")

    def agricultural(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        raise NotImplementedError("agricultural() not implemented by this provider")


class StreamProvider(ABC):
    """Real-time streaming data provider."""

    @abstractmethod
    def connect(self, symbols: list[str], on_message) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...
