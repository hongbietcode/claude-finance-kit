"""MAS financial module: balance sheet, income statement, cash flow, ratios."""

import logging
import re

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.transform import reorder_cols
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.mas.const import (
    _FINANCIAL_QUERY_TEMPLATE,
    _FINANCIAL_REPORT_MAP,
    _FINANCIAL_REPORT_PERIOD_MAP,
    _FINANCIAL_URL,
)

logger = logging.getLogger(__name__)


def _camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _flatten_content(content, lang: str = "vi") -> dict:
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and "Values" in item:
                result = {}
                for entry in item["Values"]:
                    if isinstance(entry, dict):
                        key = (
                            entry.get("NameEn", "").strip()
                            if lang == "en"
                            else entry.get("Name", "").strip()
                        )
                        if key:
                            result[key] = entry.get("Value")
                return result
    return {}


class MASFinancial:
    """Fetches financial statements and ratios from MAS GraphQL API."""

    DATA_SOURCE = "MAS"

    def __init__(self) -> None:
        self._headers = get_headers(data_source="MAS")

    def _fetch_report(
        self, report_type: str, symbol: str, period: str, lang: str = "vi",
    ) -> pd.DataFrame:
        if period not in _FINANCIAL_REPORT_PERIOD_MAP:
            raise ValueError(f"Invalid period '{period}'. Use 'year' or 'quarter'.")

        mas_type = _FINANCIAL_REPORT_MAP[report_type]
        mas_period = _FINANCIAL_REPORT_PERIOD_MAP[period]

        query = (
            _FINANCIAL_QUERY_TEMPLATE
            .replace("TARGET_SYMBOL", symbol.upper())
            .replace("TARGET_TYPE", mas_type)
            .replace("TARGET_PERIOD", mas_period)
        )

        url = f"{_FINANCIAL_URL}financialReport"
        json_data = send_request(
            url=url, headers=self._headers, method="GET",
            params={"query": query},
        )
        if not json_data:
            return pd.DataFrame()

        df = pd.DataFrame(json_data)
        if df.empty:
            return df

        df.columns = [_camel_to_snake(c) for c in df.columns]

        expanded = df["content"].apply(lambda c: _flatten_content(c, lang))
        content_df = pd.DataFrame(expanded.tolist())
        df = pd.concat(
            [df.drop("content", axis=1, errors="ignore"), content_df], axis=1,
        )

        if period == "year":
            df["period"] = df.get("year_period")
        else:
            if "year_period" in df.columns and "term_code" in df.columns:
                df["period"] = df["year_period"].astype(str) + "-" + df["term_code"].astype(str)
            df = df.drop(columns=["year_period"], errors="ignore")

        df = df.drop(columns=["_id", "id", "term_code"], errors="ignore")
        df = reorder_cols(df, ["period"], position="first")
        df = df.dropna(axis=1, how="all")

        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def income_statement(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._fetch_report("income_statement", symbol, period)

    def balance_sheet(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._fetch_report("balance_sheet", symbol, period)

    def cash_flow(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._fetch_report("cash_flow", symbol, period)

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._fetch_report("ratio", symbol, period)
