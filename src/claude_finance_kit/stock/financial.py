"""Stock financial data: balance sheet, income statement, cash flow, ratios."""

import math

import pandas as pd

from claude_finance_kit._provider._base import StockProvider


class Finance:
    def __init__(self, symbol: str, provider: StockProvider):
        self._symbol = symbol
        self._provider = provider

    @staticmethod
    def _scale(df: pd.DataFrame, unit_multiplier: float) -> pd.DataFrame:
        if isinstance(unit_multiplier, bool) or not isinstance(unit_multiplier, (int, float)):
            raise TypeError("unit_multiplier must be a positive number.")
        if not math.isfinite(unit_multiplier) or unit_multiplier <= 0:
            raise ValueError("unit_multiplier must be a finite number greater than zero.")
        source_multiplier = float(df.attrs.get("effective_unit_multiplier", df.attrs.get("unit_multiplier", 1.0)))
        if unit_multiplier == 1 or df.empty:
            result = df.copy()
        else:
            result = df.copy()
            excluded = {
                "symbol",
                "year",
                "period",
                "quarter",
                "date",
                "time",
                "year_period",
                "year_report",
                "length_report",
                "term_code",
                "report_date",
                "update_date",
                "row_number",
                "levels",
                "id",
                "_id",
            }
            numeric = [
                column
                for column in result.select_dtypes(include="number").columns
                if column not in excluded
            ]
            result[numeric] = result[numeric] * float(unit_multiplier)
        result.attrs.update(df.attrs)
        result.attrs["source_unit_multiplier"] = source_multiplier
        result.attrs["unit_multiplier"] = float(unit_multiplier)
        result.attrs["effective_unit_multiplier"] = source_multiplier * float(unit_multiplier)
        return result

    def balance_sheet(self, period: str = "quarter", unit_multiplier: float = 1.0) -> pd.DataFrame:
        return self._scale(self._provider.balance_sheet(self._symbol, period), unit_multiplier)

    def income_statement(self, period: str = "quarter", unit_multiplier: float = 1.0) -> pd.DataFrame:
        return self._scale(self._provider.income_statement(self._symbol, period), unit_multiplier)

    def cash_flow(self, period: str = "quarter", unit_multiplier: float = 1.0) -> pd.DataFrame:
        return self._scale(self._provider.cash_flow(self._symbol, period), unit_multiplier)

    def ratio(self, period: str = "quarter") -> pd.DataFrame:
        return self._provider.ratio(self._symbol, period)
