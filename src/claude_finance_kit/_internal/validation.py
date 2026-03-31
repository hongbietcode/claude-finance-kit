"""Input validation helpers: symbols, date ranges, intervals, pagination."""

from datetime import datetime, timedelta
from typing import Any, Optional

from claude_finance_kit._internal.parser import get_asset_type


def validate_symbol(
    symbol: str,
    symbol_map: Optional[dict[str, str]] = None,
) -> str:
    """Validate and normalise a ticker symbol; raise ValueError on failure."""
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    if not isinstance(symbol, str):
        raise ValueError("Symbol must be a string.")
    if not (3 <= len(symbol) <= 12):
        raise ValueError("Symbol must be between 3 and 12 characters.")

    symbol = symbol.upper()

    if symbol_map and symbol in symbol_map:
        return symbol_map[symbol]

    get_asset_type(symbol)
    return symbol


def validate_date_range(
    start: str,
    end: Optional[str] = None,
) -> tuple[datetime, datetime]:
    """
    Parse and validate a date range string pair.

    Both dates must be in YYYY-MM-DD format.
    If end is omitted it defaults to tomorrow.
    Returns (start_dt, end_dt) where end_dt is end + 1 day.
    """
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid start date format. Use YYYY-MM-DD.")

    if end is None:
        end_dt = datetime.now() + timedelta(days=1)
    else:
        try:
            end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            raise ValueError("Invalid end date format. Use YYYY-MM-DD.")

    if start_dt > end_dt:
        raise ValueError("Start date cannot be after end date.")

    return start_dt, end_dt


def convert_to_timestamps(dates: tuple[datetime, datetime]) -> tuple[int, int]:
    """Convert a (start_dt, end_dt) pair to Unix timestamp integers."""
    return int(dates[0].timestamp()), int(dates[1].timestamp())


def validate_interval(interval: str, interval_map: dict[str, str]) -> str:
    """Map a user-facing interval string to a provider-specific value."""
    if interval not in interval_map:
        valid = ", ".join(interval_map.keys())
        raise ValueError(f"Invalid interval '{interval}'. Choose from: {valid}")
    return interval_map[interval]


def validate_pagination(
    page_size: int,
    page: int = 0,
    max_page_size: int = 100,
) -> tuple[int, int]:
    """
    Validate pagination parameters.

    Returns (effective_page_size, total_pages).
    """
    if page_size <= 0:
        raise ValueError("page_size must be greater than 0.")
    if page < 0:
        raise ValueError("page must be non-negative.")

    effective = min(page_size, max_page_size)
    total_pages = page_size // max_page_size + (1 if page_size % max_page_size else 0)
    return effective, total_pages


def validate_required_fields(data: dict[str, Any], required: list[str]) -> None:
    """Raise ValueError if any required field is absent from data."""
    missing = [f for f in required if f not in data]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
