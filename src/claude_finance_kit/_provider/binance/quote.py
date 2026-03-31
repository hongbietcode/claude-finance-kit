"""Binance quote module: OHLCV history, intraday, and order book depth."""

import logging
from datetime import datetime

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._provider.binance.const import _BASE_URL, _INTERVAL_MAP, _KLINE_COLUMNS

logger = logging.getLogger(__name__)


class BinanceQuote:
    """Fetches OHLCV, trades, and depth from Binance public API."""

    DATA_SOURCE = "BINANCE"

    def __init__(self) -> None:
        self._headers = {"Accept": "application/json"}

    def history(
        self,
        symbol: str,
        start: str,
        end: str | None = None,
        interval: str = "1D",
    ) -> pd.DataFrame:
        if interval not in _INTERVAL_MAP:
            raise ValueError(
                f"Unsupported interval '{interval}'. Use: {list(_INTERVAL_MAP.keys())}"
            )

        params = {
            "symbol": symbol.upper(),
            "interval": _INTERVAL_MAP[interval],
            "limit": "1000",
        }
        if start:
            params["startTime"] = str(int(datetime.strptime(start, "%Y-%m-%d").timestamp() * 1000))
        if end:
            params["endTime"] = str(int(datetime.strptime(end, "%Y-%m-%d").timestamp() * 1000))

        url = f"{_BASE_URL}/klines"
        data = send_request(url=url, headers=self._headers, method="GET", params=params)
        if not data:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

        df = pd.DataFrame(data, columns=_KLINE_COLUMNS)
        df["time"] = pd.to_datetime(df["open_time"], unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.loc[:, ["time", "open", "high", "low", "close", "volume"]]
        df = df.sort_values("time").reset_index(drop=True)
        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def intraday(self, symbol: str) -> pd.DataFrame:
        url = f"{_BASE_URL}/trades"
        params = {"symbol": symbol.upper(), "limit": "1000"}
        data = send_request(url=url, headers=self._headers, method="GET", params=params)
        if not data:
            return pd.DataFrame(columns=["time", "price", "volume"])

        df: pd.DataFrame = pd.DataFrame(data)
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df.rename(columns={"qty": "volume", "isBuyerMaker": "is_buyer_maker"}, inplace=True)
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        df = df.loc[:, ["time", "price", "volume", "is_buyer_maker"]]
        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def price_depth(self, symbol: str, limit: int = 20) -> pd.DataFrame:
        url = f"{_BASE_URL}/depth"
        params = {"symbol": symbol.upper(), "limit": str(limit)}
        data = send_request(url=url, headers=self._headers, method="GET", params=params)
        if not data:
            return pd.DataFrame(columns=["price", "volume", "side"])

        rows = []
        for price, qty in data.get("bids", []):
            rows.append({"price": float(price), "volume": float(qty), "side": "bid"})
        for price, qty in data.get("asks", []):
            rows.append({"price": float(price), "volume": float(qty), "side": "ask"})

        df = pd.DataFrame(rows)
        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df
