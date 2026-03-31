"""VDS quote module: intraday tick data via session-based API."""

import logging
from datetime import datetime

import pandas as pd
import requests

from claude_finance_kit._internal.user_agent import get_random_user_agent
from claude_finance_kit._provider.vds.const import _COOKIE_URL, _INTRADAY_MAP, _INTRADAY_URL

logger = logging.getLogger(__name__)


class VDSQuote:
    """Fetches intraday tick data from VDS (Viet Dragon Securities)."""

    DATA_SOURCE = "VDS"

    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": get_random_user_agent(),
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        self._cookie_initialized = False

    def _ensure_cookie(self) -> None:
        if self._cookie_initialized:
            return
        self._session.get(_COOKIE_URL, timeout=15)
        self._session.headers.update(
            {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": _COOKIE_URL,
            }
        )
        self._cookie_initialized = True

    def intraday(self, symbol: str, date: str | None = None) -> pd.DataFrame:
        self._ensure_cookie()

        if date is None:
            board_date = datetime.now().strftime("%d/%m/%Y")
        else:
            dt = datetime.strptime(date, "%Y-%m-%d")
            board_date = dt.strftime("%d/%m/%Y")

        payload = f"stockCode={symbol.upper()}&boardDate={board_date}"
        resp = self._session.post(_INTRADAY_URL, data=payload, timeout=15)
        resp.raise_for_status()

        data = resp.json()
        records = data.get("list") or []
        if not records:
            return pd.DataFrame(columns=["time", "symbol", "price", "volume"])

        df = pd.DataFrame(records)
        rename = {k: v for k, v in _INTRADAY_MAP.items() if k in df.columns}
        df = df.rename(columns=rename)
        keep = [c for c in _INTRADAY_MAP.values() if c in df.columns]
        df = df.loc[:, keep]

        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df
