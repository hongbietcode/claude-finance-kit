"""KBS (KB Securities) quote module: historical OHLCV and intraday tick data."""

import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.parser import get_asset_type
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.kbs.const import (
    _IIS_BASE_URL,
    _INDEX_MAPPING,
    _INTERVAL_MAP,
    _INTRADAY_DTYPE,
    _INTRADAY_MAP,
    _OHLC_DTYPE,
    _OHLC_MAP,
)

logger = logging.getLogger(__name__)


def _format_date_kbs(date_str: str) -> str:
    """Convert YYYY-MM-DD to DD-MM-YYYY for KBS API."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%m-%Y")
    except ValueError:
        return date_str


class KBSQuote:
    """Fetches OHLCV history and intraday ticks from KBS."""

    DATA_SOURCE = "KBS"

    def __init__(self) -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)

    def history(
        self,
        symbol: str,
        start: str,
        end: Optional[str] = None,
        interval: str = "1D",
    ) -> pd.DataFrame:
        symbol = symbol.upper()
        asset_type = get_asset_type(symbol)

        if asset_type == "index" and symbol not in _INDEX_MAPPING:
            valid = ", ".join(_INDEX_MAPPING.keys())
            raise ValueError(f"Index '{symbol}' not supported by KBS. Valid: {valid}")

        if interval not in _INTERVAL_MAP:
            valid = ", ".join(_INTERVAL_MAP.keys())
            raise ValueError(f"Invalid interval '{interval}'. Valid: {valid}")

        end_date = end or datetime.now().strftime("%Y-%m-%d")
        interval_suffix = _INTERVAL_MAP[interval]

        if asset_type == "index":
            url = f"{_IIS_BASE_URL}/index/{symbol}/data_{interval_suffix}"
        else:
            url = f"{_IIS_BASE_URL}/stocks/{symbol}/data_{interval_suffix}"

        params = {
            "sdate": _format_date_kbs(start),
            "edate": _format_date_kbs(end_date),
        }

        json_data = send_request(
            url=url,
            headers=self._headers,
            method="GET",
            params=params,
        )

        if not json_data:
            return pd.DataFrame()

        data_key = f"data_{interval_suffix}"
        if data_key not in json_data:
            return pd.DataFrame()

        ohlc_data = json_data[data_key]
        if not ohlc_data:
            return pd.DataFrame()

        df = pd.DataFrame(ohlc_data)
        df = df.rename(columns=_OHLC_MAP)

        base_cols = ["time", "open", "high", "low", "close", "volume"]
        existing = [c for c in base_cols if c in df.columns]
        df = df[existing]

        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values("time").reset_index(drop=True)

        for col, dtype in _OHLC_DTYPE.items():
            if col not in df.columns:
                continue
            try:
                df[col] = df[col].astype(dtype)
            except (ValueError, TypeError):
                df[col] = df[col].astype(float).astype(dtype)

        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                df[col] = (df[col] / 1000).round(2)

        df = df[df["time"] >= pd.to_datetime(start)].reset_index(drop=True)
        df.attrs.update(symbol=symbol, source=self.DATA_SOURCE, interval=interval)
        return df

    def intraday(self, symbol: str, page_size: int = 100) -> pd.DataFrame:
        symbol = symbol.upper()
        asset_type = get_asset_type(symbol)

        if asset_type == "index":
            raise ValueError(f"Intraday data not supported for index '{symbol}'.")

        url = f"{_IIS_BASE_URL}/trade/history/{symbol}"
        params = {"page": 1, "limit": page_size}

        json_data = send_request(
            url=url,
            headers=self._headers,
            method="GET",
            params=params,
        )

        if not json_data or "data" not in json_data:
            return pd.DataFrame()

        intraday_data = json_data.get("data", [])
        if not intraday_data:
            return pd.DataFrame()

        df = pd.DataFrame(intraday_data)
        df = df.rename(columns=_INTRADAY_MAP)

        if "timestamp" in df.columns:
            df["timestamp"] = df["timestamp"].apply(
                lambda x: pd.to_datetime(x.rsplit(":", 1)[0]) if isinstance(x, str) else x
            )

        for col, dtype in _INTRADAY_DTYPE.items():
            if col in df.columns:
                try:
                    df[col] = df[col].astype(dtype)
                except (ValueError, TypeError):
                    pass

        df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)

        result = pd.DataFrame()
        if "timestamp" in df.columns:
            result["time"] = df["timestamp"]
        if "price" in df.columns:
            result["price"] = (df["price"] / 1000).round(2)
        if "match_volume" in df.columns:
            result["volume"] = df["match_volume"]
        if "side" in df.columns:
            result["match_type"] = df["side"].fillna("").str.lower()
        if "timestamp" in df.columns and "price" in df.columns and "match_volume" in df.columns:
            result["id"] = (
                df["timestamp"].astype(str).str.replace(" ", "_").str.replace(":", "")
                + "_" + df["price"].astype(str).str.replace(".", "")
                + "_" + df["match_volume"].astype(str)
            )

        result.attrs.update(symbol=symbol, source=self.DATA_SOURCE)
        return result
