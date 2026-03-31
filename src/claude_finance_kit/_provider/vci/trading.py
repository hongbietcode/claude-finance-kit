"""VCI trading module: price board and price depth."""

import logging
import re
from typing import Any

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.vci.const import _TRADING_URL

logger = logging.getLogger(__name__)


def _camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _flatten_data(d: dict[str, Any], sep: str = "_") -> dict[str, Any]:
    result: dict[str, Any] = {}
    for top_key, sub in d.items():
        if isinstance(sub, dict):
            for inner_key, value in sub.items():
                result[f"{top_key}{sep}{inner_key}"] = value
        else:
            result[top_key] = sub
    return result


_DROP_COLUMNS = {
    ("bid_ask", "code"), ("bid_ask", "symbol"), ("bid_ask", "session"),
    ("bid_ask", "received_time"), ("bid_ask", "message_type"), ("bid_ask", "time"),
    ("bid_ask", "bid_prices"), ("bid_ask", "ask_prices"),
    ("listing", "code"), ("listing", "exercise_price"), ("listing", "exercise_ratio"),
    ("listing", "maturity_date"), ("listing", "underlying_symbol"),
    ("listing", "issuer_name"), ("listing", "received_time"),
    ("listing", "message_type"), ("listing", "en_organ_name"),
    ("listing", "en_organ_short_name"), ("listing", "organ_short_name"),
    ("listing", "ticker"),
    ("match", "code"), ("match", "symbol"), ("match", "received_time"),
    ("match", "message_type"), ("match", "time"), ("match", "session"),
}


class VCITrading:
    """Fetches price board and price depth data from VCI."""

    DATA_SOURCE = "VCI"

    def __init__(self) -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)

    def price_board(self, symbols: list[str]) -> pd.DataFrame:
        if not symbols:
            raise ValueError("symbols list cannot be empty.")

        url = f"{_TRADING_URL}price/symbols/getList"
        payload = {"symbols": [s.upper() for s in symbols]}

        data = send_request(
            url=url,
            headers=self._headers,
            method="POST",
            payload=payload,
        )

        rows = []
        for item in data:
            item_data = {
                "listing": item["listingInfo"],
                "bidAsk": item["bidAsk"],
                "match": item["matchPrice"],
            }
            row = _flatten_data(item_data)

            try:
                for i, bid in enumerate(item["bidAsk"]["bidPrices"], start=1):
                    row[f"bidAsk_bid_{i}_price"] = bid["price"]
                    row[f"bidAsk_bid_{i}_volume"] = bid["volume"]
                for i, ask in enumerate(item["bidAsk"]["askPrices"], start=1):
                    row[f"bidAsk_ask_{i}_price"] = ask["price"]
                    row[f"bidAsk_ask_{i}_volume"] = ask["volume"]
            except (KeyError, TypeError):
                pass

            rows.append(row)

        df: pd.DataFrame = pd.DataFrame(rows)
        df.columns = pd.MultiIndex.from_tuples([
            tuple(_camel_to_snake(part) for part in c.split("_", 1))
            for c in df.columns
        ])
        df = df.drop(
            columns=[col for col in _DROP_COLUMNS if col in df.columns]
        )
        df = df.rename(columns={"board": "exchange"}, level=1)
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def price_depth(self, symbol: str) -> pd.DataFrame:
        url = f"{_TRADING_URL}market-watch/symbols/getPriceDepth"
        params = {"symbol": symbol.upper()}

        data = send_request(
            url=url,
            headers=self._headers,
            method="GET",
            params=params,
        )

        if not data:
            return pd.DataFrame(columns=["price", "acc_volume", "acc_buy_volume",
                                         "acc_sell_volume", "acc_undefined_volume"])

        depth_map = {
            "priceStep": "price",
            "accumulatedVolume": "acc_volume",
            "accumulatedBuyVolume": "acc_buy_volume",
            "accumulatedSellVolume": "acc_sell_volume",
            "accumulatedUndefinedVolume": "acc_undefined_volume",
        }

        if isinstance(data, dict):
            records = data.get("data", data)
        else:
            records = data

        df: pd.DataFrame = pd.DataFrame(records)
        df = df.rename(columns=depth_map)
        cols = [c for c in depth_map.values() if c in df.columns]
        df.attrs["source"] = self.DATA_SOURCE
        return df[cols]
