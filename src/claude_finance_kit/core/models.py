"""Pydantic v2 data models for claude-finance-kit."""

from datetime import date

from pydantic import BaseModel, field_validator

from claude_finance_kit.core.exceptions import InvalidDateRangeError
from claude_finance_kit.core.types import Exchange


class StockInfo(BaseModel):
    """Basic stock instrument metadata."""

    symbol: str
    exchange: Exchange
    name: str
    industry: str | None = None

    @field_validator("symbol")
    @classmethod
    def symbol_upper(cls, v: str) -> str:
        return v.upper()


class DateRange(BaseModel):
    """Validated date range for historical queries."""

    start: date
    end: date

    @field_validator("end")
    @classmethod
    def end_after_start(cls, v: date, info) -> date:
        start = info.data.get("start")
        if start and v < start:
            raise InvalidDateRangeError(str(start), str(v))
        return v
