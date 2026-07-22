"""MSN Finance symbol lookup and SecId resolution."""

import json
import re
from typing import Any

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.msn.const import (
    _MSN_ALLOWED_HOSTS,
    _SEARCH_URL,
    _STATIC_SEC_IDS,
    _SYMBOL_MAP,
)


class MSNListing:
    """Resolve display tickers to MSN internal SecId values."""

    DATA_SOURCE = "MSN"

    def __init__(self) -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)

    def search_symbol(self, query: str, locale: str | None = None, limit: int = 10) -> pd.DataFrame:
        response = send_request(
            url=_SEARCH_URL,
            headers=self._headers,
            params={"query": query, "market": locale, "count": limit},
            allowed_hosts=_MSN_ALLOWED_HOSTS,
        )
        data = response.get("data") if isinstance(response, dict) else None
        stocks = data.get("stocks", []) if isinstance(data, dict) else []
        if not isinstance(stocks, list):
            stocks = []
        rows: list[dict[str, Any]] = []
        for item in stocks:
            if isinstance(item, str):
                try:
                    item = json.loads(item)
                except json.JSONDecodeError:
                    continue
            if isinstance(item, dict):
                rows.append(item)

        df = pd.DataFrame(rows)
        available = [column for column in _SYMBOL_MAP if column in df.columns]
        df = df[available].rename(columns=_SYMBOL_MAP) if available else pd.DataFrame(columns=_SYMBOL_MAP.values())
        if locale and "locale" in df.columns:
            df = df[df["locale"].astype(str).str.lower() == locale.lower()]
        df.attrs["source"] = self.DATA_SOURCE
        return df.reset_index(drop=True)

    def resolve_symbol_id(self, symbol: str, locale: str = "vi-vn") -> str:
        """Resolve a ticker only when MSN returns an exact symbol match."""
        requested = symbol.strip()
        key = requested.upper()
        if key in _STATIC_SEC_IDS:
            return _STATIC_SEC_IDS[key]
        if re.fullmatch(r"[a-z0-9]{6}", requested):
            return requested.lower()

        matches = self.search_symbol(key, locale=locale)
        if matches.empty or "symbol" not in matches.columns or "symbol_id" not in matches.columns:
            raise ValueError(f"MSN could not resolve an internal SecId for '{symbol}'.")

        exact = matches[matches["symbol"].astype(str).str.upper() == key]
        exact = exact[exact["symbol_id"].notna()]
        if exact.empty:
            raise ValueError(f"MSN returned no exact SecId match for '{symbol}'.")
        return str(exact.iloc[0]["symbol_id"]).lower()
