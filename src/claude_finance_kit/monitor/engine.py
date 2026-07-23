"""End-to-end market monitor runtime."""

from __future__ import annotations

import asyncio
import json
import os
from collections import defaultdict, deque
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from claude_finance_kit.core.models import (
    Bar,
    ForeignFlow,
    MarketEvent,
    OrderBookSnapshot,
    Signal,
    TradeTick,
    UnusualFlowEvent,
)
from claude_finance_kit.core.types import FeedHealth, MarketRegion, SignalAction
from claude_finance_kit.monitor.config import MonitorConfig
from claude_finance_kit.monitor.flow import UnusualFlowConfig, UnusualFlowDetector
from claude_finance_kit.monitor.paper import PaperBroker
from claude_finance_kit.monitor.polling import PollingMarketStream
from claude_finance_kit.monitor.report import write_daily_summary
from claude_finance_kit.monitor.storage import MonitorStore
from claude_finance_kit.monitor.telegram import TelegramNotifier
from claude_finance_kit.monitor.validation import valid_strategy_artifact
from claude_finance_kit.strategy.rules import Strategy, StrategyRegistry, apply_flow_overlay
from claude_finance_kit.stream import MarketStream, market_session_open


class Monitor:
    """Bounded stream → flow → strategy → paper → notification workflow."""

    def __init__(
        self,
        config: MonitorConfig,
        *,
        stream: MarketStream | None = None,
        store: MonitorStore | None = None,
        notifier: TelegramNotifier | None = None,
        strategy: Strategy | None = None,
    ) -> None:
        self.config = config
        self.store = store or MonitorStore(config.database_path)
        stream_symbols = list(config.symbols)
        if (
            "ALL" not in stream_symbols
            and config.benchmark_symbol
            and config.benchmark_symbol not in stream_symbols
        ):
            stream_symbols.append(config.benchmark_symbol)
        provider_options = dict(config.provider_options)
        provider_options.setdefault("queue_size", config.queue_size)
        if stream is not None:
            self.stream = stream
        elif self._realtime_credentials_available():
            self.stream = MarketStream(
                config.market,
                stream_symbols,
                config.source,
                stale_after=config.stale_after_seconds,
                future_skew=config.future_skew_seconds,
                provider_options=provider_options,
            )
        else:
            self.stream = PollingMarketStream(
                config.market,
                stream_symbols,
                interval_seconds=config.poll_interval_seconds,
            )
        self.notifier = notifier
        if self.notifier is None and config.telegram_enabled:
            self.notifier = TelegramNotifier()
        self.strategy = strategy or StrategyRegistry.create(
            config.strategy,
            **config.strategy_parameters,
        )
        self.detector = UnusualFlowDetector(
            UnusualFlowConfig(
                alert_threshold=config.alert_threshold,
                large_trade_quantile=config.flow_quantile,
                cluster_window_seconds=config.cluster_window_seconds,
                imbalance_threshold=config.flow_imbalance_threshold,
            )
        )
        self.paper = PaperBroker(
            config.market,
            self.store,
            config.paper_starting_cash,
            config.paper_notional,
        )
        self.raw_bars: dict[str, deque[Bar]] = defaultdict(lambda: deque(maxlen=256))
        restored_symbols = None if "ALL" in config.symbols else stream_symbols
        for restored_bar in self.store.load_market_bars(
            config.market,
            restored_symbols,
            limit_per_symbol=256,
        ):
            self.raw_bars[restored_bar.symbol].append(restored_bar)
        self.minute_trade_bars: dict[str, Bar] = {}
        self.latest_flow: dict[str, UnusualFlowEvent] = {}
        self.signals_today: deque[Signal] = deque(
            maxlen=config.daily_report_event_limit
        )
        self.flows_today: deque[UnusualFlowEvent] = deque(
            maxlen=config.daily_report_event_limit
        )
        self.reported_flow_buckets: set[tuple[str, str, int]] = set()
        self.reported_flow_bucket_order: deque[tuple[str, str, int]] = deque(
            maxlen=config.daily_report_event_limit
        )
        self.summary_date = self._market_today()
        self.running = False
        self.feed_health = FeedHealth.DISCONNECTED
        self.strategy_validation = self._load_validation()
        self.last_event_timestamps: dict[tuple[str, str], datetime] = {}
        self.event_fingerprints: set[str] = set()
        self.fingerprint_order: deque[str] = deque(maxlen=20_000)
        self._stop_lock = asyncio.Lock()
        self._closed = False
        self._last_persisted_health: FeedHealth | None = None
        self._last_health_persist_at = datetime.min.replace(tzinfo=UTC)
        self._last_outbox_retry_at = datetime.min.replace(tzinfo=UTC)

    def _realtime_credentials_available(self) -> bool:
        options = self.config.provider_options
        if self.config.source == "SSI":
            return bool(
                (options.get("consumer_id") or os.getenv("SSI_CONSUMER_ID") or os.getenv("FC_DATA_CONSUMER_ID"))
                and (
                    options.get("consumer_secret")
                    or os.getenv("SSI_CONSUMER_SECRET")
                    or os.getenv("FC_DATA_CONSUMER_SECRET")
                )
            )
        if self.config.source == "DNSE":
            return bool(
                (options.get("api_key") or os.getenv("DNSE_API_KEY"))
                and (options.get("api_secret") or os.getenv("DNSE_API_SECRET"))
            )
        return bool(
            (options.get("api_key") or os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID"))
            and (
                options.get("api_secret")
                or os.getenv("ALPACA_API_SECRET")
                or os.getenv("APCA_API_SECRET_KEY")
            )
        )

    @property
    def strategy_validated(self) -> bool:
        """Whether the configured strategy has a matching validation artifact."""

        return self.strategy_validation is not None

    def _load_validation(self) -> dict[str, object] | None:
        if not self.config.require_strategy_validation:
            return {
                "passed": True,
                "market": self.config.market.value,
                "selected_strategy": self.strategy.name,
                "strategy_parameters": self.strategy.parameters(),
            }
        path = self.config.strategy_validation_path
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        valid = valid_strategy_artifact(payload, self.config, self.strategy)
        return payload if valid else None

    def _signal_validated(self, signal: Signal) -> bool:
        if not self.config.require_strategy_validation:
            return True
        self.strategy_validation = self._load_validation()
        return bool(
            self.strategy_validation
            and self.strategy_validation.get("regime") == signal.regime.value
        )

    async def run(self) -> None:
        self.running = True
        try:
            async for event in self.stream:
                if not self.running:
                    break
                await self.process(event)
        finally:
            await self.stop()

    async def stop(self) -> None:
        async with self._stop_lock:
            if self._closed:
                return
            self.running = False
            await self.stream.stop()
            self.feed_health = FeedHealth.DISCONNECTED
            self._persist_health(self.feed_health, force=True)
            write_daily_summary(
                self.config.reports_dir,
                self.summary_date,
                self.signals_today,
                self.flows_today,
            )
            self.store.close()
            self._closed = True

    async def process(self, event: MarketEvent) -> None:
        market_today = self._market_today()
        if market_today != self.summary_date:
            write_daily_summary(
                self.config.reports_dir,
                self.summary_date,
                self.signals_today,
                self.flows_today,
            )
            self.summary_date = market_today
            self.signals_today.clear()
            self.flows_today.clear()
            self.reported_flow_buckets.clear()
            self.reported_flow_bucket_order.clear()

        await self._retry_notifications()
        if event.event_type == "health":
            self.feed_health = event.health or FeedHealth.DEGRADED
            self._persist_health(
                self.feed_health,
                event.metadata,
                event.received_at,
            )
            return

        if (
            event.record is not None
            and not market_session_open(self.config.market, event.record.timestamp)
        ):
            self.feed_health = FeedHealth.IDLE
            self._persist_health(
                self.feed_health,
                {
                    **event.metadata,
                    "reason": "event outside regular market session",
                },
                event.received_at,
            )
            return

        if event.record is not None and not self._record_is_fresh(event):
            self.feed_health = FeedHealth.STALE
            self._persist_health(
                self.feed_health,
                {
                    **event.metadata,
                    "reason": "stale, duplicate, out-of-order, or future event timestamp",
                },
                event.received_at,
            )
            return

        self.feed_health = (
            FeedHealth.DEGRADED
            if event.metadata.get("degraded")
            else FeedHealth.HEALTHY
        )
        self._persist_health(
            self.feed_health,
            event.metadata,
            event.received_at,
        )
        if isinstance(event.record, OrderBookSnapshot):
            self.detector.update_order_book(event.record)
        elif isinstance(event.record, ForeignFlow):
            self.detector.update_foreign_flow(event.record)
        elif isinstance(event.record, TradeTick):
            if event.metadata.get("index_tick"):
                if event.record.symbol == self.config.benchmark_symbol:
                    await self._aggregate_trade_bar(event.record)
                return
            flow = self.detector.update_trade(event.record)
            if flow:
                self.latest_flow[flow.symbol] = flow
                flow_bucket = (
                    flow.symbol,
                    flow.direction,
                    int(flow.timestamp.timestamp())
                    // self.config.alert_cooldown_seconds,
                )
                if (
                    flow.score >= self.config.alert_threshold
                    and flow_bucket not in self.reported_flow_buckets
                ):
                    if (
                        len(self.reported_flow_bucket_order)
                        == self.reported_flow_bucket_order.maxlen
                    ):
                        expired_bucket = self.reported_flow_bucket_order.popleft()
                        self.reported_flow_buckets.discard(expired_bucket)
                    self.reported_flow_bucket_order.append(flow_bucket)
                    self.flows_today.append(flow)
                    self.reported_flow_buckets.add(flow_bucket)
                if flow.confirmed:
                    await self._notify_flow(flow)
            if event.record.source == "SSI":
                await self._aggregate_trade_bar(event.record)
        elif isinstance(event.record, Bar):
            self.paper.on_bar(
                event.record,
                allow_entry=self.feed_health is FeedHealth.HEALTHY,
            )
            await self._process_bar(event.record)

    def _persist_health(
        self,
        health: FeedHealth,
        metadata: dict[str, object] | None = None,
        event_at: datetime | None = None,
        *,
        force: bool = False,
    ) -> None:
        now = datetime.now(UTC)
        transitioned = health is not self._last_persisted_health
        heartbeat_due = (
            now - self._last_health_persist_at
        ).total_seconds() >= self.config.health_heartbeat_seconds
        if not (force or transitioned or heartbeat_due):
            return
        self.store.update_health(
            self.config.source,
            health,
            metadata,
            event_at,
        )
        self._last_persisted_health = health
        self._last_health_persist_at = now

    def _market_today(self) -> date:
        timezone = ZoneInfo(
            "Asia/Ho_Chi_Minh"
            if self.config.market is MarketRegion.VN
            else "America/New_York"
        )
        return datetime.now(UTC).astimezone(timezone).date()

    def _record_is_fresh(self, event: MarketEvent) -> bool:
        if event.record is None:
            return True
        now = datetime.now(UTC)
        age = (now - event.record.timestamp).total_seconds()
        if age > self.config.stale_after_seconds or age < -self.config.future_skew_seconds:
            return False
        key = (event.event_type, event.record.symbol)
        previous = self.last_event_timestamps.get(key)
        if previous is not None and event.record.timestamp < previous:
            return False
        fingerprint = (
            f"{event.event_type}:{event.record.source}:"
            f"{event.record.model_dump_json(exclude_none=False)}"
        )
        if fingerprint in self.event_fingerprints:
            return False
        if len(self.fingerprint_order) == self.fingerprint_order.maxlen:
            oldest = self.fingerprint_order.popleft()
            self.event_fingerprints.discard(oldest)
        self.fingerprint_order.append(fingerprint)
        self.event_fingerprints.add(fingerprint)
        if previous is None or event.record.timestamp > previous:
            self.last_event_timestamps[key] = event.record.timestamp
        return True

    async def _aggregate_trade_bar(self, trade: TradeTick) -> None:
        """Build completed one-minute bars for trade-only streaming feeds."""

        minute = trade.timestamp.replace(second=0, microsecond=0)
        current = self.minute_trade_bars.get(trade.symbol)
        if current is not None and current.timestamp != minute:
            gap = minute - current.timestamp
            if timedelta(0) < gap <= timedelta(minutes=2):
                self.paper.on_bar(
                    current,
                    allow_entry=self.feed_health is FeedHealth.HEALTHY,
                )
                await self._process_bar(current)
            self.minute_trade_bars.pop(trade.symbol, None)
            current = None
        if current is None:
            self.minute_trade_bars[trade.symbol] = Bar(
                symbol=trade.symbol,
                market=trade.market,
                timestamp=minute,
                source=trade.source,
                exchange_timezone=trade.exchange_timezone,
                open=trade.price,
                high=trade.price,
                low=trade.price,
                close=trade.price,
                volume=trade.volume,
                interval="1m",
            )
            return
        current.high = max(current.high, trade.price)
        current.low = min(current.low, trade.price)
        current.close = trade.price
        current.volume += trade.volume

    def _strategy_bars(self, symbol: str) -> pd.DataFrame:
        rows = [
            {
                "time": item.timestamp,
                "open": item.open,
                "high": item.high,
                "low": item.low,
                "close": item.close,
                "volume": item.volume,
            }
            for item in self.raw_bars[symbol]
        ]
        frame = pd.DataFrame(rows)
        if frame.empty:
            return frame
        return (
            frame.sort_values("time")
            .drop_duplicates("time", keep="last")
            .reset_index(drop=True)
        )

    async def _process_bar(self, bar: Bar) -> None:
        self.raw_bars[bar.symbol].append(bar)
        self.store.save_market_bar(bar, limit_per_symbol=256)
        if bar.symbol == self.config.benchmark_symbol:
            return
        frame = self._strategy_bars(bar.symbol)
        benchmark = self._strategy_bars(self.config.benchmark_symbol or "")
        if len(frame) < 200 or len(benchmark) < 200:
            return
        signal = self.strategy.evaluate(
            frame,
            self.config.market,
            bar.symbol,
            benchmark=benchmark,
            source=bar.source,
        )
        flow = self.latest_flow.get(bar.symbol)
        if flow and signal.timestamp - flow.timestamp > timedelta(seconds=self.config.cluster_window_seconds):
            flow = None
        signal = apply_flow_overlay(signal, flow)
        if signal.action is SignalAction.BUY and signal.confidence < self.config.alert_threshold:
            signal.action = SignalAction.NO_TRADE
            signal.reasons.append("confidence below strict alert threshold")
        if (
            signal.action is SignalAction.BUY
            and self.config.market is MarketRegion.VN
            and not (flow and flow.confirmed and flow.direction == "buy")
        ):
            signal.action = SignalAction.NO_TRADE
            signal.reasons.append("missing confirmed buy-side unusual flow")
        if self.config.market is MarketRegion.US:
            signal.coverage_warning = (
                "partial IEX coverage; whale confirmation disabled"
                if bar.source == "ALPACA"
                else f"degraded {bar.source} polling coverage"
            )
        strategy_validated = (
            self._signal_validated(signal)
            if signal.action is SignalAction.BUY
            else True
        )
        if signal.action is SignalAction.BUY and (
            self.feed_health is not FeedHealth.HEALTHY or not strategy_validated
        ):
            signal.action = SignalAction.NO_TRADE
            signal.confidence = min(signal.confidence, 40)
            signal.reasons.append(
                "strategy lacks passing walk-forward validation"
                if not strategy_validated
                else "feed is not healthy"
            )
        if signal.action not in {
            SignalAction.BUY,
            SignalAction.HOLD,
            SignalAction.EXIT,
            SignalAction.NO_TRADE,
        }:
            return
        if signal.action is SignalAction.HOLD:
            return
        if (
            signal.action is SignalAction.EXIT
            and signal.symbol not in self.paper.positions
        ):
            return
        if signal.action is SignalAction.NO_TRADE and not any(
            "veto" in reason or "validation" in reason or "feed" in reason
            for reason in signal.reasons
        ):
            return
        bucket = signal.timestamp.replace(minute=0, second=0, microsecond=0)
        dedupe_key = (
            f"signal:{signal.market.value}:{signal.symbol}:"
            f"{signal.strategy}:{signal.action.value}:{bucket.isoformat()}"
        )
        if self.store.signal_seen(dedupe_key):
            return
        self.paper.on_signal(signal, persist=False)
        text = self._signal_text(signal)
        channel = "telegram" if self.notifier else "local"
        self.store.save_signal_state_and_notification(
            dedupe_key,
            signal,
            self.paper.state_key,
            self.paper.state_payload(),
            channel,
            text,
        )
        self.signals_today.append(signal)
        await self._deliver_notification(dedupe_key)

    async def _notify_flow(self, flow: UnusualFlowEvent) -> None:
        bucket = int(flow.timestamp.timestamp()) // self.config.alert_cooldown_seconds
        key = f"flow:{flow.market.value}:{flow.symbol}:{flow.direction}:{bucket}"
        if self.store.notification_seen(key):
            return
        text = (
            f"UNUSUAL FLOW — {flow.symbol} ({flow.market.value})\n"
            f"Time: {flow.timestamp.isoformat()} | Source: {flow.source}\n"
            f"Direction: {flow.direction.upper()} | Score: {flow.score:.1f}/100\n"
            f"OFI: {flow.evidence.get('order_flow_imbalance')} | "
            f"Notional: {flow.evidence.get('notional')}\n"
            "Classification: institutional-like flow; beneficial owner is unknown."
        )
        self.store.queue_notification(
            key,
            "telegram" if self.notifier else "local",
            text,
            flow.model_dump(mode="json"),
        )
        await self._deliver_notification(key)

    @staticmethod
    def _signal_text(signal: Signal) -> str:
        text = (
            f"{signal.action.value} — {signal.symbol} ({signal.market.value})\n"
            f"Time: {signal.timestamp.isoformat()}\n"
            f"Confidence: {signal.confidence:.1f}/100 | Regime: {signal.regime.value}\n"
            f"Price: {signal.price} | Stop: {signal.stop_loss} | Target: {signal.take_profit}\n"
            f"Strategy: {signal.strategy} | Source: {signal.source}\n"
            f"Reasons: {'; '.join(signal.reasons)}"
        )
        if signal.coverage_warning:
            text += f"\nCoverage: {signal.coverage_warning}"
        text += "\nPaper trade only. Not investment advice."
        return text

    async def _deliver_notification(self, key: str) -> None:
        notification = self.store.get_notification(key)
        if notification is None:
            return
        try:
            if self.notifier:
                await self.notifier.send(notification["text"])
        except Exception as exc:
            self.store.mark_notification_failed(key, type(exc).__name__)
            return
        self.store.mark_notification_sent(
            key,
            notification["channel"],
            notification["payload"],
        )

    async def _retry_notifications(self) -> None:
        now = datetime.now(UTC)
        if (now - self._last_outbox_retry_at).total_seconds() < 30:
            return
        self._last_outbox_retry_at = now
        for notification in self.store.pending_notifications():
            last_attempt = notification["last_attempt_at"]
            if last_attempt:
                attempted_at = datetime.fromisoformat(last_attempt).astimezone(UTC)
                delay = min(900, 30 * 2 ** min(notification["attempts"], 5))
                if (now - attempted_at).total_seconds() < delay:
                    continue
            await self._deliver_notification(notification["dedupe_key"])
