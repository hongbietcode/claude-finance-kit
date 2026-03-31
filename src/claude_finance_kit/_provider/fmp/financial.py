"""FMP financial module: income statement, balance sheet, cash flow, ratios."""

import logging
import re

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.fmp.const import _FMP_DOMAIN, _PERIOD_MAP, get_api_key

logger = logging.getLogger(__name__)


def _camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class FMPFinancial:
    """Fetches financial statements and ratios from FMP."""

    DATA_SOURCE = "FMP"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = get_api_key(api_key)
        self._headers = get_headers(data_source="MSN", random_agent=True)

    def _fetch_statement(self, endpoint: str, symbol: str, period: str) -> pd.DataFrame:
        fmp_period = _PERIOD_MAP.get(period, period)
        url = (
            f"{_FMP_DOMAIN}{endpoint}"
            f"?symbol={symbol}&period={fmp_period}&apikey={self._api_key}"
        )
        data = send_request(url=url, headers=self._headers, method="GET")
        if not data:
            return pd.DataFrame()

        records = data if isinstance(data, list) else [data]
        df = pd.DataFrame(records)
        df.columns = [_camel_to_snake(col) for col in df.columns]
        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def income_statement(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._fetch_statement("/income-statement", symbol, period)

    def balance_sheet(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._fetch_statement("/balance-sheet-statement", symbol, period)

    def cash_flow(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._fetch_statement("/cash-flow-statement", symbol, period)

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._fetch_statement("/ratios", symbol, period)
