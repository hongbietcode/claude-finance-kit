"""Evidence-based unusual-flow detector."""

from __future__ import annotations

from bisect import bisect_left, insort
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import timedelta
from math import sqrt

from claude_finance_kit.core.models import ForeignFlow, OrderBookSnapshot, TradeTick, UnusualFlowEvent
from claude_finance_kit.core.types import MarketRegion


@dataclass(slots=True)
class UnusualFlowConfig:
    alert_threshold: float = 75.0
    large_trade_quantile: float = 0.995
    cluster_window_seconds: int = 300
    imbalance_threshold: float = 0.6
    min_history_trades: int = 30
    max_history_trades: int = 500


class UnusualFlowDetector:
    """Score institutional-like flow without claiming beneficial ownership."""

    def __init__(
        self,
        config: UnusualFlowConfig | None = None,
        average_daily_volume: dict[str, float] | None = None,
    ) -> None:
        self.config = config or UnusualFlowConfig()
        self.average_daily_volume = average_daily_volume or {}
        self.trades: dict[str, deque[TradeTick]] = defaultdict(
            deque
        )
        self.trade_ids: dict[str, set[str]] = defaultdict(set)
        self.sorted_notionals: dict[str, list[float]] = defaultdict(list)
        self.notional_sum: dict[str, float] = defaultdict(float)
        self.notional_sum_squares: dict[str, float] = defaultdict(float)
        self.books: dict[str, OrderBookSnapshot] = {}
        self.foreign: dict[str, ForeignFlow] = {}

    def update_order_book(self, snapshot: OrderBookSnapshot) -> None:
        self.books[snapshot.symbol] = snapshot

    def update_foreign_flow(self, flow: ForeignFlow) -> None:
        self.foreign[flow.symbol] = flow

    @staticmethod
    def _quantile(values: list[float], quantile: float) -> float:
        if not values:
            return 0.0
        index = min(len(values) - 1, max(0, int((len(values) - 1) * quantile)))
        return values[index]

    def update_trade(self, trade: TradeTick) -> UnusualFlowEvent | None:
        symbol = trade.symbol
        if trade.trade_id:
            if trade.trade_id in self.trade_ids[symbol]:
                return None
            self.trade_ids[symbol].add(trade.trade_id)
            if len(self.trade_ids[symbol]) > self.config.max_history_trades * 2:
                self.trade_ids[symbol] = {
                    item.trade_id for item in self.trades[symbol] if item.trade_id
                }

        history = self.trades[symbol]
        if len(history) >= self.config.max_history_trades:
            expired = history.popleft()
            if not expired.is_block_trade:
                expired_notional = expired.notional
                index = bisect_left(self.sorted_notionals[symbol], expired_notional)
                if index < len(self.sorted_notionals[symbol]):
                    self.sorted_notionals[symbol].pop(index)
                self.notional_sum[symbol] -= expired_notional
                self.notional_sum_squares[symbol] -= expired_notional**2
            if expired.trade_id:
                self.trade_ids[symbol].discard(expired.trade_id)

        baseline = self.sorted_notionals[symbol]
        count = len(baseline)
        mean = self.notional_sum[symbol] / count if count else 0.0
        variance = (
            (
                self.notional_sum_squares[symbol]
                - self.notional_sum[symbol] ** 2 / count
            )
            / (count - 1)
            if count > 1
            else 0.0
        )
        z_score = (trade.notional - mean) / sqrt(max(0.0, variance)) if variance > 0 else 0.0
        threshold = self._quantile(baseline, self.config.large_trade_quantile)
        is_large = trade.notional >= threshold and threshold > 0

        history.append(trade)
        if not trade.is_block_trade:
            insort(self.sorted_notionals[symbol], trade.notional)
            self.notional_sum[symbol] += trade.notional
            self.notional_sum_squares[symbol] += trade.notional**2
        if trade.is_block_trade or count < self.config.min_history_trades:
            return None

        cutoff = trade.timestamp - timedelta(seconds=self.config.cluster_window_seconds)
        cluster: list[TradeTick] = []
        for item in reversed(history):
            if item.timestamp < cutoff:
                break
            if not item.is_block_trade:
                cluster.append(item)
        cluster.reverse()
        buy_volume = sum(item.volume for item in cluster if item.side == "buy")
        sell_volume = sum(item.volume for item in cluster if item.side == "sell")
        signed_total = buy_volume + sell_volume
        imbalance = (buy_volume - sell_volume) / signed_total if signed_total else 0.0
        direction = "buy" if imbalance > 0 else "sell" if imbalance < 0 else "neutral"
        same_side_cluster = sum(1 for item in cluster if item.side == direction)
        directional_prices = [item.price for item in cluster if item.side == direction]
        sweep_levels = len(set(directional_prices))
        sweep_confirmed = bool(
            sweep_levels >= 3
            and (
                direction == "buy"
                and all(right >= left for left, right in zip(directional_prices, directional_prices[1:]))
                or direction == "sell"
                and all(right <= left for left, right in zip(directional_prices, directional_prices[1:]))
            )
        )

        vwap_denominator = sum(item.volume for item in cluster)
        vwap = (
            sum(item.price * item.volume for item in cluster) / vwap_denominator
            if vwap_denominator
            else trade.price
        )
        price_impact = (trade.price / vwap - 1) if vwap else 0.0

        book_imbalance = 0.0
        book = self.books.get(symbol)
        if book:
            bid = sum(level.volume for level in book.bids)
            ask = sum(level.volume for level in book.asks)
            book_imbalance = (bid - ask) / (bid + ask) if bid + ask else 0.0

        adv = self.average_daily_volume.get(symbol, 0)
        participation = sum(item.volume for item in cluster) / adv if adv else 0.0
        foreign_net = 0.0
        foreign = self.foreign.get(symbol)
        if foreign:
            foreign_net = foreign.buy_value - foreign.sell_value

        score = 0.0
        score += 25 if is_large else min(20, max(0, z_score * 4))
        score += min(25, same_side_cluster * 5)
        score += min(25, abs(imbalance) * 30)
        score += min(10, participation * 100)
        if direction != "neutral" and book_imbalance * imbalance > 0:
            score += min(8, abs(book_imbalance) * 10)
        if (direction == "buy" and price_impact > 0) or (direction == "sell" and price_impact < 0):
            score += min(7, abs(price_impact) * 1000)
        if sweep_confirmed:
            score += 7
        if (direction == "buy" and foreign_net > 0) or (direction == "sell" and foreign_net < 0):
            score += 5
        score = min(100.0, score)

        partial_us = trade.market is MarketRegion.US
        confirmed = (
            score >= self.config.alert_threshold
            and abs(imbalance) >= self.config.imbalance_threshold
            and is_large
            and not partial_us
        )
        return UnusualFlowEvent(
            symbol=symbol,
            market=trade.market,
            timestamp=trade.timestamp,
            score=score,
            direction=direction,
            confirmed=confirmed,
            source=trade.source,
            coverage_warning="partial IEX coverage; whale confirmation disabled" if partial_us else None,
            evidence={
                "large_trade": is_large,
                "notional": round(trade.notional, 2),
                "notional_zscore": round(z_score, 3),
                "cluster_trades": len(cluster),
                "same_side_cluster": same_side_cluster,
                "sweep_levels": sweep_levels,
                "sweep_confirmed": sweep_confirmed,
                "order_flow_imbalance": round(imbalance, 4),
                "book_imbalance": round(book_imbalance, 4),
                "participation_vs_adv": round(participation, 6),
                "price_impact": round(price_impact, 6),
                "foreign_net_value": round(foreign_net, 2),
            },
        )
