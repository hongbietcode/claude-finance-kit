"""CommodityProvider implementation using Simplize (SPL) API."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._provider._base import CommodityProvider
from claude_finance_kit._provider._registry import registry

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.simplize.vn/api"
_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
_DATE_FMT = "%Y-%m-%d"
_HEADERS = {
    "accept": "application/json",
    "user-agent": "claude-finance-kit/1.0",
}


def _lookback_start(length: str, end: str) -> str:
    """Compute start date from a lookback string like '1Y', '6M', '30D'."""
    end_dt = datetime.strptime(end, _DATE_FMT)
    length = length.upper()
    if length.endswith("Y"):
        years = int(length[:-1])
        start_dt = end_dt.replace(year=end_dt.year - years)
    elif length.endswith("M"):
        months = int(length[:-1])
        total = end_dt.month - months
        year = end_dt.year + total // 12
        month = total % 12
        if month <= 0:
            year -= 1
            month += 12
        start_dt = end_dt.replace(year=year, month=month)
    elif length.endswith("D"):
        from datetime import timedelta
        start_dt = end_dt - timedelta(days=int(length[:-1]))
    else:
        from datetime import timedelta
        start_dt = end_dt - timedelta(days=365)
    return start_dt.strftime(_DATE_FMT)


def _fetch_ohlcv(ticker: str, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
    """Fetch OHLCV data for a commodity ticker from SPL API."""
    end_date = end or datetime.now().strftime(_DATE_FMT)
    start_date = start or _lookback_start(length, end_date)

    start_dt = datetime.strptime(start_date, _DATE_FMT).replace(hour=0, minute=0, second=0, tzinfo=_TZ)
    end_dt = datetime.strptime(end_date, _DATE_FMT).replace(hour=23, minute=59, second=59, tzinfo=_TZ)

    params = {
        "ticker": ticker,
        "interval": "1d",
        "type": "commodity",
        "from": int(start_dt.timestamp()),
        "to": int(end_dt.timestamp()),
    }

    try:
        data = send_request(
            url=f"{_BASE_URL}/historical/prices/ohlcv",
            headers=_HEADERS,
            method="GET",
            params=params,
        )
        raw = data.get("data", [])
        if not raw:
            return pd.DataFrame()

        cols = ["time", "open", "high", "low", "close", "volume"]
        df = pd.DataFrame(raw, columns=cols)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df["time"] = df["time"].dt.tz_localize("UTC").dt.tz_convert(_TZ).dt.tz_localize(None)
        df.set_index("time", inplace=True)
        return df
    except Exception as exc:
        logger.error("_fetch_ohlcv(%s) failed: %s", ticker, exc)
        raise


class SPLProvider(CommodityProvider):
    """Commodity price data provider backed by Simplize API."""

    def gold(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        """Vietnamese gold prices (buy/sell) and global gold price."""
        end_date = end or datetime.now().strftime(_DATE_FMT)
        start_date = start or _lookback_start(length, end_date)
        try:
            buy = _fetch_ohlcv("GOLD:VN:BUY", start_date, end_date)[["close"]].rename(columns={"close": "buy"})
            sell = _fetch_ohlcv("GOLD:VN:SELL", start_date, end_date)[["close"]].rename(columns={"close": "sell"})
            global_gold = _fetch_ohlcv("GC=F", start_date, end_date)[["close"]].rename(columns={"close": "global"})
            df = pd.concat([buy, sell, global_gold], axis=1)
            return df
        except Exception as exc:
            logger.error("gold() failed: %s", exc)
            raise

    def oil(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        """Crude oil and Vietnam gas prices (RON92, RON95, DO)."""
        end_date = end or datetime.now().strftime(_DATE_FMT)
        start_date = start or _lookback_start(length, end_date)
        try:
            crude = _fetch_ohlcv("CL=F", start_date, end_date)[["close"]].rename(columns={"close": "crude_oil"})
            ron95 = _fetch_ohlcv("GAS:RON95:VN", start_date, end_date)[["close"]].rename(columns={"close": "ron95"})
            ron92 = _fetch_ohlcv("GAS:RON92:VN", start_date, end_date)[["close"]].rename(columns={"close": "ron92"})
            oil_do = _fetch_ohlcv("GAS:DO:VN", start_date, end_date)[["close"]].rename(columns={"close": "oil_do"})
            df = pd.concat([crude, ron95, ron92, oil_do], axis=1)
            return df
        except Exception as exc:
            logger.error("oil() failed: %s", exc)
            raise

    def steel(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        """Steel prices: Vietnam D10, HRC, and iron ore."""
        end_date = end or datetime.now().strftime(_DATE_FMT)
        start_date = start or _lookback_start(length, end_date)
        try:
            d10 = _fetch_ohlcv("STEEL:D10:VN", start_date, end_date)[["close"]].rename(columns={"close": "steel_d10"})
            hrc = _fetch_ohlcv("COMEX:HRC1!", start_date, end_date)[["close"]].rename(columns={"close": "hrc"})
            iron = _fetch_ohlcv("COMEX:TIO1!", start_date, end_date)[["close"]].rename(columns={"close": "iron_ore"})
            df = pd.concat([d10, hrc, iron], axis=1)
            return df
        except Exception as exc:
            logger.error("steel() failed: %s", exc)
            raise

    def gas(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        """Natural gas and crude oil prices."""
        end_date = end or datetime.now().strftime(_DATE_FMT)
        start_date = start or _lookback_start(length, end_date)
        try:
            natural = _fetch_ohlcv("NG=F", start_date, end_date)[["close"]].rename(columns={"close": "natural_gas"})
            crude = _fetch_ohlcv("CL=F", start_date, end_date)[["close"]].rename(columns={"close": "crude_oil"})
            df = pd.concat([natural, crude], axis=1)
            return df
        except Exception as exc:
            logger.error("gas() failed: %s", exc)
            raise

    def fertilizer(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        """Fertilizer prices: urea."""
        end_date = end or datetime.now().strftime(_DATE_FMT)
        start_date = start or _lookback_start(length, end_date)
        try:
            ure = _fetch_ohlcv("CBOT:UME1!", start_date, end_date)[["close"]].rename(columns={"close": "urea"})
            return ure
        except Exception as exc:
            logger.error("fertilizer() failed: %s", exc)
            raise

    def agricultural(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        """Agricultural commodity prices: soybean, corn, sugar."""
        end_date = end or datetime.now().strftime(_DATE_FMT)
        start_date = start or _lookback_start(length, end_date)
        try:
            soy = _fetch_ohlcv("ZM=F", start_date, end_date)[["close"]].rename(columns={"close": "soybean"})
            corn = _fetch_ohlcv("ZC=F", start_date, end_date)[["close"]].rename(columns={"close": "corn"})
            sugar = _fetch_ohlcv("SB=F", start_date, end_date)[["close"]].rename(columns={"close": "sugar"})
            df = pd.concat([soy, corn, sugar], axis=1)
            return df
        except Exception as exc:
            logger.error("agricultural() failed: %s", exc)
            raise


registry.register_commodity("SPL", SPLProvider)
