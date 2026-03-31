"""KBS financial module: balance sheet, income statement, cash flow, ratios."""

import logging
from typing import Any, Dict, List

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.parser import get_asset_type
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.kbs.const import _SAS_FINANCE_INFO_URL

logger = logging.getLogger(__name__)


def _parse_periods(head_list: List[Dict]) -> List[str]:
    """Extract period labels from Head list in KBS financial response."""
    periods = []
    for head in head_list:
        if not isinstance(head, dict):
            continue
        year = head.get("YearPeriod", "")
        term_name = head.get("TermName", "")
        if term_name and "Quý" in term_name:
            quarter_num = term_name.replace("Quý", "").strip()
            periods.append(f"{year}-Q{quarter_num}")
        else:
            periods.append(str(year))
    return periods


def _build_df_from_records(
    records: List[Dict],
    periods: List[str],
) -> pd.DataFrame:
    """Build a structured DataFrame from KBS financial records."""
    rows = []
    for record in records:
        row: Dict[str, Any] = {
            "item": record.get("Name", ""),
            "item_en": record.get("NameEn", ""),
            "unit": record.get("Unit", ""),
        }
        for i, period_label in enumerate(periods, 1):
            value = record.get(f"Value{i}")
            if value is not None:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    pass
            row[period_label] = value
        rows.append(row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df.attrs["periods"] = periods
    return df


class KBSFinancial:
    """Fetches financial statements and ratios from KBS SAS API."""

    DATA_SOURCE = "KBS"

    def __init__(self) -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)

    def _fetch(self, symbol: str, report_type: str, period_type: int) -> Dict:
        if get_asset_type(symbol) != "stock":
            raise ValueError(f"'{symbol}' is not a stock symbol.")

        url = f"{_SAS_FINANCE_INFO_URL}/{symbol.upper()}"
        params: Dict[str, Any] = {
            "page": 1,
            "pageSize": 8,
            "type": report_type,
            "unit": 1000,
            "termtype": period_type,
        }
        if report_type != "LCTT":
            params["languageid"] = 1

        return send_request(url=url, headers=self._headers, method="GET", params=params)

    def _process(
        self,
        symbol: str,
        report_type: str,
        period: str,
        content_keys: List[str],
    ) -> pd.DataFrame:
        period_type = 1 if period == "year" else 2
        response = self._fetch(symbol, report_type, period_type)

        if not response:
            raise ValueError(f"No financial data for '{symbol}' ({report_type}).")

        head_list = response.get("Head", [])
        periods = _parse_periods(head_list)
        content = response.get("Content", {})

        records: List[Dict] = []
        for key in content_keys:
            records.extend(content.get(key, []))

        if not records:
            return pd.DataFrame()

        df = _build_df_from_records(records, periods)
        df.attrs.update(symbol=symbol.upper(), source=self.DATA_SOURCE, period=period)
        return df

    def balance_sheet(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._process(symbol, "CDKT", period, ["Cân đối kế toán"])

    def income_statement(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._process(symbol, "KQKD", period, ["Kết quả kinh doanh"])

    def cash_flow(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        period_type = 1 if period == "year" else 2
        response = self._fetch(symbol, "LCTT", period_type)

        if not response:
            raise ValueError(f"No cash flow data for '{symbol}'.")

        head_list = response.get("Head", [])
        periods = _parse_periods(head_list)
        content = response.get("Content", {})

        cash_flow_key = None
        if "Lưu chuyển tiền tệ gián tiếp" in content:
            cash_flow_key = "Lưu chuyển tiền tệ gián tiếp"
        elif "Lưu chuyển tiền tệ trực tiếp" in content:
            cash_flow_key = "Lưu chuyển tiền tệ trực tiếp"

        if not cash_flow_key:
            return pd.DataFrame()

        records = content.get(cash_flow_key, [])
        df = _build_df_from_records(records, periods)
        df.attrs.update(symbol=symbol.upper(), source=self.DATA_SOURCE, period=period)
        return df

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        period_type = 1 if period == "year" else 2
        response = self._fetch(symbol, "CSTC", period_type)

        if not response:
            raise ValueError(f"No ratio data for '{symbol}'.")

        head_list = response.get("Head", [])
        periods = _parse_periods(head_list)
        content = response.get("Content", {})

        ratio_groups = [
            "Nhóm chỉ số Định giá",
            "Nhóm chỉ số Sinh lợi",
            "Nhóm chỉ số Tăng trưởng",
            "Nhóm chỉ số Thanh khoản",
            "Nhóm chỉ số Chất lượng tài sản",
        ]

        records: List[Dict] = []
        for group in ratio_groups:
            records.extend(content.get(group, []))

        if not records:
            return pd.DataFrame()

        df = _build_df_from_records(records, periods)
        df.attrs.update(symbol=symbol.upper(), source=self.DATA_SOURCE, period=period)
        return df
