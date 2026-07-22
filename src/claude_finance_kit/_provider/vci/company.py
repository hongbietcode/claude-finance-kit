"""VCI company data backed by Vietcap REST services."""

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.parser import get_asset_type
from claude_finance_kit._internal.transform import camel_to_snake, clean_html_dict, reorder_cols
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._internal.validation import validate_symbol
from claude_finance_kit._provider.vci.const import _VCI_ALLOWED_HOSTS, _VCI_COMPANY_URL, _VCIQ_URL


def _to_date(series: pd.Series) -> pd.Series:
    """Convert provider timestamps or ISO date strings to YYYY-MM-DD."""
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().any():
        unit = "ms" if numeric.dropna().abs().median() > 10_000_000_000 else "s"
        converted = pd.to_datetime(numeric, unit=unit, errors="coerce")
        fallback = pd.to_datetime(series.where(numeric.isna()), errors="coerce")
        converted = converted.fillna(fallback)
    else:
        converted = pd.to_datetime(series, errors="coerce")
    return converted.dt.strftime("%Y-%m-%d")


def _snake_frame(records: Any) -> pd.DataFrame:
    if isinstance(records, dict):
        normalized_records = [records]
    elif isinstance(records, list):
        normalized_records = [record for record in records if isinstance(record, dict)]
    else:
        normalized_records = []
    if not normalized_records:
        return pd.DataFrame()
    df = pd.DataFrame(normalized_records)
    df.columns = [camel_to_snake(column) for column in df.columns]
    return df


def _validate_stock_symbol(symbol: str) -> str:
    normalized = validate_symbol(symbol)
    if get_asset_type(normalized) != "stock":
        raise ValueError(f"VCI company data requires a stock symbol, got '{normalized}'.")
    return normalized


class VCICompany:
    """Fetch company profile, ownership, officers, news, and events from VCI."""

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

    def _data(self, url: str, params: dict[str, Any] | None = None, *, paginated: bool = False) -> Any:
        response = self._request(url, params)
        data = response.get("data") if isinstance(response, dict) else None
        if paginated and isinstance(data, dict):
            return data.get("content", [])
        return data

    def company_overview(self, symbol: str) -> pd.DataFrame:
        symbol = _validate_stock_symbol(symbol)
        data = self._data(f"{_VCI_COMPANY_URL}/details", {"ticker": symbol})
        if not isinstance(data, dict) or not data:
            raise ValueError(f"No company data found for '{symbol}'.")

        clean = clean_html_dict(data, ["profile", "enProfile"])
        df = _snake_frame(clean)
        df = df.drop(columns=[column for column in df.columns if column.startswith("en_")], errors="ignore")
        df = df.rename(
            columns={
                "ticker": "symbol",
                "vi_organ_name": "organ_name",
                "vi_organ_short_name": "organ_short_name",
                "profile": "company_profile",
                "number_of_shares_mkt_cap": "issue_share",
            }
        )
        if "symbol" not in df.columns:
            df.insert(0, "symbol", symbol)
        if "listing_date" in df.columns:
            df["listing_date"] = _to_date(df["listing_date"])
        df = reorder_cols(df, "symbol", position="first")
        df.attrs.update(symbol=symbol, source=self.DATA_SOURCE)
        return df

    def _shareholder_records(self, symbol: str) -> list[dict[str, Any]]:
        data = self._data(f"{_VCI_COMPANY_URL}/{symbol.upper()}/shareholder")
        return data if isinstance(data, list) else []

    def shareholders(self, symbol: str) -> pd.DataFrame:
        symbol = _validate_stock_symbol(symbol)
        df = _snake_frame(self._shareholder_records(symbol))
        columns = ["symbol", "share_holder", "quantity", "share_own_percent", "update_date"]
        if df.empty:
            return pd.DataFrame(columns=columns)

        df = df.rename(columns={"owner_name": "share_holder", "percentage": "share_own_percent"})
        if "share_own_percent" in df.columns:
            df["share_own_percent"] = pd.to_numeric(df["share_own_percent"], errors="coerce") * 100
        df.insert(0, "symbol", symbol)
        if "update_date" in df.columns:
            df["update_date"] = _to_date(df["update_date"])
        df = df[[column for column in columns if column in df.columns]]
        df.attrs.update(symbol=symbol, source=self.DATA_SOURCE)
        return df

    def officers(self, symbol: str, filter_by: str = "working") -> pd.DataFrame:
        if filter_by not in {"working", "resigned", "all"}:
            raise ValueError("filter_by must be 'working', 'resigned', or 'all'.")
        if filter_by != "working":
            raise NotImplementedError(
                "VCI REST does not expose resigned-officer status; only filter_by='working' is supported."
            )

        symbol = _validate_stock_symbol(symbol)
        df = _snake_frame(self._shareholder_records(symbol))
        columns = [
            "symbol",
            "officer_name",
            "officer_position",
            "officer_own_percent",
            "quantity",
            "update_date",
        ]
        if df.empty:
            return pd.DataFrame(columns=columns)

        if "owner_type" in df.columns:
            df = df[df["owner_type"].astype(str).str.upper() == "INDIVIDUAL"]
        if "position_name" in df.columns:
            df = df[df["position_name"].notna()]

        df = df.rename(
            columns={
                "owner_name": "officer_name",
                "position_name": "officer_position",
                "percentage": "officer_own_percent",
            }
        )
        if "officer_own_percent" in df.columns:
            df["officer_own_percent"] = pd.to_numeric(df["officer_own_percent"], errors="coerce") * 100
        df.insert(0, "symbol", symbol)
        if "update_date" in df.columns:
            df["update_date"] = _to_date(df["update_date"])
        df = df[[column for column in columns if column in df.columns]]
        df.attrs.update(symbol=symbol, source=self.DATA_SOURCE)
        return df.reset_index(drop=True)

    def company_news(self, symbol: str, limit: int = 20) -> pd.DataFrame:
        symbol = _validate_stock_symbol(symbol)
        end = datetime.now()
        data = self._data(
            f"{_VCIQ_URL}/v1/news",
            {
                "ticker": symbol,
                "fromDate": (end - timedelta(days=3650)).strftime("%Y%m%d"),
                "toDate": end.strftime("%Y%m%d"),
                "languageId": 1,
                "page": 0,
                "size": limit,
            },
            paginated=True,
        )
        df = _snake_frame(data)
        if df.empty:
            return pd.DataFrame(columns=["title", "short_content", "source_link", "public_date"])
        df = df.rename(
            columns={
                "news_title": "title",
                "news_short_content": "short_content",
                "news_source_link": "source_link",
            }
        )
        if "public_date" in df.columns:
            df["public_date"] = _to_date(df["public_date"])
        df.attrs.update(symbol=symbol, source=self.DATA_SOURCE)
        return df.head(limit).reset_index(drop=True)

    def company_events(self, symbol: str, **kwargs) -> pd.DataFrame:
        symbol = _validate_stock_symbol(symbol)
        end = datetime.now()
        params = {
            "ticker": symbol,
            "fromDate": kwargs.pop("from_date", (end - timedelta(days=3650)).strftime("%Y%m%d")),
            "toDate": kwargs.pop("to_date", end.strftime("%Y%m%d")),
            "eventCode": kwargs.pop(
                "event_codes",
                "DIV,ISS,DDIND,DDINS,DDRP,AGME,AGMR,EGME,AIS,MA,MOVE,NLIS,OTHE,RETU,SUSP",
            ),
            "page": kwargs.pop("page", 0),
            "size": kwargs.pop("size", 50),
        }
        if kwargs:
            raise TypeError(f"Unexpected event options: {', '.join(sorted(kwargs))}")

        data = self._data(f"{_VCIQ_URL}/v1/events", params, paginated=True)
        df = _snake_frame(data)
        if df.empty:
            return pd.DataFrame(columns=["event_title", "event_list_name", "public_date"])
        for column in ["public_date", "issue_date", "record_date", "exright_date", "display_date"]:
            if column in df.columns:
                df[column] = _to_date(df[column])
        df.attrs.update(symbol=symbol, source=self.DATA_SOURCE)
        return df.reset_index(drop=True)
