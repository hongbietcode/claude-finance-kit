"""VCI listing module: symbol lists, exchange info, and industry classifications."""

import json
import logging
from typing import Optional

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.transform import reorder_cols
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.vci.const import (
    _GRAPHQL_URL,
    _GROUP_CODE,
    _TRADING_URL,
)

logger = logging.getLogger(__name__)


def _camel_to_snake(name: str) -> str:
    import re
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _drop_cols_by_pattern(df: pd.DataFrame, patterns: list[str]) -> pd.DataFrame:
    cols_to_drop = [c for c in df.columns if any(c.startswith(p) or p in c for p in patterns)]
    return df.drop(columns=cols_to_drop, errors="ignore")


class VCIListing:
    """Fetches symbol lists, exchange info, and industry data from VCI."""

    DATA_SOURCE = "VCI"

    def __init__(self) -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)

    def all_symbols(self, exchange: Optional[str] = None) -> pd.DataFrame:
        df = self._symbols_by_exchange()
        df = df.query('type == "STOCK"').reset_index(drop=True)
        if exchange:
            df = df[df["exchange"].str.upper() == exchange.upper()].reset_index(drop=True)
        return df[["symbol", "organ_name"]]

    def symbols_by_group(self, group: str) -> pd.DataFrame:
        if group not in _GROUP_CODE:
            raise ValueError(f"Invalid group. Must be one of: {_GROUP_CODE}")

        url = f"{_TRADING_URL}price/symbols/getByGroup?group={group}"
        json_data = send_request(url=url, headers=self._headers, method="GET")

        if not json_data:
            raise ValueError(f"No data found for group '{group}'.")

        df = pd.DataFrame(json_data)
        df.attrs["source"] = self.DATA_SOURCE
        return df["symbol"]

    def symbols_by_industries(self) -> pd.DataFrame:
        payload = json.loads(
            '{"query":"{\\n  CompaniesListingInfo {\\n    ticker\\n    organName\\n    enOrganName\\n'
            '    icbName3\\n    enIcbName3\\n    icbName2\\n    enIcbName2\\n    icbName4\\n    enIcbName4\\n'
            '    comTypeCode\\n    icbCode1\\n    icbCode2\\n    icbCode3\\n    icbCode4\\n    __typename\\n'
            '  }\\n}\\n","variables":{}}'
        )

        json_data = send_request(
            url=_GRAPHQL_URL,
            headers=self._headers,
            method="POST",
            payload=payload,
        )

        if not json_data:
            raise ValueError("No industry data found.")

        df = pd.DataFrame(json_data["data"]["CompaniesListingInfo"])
        df.columns = [_camel_to_snake(col) for col in df.columns]
        df = df.drop(columns=["__typename"], errors="ignore")
        df = df.rename(columns={"ticker": "symbol"})
        df = _drop_cols_by_pattern(df, ["en_"])
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def _symbols_by_exchange(self) -> pd.DataFrame:
        url = f"{_TRADING_URL}price/symbols/getAll"
        json_data = send_request(url=url, headers=self._headers, method="GET")

        if not json_data:
            raise ValueError("No exchange data found.")

        df = pd.DataFrame(json_data)
        df.columns = [_camel_to_snake(col) for col in df.columns]
        df = df.rename(columns={"board": "exchange"})
        df = reorder_cols(df, ["symbol", "exchange", "type"], position="first")
        df = df.drop(columns=["id"], errors="ignore")
        df.attrs["source"] = self.DATA_SOURCE
        return df
