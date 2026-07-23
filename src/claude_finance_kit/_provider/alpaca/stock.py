"""Alpaca Basic/IEX REST market-data adapter."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd

from claude_finance_kit._provider._base import StockProvider
from claude_finance_kit._provider._market_http import MarketHttpClient, normalize_frame
from claude_finance_kit._provider._registry import registry
from claude_finance_kit.core.exceptions import AuthenticationError
from claude_finance_kit.core.models import ProviderDescriptor
from claude_finance_kit.core.types import MarketRegion, ProviderCapability

_BASE_URL = "https://data.alpaca.markets"
_HOSTS = {"data.alpaca.markets"}


class AlpacaStockProvider(StockProvider):
    """US market data using Alpaca's free IEX feed only."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
        self.api_secret = api_secret or os.getenv("ALPACA_API_SECRET") or os.getenv("APCA_API_SECRET_KEY")
        if not self.api_key or not self.api_secret:
            raise AuthenticationError("ALPACA", "Alpaca market-data API key and secret are required")
        self.base_url = (base_url or _BASE_URL).rstrip("/")
        self.http = MarketHttpClient(
            "ALPACA",
            _HOSTS,
            {
                "Accept": "application/json",
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret,
            },
            timeout,
        )

    def _get(self, path: str, **params: Any) -> Any:
        return self.http.request("GET", f"{self.base_url}{path}", params=params)

    @staticmethod
    def _timeframe(interval: str) -> str:
        mapping = {
            "1m": "1Min",
            "5m": "5Min",
            "15m": "15Min",
            "30m": "30Min",
            "1H": "1Hour",
            "1h": "1Hour",
            "1D": "1Day",
            "1d": "1Day",
            "1W": "1Week",
            "1w": "1Week",
            "1M": "1Month",
        }
        if interval not in mapping:
            raise ValueError(f"Unsupported Alpaca interval '{interval}'")
        return mapping[interval]

    def _paged(
        self,
        path: str,
        collection: str,
        *,
        total_limit: int | None = None,
        **params: Any,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            payload = self._get(path, **params, page_token=page_token)
            page = payload.get(collection, []) if isinstance(payload, dict) else []
            if isinstance(page, list):
                records.extend(record for record in page if isinstance(record, dict))
            if total_limit is not None and len(records) >= total_limit:
                return records[:total_limit]
            page_token = payload.get("next_page_token") if isinstance(payload, dict) else None
            if not page_token:
                return records

    def history(self, symbol: str, start: str, end: str | None = None, interval: str = "1D") -> pd.DataFrame:
        records = self._paged(
            f"/v2/stocks/{symbol.upper()}/bars",
            "bars",
            timeframe=self._timeframe(interval),
            start=start,
            end=end,
            adjustment="all",
            feed="iex",
            limit=10_000,
        )
        frame = normalize_frame(
            records,
            {
                "t": "time",
                "o": "open",
                "h": "high",
                "l": "low",
                "c": "close",
                "v": "volume",
                "n": "trades",
                "vw": "vwap",
            },
            numeric=("open", "high", "low", "close", "volume", "trades", "vwap"),
            required=("time", "open", "high", "low", "close", "volume"),
            source="ALPACA",
        )
        frame.attrs.update(
            symbol=symbol.upper(),
            market="US",
            interval=interval,
            adjusted=True,
            coverage="iex-partial",
        )
        return frame

    def intraday(self, symbol: str) -> pd.DataFrame:
        start = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        return self.history(symbol, start, interval="1m")

    def trades(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        records = self._paged(
            f"/v2/stocks/{symbol.upper()}/trades",
            "trades",
            start=start,
            end=end,
            feed="iex",
            limit=min(limit, 10_000),
            total_limit=limit,
        )
        frame = normalize_frame(
            records,
            {
                "t": "time",
                "p": "price",
                "s": "volume",
                "i": "trade_id",
                "x": "exchange",
                "c": "conditions",
            },
            numeric=("price", "volume"),
            required=("time", "price", "volume"),
            deduplicate_timestamp=False,
            source="ALPACA",
        )
        frame.attrs.update(symbol=symbol.upper(), market="US", coverage="iex-partial")
        return frame

    def order_book(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        records = self._paged(
            f"/v2/stocks/{symbol.upper()}/quotes",
            "quotes",
            start=start,
            end=end,
            feed="iex",
            limit=min(limit, 10_000),
            total_limit=limit,
        )
        frame = normalize_frame(
            records,
            {
                "t": "time",
                "bp": "bid_price",
                "bs": "bid_volume",
                "ap": "ask_price",
                "as": "ask_volume",
                "bx": "bid_exchange",
                "ax": "ask_exchange",
            },
            numeric=("bid_price", "bid_volume", "ask_price", "ask_volume"),
            deduplicate_timestamp=False,
            source="ALPACA",
        )
        frame.attrs.update(symbol=symbol.upper(), market="US", coverage="iex-partial")
        return frame

    def price_depth(self, symbol: str) -> pd.DataFrame:
        return self.order_book(symbol, limit=1)

    def price_board(self, symbols: list[str]) -> pd.DataFrame:
        payload = self._get("/v2/stocks/snapshots", symbols=",".join(symbol.upper() for symbol in symbols), feed="iex")
        rows: list[dict[str, Any]] = []
        if isinstance(payload, dict):
            for symbol, snapshot in payload.items():
                if not isinstance(snapshot, dict):
                    continue
                trade = snapshot.get("latestTrade", {})
                quote = snapshot.get("latestQuote", {})
                rows.append(
                    {
                        "symbol": symbol,
                        "price": trade.get("p"),
                        "volume": trade.get("s"),
                        "bid_price": quote.get("bp"),
                        "ask_price": quote.get("ap"),
                        "time": trade.get("t") or quote.get("t"),
                    }
                )
        frame = normalize_frame(
            rows,
            {},
            numeric=("price", "volume", "bid_price", "ask_price"),
            required=("symbol", "time"),
            deduplicate_timestamp=False,
            source="ALPACA",
        )
        frame.attrs.update(market="US", coverage="iex-partial")
        return frame

    def company_overview(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("Alpaca Market Data does not provide company fundamentals.")

    def shareholders(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("Alpaca Market Data does not provide shareholders.")

    def income_statement(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        raise NotImplementedError("Alpaca Market Data does not provide financial statements.")

    def balance_sheet(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        raise NotImplementedError("Alpaca Market Data does not provide financial statements.")

    def cash_flow(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        raise NotImplementedError("Alpaca Market Data does not provide financial statements.")

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        raise NotImplementedError("Alpaca Market Data does not provide ratios.")

    def all_symbols(self, exchange: str | None = None) -> pd.DataFrame:
        raise NotImplementedError("Asset discovery belongs to Alpaca Trading API and is intentionally out of scope.")

    def symbols_by_group(self, group: str) -> pd.DataFrame:
        raise NotImplementedError("Alpaca Market Data does not provide index constituents.")

    def symbols_by_industries(self) -> pd.DataFrame:
        raise NotImplementedError("Alpaca Market Data does not provide industries.")


_DESCRIPTOR = ProviderDescriptor(
    source="ALPACA",
    markets={MarketRegion.US},
    capabilities={
        ProviderCapability.HISTORICAL_BARS,
        ProviderCapability.INTRADAY,
        ProviderCapability.PRICE_BOARD,
        ProviderCapability.TRADES,
        ProviderCapability.ORDER_BOOK,
        ProviderCapability.REALTIME_STREAM,
    },
    requires_auth=True,
    auth_type="api_key_secret",
    realtime=True,
    coverage="iex-partial",
    max_stream_symbols=30,
)
registry.register_stock("ALPACA", AlpacaStockProvider, _DESCRIPTOR)
