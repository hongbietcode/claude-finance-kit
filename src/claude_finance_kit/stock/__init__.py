"""User-facing stock data API."""

from functools import cached_property

from claude_finance_kit._provider import (  # noqa: F401 — trigger registration
    alpaca,
    binance,
    dnse,
    fmp,
    kbs,
    mas,
    msn,
    sec,
    ssi,
    tvs,
    vci,
    vds,
)
from claude_finance_kit._provider._auto import AutoStockProvider
from claude_finance_kit._provider._registry import registry
from claude_finance_kit.core.types import MarketRegion
from claude_finance_kit.stock.company import Company
from claude_finance_kit.stock.financial import Finance
from claude_finance_kit.stock.listing import Listing
from claude_finance_kit.stock.quote import Quote
from claude_finance_kit.stock.trading import Trading


class Stock:
    """Main stock data facade.

    Usage:
        stock = Stock("FPT")
        stock.quote.history(start="2024-01-01")
        stock.company.overview()
        stock.finance.balance_sheet(period="quarter")
    """

    def __init__(
        self,
        symbol: str,
        source: str = "VCI",
        market: MarketRegion | str | None = None,
        fallback_sources: list[str] | None = None,
        provider_options: dict[str, dict] | None = None,
        **kwargs,
    ):
        self._symbol = symbol.upper()
        self._source = source.upper()
        self._market = MarketRegion(market) if market is not None else None
        if self._source == "AUTO":
            if self._market is None:
                raise ValueError("market='VN' or market='US' is required when source='AUTO'")
            self._provider = AutoStockProvider(
                market=self._market,
                fallback_sources=fallback_sources,
                provider_options=provider_options,
            )
        else:
            self._provider = registry.get_stock(self._source)(**kwargs)

    @cached_property
    def quote(self) -> Quote:
        return Quote(self._symbol, self._provider)

    @cached_property
    def company(self) -> Company:
        return Company(self._symbol, self._provider)

    @cached_property
    def finance(self) -> Finance:
        return Finance(self._symbol, self._provider)

    @cached_property
    def listing(self) -> Listing:
        return Listing(self._symbol, self._provider)

    @cached_property
    def trading(self) -> Trading:
        return Trading(self._symbol, self._provider)

    def __repr__(self) -> str:
        market = f", market={self._market.value!r}" if self._market else ""
        return f"Stock(symbol={self._symbol!r}, source={self._source!r}{market})"


__all__ = ["Stock", "Quote", "Company", "Finance", "Listing", "Trading"]
