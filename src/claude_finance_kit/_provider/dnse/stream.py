"""Authenticated DNSE WebSocket stream."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from claude_finance_kit._provider._base import AsyncStreamProvider
from claude_finance_kit._provider._registry import registry
from claude_finance_kit.core.exceptions import AuthenticationError
from claude_finance_kit.core.models import (
    Bar,
    ForeignFlow,
    MarketEvent,
    OrderBookLevel,
    OrderBookSnapshot,
    ProviderDescriptor,
    TradeTick,
)
from claude_finance_kit.core.types import MarketRegion, ProviderCapability


class DNSEStreamProvider(AsyncStreamProvider):
    """DNSE JSON stream with HMAC auth, ping/pong, and bounded buffering."""

    URI = "wss://ws-openapi.dnse.com.vn/v1/stream?encoding=json"

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        board_id: str = "G1",
        queue_size: int = 10_000,
    ) -> None:
        self.api_key = api_key or os.getenv("DNSE_API_KEY")
        self.api_secret = api_secret or os.getenv("DNSE_API_SECRET")
        if not self.api_key or not self.api_secret:
            raise AuthenticationError("DNSE", "DNSE_API_KEY and DNSE_API_SECRET are required for streaming")
        self.board_id = board_id
        self.queue: asyncio.Queue[MarketEvent | Exception] = asyncio.Queue(maxsize=queue_size)
        self.websocket: Any = None
        self.reader_task: asyncio.Task[None] | None = None
        self.symbols: list[str] = []
        self.connected_at = 0.0

    async def connect(self, symbols: list[str]) -> None:
        try:
            import websockets
        except ImportError as exc:
            raise ImportError("websockets is required: pip install claude-finance-kit[monitor]") from exc
        self.symbols = [symbol.upper() for symbol in symbols]
        self.websocket = await websockets.connect(self.URI, ping_interval=20, ping_timeout=20)
        self.connected_at = time.monotonic()
        hello = json.loads(await asyncio.wait_for(self.websocket.recv(), timeout=30))
        if hello.get("action") == "error":
            raise AuthenticationError("DNSE", hello.get("message", "DNSE rejected connection"))
        timestamp = int(time.time())
        nonce = str(time.time_ns() // 1000)
        message = f"{self.api_key}:{timestamp}:{nonce}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        await self.websocket.send(
            json.dumps(
                {
                    "action": "auth",
                    "api_key": self.api_key,
                    "signature": signature,
                    "timestamp": timestamp,
                    "nonce": nonce,
                }
            )
        )
        auth = json.loads(await asyncio.wait_for(self.websocket.recv(), timeout=30))
        if auth.get("action") != "auth_success":
            raise AuthenticationError("DNSE", auth.get("message", "DNSE authentication failed"))
        channels = [
            {"name": f"tick_extra.{self.board_id}.json", "symbols": self.symbols},
            {"name": f"top_price.{self.board_id}.json", "symbols": self.symbols},
            {"name": "ohlc.1.json", "symbols": self.symbols},
            {"name": f"foreign.{self.board_id}.json", "symbols": self.symbols},
        ]
        await self.websocket.send(json.dumps({"action": "subscribe", "channels": channels}))
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
            if time.monotonic() - self.connected_at >= 7 * 3600 + 55 * 60:
                await self.websocket.close(code=1000, reason="scheduled reconnect before 8-hour limit")
                raise ConnectionError("DNSE scheduled reconnect")
            raw = await self.websocket.recv()
            payload = json.loads(raw)
            if payload.get("action") == "ping":
                await self.websocket.send(json.dumps({"action": "pong"}))
                continue
            event = self.parse_message(payload)
            if event:
                if self.queue.full():
                    self.queue.get_nowait()
                    self.queue.task_done()
                await self.queue.put(event)

    def parse_message(self, payload: dict[str, Any]) -> MarketEvent | None:
        data = payload if payload.get("T") else payload.get("data", payload)
        message_type = str(payload.get("T", "")).lower()
        channel = str(payload.get("channel", payload.get("topic", ""))).lower()
        symbol = str(data.get("symbol", data.get("code", ""))).upper()
        if not symbol:
            return None
        raw_time = data.get("timestamp", data.get("time", datetime.now(UTC)))
        if isinstance(raw_time, dict):
            seconds = raw_time.get("Seconds", raw_time.get("seconds", 0))
            nanos = raw_time.get("Nanos", raw_time.get("nanos", 0))
            timestamp = datetime.fromtimestamp(float(seconds) + float(nanos) / 1_000_000_000, UTC)
        elif isinstance(raw_time, (int, float)):
            divisor = 1_000_000_000 if raw_time > 10**17 else 1000 if raw_time > 10**11 else 1
            timestamp = datetime.fromtimestamp(raw_time / divisor, UTC)
        else:
            timestamp = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
        common = {
            "symbol": symbol,
            "market": MarketRegion.VN,
            "timestamp": timestamp,
            "source": "DNSE",
            "exchange_timezone": "Asia/Ho_Chi_Minh",
        }
        if message_type in {"t", "te"} or "tick" in channel:
            raw_side = data.get("side", "unknown")
            side = {
                1: "buy",
                2: "sell",
                "1": "buy",
                "2": "sell",
                "BU": "buy",
                "B": "buy",
                "SD": "sell",
                "S": "sell",
            }.get(raw_side, str(raw_side).lower())
            if side not in {"buy", "sell", "unknown"}:
                side = "unknown"
            record = TradeTick(
                **common,
                price=float(data.get("price", data.get("matchPrice", 0))),
                volume=float(data.get("volume", data.get("matchQtty", data.get("quantity", 0)))),
                side=side,
                trade_id=str(data.get("id", data.get("tradeId", ""))) or None,
                board=data.get("board", data.get("boardId")),
                is_block_trade=bool(data.get("isBlockTrade", False)),
            )
            return MarketEvent(event_type="trade", record=record)
        if message_type == "q" or "top_price" in channel:
            raw_bids = data.get("bid", data.get("bids", []))
            raw_asks = data.get("offer", data.get("asks", []))
            bids = [
                OrderBookLevel(
                    price=float(row.get("price", 0)),
                    volume=float(row.get("volume", row.get("qtty", row.get("quantity", 0)))),
                )
                for row in raw_bids
            ]
            asks = [
                OrderBookLevel(
                    price=float(row.get("price", 0)),
                    volume=float(row.get("volume", row.get("qtty", row.get("quantity", 0)))),
                )
                for row in raw_asks
            ]
            return MarketEvent(event_type="order_book", record=OrderBookSnapshot(**common, bids=bids, asks=asks))
        if message_type == "f" or "foreign" in channel:
            return MarketEvent(
                event_type="foreign_flow",
                record=ForeignFlow(
                    **common,
                    buy_volume=float(data.get("totalBuyVolume", data.get("buyVolume", 0))),
                    sell_volume=float(data.get("totalSellVolume", data.get("sellVolume", 0))),
                    buy_value=float(data.get("totalBuyTradedAmount", data.get("buyValue", 0))),
                    sell_value=float(data.get("totalSellTradedAmount", data.get("sellValue", 0))),
                    room=data.get("foreignerBuyPossibleQuantity", data.get("currentRoom")),
                ),
                metadata={
                    "provider_transact_time": data.get("transactTime"),
                    "timestamp_basis": (
                        "provider_timestamp"
                        if "timestamp" in data or "time" in data
                        else "receipt_time"
                    ),
                },
            )
        if message_type in {"b", "bc"} or "ohlc" in channel:
            return MarketEvent(
                event_type="bar",
                record=Bar(
                    **common,
                    open=float(data.get("open", 0)),
                    high=float(data.get("high", 0)),
                    low=float(data.get("low", 0)),
                    close=float(data.get("close", 0)),
                    volume=float(data.get("volume", 0)),
                    interval=str(data.get("resolution", "1m")),
                ),
            )
        return None

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
    "DNSE",
    DNSEStreamProvider,
    ProviderDescriptor(
        source="DNSE",
        markets={MarketRegion.VN},
        capabilities={
            ProviderCapability.REALTIME_STREAM,
            ProviderCapability.TRADES,
            ProviderCapability.ORDER_BOOK,
            ProviderCapability.FOREIGN_FLOW,
        },
        requires_auth=True,
        auth_type="api_key_hmac",
        realtime=True,
        coverage="official-vn",
    ),
)
