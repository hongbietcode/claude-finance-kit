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
    ClaudeFinanceKitError,
    DataNotFoundError,
    InvalidDateRangeError,
    InvalidSymbolError,
    ProviderError,
    RateLimitError,
    SourceNotAvailableError,
)
from claude_finance_kit.core.models import DateRange, StockInfo
from claude_finance_kit.core.types import AssetType, DataSource, Exchange, InstrumentType, Interval


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
    "INDICES_INFO",
    "INDICES_MAP",
    "INDEX_GROUPS",
    "INDEX_ALIASES",
    "SECTOR_IDS",
    "EXCHANGES",
    "StockInfo",
    "DateRange",
]
