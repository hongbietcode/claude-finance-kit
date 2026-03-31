"""FMP company module: overview and officers."""

import logging
import re

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.fmp.const import _FMP_DOMAIN, get_api_key

logger = logging.getLogger(__name__)


def _camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class FMPCompany:
    """Fetches company profile and officers from FMP."""

    DATA_SOURCE = "FMP"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = get_api_key(api_key)
        self._headers = get_headers(data_source="MSN", random_agent=True)

    def _fetch(self, endpoint: str, symbol: str) -> list:
        url = f"{_FMP_DOMAIN}{endpoint}?symbol={symbol}&apikey={self._api_key}"
        data = send_request(url=url, headers=self._headers, method="GET")
        if isinstance(data, list):
            return data
        return [data] if data else []

    def company_overview(self, symbol: str) -> pd.DataFrame:
        records = self._fetch("/profile", symbol)
        if not records:
            raise ValueError(f"No company data found for '{symbol}'.")

        df = pd.DataFrame(records)
        df.columns = [_camel_to_snake(col) for col in df.columns]
        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def officers(self, symbol: str) -> pd.DataFrame:
        records = self._fetch("/key-executives", symbol)
        if not records:
            return pd.DataFrame(columns=["name", "title", "year_born"])

        df = pd.DataFrame(records)
        df.columns = [_camel_to_snake(col) for col in df.columns]
        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df
