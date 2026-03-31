"""Central registry mapping source names to provider classes."""

from claude_finance_kit._provider._base import (
    CommodityProvider,
    FundProvider,
    MacroProvider,
    MarketProvider,
    StockProvider,
    StreamProvider,
)
from claude_finance_kit.core.exceptions import SourceNotAvailableError


class ProviderRegistry:
    """Singleton-style registry for all provider types."""

    _stock: dict[str, type[StockProvider]] = {}
    _market: dict[str, type[MarketProvider]] = {}
    _macro: dict[str, type[MacroProvider]] = {}
    _fund: dict[str, type[FundProvider]] = {}
    _commodity: dict[str, type[CommodityProvider]] = {}
    _stream: dict[str, type[StreamProvider]] = {}

    _defaults: dict[str, str] = {
        "stock": "VCI",
        "market": "VND",
        "macro": "MBK",
        "fund": "FMARKET",
        "commodity": "SPL",
    }

    @classmethod
    def register_stock(cls, source: str, provider_cls: type[StockProvider]) -> None:
        cls._stock[source.upper()] = provider_cls

    @classmethod
    def get_stock(cls, source: str | None = None) -> type[StockProvider]:
        key = (source or cls._defaults["stock"]).upper()
        if key not in cls._stock:
            raise SourceNotAvailableError(key, list(cls._stock.keys()))
        return cls._stock[key]

    @classmethod
    def register_market(cls, source: str, provider_cls: type[MarketProvider]) -> None:
        cls._market[source.upper()] = provider_cls

    @classmethod
    def get_market(cls, source: str | None = None) -> type[MarketProvider]:
        key = (source or cls._defaults["market"]).upper()
        if key not in cls._market:
            raise SourceNotAvailableError(key, list(cls._market.keys()))
        return cls._market[key]

    @classmethod
    def register_macro(cls, source: str, provider_cls: type[MacroProvider]) -> None:
        cls._macro[source.upper()] = provider_cls

    @classmethod
    def get_macro(cls, source: str | None = None) -> type[MacroProvider]:
        key = (source or cls._defaults["macro"]).upper()
        if key not in cls._macro:
            raise SourceNotAvailableError(key, list(cls._macro.keys()))
        return cls._macro[key]

    @classmethod
    def register_fund(cls, source: str, provider_cls: type[FundProvider]) -> None:
        cls._fund[source.upper()] = provider_cls

    @classmethod
    def get_fund(cls, source: str | None = None) -> type[FundProvider]:
        key = (source or cls._defaults["fund"]).upper()
        if key not in cls._fund:
            raise SourceNotAvailableError(key, list(cls._fund.keys()))
        return cls._fund[key]

    @classmethod
    def register_commodity(cls, source: str, provider_cls: type[CommodityProvider]) -> None:
        cls._commodity[source.upper()] = provider_cls

    @classmethod
    def get_commodity(cls, source: str | None = None) -> type[CommodityProvider]:
        key = (source or cls._defaults["commodity"]).upper()
        if key not in cls._commodity:
            raise SourceNotAvailableError(key, list(cls._commodity.keys()))
        return cls._commodity[key]

    @classmethod
    def register_stream(cls, source: str, provider_cls: type[StreamProvider]) -> None:
        cls._stream[source.upper()] = provider_cls

    @classmethod
    def get_stream(cls, source: str) -> type[StreamProvider]:
        key = source.upper()
        if key not in cls._stream:
            raise SourceNotAvailableError(key, list(cls._stream.keys()))
        return cls._stream[key]

    @classmethod
    def list_sources(cls, provider_type: str) -> list[str]:
        store = getattr(cls, f"_{provider_type}", None)
        if store is None:
            raise ValueError(f"Unknown provider type: '{provider_type}'")
        return list(store.keys())

    @classmethod
    def set_default(cls, provider_type: str, source: str) -> None:
        if provider_type not in cls._defaults:
            raise ValueError(f"Unknown provider type: '{provider_type}'")
        cls._defaults[provider_type] = source.upper()


registry = ProviderRegistry()
