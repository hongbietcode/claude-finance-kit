"""Core models, constants, types, and exceptions."""

from claude_finance_kit.core.constants import (
    EXCHANGES,
    INDEX_ALIASES,
    INDEX_GROUPS,
    INDICES_INFO,
    INDICES_MAP,
    SECTOR_IDS,
)
from claude_finance_kit.core.exceptions import (
    AuthenticationError,
    ClaudeFinanceKitError,
    DataNotFoundError,
    InvalidDateRangeError,
    InvalidSymbolError,
    ProviderCapabilityError,
    ProviderError,
    RateLimitError,
    SourceNotAvailableError,
    StaleDataError,
)
from claude_finance_kit.core.models import (
    Bar,
    DateRange,
    ForeignFlow,
    MarketEvent,
    Notification,
    OrderBookLevel,
    OrderBookSnapshot,
    ProviderDescriptor,
    ProviderProvenance,
    Signal,
    StockInfo,
    TradeTick,
    UnusualFlowEvent,
)
from claude_finance_kit.core.types import (
    AssetType,
    DataSource,
    Exchange,
    FeedHealth,
    InstrumentType,
    Interval,
    MarketRegime,
    MarketRegion,
    ProviderCapability,
    SignalAction,
)


def get_asset_type(symbol: str) -> str:
    """Return the broad quote-compatible asset type for a security symbol."""
    from claude_finance_kit._internal.parser import get_asset_type as _get_asset_type

    return _get_asset_type(symbol)


def get_instrument_type(symbol: str) -> InstrumentType:
    """Return the detailed instrument type for a security symbol."""
    from claude_finance_kit._internal.parser import get_instrument_type as _get_instrument_type

    return _get_instrument_type(symbol)

__all__ = [
    "ClaudeFinanceKitError",
    "ProviderError",
    "ProviderCapabilityError",
    "AuthenticationError",
    "StaleDataError",
    "InvalidSymbolError",
    "DataNotFoundError",
    "RateLimitError",
    "SourceNotAvailableError",
    "InvalidDateRangeError",
    "Interval",
    "Exchange",
    "AssetType",
    "InstrumentType",
    "get_asset_type",
    "get_instrument_type",
    "DataSource",
    "MarketRegion",
    "ProviderCapability",
    "SignalAction",
    "MarketRegime",
    "FeedHealth",
    "INDICES_INFO",
    "INDICES_MAP",
    "INDEX_GROUPS",
    "INDEX_ALIASES",
    "SECTOR_IDS",
    "EXCHANGES",
    "StockInfo",
    "DateRange",
    "ProviderDescriptor",
    "ProviderProvenance",
    "Bar",
    "TradeTick",
    "OrderBookLevel",
    "OrderBookSnapshot",
    "ForeignFlow",
    "MarketEvent",
    "UnusualFlowEvent",
    "Signal",
    "Notification",
]
