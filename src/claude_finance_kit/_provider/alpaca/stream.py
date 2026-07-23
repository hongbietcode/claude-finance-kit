"""Alpaca IEX WebSocket stream adapter."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from claude_finance_kit._provider._base import AsyncStreamProvider
from claude_finance_kit._provider._registry import registry
from claude_finance_kit.core.exceptions import AuthenticationError
from claude_finance_kit.core.models import (
    Bar,
    MarketEvent,
    OrderBookLevel,
    OrderBookSnapshot,
    ProviderDescriptor,
    TradeTick,
)
from claude_finance_kit.core.types import MarketRegion, ProviderCapability


class AlpacaStreamProvider(AsyncStreamProvider):
    """Realtime IEX stream with an explicit free-tier symbol cap."""

    URI = "wss://stream.data.alpaca.markets/v2/iex"
    MAX_SYMBOLS = 30

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        queue_size: int = 10_000,
    ) -> None:
        self.api_key = api_key or os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
        self.api_secret = api_secret or os.getenv("ALPACA_API_SECRET") or os.getenv("APCA_API_SECRET_KEY")
        if not self.api_key or not self.api_secret:
            raise AuthenticationError("ALPACA", "Alpaca market-data API key and secret are required")
        self.queue: asyncio.Queue[MarketEvent | Exception] = asyncio.Queue(maxsize=queue_size)
        self.websocket: Any = None
        self.reader_task: asyncio.Task[None] | None = None

    async def connect(self, symbols: list[str]) -> None:
        normalized = list(dict.fromkeys(symbol.upper() for symbol in symbols))
        if len(normalized) > self.MAX_SYMBOLS:
            raise ValueError("Alpaca Basic realtime watchlist is limited to 30 symbols")
        try:
            import websockets
        except ImportError as exc:
            raise ImportError("websockets is required: pip install claude-finance-kit[monitor]") from exc
        self.websocket = await websockets.connect(self.URI, ping_interval=20, ping_timeout=20)
        await self.websocket.send(
            json.dumps({"action": "auth", "key": self.api_key, "secret": self.api_secret})
        )
        auth = json.loads(await asyncio.wait_for(self.websocket.recv(), timeout=30))
        auth_items = auth if isinstance(auth, list) else [auth]
        if not any(item.get("T") == "success" and item.get("msg") == "authenticated" for item in auth_items):
            raise AuthenticationError("ALPACA")
        await self.websocket.send(
            json.dumps(
                {
                    "action": "subscribe",
                    "trades": normalized,
                    "quotes": normalized,
                    "bars": normalized,
                }
            )
        )
        self.reader_task = asyncio.create_task(self._read_loop())
        self.reader_task.add_done_callback(self._reader_done)

    def _reader_done(self, task: asyncio.Task[None]) -> None:
        if task.cancelled():
            return
        error = task.exception()
        if error is not None:
            if self.queue.full():
                self.queue.get_nowait()
                self.queue.task_done()
            self.queue.put_nowait(error)

    async def disconnect(self) -> None:
        if self.reader_task:
            self.reader_task.cancel()
            await asyncio.gather(self.reader_task, return_exceptions=True)
            self.reader_task = None
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def _read_loop(self) -> None:
        while self.websocket:
            payload = json.loads(await self.websocket.recv())
            for item in payload if isinstance(payload, list) else [payload]:
                event = self.parse_message(item)
                if event:
                    if self.queue.full():
                        self.queue.get_nowait()
                        self.queue.task_done()
                    await self.queue.put(event)

    def parse_message(self, data: dict[str, Any]) -> MarketEvent | None:
        event_type = data.get("T")
        symbol = str(data.get("S", "")).upper()
        if event_type not in {"t", "q", "b"} or not symbol:
            return None
        timestamp = datetime.fromisoformat(str(data["t"]).replace("Z", "+00:00"))
        common = {
            "symbol": symbol,
            "market": MarketRegion.US,
            "timestamp": timestamp,
            "source": "ALPACA",
            "exchange_timezone": "America/New_York",
        }
        metadata = {"coverage": "iex-partial", "whale_confirmation": False}
        if event_type == "t":
            return MarketEvent(
                event_type="trade",
                record=TradeTick(
                    **common,
                    price=float(data["p"]),
                    volume=float(data["s"]),
                    trade_id=str(data.get("i", "")) or None,
                ),
                metadata=metadata,
            )
        if event_type == "q":
            return MarketEvent(
                event_type="order_book",
                record=OrderBookSnapshot(
                    **common,
                    bids=[OrderBookLevel(price=float(data["bp"]), volume=float(data["bs"]))],
                    asks=[OrderBookLevel(price=float(data["ap"]), volume=float(data["as"]))],
                ),
                metadata=metadata,
            )
        return MarketEvent(
            event_type="bar",
            record=Bar(
                **common,
                open=float(data["o"]),
                high=float(data["h"]),
                low=float(data["l"]),
                close=float(data["c"]),
                volume=float(data["v"]),
                interval="1m",
            ),
            metadata=metadata,
        )

    async def events(self) -> AsyncIterator[MarketEvent]:
        while True:
            event = await self.queue.get()
            try:
                if isinstance(event, Exception):
                    raise event
                yield event
            finally:
                self.queue.task_done()


registry.register_stream(
    "ALPACA",
    AlpacaStreamProvider,
    ProviderDescriptor(
        source="ALPACA",
        markets={MarketRegion.US},
        capabilities={
            ProviderCapability.REALTIME_STREAM,
            ProviderCapability.TRADES,
            ProviderCapability.ORDER_BOOK,
        },
        requires_auth=True,
        auth_type="api_key_secret",
        realtime=True,
        coverage="iex-partial",
        max_stream_symbols=30,
    ),
)
