"""KBS company module: overview, shareholders, officers, news, and events."""

import logging
import re
from typing import Any, Dict

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.parser import get_asset_type
from claude_finance_kit._internal.transform import clean_html_dict
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.kbs.const import (
    _COMPANY_PROFILE_MAP,
    _EXCHANGE_CODE_MAP,
    _SHAREHOLDERS_MAP,
    _STOCK_INFO_URL,
)

logger = logging.getLogger(__name__)

_LEADERS_MAP = {
    "FD": "from_date",
    "PN": "position_name",
    "NM": "name",
    "PE": "position_en",
    "PI": "position_id",
}


def _camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class KBSCompany:
    """Fetches company profile, shareholders, officers, news, and events from KBS."""

    DATA_SOURCE = "KBS"

    def __init__(self) -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)
        self._cache: Dict[str, Any] = {}

    def _load(self, symbol: str) -> Dict[str, Any]:
        symbol = symbol.upper()
        if symbol in self._cache:
            return self._cache[symbol]

        if get_asset_type(symbol) != "stock":
            raise ValueError(f"'{symbol}' is not a stock symbol.")

        url = f"{_STOCK_INFO_URL}/profile/{symbol}"
        json_data = send_request(
            url=url,
            headers=self._headers,
            method="GET",
            params={"l": 1},
        )
        self._cache[symbol] = json_data or {}
        return self._cache[symbol]

    def company_overview(self, symbol: str) -> pd.DataFrame:
        raw = self._load(symbol)
        if not raw:
            raise ValueError(f"No profile data found for '{symbol}'.")

        profile: Dict[str, Any] = {}
        for api_key, schema_key in _COMPANY_PROFILE_MAP.items():
            if api_key in raw:
                profile[schema_key] = raw[api_key]

        profile = clean_html_dict(profile)

        if "exchange" in profile and pd.notna(profile["exchange"]):
            profile["exchange"] = _EXCHANGE_CODE_MAP.get(profile["exchange"], profile["exchange"])

        df = pd.DataFrame([profile])
        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def shareholders(self, symbol: str) -> pd.DataFrame:
        raw = self._load(symbol)
        holders = raw.get("Shareholders", [])

        if not holders:
            return pd.DataFrame(columns=["name", "shares_owned", "ownership_percentage", "update_date"])

        df = pd.DataFrame(holders)
        df = df.rename(columns=_SHAREHOLDERS_MAP)

        for col in ["update_date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def officers(self, symbol: str) -> pd.DataFrame:
        """Fetch company officers/leaders from KBS profile data.

        Args:
            symbol: Stock ticker.

        Returns:
            pd.DataFrame with officer information.
        """
        raw = self._load(symbol)
        leaders = raw.get("Leaders", [])

        if not leaders:
            return pd.DataFrame(columns=["name", "position_name", "from_date"])

        df = pd.DataFrame(leaders)
        df = df.rename(columns=_LEADERS_MAP)

        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def company_news(self, symbol: str, limit: int = 10, page: int = 1) -> pd.DataFrame:
        """Fetch company-related news from KBS.

        Args:
            symbol: Stock ticker.
            limit: Number of news items per page. Default 10.
            page: Page number. Default 1.

        Returns:
            pd.DataFrame with news items.
        """
        symbol = symbol.upper()
        url = f"{_STOCK_INFO_URL}/news/{symbol}"
        params = {"l": 1, "p": page, "s": limit}

        json_data = send_request(
            url=url,
            headers=self._headers,
            method="GET",
            params=params,
        )

        if not json_data:
            return pd.DataFrame(columns=["title", "public_date"])

        df = pd.DataFrame(json_data)
        df.columns = [_camel_to_snake(col) for col in df.columns]
        df.attrs["symbol"] = symbol
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def company_events(self, symbol: str, limit: int = 10, page: int = 1) -> pd.DataFrame:
        """Fetch company corporate events from KBS.

        Args:
            symbol: Stock ticker.
            limit: Number of events per page. Default 10.
            page: Page number. Default 1.

        Returns:
            pd.DataFrame with corporate events.
        """
        symbol = symbol.upper()
        url = f"{_STOCK_INFO_URL}/event/{symbol}"
        params = {"l": 1, "p": page, "s": limit}

        json_data = send_request(
            url=url,
            headers=self._headers,
            method="GET",
            params=params,
        )

        if not json_data:
            return pd.DataFrame(columns=["event_title", "public_date"])

        df = pd.DataFrame(json_data)
        df.columns = [_camel_to_snake(col) for col in df.columns]
        df.attrs["symbol"] = symbol
        df.attrs["source"] = self.DATA_SOURCE
        return df
