"""Deterministic unusual-flow detector edge cases."""

from datetime import UTC, datetime, timedelta

from claude_finance_kit.core.models import OrderBookLevel, OrderBookSnapshot, TradeTick
from claude_finance_kit.core.types import MarketRegion
from claude_finance_kit.monitor.flow import UnusualFlowConfig, UnusualFlowDetector

START = datetime(2026, 7, 23, 2, 0, tzinfo=UTC)


def _trade(
    seconds: int,
    *,
    price: float = 10,
    volume: float = 100,
    side: str = "buy",
    market: MarketRegion = MarketRegion.VN,
    block: bool = False,
) -> TradeTick:
    return TradeTick(
        symbol="FPT" if market is MarketRegion.VN else "AAPL",
        market=market,
        timestamp=START + timedelta(seconds=seconds),
        source="DNSE" if market is MarketRegion.VN else "ALPACA",
        exchange_timezone="Asia/Ho_Chi_Minh" if market is MarketRegion.VN else "America/New_York",
        price=price,
        volume=volume,
        side=side,
        trade_id=f"{market.value}-{seconds}",
        is_block_trade=block,
    )


def _detector(**overrides) -> UnusualFlowDetector:
    return UnusualFlowDetector(
        UnusualFlowConfig(
            min_history_trades=overrides.pop("min_history_trades", 3),
            large_trade_quantile=overrides.pop("large_trade_quantile", 0.5),
            alert_threshold=overrides.pop("alert_threshold", 20),
            **overrides,
        )
    )


def test_detector_requires_warmup_and_excludes_block_trades():
    detector = _detector()

    assert detector.update_trade(_trade(0)) is None
    assert detector.update_trade(_trade(1)) is None
    assert detector.update_trade(_trade(2)) is None
    assert detector.update_trade(_trade(3, volume=10_000, block=True)) is None

    event = detector.update_trade(_trade(4, volume=500))

    assert event is not None
    assert event.evidence["notional"] == 5_000


def test_executed_price_sweep_is_detected_from_multiple_levels():
    detector = _detector(cluster_window_seconds=300)
    for offset in (-900, -899, -898):
        detector.update_trade(_trade(offset, price=9, volume=10))

    detector.update_trade(_trade(0, price=10, volume=100))
    detector.update_trade(_trade(1, price=11, volume=100))
    event = detector.update_trade(_trade(2, price=12, volume=100))

    assert event is not None
    assert event.evidence["sweep_levels"] == 3
    assert event.evidence["sweep_confirmed"] is True


def test_quote_spoof_alone_cannot_confirm_flow():
    detector = _detector()
    detector.update_order_book(
        OrderBookSnapshot(
            symbol="FPT",
            market=MarketRegion.VN,
            timestamp=START,
            source="DNSE",
            exchange_timezone="Asia/Ho_Chi_Minh",
            bids=[OrderBookLevel(price=10, volume=1_000_000)],
            asks=[OrderBookLevel(price=10.1, volume=1)],
        )
    )
    for offset in range(3):
        detector.update_trade(_trade(offset, side="unknown"))

    event = detector.update_trade(_trade(4, volume=10_000, side="unknown"))

    assert event is not None
    assert event.direction == "neutral"
    assert event.confirmed is False


def test_partial_iex_coverage_never_confirms_whale_flow():
    detector = _detector(alert_threshold=1, imbalance_threshold=0)
    for offset in range(3):
        detector.update_trade(_trade(offset, market=MarketRegion.US, volume=10))

    event = detector.update_trade(_trade(4, market=MarketRegion.US, volume=100_000))

    assert event is not None
    assert event.confirmed is False
    assert event.source == "ALPACA"
    assert event.coverage_warning == "partial IEX coverage; whale confirmation disabled"


def test_detector_keeps_a_bounded_rolling_baseline():
    detector = _detector(max_history_trades=5, min_history_trades=1)

    for offset in range(20):
        detector.update_trade(_trade(offset, volume=offset + 1))

    assert len(detector.trades["FPT"]) == 5
    assert len(detector.sorted_notionals["FPT"]) == 5
    assert len(detector.trade_ids["FPT"]) == 5
