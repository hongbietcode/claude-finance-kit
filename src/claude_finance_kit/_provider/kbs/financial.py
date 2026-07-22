"""KBS financial statements normalized to the VCI period-row schema."""

import math
from typing import Any

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.parser import get_asset_type
from claude_finance_kit._internal.transform import normalize_field_name
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.kbs.const import _SAS_FINANCE_INFO_URL

_CANONICAL_FIELDS = {
    "assets": "total_assets",
    "short_term_assets": "current_assets",
    "long_term_assets": "non_current_assets",
    "liabilities": "total_liabilities",
    "short_term_liabilities": "current_liabilities",
    "non_current_liabilities": "long_term_liabilities",
    "owners_equity": "equity",
    "share_capital": "charter_capital",
    "undistributed_earnings_after_tax": "retained_earnings",
    "operating_income": "revenue",
    "net_revenue": "revenue",
    "net_profit_after_tax": "net_profit",
    "general_and_administrative_expenses": "admin_expenses",
    "financial_expenses": "finance_expenses",
    "net_cash_flows_from_operating_activities": "operating_cash_flow",
    "net_cash_flows_from_investing_activities": "investing_cash_flow",
    "net_cash_flows_from_financing_activities": "financing_cash_flow",
    "net_increase_decrease_in_cash_and_cash_equivalents": "net_change_in_cash",
    "cash_and_cash_equivalents_at_beginning_of_period": "beginning_cash",
    "cash_and_cash_equivalents_at_end_of_period": "ending_cash",
    "p_e": "pe",
    "p_b": "pb",
    "p_s": "ps",
    "gross_profit_margin": "gross_margin",
    "net_profit_margin": "net_margin",
    "debt_equity": "debt_to_equity",
    "liabilities_assets": "debt_to_assets",
}
_CANONICAL_FIELDS.update({field: field for field in set(_CANONICAL_FIELDS.values())})


def _validate_multiplier(unit_multiplier: float) -> float:
    if isinstance(unit_multiplier, bool) or not isinstance(unit_multiplier, (int, float)):
        raise TypeError("unit_multiplier must be a positive number.")
    if not math.isfinite(unit_multiplier) or unit_multiplier <= 0:
        raise ValueError("unit_multiplier must be a finite number greater than zero.")
    return float(unit_multiplier)


def _periods(heads: list[dict[str, Any]], period_type: str) -> list[tuple[int | None, str]]:
    periods: list[tuple[int | None, str]] = []
    seen: dict[tuple[int | None, str], int] = {}
    for head in heads:
        year_value = pd.to_numeric(head.get("YearPeriod"), errors="coerce")
        year = int(year_value) if pd.notna(year_value) else None
        if period_type == "quarter":
            term = str(head.get("TermCode") or head.get("TermNameEN") or head.get("TermName") or "")
            digits = "".join(character for character in term if character.isdigit())
            label = f"Q{digits}" if digits else term or "Q"
        else:
            label = "FY"

        key = (year, label)
        count = seen.get(key, 0) + 1
        seen[key] = count
        periods.append((year, label if count == 1 else f"{label}_{count}"))
    return periods


def _content_records(content: Any, report_type: str) -> list[dict[str, Any]]:
    if not isinstance(content, dict):
        return []
    groups = [(str(key).lower(), value) for key, value in content.items() if isinstance(value, list)]
    if report_type == "balance_sheet":
        matches = [value for key, value in groups if "cân đối" in key or "tình hình tài chính" in key]
    elif report_type == "income_statement":
        matches = [value for key, value in groups if "kết quả" in key]
    elif report_type == "cash_flow":
        matches = [value for key, value in groups if "gián tiếp" in key]
        matches = matches or [value for key, value in groups if "trực tiếp" in key or "lưu chuyển" in key]
    else:
        matches = [value for _, value in groups]
    selected = matches or [value for _, value in groups]
    return [record for group in selected for record in group if isinstance(record, dict)]


class KBSFinancial:
    """Fetch and normalize KBS financial reports."""

    DATA_SOURCE = "KBS"

    def __init__(self) -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)

    def _fetch(self, symbol: str, report_code: str, period_type: int) -> dict[str, Any]:
        if get_asset_type(symbol) != "stock":
            raise ValueError(f"'{symbol}' is not a stock symbol.")
        response = send_request(
            url=f"{_SAS_FINANCE_INFO_URL}/{symbol.upper()}",
            headers=self._headers,
            params={
                "page": 1,
                "pageSize": 8,
                "type": report_code,
                "unit": 1000,
                "termtype": period_type,
                **(
                    {"code": symbol.upper(), "termType": period_type}
                    if report_code == "LCTT"
                    else {"languageid": 1}
                ),
            },
        )
        return response if isinstance(response, dict) else {}

    def _process(
        self,
        symbol: str,
        report_code: str,
        report_type: str,
        period: str,
        unit_multiplier: float = 1.0,
    ) -> pd.DataFrame:
        if period not in {"year", "quarter"}:
            raise ValueError("period must be 'year' or 'quarter'.")
        multiplier = _validate_multiplier(unit_multiplier)
        response = self._fetch(symbol, report_code, 1 if period == "year" else 2)
        heads = [head for head in (response.get("Head") or []) if isinstance(head, dict)]
        periods = _periods(heads, period)
        records = _content_records(response.get("Content"), report_type)
        if not periods or not records:
            empty = pd.DataFrame(columns=["symbol", "year", "period"])
            empty.attrs.update(
                symbol=symbol.upper(), source=self.DATA_SOURCE, period_type=period, unit_multiplier=multiplier
            )
            return empty

        rows = [
            {"symbol": symbol.upper(), "year": year, "period": label}
            for year, label in periods
        ]
        used: set[str] = set()
        for record in records:
            normalized = normalize_field_name(record.get("NameEn") or record.get("Name"))
            if not normalized:
                continue
            canonical = _CANONICAL_FIELDS.get(normalized, normalized)
            if canonical in used and normalized not in _CANONICAL_FIELDS:
                suffix = record.get("ReportNormID") or record.get("ID")
                canonical = f"{canonical}__{suffix}" if suffix is not None else canonical
            used.add(canonical)
            for index, row in enumerate(rows, 1):
                value = pd.to_numeric(record.get(f"Value{index}"), errors="coerce")
                if canonical not in row or pd.isna(row[canonical]):
                    row[canonical] = value * multiplier if pd.notna(value) else pd.NA

        df = pd.DataFrame(rows)
        df["year"] = pd.array(df["year"], dtype="Int64")
        df.attrs.update(
            symbol=symbol.upper(), source=self.DATA_SOURCE, period_type=period, unit_multiplier=multiplier
        )
        return df

    def balance_sheet(
        self, symbol: str, period: str = "quarter", unit_multiplier: float = 1000.0
    ) -> pd.DataFrame:
        return self._process(symbol, "CDKT", "balance_sheet", period, unit_multiplier)

    def income_statement(
        self, symbol: str, period: str = "quarter", unit_multiplier: float = 1000.0
    ) -> pd.DataFrame:
        return self._process(symbol, "KQKD", "income_statement", period, unit_multiplier)

    def cash_flow(
        self, symbol: str, period: str = "quarter", unit_multiplier: float = 1000.0
    ) -> pd.DataFrame:
        return self._process(symbol, "LCTT", "cash_flow", period, unit_multiplier)

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._process(symbol, "CSTC", "ratio", period, unit_multiplier=1.0)
