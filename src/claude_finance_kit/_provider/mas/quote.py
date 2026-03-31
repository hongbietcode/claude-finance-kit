"""MAS quote module: historical OHLCV, intraday, and price depth."""

import logging
from datetime import datetime

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.parser import get_asset_type
from claude_finance_kit._internal.transform import intraday_to_df, ohlc_to_df
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.mas.const import (
    _CHART_URL,
    _INDEX_MAPPING,
    _INTRADAY_DTYPE,
    _INTRADAY_MAP,
    _INTERVAL_MAP,
    _OHLC_DTYPE,
    _OHLC_MAP,
    _PRICE_DEPTH_MAP,
    _RESAMPLE_MAP,
)

logger = logging.getLogger(__name__)


class MASQuote:
    """Fetches OHLCV, intraday, and price depth data from MAS."""

    DATA_SOURCE = "MAS"

    def __init__(self) -> None:
        self._headers = get_headers(data_source="MAS", random_agent=True)

    def _resolve_symbol(self, symbol: str) -> tuple[str, str]:
        symbol = symbol.upper()
        asset_type = get_asset_type(symbol)
        if "INDEX" in symbol:
            if symbol not in _INDEX_MAPPING:
                raise ValueError(
                    f"Index '{symbol}' not supported. "
                    f"Valid: {list(_INDEX_MAPPING.keys())}"
                )
            symbol = _INDEX_MAPPING[symbol]
        return symbol, asset_type

    def history(
        self,
        symbol: str,
        start: str,
        end: str | None = None,
        interval: str = "1D",
    ) -> pd.DataFrame:
        if interval not in _INTERVAL_MAP:
            raise ValueError(
                f"Unsupported interval '{interval}'. "
                f"Use: {list(_INTERVAL_MAP.keys())}"
            )

        resolved, asset_type = self._resolve_symbol(symbol)

        start_ts = int(datetime.strptime(start, "%Y-%m-%d").timestamp())
        if end:
            end_dt = datetime.strptime(end, "%Y-%m-%d")
            end_ts = int((end_dt + pd.Timedelta(days=1)).timestamp())
        else:
            end_ts = int((datetime.now() + pd.Timedelta(days=1)).timestamp())

        url = f"{_CHART_URL}tradingview/history"
        params = {
            "symbol": resolved,
            "resolution": _INTERVAL_MAP[interval],
            "from": str(start_ts),
            "to": str(end_ts),
        }

        json_data = send_request(
            url=url, headers=self._headers, method="GET", params=params,
        )
        if not json_data:
            return pd.DataFrame(columns=list(_OHLC_MAP.values()))

        df = ohlc_to_df(
            data=json_data,
            column_map=_OHLC_MAP,
            dtype_map=_OHLC_DTYPE,
            asset_type=asset_type,
            symbol=symbol.upper(),
            source=self.DATA_SOURCE,
            interval=interval,
            resample_map=_RESAMPLE_MAP,
        )
        return df

    def intraday(self, symbol: str) -> pd.DataFrame:
        resolved, asset_type = self._resolve_symbol(symbol)
        if asset_type == "index":
            raise ValueError(f"Intraday not supported for index '{symbol}'.")

        url = f"{_CHART_URL}market/{resolved}/quote"
        params = {"symbol": resolved, "fetchCount": "5000"}

        json_data = send_request(
            url=url, headers=self._headers, method="GET", params=params,
        )
        if not json_data or "data" not in json_data:
            return pd.DataFrame(columns=["time", "price", "volume", "match_type"])

        df = intraday_to_df(
            data=json_data["data"],
            column_map=_INTRADAY_MAP,
            dtype_map=_INTRADAY_DTYPE,
            symbol=symbol.upper(),
            asset_type=asset_type,
            source=self.DATA_SOURCE,
        )
        return df.loc[:, ["time", "price", "volume", "match_type"]]

    def price_depth(self, symbol: str) -> pd.DataFrame:
        resolved, _ = self._resolve_symbol(symbol)
        url = f"{_CHART_URL}market/quoteSummary"
        params = {"symbol": resolved}

        json_data = send_request(
            url=url, headers=self._headers, method="GET", params=params,
        )
        if not json_data:
            return pd.DataFrame(columns=list(_PRICE_DEPTH_MAP.values()))

        df = pd.DataFrame(json_data)
        keep = [c for c in _PRICE_DEPTH_MAP if c in df.columns]
        df = df.loc[:, keep].rename(columns=_PRICE_DEPTH_MAP)
        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df
