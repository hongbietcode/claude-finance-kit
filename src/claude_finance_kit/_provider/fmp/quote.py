"""FMP quote module: historical OHLCV and intraday data."""

import logging

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.transform import resample_ohlcv
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.fmp.const import (
    _FMP_DOMAIN,
    _INTERVAL_MAP,
    _OHLC_DTYPE,
    _OHLC_MAP,
    _RESAMPLE_MAP,
    get_api_key,
)

logger = logging.getLogger(__name__)


class FMPQuote:
    """Fetches OHLCV and intraday price data from FMP."""

    DATA_SOURCE = "FMP"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = get_api_key(api_key)
        self._headers = get_headers(data_source="MSN", random_agent=True)

    def _build_url(self, endpoint: str, symbol: str, **params: str) -> str:
        base = f"{_FMP_DOMAIN}{endpoint}?symbol={symbol}&apikey={self._api_key}"
        for k, v in params.items():
            if v is not None:
                base += f"&{k}={v}"
        return base

    def history(
        self,
        symbol: str,
        start: str,
        end: str | None = None,
        interval: str = "1D",
    ) -> pd.DataFrame:
        if interval not in _INTERVAL_MAP:
            raise ValueError(f"Unsupported interval '{interval}'. Use: {list(_INTERVAL_MAP.keys())}")

        endpoint_key = _INTERVAL_MAP[interval]
        endpoint = (
            f"/{endpoint_key.replace('_', '-')}"
            if "historical" not in endpoint_key
            else {
                "historical_price_eod": "/historical-price-eod/full",
                "historical_chart_1min": "/historical-chart/1min",
                "historical_chart_5min": "/historical-chart/5min",
                "historical_chart_15min": "/historical-chart/15min",
                "historical_chart_30min": "/historical-chart/30min",
                "historical_chart_1hour": "/historical-chart/1hour",
                "historical_chart_4hour": "/historical-chart/4hour",
            }[endpoint_key]
        )

        params = {"from": start}
        if end:
            params["to"] = end

        url = self._build_url(endpoint, symbol, **params)
        json_data = send_request(url=url, headers=self._headers, method="GET")

        if not json_data:
            return pd.DataFrame(columns=list(_OHLC_MAP.values()))

        records = json_data.get("historical", json_data) if isinstance(json_data, dict) else json_data
        if not records:
            return pd.DataFrame(columns=list(_OHLC_MAP.values()))

        df = pd.DataFrame(records)
        df = df.rename(columns=_OHLC_MAP)

        keep_cols = [c for c in _OHLC_MAP.values() if c in df.columns]
        df = df.loc[:, keep_cols]

        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
            df = df.sort_values("time", ascending=True).reset_index(drop=True)

        for col in _OHLC_DTYPE:
            if col in df.columns and col != "time":
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if interval in _RESAMPLE_MAP:
            df = resample_ohlcv(df, _RESAMPLE_MAP[interval])

        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def intraday(self, symbol: str) -> pd.DataFrame:
        return self.history(symbol, start="", interval="1m")
