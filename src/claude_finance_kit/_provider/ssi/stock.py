"""SSI FastConnect REST adapter."""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any

import pandas as pd

from claude_finance_kit._provider._base import StockProvider
from claude_finance_kit._provider._market_http import MarketHttpClient, normalize_frame, records_from_payload
from claude_finance_kit._provider._registry import registry
from claude_finance_kit.core.exceptions import AuthenticationError
from claude_finance_kit.core.models import ProviderDescriptor
from claude_finance_kit.core.types import MarketRegion, ProviderCapability

_BASE_URL = "https://fc-data.ssi.com.vn/api/v2"
_HOSTS = {"fc-data.ssi.com.vn"}


def _ssi_date(value: str | None) -> str:
    parsed = datetime.fromisoformat(value).date() if value else date.today()
    return parsed.strftime("%d/%m/%Y")


class SSIStockProvider(StockProvider):
    """Official SSI FastConnect end-of-day and intraday market data."""

    def __init__(
        self,
        consumer_id: str | None = None,
        consumer_secret: str | None = None,
        base_url: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.consumer_id = consumer_id or os.getenv("SSI_CONSUMER_ID") or os.getenv("FC_DATA_CONSUMER_ID")
        self.consumer_secret = (
            consumer_secret or os.getenv("SSI_CONSUMER_SECRET") or os.getenv("FC_DATA_CONSUMER_SECRET")
        )
        if not self.consumer_id or not self.consumer_secret:
            raise AuthenticationError(
                "SSI",
                "SSI_CONSUMER_ID and SSI_CONSUMER_SECRET are required",
            )
        configured = base_url or os.getenv("SSI_DATA_URL") or _BASE_URL
        self.base_url = configured.rstrip("/")
        if self.base_url.endswith("/api/v2"):
            pass
        elif self.base_url.endswith("fc-data.ssi.com.vn"):
            self.base_url += "/api/v2"
        self.http = MarketHttpClient("SSI", _HOSTS, {"Accept": "application/json"}, timeout)
        self._token: str | None = None

    def _access_token(self) -> str:
        if self._token:
            return self._token
        payload = self.http.request(
            "POST",
            f"{self.base_url}/Market/AccessToken",
            json={"consumerID": self.consumer_id, "consumerSecret": self.consumer_secret},
        )
        token = payload.get("data", {}).get("accessToken") if isinstance(payload, dict) else None
        token = token or (payload.get("accessToken") if isinstance(payload, dict) else None)
        if not token:
            raise AuthenticationError("SSI", "SSI did not return an access token")
        self._token = str(token)
        return self._token

    def _get(self, endpoint: str, **params: Any) -> Any:
        return self.http.request(
            "GET",
            f"{self.base_url}/Market/{endpoint}",
            params=params,
            headers={"Authorization": f"Bearer {self._access_token()}"},
        )

    def _paged(self, endpoint: str, *, page_size: int = 1000, **params: Any) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        page_index = 1
        while True:
            payload = self._get(
                endpoint,
                **params,
                pageIndex=page_index,
                pageSize=page_size,
            )
            page = records_from_payload(payload)
            records.extend(page)
            if not page or len(page) < page_size:
                return records
            page_index += 1

    @staticmethod
    def _normalize(
        records: list[dict[str, Any]],
        aliases: dict[str, str],
        *,
        numeric: tuple[str, ...] = (),
        required: tuple[str, ...] = (),
    ) -> pd.DataFrame:
        frame = normalize_frame(
            records,
            aliases,
            numeric=numeric,
            required=required,
            timestamp=None,
            source="SSI",
        )
        if "time" in frame:
            parsed = pd.to_datetime(frame["time"], dayfirst=True, errors="coerce")
            frame["time"] = (
                parsed.dt.tz_localize(
                    "Asia/Ho_Chi_Minh",
                    ambiguous="NaT",
                    nonexistent="shift_forward",
                )
                .dt.tz_convert("UTC")
            )
            frame = frame.sort_values("time").drop_duplicates("time", keep="last").reset_index(drop=True)
        return frame

    def history(self, symbol: str, start: str, end: str | None = None, interval: str = "1D") -> pd.DataFrame:
        if interval not in {"1D", "1d", "1m"}:
            raise ValueError("SSI REST supports 1D and 1m intervals")
        endpoint = "DailyOhlc" if interval.lower() == "1d" else "IntradayOhlc"
        records = self._paged(
            endpoint,
            symbol=symbol.upper(),
            fromDate=_ssi_date(start),
            toDate=_ssi_date(end),
            ascending=True,
            **({"resolution": 1} if endpoint == "IntradayOhlc" else {}),
        )
        for record in records:
            if record.get("Time"):
                record["Timestamp"] = f"{record.get('TradingDate', '')} {record['Time']}"
            else:
                record["Timestamp"] = record.get("TradingDate")
        frame = self._normalize(
            records,
            {
                "timestamp": "time",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
                "value": "value",
                "symbol": "symbol",
                "market": "exchange",
            },
            numeric=("open", "high", "low", "close", "volume", "value"),
            required=("time", "open", "high", "low", "close", "volume"),
        )
        frame.attrs.update(symbol=symbol.upper(), market="VN", interval=interval)
        return frame

    def intraday(self, symbol: str) -> pd.DataFrame:
        today = date.today().isoformat()
        return self.history(symbol, today, today, "1m")

    def _daily_stock_price(self, symbol: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        records = self._paged(
            "DailyStockPrice",
            symbol=symbol.upper(),
            fromDate=_ssi_date(start),
            toDate=_ssi_date(end),
            ascending=True,
        )
        for record in records:
            record["Timestamp"] = record.get("TradingDate")
        return self._normalize(
            records,
            {
                "timestamp": "time",
                "symbol": "symbol",
                "closeprice": "price",
                "totalmatchvol": "volume",
                "foreignbuyvoltotal": "foreign_buy_volume",
                "foreignsellvoltotal": "foreign_sell_volume",
                "foreignbuyvaltotal": "foreign_buy_value",
                "foreignsellvaltotal": "foreign_sell_value",
                "foreigncurrentroom": "foreign_room",
            },
            numeric=(
                "price",
                "volume",
                "foreign_buy_volume",
                "foreign_sell_volume",
                "foreign_buy_value",
                "foreign_sell_value",
                "foreign_room",
            ),
        )

    def price_board(self, symbols: list[str]) -> pd.DataFrame:
        if len(symbols) > 30:
            raise ValueError("SSI price_board is bounded to 30 symbols per call")
        frames = [self._daily_stock_price(symbol).tail(1) for symbol in symbols]
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def foreign_flow(self, symbol: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        frame = self._daily_stock_price(symbol, start, end)
        columns = [
            column
            for column in (
                "time",
                "symbol",
                "foreign_buy_volume",
                "foreign_sell_volume",
                "foreign_buy_value",
                "foreign_sell_value",
                "foreign_room",
            )
            if column in frame
        ]
        result = frame.loc[:, columns].copy()
        result.attrs.update(source="SSI", symbol=symbol.upper(), market="VN")
        return result

    def all_symbols(self, exchange: str | None = None) -> pd.DataFrame:
        exchanges = [exchange.upper()] if exchange else ["HOSE", "HNX", "UPCOM"]
        frames: list[pd.DataFrame] = []
        for market in exchanges:
            records = self._paged("Securities", market=market)
            frame = normalize_frame(
                records,
                {
                    "symbol": "symbol",
                    "market": "exchange",
                    "stockname": "name",
                    "stockenname": "name_en",
                },
                timestamp=None,
                required=("symbol",),
                source="SSI",
            )
            frames.append(frame)
        result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        result.attrs["source"] = "SSI"
        return result

    def price_depth(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("SSI REST has no order-book history; use SSIStreamProvider.")

    def company_overview(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("SSI FastConnect Data does not provide company fundamentals.")

    def shareholders(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("SSI FastConnect Data does not provide shareholders.")

    def income_statement(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        raise NotImplementedError("SSI FastConnect Data does not provide financial statements.")

    def balance_sheet(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        raise NotImplementedError("SSI FastConnect Data does not provide financial statements.")

    def cash_flow(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        raise NotImplementedError("SSI FastConnect Data does not provide financial statements.")

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        raise NotImplementedError("SSI FastConnect Data does not provide financial ratios.")

    def symbols_by_group(self, group: str) -> pd.DataFrame:
        records = self._paged("IndexComponents", indexCode=group.upper())
        return normalize_frame(
            records,
            {"symbol": "symbol", "indexcode": "group"},
            timestamp=None,
            required=("symbol",),
            source="SSI",
        )

    def symbols_by_industries(self) -> pd.DataFrame:
        raise NotImplementedError("SSI FastConnect Data does not provide industry classifications.")


_DESCRIPTOR = ProviderDescriptor(
    source="SSI",
    markets={MarketRegion.VN},
    capabilities={
        ProviderCapability.HISTORICAL_BARS,
        ProviderCapability.INTRADAY,
        ProviderCapability.PRICE_BOARD,
        ProviderCapability.FOREIGN_FLOW,
        ProviderCapability.LISTING,
        ProviderCapability.REALTIME_STREAM,
    },
    requires_auth=True,
    auth_type="client_credentials_bearer",
    realtime=True,
    coverage="official-vn-entitlement-dependent",
)
registry.register_stock("SSI", SSIStockProvider, _DESCRIPTOR)
