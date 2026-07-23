"""Canonical model and timestamp validation tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from claude_finance_kit.core.models import (
    Bar,
    MarketEvent,
    MarketRecord,
    OrderBookLevel,
    OrderBookSnapshot,
    ProviderDescriptor,
    ProviderProvenance,
    Signal,
    TradeTick,
    UnusualFlowEvent,
)
from claude_finance_kit.core.types import FeedHealth, MarketRegime, MarketRegion, ProviderCapability, SignalAction


def test_provider_descriptor_normalizes_source_and_keeps_capabilities_frozen():
    descriptor = ProviderDescriptor(
        source="alpaca",
        markets={MarketRegion.US},
        capabilities={ProviderCapability.HISTORICAL_BARS, ProviderCapability.PRICE_BOARD},
    )

    assert descriptor.source == "ALPACA"
    assert descriptor.markets == frozenset({MarketRegion.US})
    assert descriptor.capabilities == frozenset({ProviderCapability.HISTORICAL_BARS, ProviderCapability.PRICE_BOARD})


def test_provider_provenance_normalizes_naive_timestamps_to_utc():
    provenance = ProviderProvenance(
        source="dnse",
        market=MarketRegion.VN,
        fetched_at=datetime(2026, 7, 23, 9, 0, 0),
    )

    assert provenance.source == "dnse"
    assert provenance.fetched_at.tzinfo is UTC
    assert provenance.fetched_at.hour == 9


def test_market_record_rejects_naive_timestamps():
    with pytest.raises(ValidationError, match="timezone-aware"):
        MarketRecord(
            symbol="fpt",
            market=MarketRegion.VN,
            timestamp=datetime(2026, 7, 23, 9, 0, 0),
            source="vci",
            exchange_timezone="Asia/Ho_Chi_Minh",
        )


def test_trade_tick_and_order_book_models_uppercase_identifiers():
    trade = TradeTick(
        symbol="fpt",
        market=MarketRegion.VN,
        timestamp=datetime(2026, 7, 23, 9, 0, tzinfo=UTC),
        source="dnse",
        exchange_timezone="Asia/Ho_Chi_Minh",
        price=123.5,
        volume=200,
        side="buy",
        trade_id="t-1",
        board="G1",
        is_block_trade=True,
    )
    book = OrderBookSnapshot(
        symbol="aapl",
        market=MarketRegion.US,
        timestamp=datetime(2026, 7, 23, 9, 30, tzinfo=UTC),
        source="alpaca",
        exchange_timezone="America/New_York",
        bids=[OrderBookLevel(price=123.0, volume=10)],
        asks=[OrderBookLevel(price=124.0, volume=12)],
    )

    assert trade.symbol == "FPT"
    assert trade.source == "DNSE"
    assert trade.notional == pytest.approx(24_700)
    assert book.symbol == "AAPL"
    assert book.source == "ALPACA"


def test_flow_signal_and_market_event_timestamps_normalize_to_utc():
    flow = UnusualFlowEvent(
        symbol="fpt",
        market=MarketRegion.VN,
        timestamp=datetime(2026, 7, 23, 9, 0),
        score=75,
        direction="buy",
        evidence={"notional": 1_000_000},
    )
    signal = Signal(
        symbol="fpt",
        market=MarketRegion.US,
        timestamp=datetime(2026, 7, 23, 9, 30),
        action=SignalAction.BUY,
        confidence=80,
        regime=MarketRegime.BULL,
        strategy="trend-momentum",
    )
    event = MarketEvent(
        event_type="health",
        health=FeedHealth.HEALTHY,
        received_at=datetime(2026, 7, 23, 9, 0),
    )

    assert flow.symbol == "FPT"
    assert flow.timestamp.tzinfo is UTC
    assert signal.symbol == "FPT"
    assert signal.timestamp.tzinfo is UTC
    assert event.received_at.tzinfo is UTC


def test_bar_model_uppercases_identifiers_and_keeps_utc_timestamp():
    bar = Bar(
        symbol="fpt",
        market=MarketRegion.VN,
        timestamp=datetime(2026, 7, 23, 9, 0, tzinfo=UTC),
        source="dnse",
        exchange_timezone="Asia/Ho_Chi_Minh",
        open=10,
        high=11,
        low=9,
        close=10.5,
        volume=1_000,
    )

    assert bar.symbol == "FPT"
    assert bar.timestamp.tzinfo is UTC
    assert bar.interval == "1D"
    assert bar.adjusted is False
