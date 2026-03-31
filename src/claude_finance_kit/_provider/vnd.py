"""MarketProvider implementation using VNDirect (VND) API."""

import logging
from datetime import datetime, timedelta

import pandas as pd
import requests

from claude_finance_kit._provider._base import MarketProvider
from claude_finance_kit._provider._registry import registry

logger = logging.getLogger(__name__)

_RATIOS_BASE = "https://api-finfo.vndirect.com.vn/v4/ratios"
_INSIGHT_BASE = "https://api-finfo.vndirect.com.vn/v4"
_DATE_FMT = "%Y-%m-%d"

_INDEX_MAPPING = {
    "VNINDEX": "VNINDEX",
    "HNXINDEX": "HNX",
    "UPCOMINDEX": "UPCOM",
    "VN30": "VN30",
}

_TOP_STOCK_INDEX = {
    "VNINDEX": "VNIndex",
    "HNX": "HNX",
    "VN30": "VN30",
}

_TOP_STOCK_COLS = {
    "code": "symbol",
    "index": "index",
    "lastPrice": "last_price",
    "lastUpdated": "last_updated",
    "priceChgCr1D": "price_change_1d",
    "priceChgPctCr1D": "price_change_pct_1d",
    "accumulatedVal": "accumulated_value",
    "nmVolumeAvgCr20D": "avg_volume_20d",
}

_HEADERS = {
    "accept": "application/json",
    "user-agent": "claude-finance-kit/1.0",
}


def _lookback_date(duration: str) -> str:
    """Convert duration string like '5Y', '6M', '30D' to a start date string."""
    today = datetime.now()
    duration = duration.upper()
    if duration.endswith("Y"):
        start = today.replace(year=today.year - int(duration[:-1]))
    elif duration.endswith("M"):
        months = int(duration[:-1])
        total = today.month - months
        year = today.year + total // 12
        month = total % 12
        if month <= 0:
            year -= 1
            month += 12
        start = today.replace(year=year, month=month)
    elif duration.endswith("D"):
        start = today - timedelta(days=int(duration[:-1]))
    else:
        start = today.replace(year=today.year - 5)
    return start.strftime(_DATE_FMT)


def _validate_index(index: str) -> str:
    key = index.upper()
    if key not in _INDEX_MAPPING:
        raise ValueError(f"Invalid index '{key}'. Valid: {list(_INDEX_MAPPING)}")
    return _INDEX_MAPPING[key]


def _fetch_ratio(index_code: str, ratio_code: str, start_date: str) -> pd.DataFrame:
    url = (
        f"{_RATIOS_BASE}?q=ratioCode:{ratio_code}~code:{index_code}"
        f"~reportDate:gte:{start_date}&sort=reportDate:desc&size=10000"
        f"&fields=value,reportDate"
    )
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df["reportDate"] = pd.to_datetime(df["reportDate"])
        col_name = ratio_code.lower().replace("price_to_earnings", "pe").replace("price_to_book", "pb")
        df = df.rename(columns={"value": col_name})
        return df.set_index("reportDate").sort_index()
    except requests.RequestException as exc:
        logger.error("_fetch_ratio(%s, %s) failed: %s", ratio_code, index_code, exc)
        return pd.DataFrame()


def _fetch_top_stocks(url: str) -> pd.DataFrame:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        existing = {k: v for k, v in _TOP_STOCK_COLS.items() if k in df.columns}
        df.rename(columns=existing, inplace=True)
        return df
    except requests.RequestException as exc:
        logger.error("_fetch_top_stocks(%s) failed: %s", url, exc)
        return pd.DataFrame()


class VNDProvider(MarketProvider):
    """Market-level data provider backed by VNDirect API."""

    def pe(self, index: str, duration: str = "5Y") -> pd.DataFrame:
        """P/E ratio history for given index and duration."""
        index_code = _validate_index(index)
        start_date = _lookback_date(duration)
        return _fetch_ratio(index_code, "PRICE_TO_EARNINGS", start_date)

    def pb(self, index: str, duration: str = "5Y") -> pd.DataFrame:
        """P/B ratio history for given index and duration."""
        index_code = _validate_index(index)
        start_date = _lookback_date(duration)
        return _fetch_ratio(index_code, "PRICE_TO_BOOK", start_date)

    def top_gainer(self, index: str, limit: int = 10) -> pd.DataFrame:
        """Top stocks by price gain for given index."""
        index_code = _TOP_STOCK_INDEX.get(index.upper(), "VNIndex")
        url = (
            f"{_INSIGHT_BASE}/top_stocks?q=index:{index_code}"
            f"~nmVolumeAvgCr20D:gte:10000~priceChgPctCr1D:gt:0"
            f"&size={limit}&sort=priceChgPctCr1D"
        )
        return _fetch_top_stocks(url)

    def top_loser(self, index: str, limit: int = 10) -> pd.DataFrame:
        """Top stocks by price decline for given index."""
        index_code = _TOP_STOCK_INDEX.get(index.upper(), "VNIndex")
        url = (
            f"{_INSIGHT_BASE}/top_stocks?q=index:{index_code}"
            f"~nmVolumeAvgCr20D:gte:10000~priceChgPctCr1D:lt:0"
            f"&size={limit}&sort=priceChgPctCr1D:asc"
        )
        return _fetch_top_stocks(url)

    def top_liquidity(self, index: str, limit: int = 10) -> pd.DataFrame:
        """Top stocks by accumulated trading value (liquidity) for given index."""
        index_code = _TOP_STOCK_INDEX.get(index.upper(), "VNIndex")
        url = (
            f"{_INSIGHT_BASE}/top_stocks?q=index:{index_code}"
            f"~accumulatedVal:gt:0"
            f"&size={limit}&sort=accumulatedVal"
        )
        return _fetch_top_stocks(url)


registry.register_market("VND", VNDProvider)
