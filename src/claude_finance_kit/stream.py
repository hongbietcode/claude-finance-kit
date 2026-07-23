"""Public resilient market-stream facade."""

from __future__ import annotations

import asyncio
import random
from collections import deque
from collections.abc import AsyncIterator
from datetime import UTC, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from claude_finance_kit._provider import alpaca, dnse, ssi  # noqa: F401
from claude_finance_kit._provider._base import AsyncStreamProvider
from claude_finance_kit._provider._registry import ProviderRegistry, registry
from claude_finance_kit.core.models import MarketEvent
from claude_finance_kit.core.types import FeedHealth, MarketRegion


def market_session_open(
    market: MarketRegion | str,
    now: datetime | None = None,
) -> bool:
    """Return the known regular weekday session without inventing holidays."""

    market_value = MarketRegion(market)
    timezone = ZoneInfo(
        "Asia/Ho_Chi_Minh"
        if market_value is MarketRegion.VN
        else "America/New_York"
    )
    local = (now or datetime.now(UTC)).astimezone(timezone)
    if local.weekday() >= 5:
        return False
    current = local.time()
    if market_value is MarketRegion.VN:
        return (
            time(9, 0) <= current <= time(11, 30)
            or time(13, 0) <= current <= time(15, 0)
        )
    return time(9, 30) <= current <= time(16, 0)


class MarketStream:
    """Reconnectable async market stream with staleness and backoff handling."""

    def __init__(
        self,
        market: MarketRegion | str,
        symbols: list[str] | str,
        source: str | None = None,
        *,
        stale_after: float = 90.0,
        future_skew: float = 10.0,
        max_backoff: float = 60.0,
        provider_options: dict[str, Any] | None = None,
        provider_registry: ProviderRegistry | None = None,
    ) -> None:
        self.market = MarketRegion(market)
        self.symbols = [symbols.upper()] if isinstance(symbols, str) else [item.upper() for item in symbols]
        self.source = (source or ("SSI" if self.market is MarketRegion.VN else "ALPACA")).upper()
        self.stale_after = stale_after
        self.future_skew = future_skew
        self.max_backoff = max_backoff
        self.provider_options = provider_options or {}
        self.registry = provider_registry or registry
        self.health = FeedHealth.DISCONNECTED
        self._provider: AsyncStreamProvider | None = None
        self._stopped = False
        self._last_timestamps: dict[tuple[str, str], datetime] = {}
        self._event_fingerprints: set[str] = set()
        self._fingerprint_order: deque[str] = deque(maxlen=20_000)

        descriptor = self.registry.get_descriptor(self.source)
        if self.market not in descriptor.markets:
            raise ValueError(f"{self.source} does not support market {self.market.value}")
        if descriptor.max_stream_symbols and len(self.symbols) > descriptor.max_stream_symbols:
            raise ValueError(
                f"{self.source} supports at most {descriptor.max_stream_symbols} realtime symbols"
            )

    async def stop(self) -> None:
        self._stopped = True
        if self._provider:
            await self._provider.disconnect()
            self._provider = None
        self.health = FeedHealth.DISCONNECTED

    async def events(self) -> AsyncIterator[MarketEvent]:
        attempt = 0
        while not self._stopped:
            try:
                provider_cls = self.registry.get_stream(self.source)
                self._provider = provider_cls(**self.provider_options)
                await self._provider.connect(self.symbols)
                self.health = FeedHealth.HEALTHY
                attempt = 0
                yield MarketEvent(
                    event_type="health",
                    health=self.health,
                    metadata={"source": self.source, "market": self.market.value},
                )
                iterator = self._provider.events().__aiter__()
                pending_next: asyncio.Task[MarketEvent] | None = None
                try:
                    while not self._stopped:
                        if pending_next is None:
                            pending_next = asyncio.create_task(iterator.__anext__())
                        done, _ = await asyncio.wait({pending_next}, timeout=self.stale_after)
                        if not done:
                            if not self._session_open():
                                self.health = FeedHealth.IDLE
                                yield MarketEvent(
                                    event_type="health",
                                    health=self.health,
                                    metadata={
                                        "source": self.source,
                                        "market": self.market.value,
                                        "reason": "market session closed",
                                    },
                                )
                                continue
                            pending_next.cancel()
                            await asyncio.gather(pending_next, return_exceptions=True)
                            pending_next = None
                            self.health = FeedHealth.STALE
                            yield MarketEvent(
                                event_type="health",
                                health=self.health,
                                metadata={
                                    "source": self.source,
                                    "market": self.market.value,
                                    "reason": "no events before stale_after",
                                },
                            )
                            raise ConnectionError(f"{self.source} stream became stale")
                        event = pending_next.result()
                        pending_next = None
                        if (
                            event.record is not None
                            and not self._session_open(event.record.timestamp)
                        ):
                            if self.health is not FeedHealth.IDLE:
                                self.health = FeedHealth.IDLE
                                yield MarketEvent(
                                    event_type="health",
                                    health=self.health,
                                    metadata={
                                        "source": self.source,
                                        "market": self.market.value,
                                        "reason": "event outside regular market session",
                                    },
                                )
                            continue
                        if not self._fresh_event(event):
                            self.health = FeedHealth.STALE
                            yield MarketEvent(
                                event_type="health",
                                health=self.health,
                                metadata={
                                    "source": self.source,
                                    "market": self.market.value,
                                    "reason": "stale, duplicate, out-of-order, or future event timestamp",
                                },
                            )
                            continue
                        self.health = FeedHealth.HEALTHY
                        yield event
                finally:
                    if pending_next is not None:
                        pending_next.cancel()
                        await asyncio.gather(pending_next, return_exceptions=True)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if self._stopped:
                    break
                self.health = FeedHealth.DEGRADED
                yield MarketEvent(
                    event_type="health",
                    health=self.health,
                    metadata={
                        "source": self.source,
                        "market": self.market.value,
                        "reason": "stream provider error",
                        "error_type": type(exc).__name__,
                    },
                )
                attempt += 1
                delay = min(self.max_backoff, 2 ** min(attempt, 6)) + random.uniform(0, 1)
                await asyncio.sleep(delay)
            finally:
                if self._provider:
                    await self._provider.disconnect()
                    self._provider = None

    def __aiter__(self) -> AsyncIterator[MarketEvent]:
        return self.events()

    def _fresh_event(self, event: MarketEvent) -> bool:
        if event.record is None:
            return True
        now = datetime.now(UTC)
        age = (now - event.record.timestamp).total_seconds()
        if age > self.stale_after or age < -self.future_skew:
            return False
        key = (event.event_type, event.record.symbol)
        previous = self._last_timestamps.get(key)
        if previous is not None and event.record.timestamp < previous:
            return False
        fingerprint = (
            f"{event.event_type}:{event.record.source}:"
            f"{event.record.model_dump_json(exclude_none=False)}"
        )
        if fingerprint in self._event_fingerprints:
            return False
        if len(self._fingerprint_order) == self._fingerprint_order.maxlen:
            oldest = self._fingerprint_order.popleft()
            self._event_fingerprints.discard(oldest)
        self._fingerprint_order.append(fingerprint)
        self._event_fingerprints.add(fingerprint)
        if previous is None or event.record.timestamp > previous:
            self._last_timestamps[key] = event.record.timestamp
        return True

    def _session_open(self, now: datetime | None = None) -> bool:
        """Return expected weekday session state without inventing holiday data."""

        return market_session_open(self.market, now)
