"""Credential-free/degraded watchlist polling fallback."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

import pandas as pd

from claude_finance_kit._internal.parser import get_asset_type
from claude_finance_kit.core.models import Bar, MarketEvent
from claude_finance_kit.core.types import FeedHealth, MarketRegion
from claude_finance_kit.stock import Stock


class PollingMarketStream:
    """Poll AUTO intraday providers when credentialed realtime is unavailable."""

    def __init__(
        self,
        market: MarketRegion | str,
        symbols: list[str],
        *,
        interval_seconds: float = 60,
    ) -> None:
        if "ALL" in symbols:
            raise ValueError("Degraded polling requires an explicit watchlist")
        if interval_seconds <= 0:
            raise ValueError("Polling interval must be positive")
        self.market = MarketRegion(market)
        self.symbols = list(dict.fromkeys(symbol.upper() for symbol in symbols))
        self.interval_seconds = interval_seconds
        self.health = FeedHealth.DEGRADED
        self._stopped = False

    async def stop(self) -> None:
        self._stopped = True
        self.health = FeedHealth.DISCONNECTED

    def _session_open(self, now: datetime | None = None) -> bool:
        timezone = ZoneInfo(
            "Asia/Ho_Chi_Minh"
            if self.market is MarketRegion.VN
            else "America/New_York"
        )
        local = (now or datetime.now(UTC)).astimezone(timezone)
        if local.weekday() >= 5:
            return False
        current = local.time()
        if self.market is MarketRegion.VN:
            return time(9, 0) <= current <= time(11, 30) or time(13, 0) <= current <= time(15, 0)
        return time(9, 30) <= current <= time(16, 0)

    def _latest_bar(self, symbol: str) -> MarketEvent | None:
        stock = Stock(symbol, market=self.market, source="AUTO")
        try:
            frame = stock.quote.intraday()
        except ValueError:
            if self.market is not MarketRegion.VN or get_asset_type(symbol) != "index":
                raise
            timezone = ZoneInfo("Asia/Ho_Chi_Minh")
            start = datetime.now(UTC).astimezone(timezone).date().isoformat()
            frame = stock.quote.history(start=start, interval="1m")
        if frame.empty:
            return None
        timezone_name = (
            "Asia/Ho_Chi_Minh"
            if self.market is MarketRegion.VN
            else "America/New_York"
        )
        if "time" not in frame:
            raise ValueError("Polling provider returned no time column")
        timestamps = pd.to_datetime(frame["time"], errors="coerce")
        if timestamps.isna().any():
            raise ValueError("Polling provider returned invalid timestamps")
        if timestamps.dt.tz is None:
            timestamps = timestamps.dt.tz_localize(
                timezone_name,
                ambiguous="NaT",
                nonexistent="shift_forward",
            )
        frame = frame.copy()
        frame["time"] = timestamps.dt.tz_convert(UTC)
        ohlc_columns = {"open", "high", "low", "close", "volume"}
        if ohlc_columns.issubset(frame.columns):
            row = frame.sort_values("time").iloc[-1]
        else:
            price_column = next(
                (
                    column
                    for column in ("price", "match_price", "matchprice", "close")
                    if column in frame
                ),
                None,
            )
            volume_column = next(
                (
                    column
                    for column in ("volume", "match_volume", "matchqtty", "volume_last")
                    if column in frame
                ),
                None,
            )
            if price_column is None or volume_column is None:
                raise ValueError("Polling provider returned neither OHLCV nor tick data")
            ticks = frame.loc[:, ["time", price_column, volume_column]].copy()
            ticks[price_column] = pd.to_numeric(ticks[price_column], errors="raise")
            ticks[volume_column] = pd.to_numeric(ticks[volume_column], errors="raise")
            ticks["minute"] = ticks["time"].dt.floor("min")
            latest_minute = ticks["minute"].max()
            minute_ticks = ticks.loc[ticks["minute"] == latest_minute].sort_values("time")
            row = pd.Series(
                {
                    "time": latest_minute,
                    "open": minute_ticks.iloc[0][price_column],
                    "high": minute_ticks[price_column].max(),
                    "low": minute_ticks[price_column].min(),
                    "close": minute_ticks.iloc[-1][price_column],
                    "volume": minute_ticks[volume_column].sum(),
                }
            )
        timestamp = pd.Timestamp(row["time"])
        source = str(frame.attrs.get("source", "AUTO"))
        return MarketEvent(
            event_type="bar",
            record=Bar(
                symbol=symbol,
                market=self.market,
                timestamp=timestamp.to_pydatetime(),
                source=source,
                exchange_timezone=timezone_name,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
                interval=str(frame.attrs.get("interval", "1m")),
            ),
            metadata={
                "degraded": True,
                "polling": True,
                "actual_source": source,
                "attempted_sources": frame.attrs.get("attempted_sources", []),
                "coverage": frame.attrs.get("coverage"),
            },
        )

    async def events(self) -> AsyncIterator[MarketEvent]:
        yield MarketEvent(
            event_type="health",
            health=FeedHealth.DEGRADED,
            metadata={
                "degraded": True,
                "polling": True,
                "reason": "credentialed realtime unavailable; polling explicit watchlist",
            },
        )
        while not self._stopped:
            if not self._session_open():
                self.health = FeedHealth.IDLE
                yield MarketEvent(
                    event_type="health",
                    health=self.health,
                    metadata={
                        "degraded": True,
                        "polling": True,
                        "reason": "market session closed",
                    },
                )
            else:
                self.health = FeedHealth.DEGRADED
                for symbol in self.symbols:
                    if self._stopped:
                        break
                    try:
                        event = await asyncio.to_thread(self._latest_bar, symbol)
                    except Exception as exc:
                        yield MarketEvent(
                            event_type="health",
                            health=FeedHealth.DEGRADED,
                            metadata={
                                "degraded": True,
                                "polling": True,
                                "reason": "polling provider error",
                                "error_type": type(exc).__name__,
                            },
                        )
                        continue
                    if event is not None:
                        yield event
            try:
                await asyncio.wait_for(
                    self._wait_until_stopped(),
                    timeout=self.interval_seconds,
                )
            except asyncio.TimeoutError:
                pass

    async def _wait_until_stopped(self) -> None:
        while not self._stopped:
            await asyncio.sleep(min(0.25, self.interval_seconds))

    def __aiter__(self) -> AsyncIterator[MarketEvent]:
        return self.events()
