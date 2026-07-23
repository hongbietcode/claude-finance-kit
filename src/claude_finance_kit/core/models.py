"""Pydantic v2 data models for claude-finance-kit."""

from datetime import UTC, date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from claude_finance_kit.core.exceptions import InvalidDateRangeError
from claude_finance_kit.core.types import (
    Exchange,
    FeedHealth,
    MarketRegime,
    MarketRegion,
    ProviderCapability,
    SignalAction,
)


class StockInfo(BaseModel):
    """Basic stock instrument metadata."""

    symbol: str
    exchange: Exchange
    name: str
    industry: str | None = None

    @field_validator("symbol")
    @classmethod
    def symbol_upper(cls, v: str) -> str:
        return v.upper()


class DateRange(BaseModel):
    """Validated date range for historical queries."""

    start: date
    end: date

    @field_validator("end")
    @classmethod
    def end_after_start(cls, v: date, info) -> date:
        start = info.data.get("start")
        if start and v < start:
            raise InvalidDateRangeError(str(start), str(v))
        return v


class ProviderDescriptor(BaseModel):
    """Discoverable provider capabilities and data-quality constraints."""

    model_config = ConfigDict(frozen=True)

    source: str
    markets: frozenset[MarketRegion]
    capabilities: frozenset[ProviderCapability]
    requires_auth: bool = False
    auth_type: str = "none"
    realtime: bool = False
    delayed_seconds: int = 0
    coverage: str = "full"
    max_stream_symbols: int | None = None
    schema_version: str = "1"

    @field_validator("source")
    @classmethod
    def source_upper(cls, value: str) -> str:
        return value.upper()


class ProviderProvenance(BaseModel):
    """Source selection details attached to AUTO-routed results."""

    source: str
    attempted_sources: list[str] = Field(default_factory=list)
    market: MarketRegion
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data_timestamp: datetime | None = None
    delayed_seconds: int = 0
    coverage: str = "full"

    @field_validator("fetched_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @field_validator("data_timestamp")
    @classmethod
    def normalize_data_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class MarketRecord(BaseModel):
    """Common UTC-normalized fields for canonical market records."""

    symbol: str
    market: MarketRegion
    timestamp: datetime
    source: str
    exchange_timezone: str

    @field_validator("symbol", "source")
    @classmethod
    def uppercase_identifier(cls, value: str) -> str:
        return value.upper()

    @field_validator("timestamp")
    @classmethod
    def timestamp_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Market timestamps must be timezone-aware")
        return value.astimezone(UTC)


class Bar(MarketRecord):
    """Canonical OHLCV bar."""

    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    adjusted: bool = False
    interval: str = "1D"

    @model_validator(mode="after")
    def valid_price_range(self) -> "Bar":
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("Bar high/low must contain open and close")
        if self.high < self.low:
            raise ValueError("Bar high cannot be below low")
        return self


class TradeTick(MarketRecord):
    """Canonical executed trade."""

    price: float = Field(gt=0)
    volume: float = Field(ge=0)
    side: Literal["buy", "sell", "unknown"] = "unknown"
    trade_id: str | None = None
    board: str | None = None
    is_block_trade: bool = False

    @property
    def notional(self) -> float:
        return self.price * self.volume


class OrderBookLevel(BaseModel):
    """One price level in a canonical order-book snapshot."""

    price: float = Field(ge=0)
    volume: float = Field(ge=0)
    orders: int | None = None


class OrderBookSnapshot(MarketRecord):
    """Canonical top-of-book or depth snapshot."""

    bids: list[OrderBookLevel] = Field(default_factory=list)
    asks: list[OrderBookLevel] = Field(default_factory=list)


class ForeignFlow(MarketRecord):
    """Foreign investor flow for a symbol."""

    buy_volume: float = 0
    sell_volume: float = 0
    buy_value: float = 0
    sell_value: float = 0
    room: float | None = None


class MarketEvent(BaseModel):
    """Envelope consumed by the asynchronous monitor pipeline."""

    event_type: Literal["bar", "trade", "order_book", "foreign_flow", "health"]
    record: Bar | TradeTick | OrderBookSnapshot | ForeignFlow | None = None
    health: FeedHealth | None = None
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("received_at")
    @classmethod
    def received_at_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class UnusualFlowEvent(BaseModel):
    """Evidence-based unusual/institutional-like flow assessment."""

    symbol: str
    market: MarketRegion
    timestamp: datetime
    score: float = Field(ge=0, le=100)
    direction: Literal["buy", "sell", "neutral"]
    evidence: dict[str, float | int | str | bool] = Field(default_factory=dict)
    confirmed: bool = False
    source: str | None = None
    coverage_warning: str | None = None

    @field_validator("symbol")
    @classmethod
    def flow_symbol_upper(cls, value: str) -> str:
        return value.upper()

    @field_validator("source")
    @classmethod
    def flow_source_upper(cls, value: str | None) -> str | None:
        return value.upper() if value else None

    @field_validator("timestamp")
    @classmethod
    def flow_timestamp_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class Signal(BaseModel):
    """Research signal produced by a strategy and strict validation gate."""

    symbol: str
    market: MarketRegion
    timestamp: datetime
    action: SignalAction
    confidence: float = Field(ge=0, le=100)
    regime: MarketRegime = MarketRegime.UNKNOWN
    strategy: str
    price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    reasons: list[str] = Field(default_factory=list)
    source: str | None = None
    coverage_warning: str | None = None

    @field_validator("symbol")
    @classmethod
    def signal_symbol_upper(cls, value: str) -> str:
        return value.upper()

    @field_validator("timestamp")
    @classmethod
    def signal_timestamp_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class Notification(BaseModel):
    """Outbound monitor notification."""

    channel: Literal["telegram"] = "telegram"
    dedupe_key: str
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
