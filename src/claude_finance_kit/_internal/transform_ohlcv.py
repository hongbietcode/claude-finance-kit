"""OHLCV normalisation, intraday conversion, and resampling utilities."""

from datetime import datetime, time, timedelta
from typing import Any, Optional

import pandas as pd
import pytz

from claude_finance_kit._internal.parser import localize_timestamp
from claude_finance_kit._internal.transform_utils import clean_numeric_string

VIETNAM_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


def get_trading_date() -> datetime:
    """Return the most recent Vietnam-market trading date."""
    now = datetime.now(VIETNAM_TZ)
    weekday = now.weekday()
    if weekday >= 5:
        return (now - timedelta(days=weekday - 4)).date()
    if weekday == 0 and now.time() < time(8, 30):
        return (now - timedelta(days=3)).date()
    return now.date()


def resample_ohlcv(
    df: pd.DataFrame,
    interval: str,
    freq_map: Optional[dict[str, str]] = None,
    time_col: str = "time",
) -> pd.DataFrame:
    """Resample an OHLCV DataFrame to a coarser time frequency."""
    if time_col not in df.columns:
        raise KeyError(f"Time column '{time_col}' not in DataFrame.")

    default_freq_map = {
        "1W": "W",
        "1M": "ME",
        "1H": "h",
        "5min": "5min",
        "15min": "15min",
        "30min": "30min",
        "4H": "4h",
        "4hour": "4h",
    }
    freq = (freq_map or default_freq_map).get(interval, interval)

    df_idx = df.set_index(time_col)
    agg_rules = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    agg_dict = {col: agg_rules.get(col, "last") for col in df_idx.columns}

    if not agg_dict:
        raise ValueError("No resampable columns found.")

    result = df_idx.resample(freq).agg(agg_dict).reset_index()
    return result.sort_values(time_col).reset_index(drop=True)


def ohlc_to_df(
    data: Any,
    column_map: dict[str, str],
    dtype_map: dict[str, str],
    asset_type: str,
    symbol: str,
    source: str,
    interval: str = "1D",
    floating: int = 2,
    resample_map: Optional[dict[str, str]] = None,
) -> pd.DataFrame:
    """Convert raw OHLC data from any provider into a standardised DataFrame."""
    if not data:
        raise ValueError("Input data is empty.")

    if source == "TCBS" or isinstance(data, list):
        df = pd.DataFrame(data)
        df.rename(columns=column_map, inplace=True)
    else:
        available = {k: column_map[k] for k in column_map if k in data}
        df = pd.DataFrame(data)[list(available.keys())].rename(columns=column_map)

    required = ["time", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Available: {df.columns.tolist()}")

    df = df[required]

    if "time" in df.columns:
        if source in ("VCI", "MAS"):
            df["time"] = pd.to_datetime(df["time"].astype(int), unit="s").dt.tz_localize("UTC")
            df["time"] = df["time"].dt.tz_convert("Asia/Ho_Chi_Minh")
        else:
            df["time"] = pd.to_datetime(df["time"], errors="coerce")

    if asset_type not in ("index", "derivative"):
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].div(1000)

    df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].round(floating)

    if resample_map and interval not in ("1m", "1H", "1D"):
        df = resample_ohlcv(df, interval, freq_map=resample_map)

    for col, dtype in dtype_map.items():
        if col not in df.columns:
            continue
        if dtype == "datetime64[ns]" and hasattr(df[col], "dt") and df[col].dt.tz is not None:
            df[col] = df[col].dt.tz_localize(None)
        if col == "time" and interval == "1D":
            df[col] = df[col].dt.date
        df[col] = df[col].astype(dtype)

    df.attrs.update(symbol=symbol, category=asset_type, source=source)
    return df


def _process_match_types(df: pd.DataFrame, asset_type: str, source: str) -> pd.DataFrame:
    """Normalise match_type labels and tag ATO/ATC sessions for stock data."""
    replacements = {
        "VCI": {"b": "Buy", "s": "Sell"},
        "MAS": {"BUY": "Buy", "SELL": "Sell"},
        "TCBS": {"BU": "Buy", "SD": "Sell"},
        "KBS": {"B": "Buy", "S": "Sell"},
    }
    if source in replacements:
        df["match_type"] = df["match_type"].replace(replacements[source])
    if source == "MAS":
        df["match_type"] = df["match_type"].fillna("unknown")

    unknown_val = "unknown" if source in ("VCI", "MAS") else ""

    if asset_type == "stock" and (
        df["match_type"].eq(unknown_val).any() or df["match_type"].eq("").any()
    ):
        df = df.sort_values("time")
        df["_date"] = df["time"].dt.date

        def _tag_day(day_df: pd.DataFrame) -> pd.DataFrame:
            unknowns = day_df[day_df["match_type"] == unknown_val]
            if unknowns.empty:
                return day_df
            morning = unknowns[
                (unknowns["time"].dt.hour == 9) & unknowns["time"].dt.minute.between(13, 17)
            ]
            if not morning.empty:
                day_df.loc[morning["time"].idxmin(), "match_type"] = "ATO"
            afternoon = unknowns[
                (unknowns["time"].dt.hour == 14) & unknowns["time"].dt.minute.between(43, 47)
            ]
            if not afternoon.empty:
                day_df.loc[afternoon["time"].idxmax(), "match_type"] = "ATC"
            return day_df

        try:
            df = df.groupby("_date", group_keys=False).apply(_tag_day, include_groups=False)
        except TypeError:
            df = df.groupby("_date", group_keys=False).apply(_tag_day)

        df.drop(columns=["_date"], errors="ignore", inplace=True)

    return df


def intraday_to_df(
    data: list[dict[str, Any]],
    column_map: dict[str, str],
    dtype_map: dict[str, str],
    symbol: str,
    asset_type: str,
    source: str,
) -> pd.DataFrame:
    """Convert intraday tick data from any provider into a standardised DataFrame."""
    if not data:
        empty = pd.DataFrame(columns=list(column_map.values()))
        empty.attrs.update(symbol=symbol, category=asset_type, source=source)
        return empty

    df = pd.DataFrame(data)
    available = [c for c in column_map if c in df.columns]
    if not available:
        raise ValueError(f"Expected columns {list(column_map)} not in {df.columns.tolist()}")

    df = df[available].rename(columns={k: column_map[k] for k in available})

    for col in ("price", "volume"):
        if col in df.columns:
            df[col] = df[col].map(clean_numeric_string)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    scale = {"VCI": 1000, "MAS": 1000}.get(source, 1)
    if "price" in df.columns:
        df["price"] = df["price"] / scale

    if "volume" in df.columns:
        df["volume"] = df["volume"].fillna(0).round().astype(int)

    if "time" in df.columns:
        trading_date = get_trading_date()
        if source == "VCI":
            df["time"] = localize_timestamp(df["time"].astype(int), unit="s")
        elif source == "MAS":
            df["time"] = localize_timestamp(df["time"].astype(int), unit="ms")
            df["time"] = df["time"].dt.floor("s")
        else:
            sample = str(df["time"].iloc[0]) if not df.empty else ""
            if ":" in sample and len(sample) <= 8:
                df["time"] = df["time"].apply(
                    lambda x: datetime.combine(
                        trading_date,
                        datetime.strptime(x, "%H:%M:%S").time(),
                    )
                    if isinstance(x, str) and ":" in x
                    else pd.NaT
                )
                df["time"] = localize_timestamp(df["time"], return_string=False)
            else:
                df["time"] = pd.to_datetime(
                    df["time"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
                )
                if df["time"].dt.tz is None:
                    df["time"] = localize_timestamp(df["time"], return_string=False)

    if "match_type" in df.columns:
        df = _process_match_types(df, asset_type, source)

    if "time" in df.columns:
        df = df.sort_values("time")

    df = df.reset_index(drop=True)

    type_map = {k: v for k, v in dtype_map.items() if k in df.columns and k != "time"}
    if type_map:
        df = df.astype(type_map)

    df.attrs.update(symbol=symbol, category=asset_type, source=source)
    return df
