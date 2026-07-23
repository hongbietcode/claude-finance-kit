"""SSI FastConnect official SDK stream adapter."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

from claude_finance_kit._provider._base import AsyncStreamProvider
from claude_finance_kit._provider._registry import registry
from claude_finance_kit.core.exceptions import AuthenticationError
from claude_finance_kit.core.models import (
    ForeignFlow,
    MarketEvent,
    OrderBookLevel,
    OrderBookSnapshot,
    ProviderDescriptor,
    TradeTick,
)
from claude_finance_kit.core.types import MarketRegion, ProviderCapability


class SSIStreamProvider(AsyncStreamProvider):
    """Bridge the synchronous `ssi-fc-data` SDK into an asyncio event stream."""

    def __init__(
        self,
        consumer_id: str | None = None,
        consumer_secret: str | None = None,
        channel: str | None = None,
        queue_size: int = 10_000,
    ) -> None:
        self.consumer_id = consumer_id or os.getenv("SSI_CONSUMER_ID") or os.getenv("FC_DATA_CONSUMER_ID")
        self.consumer_secret = (
            consumer_secret or os.getenv("SSI_CONSUMER_SECRET") or os.getenv("FC_DATA_CONSUMER_SECRET")
        )
        if not self.consumer_id or not self.consumer_secret:
            raise AuthenticationError("SSI", "SSI_CONSUMER_ID and SSI_CONSUMER_SECRET are required")
        self.channel = channel
        self.queue: asyncio.Queue[MarketEvent | Exception] = asyncio.Queue(maxsize=queue_size)
        self.loop: asyncio.AbstractEventLoop | None = None
        self.streams: list[Any] = []
        self.thread_tasks: list[asyncio.Task[Any]] = []
        self.index_total_volume: dict[str, float] = {}

    async def connect(self, symbols: list[str]) -> None:
        try:
            from ssi_fc_data.fc_md_client import MarketDataClient
            from ssi_fc_data.fc_md_stream import MarketDataStream
        except ImportError as exc:
            raise ImportError("ssi-fc-data is required: pip install claude-finance-kit[monitor]") from exc
        targets = "ALL" if len(symbols) == 1 and symbols[0].upper() == "ALL" else "-".join(
            symbol.upper() for symbol in symbols
        )
        selected_channels = (
            [self.channel]
            if self.channel
            else [
                f"X-TRADE:{targets}",
                f"X-QUOTE:{targets}",
                f"R:{targets}",
                "MI:ALL",
            ]
        )
        config = SimpleNamespace(
            auth_type="Bearer",
            consumerID=self.consumer_id,
            consumerSecret=self.consumer_secret,
            url=os.getenv("SSI_DATA_URL", "https://fc-data.ssi.com.vn/"),
            stream_url=os.getenv("SSI_STREAM_URL", "https://fc-datahub.ssi.com.vn/"),
        )
        self.loop = asyncio.get_running_loop()
        for selected in selected_channels:
            client = MarketDataClient(config)
            stream = MarketDataStream(config, client)
            self.streams.append(stream)
            task = asyncio.create_task(
                asyncio.to_thread(stream.start, self._on_message, self._on_error, selected)
            )
            task.add_done_callback(self._reader_done)
            self.thread_tasks.append(task)

    async def disconnect(self) -> None:
        for stream in self.streams:
            connection = getattr(stream, "connection", None)
            if connection is not None and callable(getattr(connection, "close", None)):
                connection.close()
            for method_name in ("disconnect", "stop", "close"):
                method = getattr(stream, method_name, None)
                if callable(method):
                    method()
                    break
        self.streams.clear()
        for task in self.thread_tasks:
            task.cancel()
        if self.thread_tasks:
            await asyncio.gather(*self.thread_tasks, return_exceptions=True)
        self.thread_tasks.clear()

    def _reader_done(self, task: asyncio.Task[Any]) -> None:
        if task.cancelled() or not self.loop:
            return
        error = task.exception()
        if error is not None:
            self.loop.call_soon_threadsafe(self._enqueue, error)

    def _on_message(self, raw: str | dict[str, Any]) -> None:
        payload = json.loads(raw) if isinstance(raw, str) else raw
        event = self.parse_message(payload)
        if event and self.loop:
            self.loop.call_soon_threadsafe(self._enqueue, event)

    def _on_error(self, error: Any) -> None:
        if self.loop:
            self.loop.call_soon_threadsafe(
                self._enqueue,
                ConnectionError("SSI stream callback reported an error"),
            )

    def _enqueue(self, event: MarketEvent | Exception) -> None:
        if self.queue.full():
            self.queue.get_nowait()
            self.queue.task_done()
        self.queue.put_nowait(event)

    @staticmethod
    def _first_present(data: dict[str, Any], *keys: str, default: Any = 0) -> Any:
        for key in keys:
            if key in data:
                return data[key]
        return default

    def parse_message(self, payload: dict[str, Any]) -> MarketEvent | None:
        content = payload.get("Content", payload.get("content"))
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except ValueError:
                return None
        data = content if isinstance(content, dict) else payload.get("data", payload.get("Data", payload))
        message_type = str(
            payload.get(
                "DataType",
                payload.get("type", payload.get("Type", payload.get("channel", data.get("RType", "")))),
            )
        ).upper()
        symbol = str(
            data.get(
                "Symbol",
                data.get("symbol", data.get("IndexId", data.get("IndexID", ""))),
            )
        ).upper()
        if not symbol:
            return None
        trading_date = data.get("TradingDate", data.get("tradingDate"))
        raw_time = data.get(
            "Time",
            data.get(
                "time",
                data.get("TradingTime", data.get("tradingTime", datetime.now(UTC))),
            ),
        )
        if isinstance(raw_time, (int, float)):
            timestamp = datetime.fromtimestamp(raw_time / (1000 if raw_time > 10_000_000_000 else 1), UTC)
        else:
            raw_value = f"{trading_date} {raw_time}" if trading_date else str(raw_time)
            try:
                if trading_date:
                    parsed = datetime.strptime(raw_value, "%d/%m/%Y %H:%M:%S")
                elif ":" in raw_value and "T" not in raw_value and " " not in raw_value:
                    local_now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
                    clock = datetime.strptime(raw_value, "%H:%M:%S").time()
                    parsed = datetime.combine(local_now.date(), clock)
                else:
                    parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
            except ValueError:
                return None
            timestamp = parsed if parsed.tzinfo else parsed.replace(tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
        common = {
            "symbol": symbol,
            "market": MarketRegion.VN,
            "timestamp": timestamp,
            "source": "SSI",
            "exchange_timezone": "Asia/Ho_Chi_Minh",
        }
        if message_type in {"X-QUOTE", "X"}:
            bids = [
                OrderBookLevel(
                    price=float(data.get(f"BidPrice{i}", 0)),
                    volume=float(data.get(f"BidVol{i}", 0)),
                )
                for i in range(1, 11)
                if data.get(f"BidPrice{i}") is not None
            ]
            asks = [
                OrderBookLevel(
                    price=float(data.get(f"AskPrice{i}", 0)),
                    volume=float(data.get(f"AskVol{i}", 0)),
                )
                for i in range(1, 11)
                if data.get(f"AskPrice{i}") is not None
            ]
            return MarketEvent(event_type="order_book", record=OrderBookSnapshot(**common, bids=bids, asks=asks))
        if message_type == "R":
            return MarketEvent(
                event_type="foreign_flow",
                record=ForeignFlow(
                    **common,
                    buy_volume=float(self._first_present(data, "BuyVol", "FBuyVol")),
                    sell_volume=float(self._first_present(data, "SellVol", "FSellVol")),
                    buy_value=float(self._first_present(data, "BuyVal", "FBuyVal")),
                    sell_value=float(self._first_present(data, "SellVal", "FSellVal")),
                    room=self._first_present(data, "CurrentRoom", default=None),
                ),
            )
        if message_type == "MI":
            price = data.get("IndexValue", data.get("IndexValEst"))
            if price is None or float(price) <= 0:
                return None
            total_volume = float(
                self._first_present(data, "AllQty", "TotalQtty", default=0)
            )
            previous_volume = self.index_total_volume.get(symbol)
            self.index_total_volume[symbol] = total_volume
            incremental_volume = (
                max(0.0, total_volume - previous_volume)
                if previous_volume is not None
                else 0.0
            )
            return MarketEvent(
                event_type="trade",
                record=TradeTick(
                    **common,
                    price=float(price),
                    volume=incremental_volume,
                    side="unknown",
                    trade_id=(
                        f"MI:{symbol}:{timestamp.isoformat()}:"
                        f"{float(price)}:{total_volume}"
                    ),
                ),
                metadata={"index_tick": True},
            )
        price = data.get("LastPrice", data.get("MatchPrice", data.get("price")))
        volume = data.get("LastVol", data.get("MatchVol", data.get("volume")))
        if message_type == "X-TRADE" and price is not None and volume is not None:
            side_raw = str(data.get("Side", "unknown")).upper()
            side = {"BU": "buy", "B": "buy", "SD": "sell", "S": "sell"}.get(side_raw, "unknown")
            return MarketEvent(
                event_type="trade",
                record=TradeTick(
                    **common,
                    price=float(price),
                    volume=float(volume),
                    side=side,
                    trade_id=str(data.get("TradeId", "")) or None,
                    is_block_trade=bool(data.get("IsDeal", False)),
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
    "SSI",
    SSIStreamProvider,
    ProviderDescriptor(
        source="SSI",
        markets={MarketRegion.VN},
        capabilities={
            ProviderCapability.REALTIME_STREAM,
            ProviderCapability.TRADES,
            ProviderCapability.ORDER_BOOK,
            ProviderCapability.FOREIGN_FLOW,
        },
        requires_auth=True,
        auth_type="client_credentials_bearer",
        realtime=True,
        coverage="official-vn-entitlement-dependent",
    ),
)
