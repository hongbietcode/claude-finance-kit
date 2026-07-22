"""VCI listing data backed by Vietcap REST services."""

from typing import Any

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.transform import camel_to_snake, reorder_cols
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.vci.const import (
    _GROUP_CODE_MAPPING,
    _INDEX_MAPPING,
    _TRADING_URL,
    _VCI_ALLOWED_HOSTS,
    _VCIQ_URL,
)


class VCIListing:
    """Fetch symbol, exchange, group, and industry metadata from VCI."""

    DATA_SOURCE = "VCI"

    def __init__(self) -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)

    def _request(self, url: str, params: dict[str, Any] | None = None) -> Any:
        return send_request(
            url=url,
            headers=self._headers,
            method="GET",
            params=params,
            allowed_hosts=_VCI_ALLOWED_HOSTS,
        )

    def all_symbols(self, exchange: str | None = None) -> pd.DataFrame:
        """Return listed equities, falling back to the stable industry endpoint."""
        try:
            df = self.symbols_by_exchange()
            required = {"symbol", "organ_name", "type"}
            if exchange:
                required.add("exchange")
            missing = required - set(df.columns)
            if missing:
                raise ValueError(f"VCI exchange response is missing columns: {sorted(missing)}")
            df = df[df["type"].astype(str).str.upper() == "STOCK"]
            if exchange:
                df = df[df["exchange"].astype(str).str.upper() == exchange.upper()]
            result = df[["symbol", "organ_name"]].drop_duplicates("symbol").reset_index(drop=True)
        except (ConnectionError, KeyError, ValueError):
            df = self.symbols_by_industries()
            required = {"symbol", "organ_name"}
            if exchange:
                required.add("exchange")
            missing = required - set(df.columns)
            if missing:
                raise ValueError(f"VCI industry response is missing columns: {sorted(missing)}")
            if exchange:
                df = df[df["exchange"].astype(str).str.upper() == exchange.upper()]
            result = df[["symbol", "organ_name"]].drop_duplicates("symbol").reset_index(drop=True)

        result.attrs["source"] = self.DATA_SOURCE
        return result

    def symbols_by_group(self, group: str) -> pd.Series:
        """Return symbols belonging to an exchange, instrument, or index group."""
        key = group.upper()
        group_code = _INDEX_MAPPING.get(key, _GROUP_CODE_MAPPING.get(key))
        if group_code is None:
            valid = sorted(set(_INDEX_MAPPING) | set(_GROUP_CODE_MAPPING))
            raise ValueError(f"Invalid group '{group}'. Must be one of: {valid}")

        data = self._request(
            f"{_TRADING_URL.rstrip('/')}/price/symbols/getByGroup",
            params={"group": group_code},
        )
        if not data:
            raise ValueError(f"No data found for group '{group}'.")

        df = pd.DataFrame(data)
        if "symbol" not in df.columns:
            raise ValueError(f"VCI group response for '{group}' has no symbol field.")
        result = df["symbol"].dropna().astype(str).str.upper().drop_duplicates().reset_index(drop=True)
        result.attrs["source"] = self.DATA_SOURCE
        return result

    def symbols_by_industries(self, lang: str = "vi") -> pd.DataFrame:
        """Return long-form ICB classifications from the Vietcap search service."""
        if lang not in {"vi", "en"}:
            raise ValueError("lang must be 'vi' or 'en'.")

        response = self._request(
            f"{_VCIQ_URL}/v2/company/search-bar",
            params={"language": "1" if lang == "vi" else "2"},
        )
        data = response.get("data") if isinstance(response, dict) else None
        if data is None:
            raise ValueError("VCI industry response does not contain data.")

        rows: list[dict[str, Any]] = []
        for company in data:
            if not isinstance(company, dict):
                continue
            for level in range(1, 5):
                icb = company.get(f"icbLv{level}")
                if not isinstance(icb, dict) or not icb.get("code"):
                    continue
                rows.append(
                    {
                        "symbol": company.get("code"),
                        "organ_name": company.get("name"),
                        "exchange": company.get("floor"),
                        "com_type_code": company.get("comTypeCode"),
                        "icb_level": level,
                        "icb_code": icb.get("code"),
                        "icb_name": icb.get("name"),
                    }
                )

        columns = [
            "symbol",
            "organ_name",
            "exchange",
            "com_type_code",
            "icb_level",
            "icb_code",
            "icb_name",
        ]
        df = pd.DataFrame(rows, columns=columns)
        if not df.empty:
            df = df.sort_values(["symbol", "icb_level"]).reset_index(drop=True)
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def symbols_by_exchange(self, lang: str = "vi") -> pd.DataFrame:
        """Return all VCI instruments with exchange metadata."""
        if lang not in {"vi", "en"}:
            raise ValueError("lang must be 'vi' or 'en'.")

        data = self._request(f"{_TRADING_URL.rstrip('/')}/price/symbols/getAll")
        if not data:
            raise ValueError("No exchange data found from VCI.")

        df = pd.DataFrame([data] if isinstance(data, dict) else data)
        df.columns = [camel_to_snake(column) for column in df.columns]
        df = df.rename(columns={"board": "exchange"})
        df = df.drop(columns=["id"], errors="ignore")

        if lang == "vi":
            df = df.drop(columns=[column for column in df.columns if column.startswith("en_")], errors="ignore")
        else:
            df = df.drop(columns=["organ_name", "organ_short_name"], errors="ignore")
            df.columns = [column.removeprefix("en_") for column in df.columns]

        df = reorder_cols(df, ["symbol", "exchange", "type"], position="first")
        df.attrs["source"] = self.DATA_SOURCE
        return df
