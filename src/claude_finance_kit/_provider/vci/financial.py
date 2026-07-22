"""VCI financial statements and ratios backed by Vietcap REST services."""

import math
from typing import Any

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.parser import get_asset_type
from claude_finance_kit._internal.transform import camel_to_snake, normalize_field_name
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._internal.validation import validate_symbol
from claude_finance_kit._provider.vci.const import (
    _FINANCIAL_SECTIONS,
    _VCI_ALLOWED_HOSTS,
    _VCI_COMPANY_URL,
)


def _validate_period(period: str) -> str:
    if period not in {"year", "quarter"}:
        raise ValueError("period must be 'year' or 'quarter'.")
    return period


def _validate_multiplier(unit_multiplier: float) -> float:
    if isinstance(unit_multiplier, bool) or not isinstance(unit_multiplier, (int, float)):
        raise TypeError("unit_multiplier must be a positive number.")
    if not math.isfinite(unit_multiplier) or unit_multiplier <= 0:
        raise ValueError("unit_multiplier must be a finite number greater than zero.")
    return float(unit_multiplier)


def _numeric_series(df: pd.DataFrame, *columns: str) -> pd.Series:
    """Return the first available numeric column or an aligned NaN series."""
    for column in columns:
        if column in df.columns:
            return pd.to_numeric(df[column], errors="coerce")
    return pd.Series(float("nan"), index=df.index, dtype="float64")


def _validate_stock_symbol(symbol: str) -> str:
    normalized = validate_symbol(symbol)
    if get_asset_type(normalized) != "stock":
        raise ValueError(f"VCI financial data requires a stock symbol, got '{normalized}'.")
    return normalized


class VCIFinancial:
    """Fetch normalized financial data from Vietcap REST APIs."""

    DATA_SOURCE = "VCI"

    def __init__(self) -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)
        self._metric_maps: dict[str, dict[str, dict[str, str]]] = {}

    def _request(self, url: str, params: dict[str, Any] | None = None) -> Any:
        return send_request(
            url=url,
            headers=self._headers,
            method="GET",
            params=params,
            allowed_hosts=_VCI_ALLOWED_HOSTS,
        )

    def _data(self, url: str, params: dict[str, Any] | None = None) -> Any:
        response = self._request(url, params)
        if not isinstance(response, dict) or "data" not in response:
            raise ValueError("VCI financial response does not contain data.")
        return response["data"]

    def _load_metric_maps(self, symbol: str) -> dict[str, dict[str, str]]:
        symbol_key = _validate_stock_symbol(symbol)
        if symbol_key in self._metric_maps:
            return self._metric_maps[symbol_key]

        data = self._data(f"{_VCI_COMPANY_URL}/{symbol_key}/financial-statement/metrics")
        if not isinstance(data, dict):
            raise ValueError(f"VCI financial metadata is unavailable for '{symbol}'.")

        maps: dict[str, dict[str, str]] = {}
        for section, records in data.items():
            used: set[str] = set()
            field_map: dict[str, str] = {}
            for record in records if isinstance(records, list) else []:
                if not isinstance(record, dict) or not record.get("field"):
                    continue
                field = str(record["field"])
                name = normalize_field_name(record.get("titleEn")) or field.lower()
                if name in used:
                    name = f"{name}__{field.lower()}"
                used.add(name)
                field_map[field] = name
            maps[section] = field_map

        self._metric_maps[symbol_key] = maps
        return maps

    def _statement(
        self,
        symbol: str,
        report_type: str,
        period: str,
        unit_multiplier: float,
    ) -> pd.DataFrame:
        symbol = _validate_stock_symbol(symbol)
        period = _validate_period(period)
        multiplier = _validate_multiplier(unit_multiplier)
        section = _FINANCIAL_SECTIONS[report_type]
        data = self._data(
            f"{_VCI_COMPANY_URL}/{symbol}/financial-statement",
            {"section": section},
        )
        raw_records = (
            data.get("years" if period == "year" else "quarters") or []
            if isinstance(data, dict)
            else []
        )
        records = [record for record in raw_records if isinstance(record, dict)]
        if not records:
            empty = pd.DataFrame(columns=["symbol", "year", "period"])
            empty.attrs.update(
                symbol=symbol, source=self.DATA_SOURCE, period_type=period, unit_multiplier=multiplier
            )
            return empty

        df = pd.DataFrame(records)
        df.columns = [camel_to_snake(column) for column in df.columns]
        field_map = self._load_metric_maps(symbol).get(section, {})
        if not field_map:
            raise ValueError(f"VCI financial metadata has no '{section}' section for '{symbol}'.")
        snake_map = {camel_to_snake(field): name for field, name in field_map.items()}
        metric_source_columns = [column for column in df.columns if column in snake_map]
        if not metric_source_columns:
            raise ValueError(f"VCI '{section}' records have no fields present in financial metadata.")
        df = df.rename(columns=snake_map)
        metric_columns = [snake_map[column] for column in metric_source_columns]

        result = pd.DataFrame(index=df.index)
        if "ticker" in df.columns:
            symbol_values = df["ticker"]
        elif "organ_code" in df.columns:
            symbol_values = df["organ_code"]
        else:
            symbol_values = pd.Series(symbol, index=df.index)
        result["symbol"] = symbol_values.fillna(symbol)
        result["year"] = _numeric_series(df, "year_report", "year").astype("Int64")
        if period == "quarter":
            quarter = _numeric_series(df, "length_report", "quarter").astype("Int64")
            result["period"] = quarter.map(lambda value: f"Q{value}" if pd.notna(value) else pd.NA)
        else:
            result["period"] = "FY"

        metric_frame = pd.DataFrame(
            {
                column: pd.to_numeric(df[column], errors="coerce") * multiplier
                for column in metric_columns
            },
            index=df.index,
        )
        result = pd.concat([result, metric_frame], axis=1)

        result.attrs.update(
            symbol=symbol, source=self.DATA_SOURCE, period_type=period, unit_multiplier=multiplier
        )
        return result.reset_index(drop=True)

    def balance_sheet(
        self, symbol: str, period: str = "quarter", unit_multiplier: float = 1.0
    ) -> pd.DataFrame:
        return self._statement(symbol, "balance_sheet", period, unit_multiplier)

    def income_statement(
        self, symbol: str, period: str = "quarter", unit_multiplier: float = 1.0
    ) -> pd.DataFrame:
        return self._statement(symbol, "income_statement", period, unit_multiplier)

    def cash_flow(
        self, symbol: str, period: str = "quarter", unit_multiplier: float = 1.0
    ) -> pd.DataFrame:
        return self._statement(symbol, "cash_flow", period, unit_multiplier)

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        symbol = _validate_stock_symbol(symbol)
        period = _validate_period(period)
        data = self._data(f"{_VCI_COMPANY_URL}/{symbol}/statistics-financial")
        records = [record for record in data if isinstance(record, dict)] if isinstance(data, list) else []
        df = pd.DataFrame(records)
        if df.empty:
            empty = pd.DataFrame(columns=["symbol", "year", "period"])
            empty.attrs.update(symbol=symbol, source=self.DATA_SOURCE, period_type=period)
            return empty

        df.columns = [camel_to_snake(column) for column in df.columns]
        quarter = _numeric_series(df, "quarter", "length_report")
        ratio_type = (
            df["ratio_type"].astype(str).str.upper()
            if "ratio_type" in df.columns
            else pd.Series("", index=df.index)
        )
        if period == "year":
            df = df[(quarter == 5) | (ratio_type == "RATIO_YEAR")]
            period_values = pd.Series("FY", index=df.index)
        else:
            df = df[quarter.between(1, 4)]
            period_values = quarter[df.index].map(lambda value: f"Q{int(value)}")

        metadata = {
            "year",
            "quarter",
            "year_report",
            "organ_code",
            "ticker",
            "ratio_ttm_id",
            "ratio_year_id",
            "ratio_type",
        }
        result = pd.DataFrame(index=df.index)
        if "ticker" in df.columns:
            symbol_values = df["ticker"]
        elif "organ_code" in df.columns:
            symbol_values = df["organ_code"]
        else:
            symbol_values = pd.Series(symbol, index=df.index)
        result["symbol"] = symbol_values.fillna(symbol)
        result["year"] = _numeric_series(df, "year_report", "year").astype("Int64")
        result["period"] = period_values
        metric_frame = pd.DataFrame(
            {
                column: pd.to_numeric(df[column], errors="coerce")
                for column in df.columns
                if column not in metadata
            },
            index=df.index,
        )
        result = pd.concat([result, metric_frame], axis=1)

        result.attrs.update(symbol=symbol, source=self.DATA_SOURCE, period_type=period)
        return result.reset_index(drop=True)
