"""Central registry mapping source names to provider classes."""

from collections.abc import Iterable

from claude_finance_kit._provider._base import (
    AsyncStreamProvider,
    CommodityProvider,
    FundProvider,
    MacroProvider,
    MarketProvider,
    StockProvider,
)
from claude_finance_kit.core.exceptions import SourceNotAvailableError
from claude_finance_kit.core.models import ProviderDescriptor
from claude_finance_kit.core.types import MarketRegion, ProviderCapability

_LEGACY_STOCK_DESCRIPTORS: dict[str, ProviderDescriptor] = {
    "VCI": ProviderDescriptor(
        source="VCI",
        markets={MarketRegion.VN},
        capabilities={
            ProviderCapability.HISTORICAL_BARS,
            ProviderCapability.INTRADAY,
            ProviderCapability.PRICE_BOARD,
            ProviderCapability.ORDER_BOOK,
            ProviderCapability.COMPANY,
            ProviderCapability.FUNDAMENTALS,
            ProviderCapability.LISTING,
        },
    ),
    "KBS": ProviderDescriptor(
        source="KBS",
        markets={MarketRegion.VN},
        capabilities={
            ProviderCapability.HISTORICAL_BARS,
            ProviderCapability.INTRADAY,
            ProviderCapability.PRICE_BOARD,
            ProviderCapability.ORDER_BOOK,
            ProviderCapability.COMPANY,
            ProviderCapability.FUNDAMENTALS,
            ProviderCapability.LISTING,
        },
    ),
    "MAS": ProviderDescriptor(
        source="MAS",
        markets={MarketRegion.VN},
        capabilities={
            ProviderCapability.HISTORICAL_BARS,
            ProviderCapability.INTRADAY,
            ProviderCapability.ORDER_BOOK,
            ProviderCapability.FUNDAMENTALS,
        },
    ),
    "MSN": ProviderDescriptor(
        source="MSN",
        markets={MarketRegion.VN},
        capabilities={ProviderCapability.HISTORICAL_BARS, ProviderCapability.LISTING},
    ),
    "TVS": ProviderDescriptor(
        source="TVS",
        markets={MarketRegion.VN},
        capabilities={ProviderCapability.COMPANY},
    ),
    "VDS": ProviderDescriptor(
        source="VDS",
        markets={MarketRegion.VN},
        capabilities={ProviderCapability.INTRADAY},
    ),
    "FMP": ProviderDescriptor(
        source="FMP",
        markets={MarketRegion.US},
        capabilities={
            ProviderCapability.HISTORICAL_BARS,
            ProviderCapability.INTRADAY,
            ProviderCapability.COMPANY,
            ProviderCapability.FUNDAMENTALS,
        },
        requires_auth=True,
        auth_type="api_key",
        delayed_seconds=900,
        coverage="free-tier-limited",
    ),
}


class ProviderRegistry:
    """Singleton-style registry for all provider types."""

    _stock: dict[str, type[StockProvider]] = {}
    _market: dict[str, type[MarketProvider]] = {}
    _macro: dict[str, type[MacroProvider]] = {}
    _fund: dict[str, type[FundProvider]] = {}
    _commodity: dict[str, type[CommodityProvider]] = {}
    _stream: dict[str, type[AsyncStreamProvider]] = {}
    _descriptors: dict[str, ProviderDescriptor] = {}
    _stock_descriptors: dict[str, ProviderDescriptor] = {}
    _stream_descriptors: dict[str, ProviderDescriptor] = {}

    _defaults: dict[str, str] = {
        "stock": "VCI",
        "market": "VND",
        "macro": "MBK",
        "fund": "FMARKET",
        "commodity": "SPL",
    }

    @classmethod
    def _store_descriptor(cls, descriptor: ProviderDescriptor) -> None:
        existing = cls._descriptors.get(descriptor.source)
        if existing is None:
            cls._descriptors[descriptor.source] = descriptor
            return
        cls._descriptors[descriptor.source] = existing.model_copy(
            update={
                "markets": existing.markets | descriptor.markets,
                "capabilities": existing.capabilities | descriptor.capabilities,
                "requires_auth": existing.requires_auth or descriptor.requires_auth,
                "auth_type": (
                    descriptor.auth_type
                    if existing.auth_type == "none"
                    else existing.auth_type
                ),
                "realtime": existing.realtime or descriptor.realtime,
                "delayed_seconds": max(existing.delayed_seconds, descriptor.delayed_seconds),
                "coverage": (
                    descriptor.coverage
                    if existing.coverage == "full" and descriptor.coverage != "full"
                    else existing.coverage
                ),
                "max_stream_symbols": descriptor.max_stream_symbols or existing.max_stream_symbols,
                "schema_version": descriptor.schema_version,
            }
        )

    @classmethod
    def register_stock(
        cls,
        source: str,
        provider_cls: type[StockProvider],
        descriptor: ProviderDescriptor | None = None,
    ) -> None:
        key = source.upper()
        cls._stock[key] = provider_cls
        resolved = descriptor or _LEGACY_STOCK_DESCRIPTORS.get(key)
        if resolved is not None:
            cls._stock_descriptors[key] = resolved
            cls._store_descriptor(resolved)

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
    def register_stream(
        cls,
        source: str,
        provider_cls: type[AsyncStreamProvider],
        descriptor: ProviderDescriptor | None = None,
    ) -> None:
        key = source.upper()
        cls._stream[key] = provider_cls
        if descriptor is not None:
            cls._stream_descriptors[key] = descriptor
            cls._store_descriptor(descriptor)

    @classmethod
    def get_stream(cls, source: str) -> type[AsyncStreamProvider]:
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
    def get_descriptor(cls, source: str) -> ProviderDescriptor:
        key = source.upper()
        if key not in cls._descriptors:
            raise SourceNotAvailableError(key, list(cls._descriptors))
        return cls._descriptors[key]

    @classmethod
    def list_descriptors(
        cls,
        market: MarketRegion | str | None = None,
        capability: ProviderCapability | str | None = None,
    ) -> list[ProviderDescriptor]:
        market_value = MarketRegion(market) if market is not None else None
        capability_value = ProviderCapability(capability) if capability is not None else None
        return [
            descriptor
            for descriptor in cls._descriptors.values()
            if (market_value is None or market_value in descriptor.markets)
            and (capability_value is None or capability_value in descriptor.capabilities)
        ]

    @classmethod
    def stock_sources_for(
        cls,
        market: MarketRegion | str,
        capability: ProviderCapability | str,
        preferred: Iterable[str] | None = None,
    ) -> list[str]:
        market_value = MarketRegion(market)
        capability_value = ProviderCapability(capability)
        supported = {
            descriptor.source
            for descriptor in cls._stock_descriptors.values()
            if market_value in descriptor.markets
            and capability_value in descriptor.capabilities
            and descriptor.source in cls._stock
        }
        if preferred is None:
            if market_value is MarketRegion.VN:
                preferred = ["DNSE", "SSI", "VCI", "KBS", "MAS"]
            elif capability_value in {
                ProviderCapability.COMPANY,
                ProviderCapability.FUNDAMENTALS,
                ProviderCapability.FILINGS,
            }:
                preferred = ["SEC", "FMP"]
            else:
                preferred = ["ALPACA", "FMP", "SEC"]
        ordered = [source.upper() for source in preferred if source.upper() in supported]
        ordered.extend(sorted(supported.difference(ordered)))
        return ordered

    @classmethod
    def set_default(cls, provider_type: str, source: str) -> None:
        if provider_type not in cls._defaults:
            raise ValueError(f"Unknown provider type: '{provider_type}'")
        cls._defaults[provider_type] = source.upper()


registry = ProviderRegistry()
