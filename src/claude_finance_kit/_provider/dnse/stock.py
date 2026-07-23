"""DNSE OpenAPI REST market-data adapter."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import UTC, date, datetime
from typing import Any
from urllib.parse import quote
from uuid import uuid4

import pandas as pd

from claude_finance_kit._internal.parser import get_asset_type
from claude_finance_kit._provider._base import StockProvider
from claude_finance_kit._provider._market_http import MarketHttpClient, normalize_frame, records_from_payload
from claude_finance_kit._provider._registry import registry
from claude_finance_kit.core.exceptions import AuthenticationError
from claude_finance_kit.core.models import ProviderDescriptor
from claude_finance_kit.core.types import MarketRegion, ProviderCapability

_BASE_URL = "https://openapi.dnse.com.vn"
_HOSTS = {"openapi.dnse.com.vn"}
_API_VERSION = "2026-05-07"


class DNSEStockProvider(StockProvider):
    """Vietnam market data from documented DNSE REST endpoints."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("DNSE_API_KEY")
        self.api_secret = api_secret or os.getenv("DNSE_API_SECRET")
        if not self.api_key or not self.api_secret:
            raise AuthenticationError("DNSE", "DNSE_API_KEY and DNSE_API_SECRET are required")
        self.base_url = (base_url or os.getenv("DNSE_MARKET_DATA_URL") or _BASE_URL).rstrip("/")
        self.http = MarketHttpClient("DNSE", _HOSTS, {"Accept": "application/json"}, timeout)

    def _get(self, path: str, **params: Any) -> Any:
        date_value = datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S %z")
        nonce = uuid4().hex
        signature_input = f"(request-target): get {path}\ndate: {date_value}\nnonce: {nonce}"
        digest = hmac.new(
            self.api_secret.encode(),
            signature_input.encode(),
            hashlib.sha256,
        ).digest()
        signature = quote(base64.b64encode(digest).decode(), safe="")
        signature_header = (
            f'Signature keyId="{self.api_key}",algorithm="hmac-sha256",'
            f'headers="(request-target) date",signature="{signature}",nonce="{nonce}"'
        )
        return self.http.request(
            "GET",
            f"{self.base_url}{path}",
            params={key: value for key, value in params.items() if value is not None},
            headers={
                "Date": date_value,
                "X-Signature": signature_header,
                "x-api-key": self.api_key,
                "version": os.getenv("DNSE_API_VERSION", _API_VERSION),
            },
        )

    @staticmethod
    def _epoch(value: str | None, *, end: bool = False) -> int:
        timestamp = pd.Timestamp(value or date.today().isoformat())
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("Asia/Ho_Chi_Minh")
        if end and len(str(value or "")) <= 10:
            timestamp += pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        return int(timestamp.tz_convert(UTC).timestamp())

    def _paged_get(
        self,
        path: str,
        *,
        total_limit: int = 10_000,
        use_page: bool = False,
        **params: Any,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        token: str | None = None
        page_index = 1
        while len(records) < total_limit:
            payload = self._get(
                path,
                **params,
                limit=min(1000, total_limit - len(records)),
                **({"page": page_index} if use_page else {"nextPageToken": token}),
            )
            page = records_from_payload(payload)
            records.extend(page)
            token = (
                payload.get("nextPageToken") or payload.get("next_page_token")
                if isinstance(payload, dict)
                else None
            )
            if use_page:
                if not page or len(page) < min(1000, total_limit - len(records) + len(page)):
                    break
                page_index += 1
            elif not token or not page:
                break
        return records[:total_limit]

    def history(self, symbol: str, start: str, end: str | None = None, interval: str = "1D") -> pd.DataFrame:
        resolution = {
            "1m": "1",
            "5m": "5",
            "15m": "15",
            "30m": "30",
            "1H": "60",
            "1h": "60",
            "1D": "1D",
            "1d": "1D",
        }.get(interval)
        if resolution is None:
            raise ValueError(f"DNSE does not support interval '{interval}'")
        payload = self._get(
            "/price/ohlc",
            symbol=symbol.upper(),
            type="INDEX" if get_asset_type(symbol) == "index" else "STOCK",
            **{
                "from": self._epoch(start),
                "to": self._epoch(end, end=True),
                "resolution": resolution,
            },
        )
        if isinstance(payload, dict) and isinstance(payload.get("t"), list):
            keys = ("t", "o", "h", "l", "c", "v")
            records = [
                dict(zip(keys, values, strict=False))
                for values in zip(*(payload.get(key, []) for key in keys), strict=False)
            ]
        else:
            records = records_from_payload(payload)
        frame = normalize_frame(
            records,
            {
                "t": "time",
                "timestamp": "time",
                "time": "time",
                "o": "open",
                "h": "high",
                "l": "low",
                "c": "close",
                "v": "volume",
            },
            numeric=("open", "high", "low", "close", "volume"),
            required=("time", "open", "high", "low", "close", "volume"),
            source="DNSE",
        )
        frame.attrs.update(symbol=symbol.upper(), market="VN", interval=interval)
        return frame

    def intraday(self, symbol: str) -> pd.DataFrame:
        today = date.today().isoformat()
        return self.history(symbol, today, today, "1m")

    def trades(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        records = self._paged_get(
            f"/price/{symbol.upper()}/trades",
            total_limit=limit,
            boardId="G1",
            **{
                "from": self._epoch(start) if start else None,
                "to": self._epoch(end, end=True) if end else None,
                "order": "ASC",
            },
        )
        frame = normalize_frame(
            records,
            {
                "t": "time",
                "timestamp": "time",
                "matchtime": "time",
                "p": "price",
                "matchprice": "price",
                "q": "volume",
                "matchqtty": "volume",
                "side": "side",
                "id": "trade_id",
                "board": "board",
            },
            numeric=("price", "volume"),
            required=("time", "price", "volume"),
            deduplicate_timestamp=False,
            source="DNSE",
        )
        frame.attrs.update(symbol=symbol.upper(), market="VN")
        return frame

    def order_book(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        if start or end:
            records = self._paged_get(
                f"/price/{symbol.upper()}/quotes",
                total_limit=limit,
                boardId="G1",
                **{
                    "from": self._epoch(start) if start else None,
                    "to": self._epoch(end, end=True) if end else None,
                    "order": "ASC",
                },
            )
        else:
            records = records_from_payload(
                self._get(f"/price/{symbol.upper()}/quotes/latest", boardId="G1")
            )
        frame = normalize_frame(
            records,
            {
                "t": "time",
                "timestamp": "time",
                "bidprice": "bid_price",
                "bidqtty": "bid_volume",
                "askprice": "ask_price",
                "askqtty": "ask_volume",
            },
            numeric=("bid_price", "bid_volume", "ask_price", "ask_volume"),
            deduplicate_timestamp=False,
            source="DNSE",
        )
        frame.attrs.update(symbol=symbol.upper(), market="VN")
        return frame

    def foreign_flow(self, symbol: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        records = self._paged_get(
            f"/price/{symbol.upper()}/foreign-trading",
            boardId="G1",
            **{
                "from": self._epoch(start) if start else None,
                "to": self._epoch(end, end=True) if end else None,
                "order": "ASC",
            },
        )
        frame = normalize_frame(
            records,
            {
                "t": "time",
                "timestamp": "time",
                "buyvolume": "buy_volume",
                "sellvolume": "sell_volume",
                "buyvalue": "buy_value",
                "sellvalue": "sell_value",
                "currentroom": "room",
            },
            numeric=("buy_volume", "sell_volume", "buy_value", "sell_value", "room"),
            source="DNSE",
        )
        frame.attrs.update(symbol=symbol.upper(), market="VN")
        return frame

    def all_symbols(self, exchange: str | None = None) -> pd.DataFrame:
        records = self._paged_get("/instruments", marketId=exchange, use_page=True)
        frame = normalize_frame(
            records,
            {
                "symbol": "symbol",
                "code": "symbol",
                "exchange": "exchange",
                "name": "name",
                "securityname": "name",
            },
            timestamp=None,
            required=("symbol",),
            source="DNSE",
        )
        if "symbol" in frame:
            frame["symbol"] = frame["symbol"].astype(str).str.upper()
        return frame

    def price_depth(self, symbol: str) -> pd.DataFrame:
        return self.order_book(symbol)

    def price_board(self, symbols: list[str]) -> pd.DataFrame:
        raise NotImplementedError("DNSE REST does not expose a normalized multi-symbol price board.")

    def company_overview(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("DNSE does not provide company fundamentals.")

    def shareholders(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("DNSE does not provide shareholders.")

    def income_statement(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        raise NotImplementedError("DNSE does not provide financial statements.")

    def balance_sheet(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        raise NotImplementedError("DNSE does not provide financial statements.")

    def cash_flow(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        raise NotImplementedError("DNSE does not provide financial statements.")

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        raise NotImplementedError("DNSE does not provide financial ratios.")

    def symbols_by_group(self, group: str) -> pd.DataFrame:
        frame = self.all_symbols()
        if "group" not in frame:
            raise NotImplementedError("DNSE instrument response does not include index membership.")
        return frame.loc[frame["group"].astype(str).str.upper() == group.upper()].reset_index(drop=True)

    def symbols_by_industries(self) -> pd.DataFrame:
        frame = self.all_symbols()
        if "industry" not in frame:
            raise NotImplementedError("DNSE instrument response does not include industries.")
        return frame


_DESCRIPTOR = ProviderDescriptor(
    source="DNSE",
    markets={MarketRegion.VN},
    capabilities={
        ProviderCapability.HISTORICAL_BARS,
        ProviderCapability.INTRADAY,
        ProviderCapability.TRADES,
        ProviderCapability.ORDER_BOOK,
        ProviderCapability.FOREIGN_FLOW,
        ProviderCapability.LISTING,
        ProviderCapability.REALTIME_STREAM,
    },
    requires_auth=True,
    auth_type="api_key_hmac",
    realtime=True,
    coverage="official-vn",
)
registry.register_stock("DNSE", DNSEStockProvider, _DESCRIPTOR)
