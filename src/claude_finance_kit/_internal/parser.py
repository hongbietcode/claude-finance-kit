"""Data parsing utilities: timestamps, asset-type detection, JSON helpers."""

import re
from datetime import datetime
from typing import Any, Literal, Union

import numpy as np
import pandas as pd
from pytz import timezone

VIETNAM_TZ = timezone("Asia/Ho_Chi_Minh")

KNOWN_INDICES: set[str] = {"VNINDEX", "HNXINDEX", "UPCOMINDEX", "HNX30"}


def get_asset_type(symbol: str) -> str:
    """
    Determine asset type from a VN-market security code.

    Returns one of: 'index', 'stock', 'derivative', 'bond', 'coveredWarr'.
    Raises ValueError for unrecognised formats.
    """
    symbol = symbol.upper()

    if symbol in KNOWN_INDICES:
        return "index"

    if len(symbol) == 3:
        return "stock"

    krx_pattern = re.compile(r"^4[12][A-Z0-9]{2}[0-9A-HJ-NP-TV-W][1-9A-C]\d{3}$")
    if krx_pattern.match(symbol):
        return "derivative"

    vn100_pattern = re.compile(r"^VN100F\d{1,2}[MQ]$")
    if vn100_pattern.match(symbol):
        return "derivative"

    if len(symbol) in (7, 9):
        gov_bond = re.compile(r"^GB\d{2}F\d{4}$")
        comp_bond = re.compile(r"^(?!VN30F)[A-Z]{3}\d{6}$")
        vn30_fm = re.compile(r"^VN30F\d{1,2}[MQ]$")
        vn30_ym = re.compile(r"^VN30F\d{4}$")
        if gov_bond.match(symbol) or comp_bond.match(symbol):
            return "bond"
        if vn30_fm.match(symbol) or vn30_ym.match(symbol):
            return "derivative"
        raise ValueError(
            f"Unrecognised derivative/bond symbol: {symbol}. "
            "Expected formats: VN30F1M, VN30F2024, GB10F2024, or BAB122032."
        )

    if len(symbol) == 8:
        return "coveredWarr"

    raise ValueError(f"Unrecognised symbol format: {symbol!r}")


def parse_timestamp(time_value: Union[datetime, str]) -> int | None:
    """Convert a datetime object or date string to a Unix timestamp (seconds)."""
    try:
        if isinstance(time_value, datetime):
            time_value = VIETNAM_TZ.localize(time_value)
        elif isinstance(time_value, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    time_value = datetime.strptime(time_value, fmt)
                    break
                except ValueError:
                    continue
            else:
                return None
        else:
            return None
        return int(time_value.timestamp())
    except (ValueError, OSError, OverflowError):
        return None


def localize_timestamp(
    timestamp: Union[pd.Series, int, float, list, np.ndarray, pd.Timestamp, Any],
    unit: Literal["s", "ms", "us", "ns"] = "s",
    return_scalar: bool = False,
    return_string: bool = False,
    string_format: str = "%Y-%m-%d %H:%M:%S",
) -> Union[pd.Series, pd.Timestamp, str]:
    """
    Convert timestamp value(s) to Vietnam timezone (UTC+7).

    Returns a Series by default; pass return_scalar=True for a single value.
    """
    treat_as_scalar = False

    if np.isscalar(timestamp) or isinstance(timestamp, (pd.Timestamp, datetime)):
        treat_as_scalar = True
        ts_series = pd.Series([timestamp])
    elif isinstance(timestamp, pd.Series) and len(timestamp) == 1:
        treat_as_scalar = True
        ts_series = timestamp
    elif hasattr(timestamp, "__len__") and len(timestamp) == 1:
        treat_as_scalar = True
        ts_series = pd.Series(timestamp)
    else:
        ts_series = timestamp if isinstance(timestamp, pd.Series) else pd.Series(timestamp)

    dt_series = pd.to_datetime(ts_series, unit=unit)
    vietnam_series = dt_series.dt.tz_localize("UTC").dt.tz_convert("Asia/Ho_Chi_Minh")

    if return_string:
        vietnam_series = vietnam_series.dt.strftime(string_format)

    if return_scalar and treat_as_scalar:
        return vietnam_series.iloc[0]

    return vietnam_series


def safe_json_get(data: dict, *keys: str, default: Any = None) -> Any:
    """Safely traverse nested dict keys, returning default on any miss."""
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
        if current is default:
            return default
    return current
