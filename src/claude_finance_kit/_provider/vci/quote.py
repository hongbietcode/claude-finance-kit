"""VCI quote module: historical OHLCV and intraday tick data."""

import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.parser import get_asset_type
from claude_finance_kit._internal.transform import intraday_to_df, ohlc_to_df
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.vci.const import (
    _INDEX_MAPPING,
    _INTERVAL_MAP,
    _INTRADAY_DTYPE,
    _INTRADAY_MAP,
    _OHLC_DTYPE,
    _OHLC_MAP,
    _RESAMPLE_MAP,
    _TRADING_URL,
)

logger = logging.getLogger(__name__)


class VCIQuote:
    """Fetches OHLCV history and intraday ticks from VCI."""

    DATA_SOURCE = "VCI"

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

        if "INDEX" in symbol and symbol in _INDEX_MAPPING:
            symbol = _INDEX_MAPPING[symbol]

        interval_key = interval if interval in _INTERVAL_MAP else "1D"
        interval_value = _INTERVAL_MAP[interval_key]

        try:
            start_time = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            start_time = datetime.strptime(start, "%Y-%m-%d")

        if end is not None:
            try:
                end_time = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                end_time = datetime.strptime(end, "%Y-%m-%d") + pd.Timedelta(days=1)
        else:
            end_time = datetime.now() + pd.Timedelta(days=1)

        if start_time > end_time:
            raise ValueError("start date cannot be after end date.")

        end_stamp = int(end_time.timestamp())
        business_days = pd.bdate_range(start=start_time, end=end_time)

        if interval_value == "ONE_DAY":
            count_back = len(business_days) + 1
        elif interval_value == "ONE_HOUR":
            count_back = int(len(business_days) * 5 + 1)
        else:
            count_back = int(len(business_days) * 255 + 1)

        url = f"{_TRADING_URL}chart/OHLCChart/gap-chart"
        payload = {
            "timeFrame": interval_value,
            "symbols": [symbol],
            "to": end_stamp,
            "countBack": count_back,
        }

        json_data = send_request(
            url=url,
            headers=self._headers,
            method="POST",
            payload=payload,
        )

        if isinstance(json_data, dict) and "data" in json_data:
            json_data = json_data["data"]

        if isinstance(json_data, list) and len(json_data) > 0:
            symbol_data = json_data[0]
            if isinstance(symbol_data, dict) and "o" in symbol_data and isinstance(symbol_data["o"], list):
                json_data = pd.DataFrame({
                    "t": symbol_data["t"],
                    "o": symbol_data["o"],
                    "h": symbol_data["h"],
                    "l": symbol_data["l"],
                    "c": symbol_data["c"],
                    "v": symbol_data["v"],
                }).to_dict("records")

        if not json_data:
            return pd.DataFrame()

        return ohlc_to_df(
            data=json_data,
            column_map=_OHLC_MAP,
            dtype_map=_OHLC_DTYPE,
            symbol=symbol,
            asset_type=asset_type,
            source=self.DATA_SOURCE,
            interval=interval_key,
            resample_map=_RESAMPLE_MAP,
        )

    def intraday(self, symbol: str) -> pd.DataFrame:
        symbol = symbol.upper()
        asset_type = get_asset_type(symbol)

        if asset_type == "index":
            raise ValueError(f"Intraday data not supported for index '{symbol}'.")

        url = f"{_TRADING_URL}market-watch/LEData/getAll"
        payload = {
            "symbol": symbol,
            "limit": 100,
            "truncTime": None,
        }

        data = send_request(
            url=url,
            headers=self._headers,
            method="POST",
            payload=payload,
        )

        if isinstance(data, dict):
            data = data.get("data", []) if "data" in data else []

        return intraday_to_df(
            data=data,
            column_map=_INTRADAY_MAP,
            dtype_map=_INTRADAY_DTYPE,
            symbol=symbol,
            asset_type=asset_type,
            source=self.DATA_SOURCE,
        )
