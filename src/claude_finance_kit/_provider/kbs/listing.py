"""KBS listing module: symbol lists and industry classifications."""

import logging
from typing import Dict, List, Optional

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.kbs.const import (
    _GROUP_CODE,
    _INDEX_URL,
    _SEARCH_URL,
    _SECTOR_ALL_URL,
    _SECTOR_STOCK_URL,
)

logger = logging.getLogger(__name__)


class KBSListing:
    """Fetches symbol lists and industry data from KBS."""

    DATA_SOURCE = "KBS"

    def __init__(self) -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)

    def all_symbols(self, exchange: Optional[str] = None) -> pd.DataFrame:
        stocks = self._get_full_stock_data()
        if not stocks:
            return pd.DataFrame(columns=["symbol", "organ_name"])

        df = pd.DataFrame(stocks)
        df = df[df.get("type", pd.Series(dtype=str)) == "stock"] if "type" in df.columns else df
        if "name" in df.columns:
            df = df.rename(columns={"name": "organ_name"})
        if exchange and "exchange" in df.columns:
            df = df[df["exchange"].str.upper() == exchange.upper()]
        df = df[["symbol", "organ_name"]].reset_index(drop=True)
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def symbols_by_group(self, group: str) -> pd.DataFrame:
        if group not in _GROUP_CODE:
            raise ValueError(
                f"Invalid group '{group}'. Valid groups: {list(_GROUP_CODE.keys())}"
            )

        symbols = self._get_symbols_by_group_internal(group)
        series = pd.Series(symbols, name="symbol")
        series.attrs["source"] = self.DATA_SOURCE
        return series

    def symbols_by_industries(self) -> pd.DataFrame:
        industries = self._get_industries_internal()
        rows: List[Dict] = []

        for ind in industries:
            code = ind.get("code")
            name = ind.get("name", "")
            try:
                syms = self._get_symbols_by_industry_internal(code)
                for sym in syms:
                    rows.append({"symbol": sym, "industry_code": code, "industry_name": name})
            except Exception:
                pass

        if rows:
            df = pd.DataFrame(rows)
        else:
            df = pd.DataFrame(columns=["symbol", "industry_code", "industry_name"])

        df.attrs["source"] = self.DATA_SOURCE
        return df

    def _get_full_stock_data(self) -> List[Dict]:
        try:
            json_data = send_request(
                url=_SEARCH_URL,
                headers=self._headers,
                method="GET",
            )
            if not json_data:
                return []
            if isinstance(json_data, list):
                return json_data
            if isinstance(json_data, dict) and "data" in json_data:
                return json_data["data"]
        except Exception as exc:
            logger.error("Failed to fetch stock data: %s", exc)
        return []

    def _get_symbols_by_group_internal(self, group: str) -> List[str]:
        group_code = _GROUP_CODE.get(group, group)
        url = f"{_INDEX_URL}/{group_code}/stocks"

        json_data = send_request(url=url, headers=self._headers, method="GET")
        if not json_data:
            raise ValueError(f"No data found for group '{group}'.")

        if isinstance(json_data, dict) and "data" in json_data:
            return json_data["data"]
        if isinstance(json_data, list):
            return json_data
        return []

    def _get_industries_internal(self) -> List[Dict]:
        try:
            json_data = send_request(
                url=_SECTOR_ALL_URL,
                headers=self._headers,
                method="GET",
            )
            if not json_data:
                return []
            if isinstance(json_data, list):
                return json_data
            if isinstance(json_data, dict) and "data" in json_data:
                return json_data["data"]
        except Exception as exc:
            logger.error("Failed to fetch industries: %s", exc)
        return []

    def _get_symbols_by_industry_internal(self, industry_code: int) -> List[str]:
        url = f"{_SECTOR_STOCK_URL}?code={industry_code}&l=1"
        try:
            json_data = send_request(url=url, headers=self._headers, method="GET")
            if not json_data:
                return []
            if isinstance(json_data, dict) and "stocks" in json_data:
                return [s["sb"] for s in json_data["stocks"] if "sb" in s]
            if isinstance(json_data, dict) and "data" in json_data:
                return json_data["data"]
            if isinstance(json_data, list):
                return json_data
        except Exception:
            pass
        return []
