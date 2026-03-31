"""KBS trading module: price board (ISS endpoint)."""

import json
import logging
from typing import List

import pandas as pd
import requests

from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.kbs.const import (
    _EXCHANGE_CODE_MAP,
    _PRICE_BOARD_MAP,
    _PRICE_BOARD_STANDARD_COLUMNS,
    _STOCK_ISS_URL,
)

logger = logging.getLogger(__name__)


class KBSTrading:
    """Fetches price board data from KBS ISS endpoint."""

    DATA_SOURCE = "KBS"

    def __init__(self) -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)

    def price_board(self, symbols: List[str]) -> pd.DataFrame:
        if not symbols:
            raise ValueError("symbols list cannot be empty.")

        symbols = [s.upper() for s in symbols]
        payload = {"code": ",".join(symbols)}

        headers = {**self._headers, "Content-Type": "application/json", "x-lang": "vi"}

        try:
            response = requests.post(
                _STOCK_ISS_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=30,
            )
            if response.status_code not in (200, 201):
                logger.warning("KBS ISS returned HTTP %d", response.status_code)
                return pd.DataFrame()
            json_data = response.json()
        except Exception as exc:
            logger.error("Failed to fetch KBS price board: %s", exc)
            return pd.DataFrame()

        if not json_data or not isinstance(json_data, list):
            return pd.DataFrame()

        df = pd.DataFrame(json_data)
        df = df.rename(columns=_PRICE_BOARD_MAP)

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", errors="coerce")

        available = [c for c in _PRICE_BOARD_STANDARD_COLUMNS if c in df.columns]
        df = df[available]

        if "exchange" in df.columns:
            df["exchange"] = df["exchange"].map(
                lambda x: _EXCHANGE_CODE_MAP.get(x, x) if pd.notna(x) else x
            )

        df.attrs["source"] = self.DATA_SOURCE
        return df

    def price_depth(self, symbol: str) -> pd.DataFrame:
        """KBS does not provide a dedicated price depth endpoint."""
        raise NotImplementedError(
            "KBS does not provide a price depth endpoint. Use price_board() instead."
        )
