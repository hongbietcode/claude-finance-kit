"""VCI financial module: balance sheet, income statement, cash flow, ratios."""

import json
import logging
import re

import pandas as pd

from ..._internal.http_client import send_request
from ..._internal.user_agent import get_headers
from .const import (
    _FINANCIAL_REPORT_PERIOD_MAP,
    _GRAPHQL_URL,
    _UNIT_MAP,
    SUPPORTED_LANGUAGES,
)

logger = logging.getLogger(__name__)

_RATIOS_QUERY = (
    '{"query":"fragment Ratios on CompanyFinancialRatio {\\n  ticker\\n  yearReport\\n  lengthReport\\n'
    "  updateDate\\n  revenue\\n  revenueGrowth\\n  netProfit\\n  netProfitGrowth\\n  ebitMargin\\n"
    "  roe\\n  roic\\n  roa\\n  pe\\n  pb\\n  eps\\n  currentRatio\\n  cashRatio\\n  quickRatio\\n"
    "  interestCoverage\\n  ae\\n  netProfitMargin\\n  grossMargin\\n  ev\\n  issueShare\\n  ps\\n"
    "  pcf\\n  bvps\\n  evPerEbitda\\n  at\\n  fat\\n  acp\\n  dso\\n  dpo\\n  ccc\\n  de\\n  le\\n"
    "  ebitda\\n  ebit\\n  dividend\\n  charterCapital\\n  epsTTM\\n  __typename\\n}\\n\\n"
    "query Query($ticker: String!, $period: String!) {\\n  CompanyFinancialRatio(ticker: $ticker, period: $period) {\\n"
    '    ratio {\\n      ...Ratios\\n      __typename\\n    }\\n    period\\n    __typename\\n  }\\n}\\n",'
    '"variables":{"ticker":"VCI","period":"Q"}}'
)

_RATIO_DICT_QUERY = (
    '{"query":"query Query {\\n  ListFinancialRatio {\\n    id\\n    type\\n    name\\n    unit\\n'
    "    isDefault\\n    fieldName\\n    en_Type\\n    en_Name\\n    tagName\\n    comTypeCode\\n"
    '    order\\n    __typename\\n  }\\n}\\n","variables":{}}'
)


def _camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class VCIFinancial:
    """Fetches financial statements and ratios from VCI GraphQL API."""

    DATA_SOURCE = "VCI"

    def __init__(self) -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)

    def _fetch_ratio_data(self, symbol: str, period: str) -> pd.DataFrame:
        payload = json.loads(_RATIOS_QUERY)
        payload["variables"]["ticker"] = symbol.upper()
        payload["variables"]["period"] = period

        response = send_request(
            url=_GRAPHQL_URL,
            headers=self._headers,
            method="POST",
            payload=payload,
        )

        selected = response["data"]["CompanyFinancialRatio"]["ratio"]
        return pd.DataFrame(selected)

    def _fetch_ratio_dict(self) -> pd.DataFrame:
        payload = json.loads(_RATIO_DICT_QUERY)
        response = send_request(
            url=_GRAPHQL_URL,
            headers=self._headers,
            method="POST",
            payload=payload,
        )

        data = response["data"]["ListFinancialRatio"]
        df = pd.DataFrame(data)
        df.columns = [_camel_to_snake(col).replace("__", "_") for col in df.columns]
        df["unit"] = df["unit"].map(_UNIT_MAP)
        return df[["field_name", "name", "en_name", "type", "order", "unit", "com_type_code"]]

    def _process_report(
        self,
        symbol: str,
        period: str,
        report_key: str,
        lang: str = "en",
    ) -> pd.DataFrame:
        if lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language '{lang}'. Use one of {SUPPORTED_LANGUAGES}.")

        period_code = _FINANCIAL_REPORT_PERIOD_MAP.get(period, "Q")
        ratio_df: pd.DataFrame = self._fetch_ratio_data(symbol, period_code)

        if ratio_df.empty:
            return pd.DataFrame()

        mapping_df = self._fetch_ratio_dict()
        target_col = "name" if lang == "vi" else "en_name"
        name_map = dict(zip(mapping_df["field_name"], mapping_df[target_col]))
        type_field_dict = mapping_df.groupby("type")["field_name"].apply(list).to_dict()

        if lang == "vi":
            index_cols = ["ticker", "yearReport", "lengthReport"]
        else:
            index_cols = ["ticker", "yearReport", "lengthReport"]

        orphan_cols = [c for c in ratio_df.columns if c not in mapping_df["field_name"].values and c not in index_cols]
        ratio_df: pd.DataFrame = ratio_df.drop(columns=orphan_cols, errors="ignore")

        fields = type_field_dict.get(report_key, [])
        if not fields:
            return pd.DataFrame()

        available_fields = [f for f in fields if f in ratio_df.columns]
        report_df = ratio_df[index_cols + available_fields].copy()  # pylint: disable=unsubscriptable-object
        report_df = report_df.rename(columns=name_map)
        report_df = report_df.rename(
            columns={
                "ticker": "symbol",
                "yearReport": "year",
                "lengthReport": "period",
            }
        )
        return report_df

    def balance_sheet(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._process_report(symbol, period, "Chỉ tiêu cân đối kế toán")

    def income_statement(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._process_report(symbol, period, "Chỉ tiêu kết quả kinh doanh")

    def cash_flow(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._process_report(symbol, period, "Chỉ tiêu lưu chuyển tiền tệ")

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        period_code = _FINANCIAL_REPORT_PERIOD_MAP.get(period, "Q")
        ratio_df: pd.DataFrame = self._fetch_ratio_data(symbol, period_code)

        if ratio_df.empty:
            return pd.DataFrame()

        mapping_df = self._fetch_ratio_dict()
        other_types = [
            t
            for t in mapping_df["type"].unique()
            if t
            not in (
                "Chỉ tiêu cân đối kế toán",
                "Chỉ tiêu lưu chuyển tiền tệ",
                "Chỉ tiêu kết quả kinh doanh",
            )
        ]

        index_cols = ["ticker", "yearReport", "lengthReport"]
        result_frames = []
        for rtype in other_types:
            fields = mapping_df[mapping_df["type"] == rtype]["field_name"].tolist()
            available = [f for f in fields if f in ratio_df.columns]
            if available:
                result_frames.append(ratio_df[available])

        if not result_frames:
            return pd.DataFrame()

        merged = pd.concat(result_frames, axis=1)
        name_map = dict(zip(mapping_df["field_name"], mapping_df["en_name"]))
        merged = merged.rename(columns=name_map)

        index_part = ratio_df[index_cols].rename(
            columns={
                "ticker": "symbol",
                "yearReport": "year",
                "lengthReport": "period",
            }
        )
        return pd.concat([index_part, merged], axis=1)
