"""Pure strategy rules shared by live evaluation and backtests."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC
from typing import Any

import numpy as np
import pandas as pd

from claude_finance_kit.core.models import Signal, UnusualFlowEvent
from claude_finance_kit.core.types import MarketRegime, MarketRegion, SignalAction


def _validate_bars(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"open", "high", "low", "close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"OHLCV data is missing columns: {sorted(missing)}")
    result = frame.copy()
    if "time" in result:
        result["time"] = pd.to_datetime(result["time"], utc=True, errors="raise")
        result = result.sort_values("time").drop_duplicates("time", keep="last")
    else:
        result = result.sort_index()
        if result.index.has_duplicates:
            result = result.loc[~result.index.duplicated(keep="last")]
    return result.reset_index(drop=True)


def _true_range(frame: pd.DataFrame) -> pd.Series:
    previous = frame["close"].shift(1)
    return pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous).abs(),
            (frame["low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)


def _atr(frame: pd.DataFrame, length: int = 14) -> pd.Series:
    return _true_range(frame).ewm(alpha=1 / length, min_periods=length, adjust=False).mean()


def _adx(frame: pd.DataFrame, length: int = 14) -> pd.Series:
    up = frame["high"].diff()
    down = -frame["low"].diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    atr = _atr(frame, length).replace(0, np.nan)
    plus_di = 100 * plus_dm.ewm(alpha=1 / length, min_periods=length, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1 / length, min_periods=length, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()


def _rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


class RegimeDetector:
    """SMA50/SMA200 and ADX market regime classifier."""

    def __init__(self, adx_threshold: float = 20.0) -> None:
        self.adx_threshold = adx_threshold

    def detect(self, bars: pd.DataFrame) -> pd.Series:
        frame = _validate_bars(bars)
        sma50 = frame["close"].rolling(50).mean()
        sma200 = frame["close"].rolling(200).mean()
        adx = _adx(frame)
        result = pd.Series(MarketRegime.UNKNOWN.value, index=frame.index, dtype="object")
        ready = sma200.notna() & adx.notna()
        result.loc[ready] = MarketRegime.RANGE.value
        result.loc[ready & (frame["close"] > sma200) & (sma50 > sma200) & (adx >= self.adx_threshold)] = (
            MarketRegime.BULL.value
        )
        result.loc[ready & (frame["close"] < sma200) & (sma50 < sma200) & (adx >= self.adx_threshold)] = (
            MarketRegime.BEAR.value
        )
        return result


class Strategy(ABC):
    """Pure strategy interface used by both live and historical paths."""

    name: str

    @abstractmethod
    def generate(
        self,
        bars: pd.DataFrame,
        market: MarketRegion | str,
        benchmark: pd.DataFrame | None = None,
    ) -> pd.DataFrame: ...

    def parameters(self) -> dict[str, str | int | float | bool]:
        """Serializable parameters that uniquely identify deployed strategy logic."""

        return {
            key: value
            for key, value in vars(self).items()
            if isinstance(value, (str, int, float, bool))
        }

    def evaluate(
        self,
        bars: pd.DataFrame,
        market: MarketRegion | str,
        symbol: str,
        benchmark: pd.DataFrame | None = None,
        source: str | None = None,
    ) -> Signal:
        frame = _validate_bars(bars)
        generated = self.generate(frame, market, benchmark)
        if generated.empty:
            raise ValueError("At least one OHLCV bar is required")
        row = generated.iloc[-1]
        raw_time = frame.iloc[-1].get("time") if "time" in frame else frame.index[-1]
        timestamp = pd.Timestamp(raw_time)
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize(UTC)
        return Signal(
            symbol=symbol,
            market=MarketRegion(market),
            timestamp=timestamp.to_pydatetime(),
            action=SignalAction(row["action"]),
            confidence=float(row["confidence"]),
            regime=MarketRegime(row["regime"]),
            strategy=self.name,
            price=float(frame.iloc[-1]["close"]),
            stop_loss=float(row["stop_loss"]) if pd.notna(row["stop_loss"]) else None,
            take_profit=float(row["take_profit"]) if pd.notna(row["take_profit"]) else None,
            reasons=[str(row["reason"])],
            source=source,
        )

    @staticmethod
    def _base(
        bars: pd.DataFrame,
        benchmark: pd.DataFrame | None,
    ) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
        frame = _validate_bars(bars)
        if benchmark is not None:
            benchmark_frame = _validate_bars(benchmark)
            benchmark_regimes = RegimeDetector().detect(benchmark_frame)
            if "time" in frame and "time" in benchmark_frame:
                regime_table = pd.DataFrame(
                    {
                        "time": benchmark_frame["time"],
                        "regime": benchmark_regimes,
                    }
                )
                aligned = pd.merge_asof(
                    frame[["time"]].sort_values("time"),
                    regime_table.sort_values("time"),
                    on="time",
                    direction="backward",
                )
                regimes = aligned["regime"]
            else:
                regimes = benchmark_regimes.reindex(frame.index)
        else:
            regimes = RegimeDetector().detect(frame)
        regimes = regimes.fillna(MarketRegime.UNKNOWN.value)
        atr = _atr(frame)
        return frame, regimes, atr


class TrendMomentumStrategy(Strategy):
    name = "trend-momentum"

    def __init__(self, fast: int = 20, slow: int = 50, adx_threshold: float = 20, volume_length: int = 20):
        if fast >= slow:
            raise ValueError("fast EMA must be shorter than slow EMA")
        self.fast = fast
        self.slow = slow
        self.adx_threshold = adx_threshold
        self.volume_length = volume_length

    def generate(
        self,
        bars: pd.DataFrame,
        market: MarketRegion | str,
        benchmark: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        frame, regimes, atr = self._base(bars, benchmark)
        fast = frame["close"].ewm(span=self.fast, adjust=False).mean()
        slow = frame["close"].ewm(span=self.slow, adjust=False).mean()
        adx = _adx(frame)
        volume_mean = frame["volume"].rolling(self.volume_length).mean()
        active = (
            (fast > slow)
            & (frame["close"] > fast)
            & (adx >= self.adx_threshold)
            & (frame["volume"] >= volume_mean)
            & (regimes == MarketRegime.BULL.value)
        )
        actions = pd.Series(SignalAction.NO_TRADE.value, index=frame.index, dtype="object")
        actions.loc[active] = SignalAction.HOLD.value
        actions.loc[active & ~active.shift(1, fill_value=False)] = SignalAction.BUY.value
        actions.loc[(fast < slow) | (regimes == MarketRegime.BEAR.value)] = SignalAction.EXIT.value
        confidence = (
            55
            + (adx - self.adx_threshold).clip(lower=0, upper=20)
            + ((frame["volume"] / volume_mean.replace(0, np.nan) - 1).clip(0, 1) * 15)
        ).fillna(0).clip(0, 90)
        return pd.DataFrame(
            {
                "action": actions,
                "confidence": confidence,
                "regime": regimes,
                "stop_loss": frame["close"] - 2 * atr,
                "take_profit": frame["close"] + 3 * atr,
                "reason": "EMA trend + ADX + volume",
            }
        )


class DonchianBreakoutStrategy(Strategy):
    name = "donchian-breakout"

    def __init__(self, entry_length: int = 20, exit_length: int = 10, atr_multiple: float = 2.0):
        self.entry_length = entry_length
        self.exit_length = exit_length
        self.atr_multiple = atr_multiple

    def generate(
        self,
        bars: pd.DataFrame,
        market: MarketRegion | str,
        benchmark: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        frame, regimes, atr = self._base(bars, benchmark)
        upper = frame["high"].rolling(self.entry_length).max().shift(1)
        lower = frame["low"].rolling(self.exit_length).min().shift(1)
        breakout = (frame["close"] > upper) & (regimes == MarketRegime.BULL.value)
        exit_condition = (frame["close"] < lower) | (regimes == MarketRegime.BEAR.value)
        active = breakout.rolling(self.exit_length, min_periods=1).max().astype(bool) & ~exit_condition
        actions = pd.Series(SignalAction.NO_TRADE.value, index=frame.index, dtype="object")
        actions.loc[active] = SignalAction.HOLD.value
        actions.loc[breakout] = SignalAction.BUY.value
        actions.loc[exit_condition] = SignalAction.EXIT.value
        distance = ((frame["close"] - upper) / atr.replace(0, np.nan)).clip(lower=0, upper=2)
        confidence = (60 + distance * 12).fillna(0).clip(0, 88)
        return pd.DataFrame(
            {
                "action": actions,
                "confidence": confidence,
                "regime": regimes,
                "stop_loss": frame["close"] - self.atr_multiple * atr,
                "take_profit": frame["close"] + 3 * atr,
                "reason": "Donchian breakout + ATR",
            }
        )


class MeanReversionStrategy(Strategy):
    name = "mean-reversion"

    def __init__(self, length: int = 20, rsi_length: int = 14, entry_rsi: float = 30, exit_rsi: float = 55):
        self.length = length
        self.rsi_length = rsi_length
        self.entry_rsi = entry_rsi
        self.exit_rsi = exit_rsi

    def generate(
        self,
        bars: pd.DataFrame,
        market: MarketRegion | str,
        benchmark: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        frame, regimes, atr = self._base(bars, benchmark)
        middle = frame["close"].rolling(self.length).mean()
        deviation = frame["close"].rolling(self.length).std()
        lower = middle - 2 * deviation
        rsi = _rsi(frame["close"], self.rsi_length)
        entry = (
            (regimes == MarketRegime.RANGE.value)
            & (frame["close"] < lower)
            & (rsi < self.entry_rsi)
        )
        exit_condition = (frame["close"] >= middle) | (rsi > self.exit_rsi) | (regimes == MarketRegime.BEAR.value)
        actions = pd.Series(SignalAction.NO_TRADE.value, index=frame.index, dtype="object")
        actions.loc[entry] = SignalAction.BUY.value
        actions.loc[exit_condition] = SignalAction.EXIT.value
        confidence = (60 + (self.entry_rsi - rsi).clip(0, 15) * 1.5).fillna(0).clip(0, 85)
        return pd.DataFrame(
            {
                "action": actions,
                "confidence": confidence,
                "regime": regimes,
                "stop_loss": frame["close"] - 1.5 * atr,
                "take_profit": middle,
                "reason": "range-only RSI/Bollinger reversion",
            }
        )


def apply_flow_overlay(signal: Signal, flow: UnusualFlowEvent | None) -> Signal:
    """Confirm or veto a strategy signal; flow never creates BUY by itself."""

    if flow is None:
        return signal
    updated = signal.model_copy(deep=True)
    if flow.coverage_warning:
        updated.coverage_warning = flow.coverage_warning
    if updated.action is SignalAction.BUY:
        if flow.confirmed and flow.direction == "buy":
            updated.confidence = min(100, updated.confidence + 15)
            updated.reasons.append(f"unusual-flow confirmation {flow.score:.1f}/100")
        elif flow.direction == "sell" and flow.score >= 60:
            updated.action = SignalAction.NO_TRADE
            updated.confidence = min(updated.confidence, 40)
            updated.reasons.append("sell-side unusual flow veto")
    elif updated.action is SignalAction.HOLD and flow.confirmed and flow.direction == "sell":
        updated.action = SignalAction.EXIT
        updated.reasons.append("confirmed sell-side unusual flow")
    return updated


class StrategyRegistry:
    """Fixed, bounded strategy family; no arbitrary strategy mining."""

    _strategies: dict[str, type[Strategy]] = {
        TrendMomentumStrategy.name: TrendMomentumStrategy,
        DonchianBreakoutStrategy.name: DonchianBreakoutStrategy,
        MeanReversionStrategy.name: MeanReversionStrategy,
    }

    @classmethod
    def create(cls, name: str, **params: Any) -> Strategy:
        key = name.lower()
        if key not in cls._strategies:
            raise ValueError(f"Unknown strategy '{name}'. Use: {sorted(cls._strategies)}")
        return cls._strategies[key](**params)

    @classmethod
    def candidates(cls) -> list[Strategy]:
        return [
            TrendMomentumStrategy(20, 50, 20),
            TrendMomentumStrategy(10, 40, 25),
            DonchianBreakoutStrategy(20, 10, 2),
            DonchianBreakoutStrategy(55, 20, 2.5),
            MeanReversionStrategy(20, 14, 30, 55),
            MeanReversionStrategy(30, 14, 25, 50),
        ]

    @classmethod
    def names(cls) -> list[str]:
        return sorted(cls._strategies)
