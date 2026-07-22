"""MSN Finance historical price provider."""

from datetime import datetime
from typing import Any

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.msn.const import (
    _BASE_URL,
    _CONFIG_URL,
    _MSN_ALLOWED_HOSTS,
    _OHLC_MAP,
    _RESAMPLE_MAP,
)
from claude_finance_kit._provider.msn.listing import MSNListing


def _find_api_key(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() == "apikey" and isinstance(item, str) and item:
                return item
            found = _find_api_key(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_api_key(item)
            if found:
                return found
    return None


def _utc_day_boundary(value: str, *, end: bool = False) -> tuple[pd.Timestamp, str]:
    """Convert a Vietnam market date to its exact UTC day boundary."""
    try:
        local = pd.Timestamp(datetime.strptime(value, "%Y-%m-%d"), tz="Asia/Ho_Chi_Minh")
    except ValueError as exc:
        raise ValueError("MSN dates must use YYYY-MM-DD format.") from exc
    boundary = local + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1) if end else local
    utc = boundary.tz_convert("UTC")
    suffix = ".999Z" if end else ".000Z"
    return local, utc.strftime("%Y-%m-%dT%H:%M:%S") + suffix


class MSNQuote:
    """Fetch daily history after resolving MSN's internal security identifier."""

    DATA_SOURCE = "MSN"

    def __init__(self, api_version: str = "20240430") -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)
        self._api_version = api_version
        self._api_key: str | None = None
        self._listing = MSNListing()

    def _get_api_key(self) -> str:
        if self._api_key:
            return self._api_key
        scope = (
            '{"audienceMode":"adult","browser":{"browserType":"chrome","version":"0",'
            '"ismobile":"false"},"deviceFormFactor":"desktop","domain":"www.msn.com",'
            '"locale":{"content":{"language":"vi","market":"vn"},"display":'
            '{"language":"vi","market":"vn"}},"os":"macos","platform":"web",'
            '"pageType":"financestockdetails"}'
        )
        response = send_request(
            url=_CONFIG_URL,
            headers=self._headers,
            params={
                "expType": "AppConfig",
                "expInstance": "default",
                "apptype": "finance",
                "v": f"{self._api_version}.168",
                "targetScope": scope,
            },
            allowed_hosts=_MSN_ALLOWED_HOSTS,
        )
        api_key = _find_api_key(response)
        if not api_key:
            raise ValueError("MSN configuration response did not include an API key.")
        self._api_key = api_key
        return api_key

    def history(
        self,
        symbol: str,
        start: str,
        end: str | None = None,
        interval: str = "1D",
    ) -> pd.DataFrame:
        interval = interval.upper()
        if interval not in _RESAMPLE_MAP:
            raise ValueError(f"MSN supports intervals: {', '.join(_RESAMPLE_MAP)}")
        end = end or datetime.now().strftime("%Y-%m-%d")
        start_date, start_boundary = _utc_day_boundary(start)
        end_date, end_boundary = _utc_day_boundary(end, end=True)
        if start_date > end_date:
            raise ValueError("start date cannot be after end date.")
        sec_id = self._listing.resolve_symbol_id(symbol)
        endpoint = "Cryptocurrency/chart" if sec_id.startswith("c211") else "Charts/TimeRange"
        response = send_request(
            url=f"{_BASE_URL}/{endpoint}",
            headers=self._headers,
            params={
                "apikey": self._get_api_key(),
                "StartTime": start_boundary,
                "EndTime": end_boundary,
                "timeframe": 1,
                "ocid": "finance-utils-peregrine",
                "cm": "vi-vn",
                "it": "web",
                "scn": "ANON",
                "ids": sec_id,
                "type": "All",
                "wrapodata": "false",
                "disableSymbol": "false",
            },
            allowed_hosts=_MSN_ALLOWED_HOSTS,
        )
        first = response[0] if isinstance(response, list) and response else None
        series = first.get("series", []) if isinstance(first, dict) else []
        if not isinstance(series, list):
            series = []
        df = pd.DataFrame(series)
        if df.empty:
            empty = pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
            empty.attrs.update(symbol=symbol.upper(), source=self.DATA_SOURCE, sec_id=sec_id)
            return empty

        df = df.rename(columns=_OHLC_MAP)
        required = ["time", "open", "high", "low", "close"]
        missing = [column for column in required if column not in df.columns]
        if missing:
            raise ValueError(f"MSN history response is missing fields: {', '.join(missing)}")
        if "volume" not in df.columns:
            df["volume"] = pd.NA
        df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True).dt.tz_convert("Asia/Ho_Chi_Minh")
        df["time"] = df["time"].dt.tz_localize(None).dt.floor("D")
        for column in ["open", "high", "low", "close", "volume"]:
            df[column] = pd.to_numeric(df[column], errors="coerce")
        df = df.dropna(subset=["time", "open", "high", "low", "close"])
        df = df[(df["time"] >= pd.Timestamp(start)) & (df["time"] <= pd.Timestamp(end))]
        df = df[["time", "open", "high", "low", "close", "volume"]]

        if interval != "1D":
            df = (
                df.set_index("time")
                .resample(_RESAMPLE_MAP[interval])
                .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
                .dropna(subset=["open", "high", "low", "close"])
                .reset_index()
            )
        df.attrs.update(symbol=symbol.upper(), source=self.DATA_SOURCE, sec_id=sec_id)
        return df.reset_index(drop=True)
