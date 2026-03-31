"""VCI company module: overview, shareholders, officers, news, and events."""

import json
import logging
import re
from typing import Any

import pandas as pd

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._internal.transform import clean_html_dict, reorder_cols
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider.vci.const import _GRAPHQL_URL

logger = logging.getLogger(__name__)

_COMPANY_QUERY = (
    '{"query":"query Query($ticker: String!, $lang: String!) {\\n'
    "  CompanyListingInfo(ticker: $ticker) {\\n    id\\n    issueShare\\n"
    "    history\\n    companyProfile\\n    icbName3\\n    icbName2\\n    icbName4\\n"
    "    financialRatio {\\n      id\\n      ticker\\n      issueShare\\n"
    "      charterCapital\\n      __typename\\n    }\\n    __typename\\n  }\\n"
    "  OrganizationShareHolders(ticker: $ticker) {\\n    id\\n    ticker\\n    ownerFullName\\n"
    "    en_OwnerFullName\\n    quantity\\n    percentage\\n    updateDate\\n    __typename\\n  }\\n"
    "  OrganizationManagers(ticker: $ticker) {\\n    id\\n    ticker\\n    fullName\\n"
    "    positionName\\n    positionShortName\\n    en_PositionName\\n    en_PositionShortName\\n"
    "    updateDate\\n    percentage\\n    quantity\\n    __typename\\n  }\\n"
    "  OrganizationResignedManagers(ticker: $ticker) {\\n    id\\n    ticker\\n    fullName\\n"
    "    positionName\\n    positionShortName\\n    en_PositionName\\n    en_PositionShortName\\n"
    "    updateDate\\n    percentage\\n    quantity\\n    __typename\\n  }\\n"
    "  News(ticker: $ticker, langCode: $lang) {\\n    id\\n    ticker\\n    newsTitle\\n"
    "    newsShortContent\\n    newsSourceLink\\n    publicDate\\n    __typename\\n  }\\n"
    "  OrganizationEvents(ticker: $ticker) {\\n    id\\n    ticker\\n    eventTitle\\n"
    "    en_EventTitle\\n    publicDate\\n    issueDate\\n    sourceUrl\\n    eventListCode\\n"
    "    ratio\\n    value\\n    recordDate\\n    exrightDate\\n    eventListName\\n"
    "    en_EventListName\\n    __typename\\n  }\\n"
    '}\\n","variables":{"ticker":"VCI","lang":"vi"}}'
)


def _camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _drop_cols_by_pattern(df: pd.DataFrame, patterns: list[str]) -> pd.DataFrame:
    cols_to_drop = [c for c in df.columns if any(p in c for p in patterns)]
    return df.drop(columns=cols_to_drop, errors="ignore")


def _flatten_dict(d: dict[str, Any], nested_key: str) -> dict[str, Any]:
    result = {k: v for k, v in d.items() if k != nested_key}
    nested = d.get(nested_key, {})
    if isinstance(nested, dict):
        for k, v in nested.items():
            result[f"{nested_key}_{k}"] = v
    return result


class VCICompany:
    """Fetches company profile, shareholders, officers, news, and events from VCI."""

    DATA_SOURCE = "VCI"

    def __init__(self) -> None:
        self._headers = get_headers(data_source=self.DATA_SOURCE, random_agent=True)

    def _fetch_data(self, symbol: str) -> dict[str, Any]:
        payload = json.loads(_COMPANY_QUERY)
        payload["variables"]["ticker"] = symbol.upper()

        response = send_request(
            url=_GRAPHQL_URL,
            headers=self._headers,
            method="POST",
            payload=payload,
        )
        return response.get("data", {})

    def company_overview(self, symbol: str) -> pd.DataFrame:
        raw = self._fetch_data(symbol)
        listing_info = raw.get("CompanyListingInfo", {})
        if not listing_info:
            raise ValueError(f"No company data found for '{symbol}'.")

        clean = clean_html_dict(listing_info)
        flat = _flatten_dict(clean, "financialRatio")

        df = pd.DataFrame([flat])
        df.columns = [_camel_to_snake(col) for col in df.columns]
        df = _drop_cols_by_pattern(df, ["en_", "__", "_ratio_id"])
        df = df.rename(columns={"ticker": "symbol"}, errors="ignore")

        if "symbol" not in df.columns:
            df.insert(0, "symbol", symbol.upper())
        else:
            df = reorder_cols(df, ["symbol"], position="first")

        df.attrs["symbol"] = symbol.upper()
        df.attrs["source"] = self.DATA_SOURCE
        return df

    def shareholders(self, symbol: str) -> pd.DataFrame:
        raw = self._fetch_data(symbol)
        holders = raw.get("OrganizationShareHolders", [])
        if not holders:
            return pd.DataFrame(columns=["share_holder", "quantity", "share_own_percent"])

        df: pd.DataFrame = pd.DataFrame(holders)
        df.columns = [_camel_to_snake(col) for col in df.columns]
        df: pd.DataFrame = _drop_cols_by_pattern(df, ["__typename", "ticker", "en_"])
        df["update_date"] = pd.to_datetime(  # pylint: disable=unsupported-assignment-operation,unsubscriptable-object
            df["update_date"], unit="ms"  # pylint: disable=unsubscriptable-object
        ).dt.strftime("%Y-%m-%d")
        df = df.rename(columns={
            "owner_full_name": "share_holder",
            "percentage": "share_own_percent",
        })
        return df

    def officers(self, symbol: str, filter_by: str = "working") -> pd.DataFrame:
        """Fetch company officers/managers.

        Args:
            symbol: Stock ticker.
            filter_by: 'working', 'resigned', or 'all'.

        Returns:
            pd.DataFrame with officer information.
        """
        if filter_by not in ("working", "resigned", "all"):
            raise ValueError("filter_by must be 'working', 'resigned', or 'all'.")

        raw = self._fetch_data(symbol)

        if filter_by == "working":
            records = raw.get("OrganizationManagers", [])
            df = pd.DataFrame(records) if records else pd.DataFrame()
        elif filter_by == "resigned":
            records = raw.get("OrganizationResignedManagers", [])
            df = pd.DataFrame(records) if records else pd.DataFrame()
        else:
            working = raw.get("OrganizationManagers", [])
            resigned = raw.get("OrganizationResignedManagers", [])
            df_w = pd.DataFrame(working) if working else pd.DataFrame()
            df_r = pd.DataFrame(resigned) if resigned else pd.DataFrame()
            if not df_w.empty:
                df_w["type"] = "working"
            if not df_r.empty:
                df_r["type"] = "resigned"
            df = pd.concat([df_w, df_r], ignore_index=True)

        if df.empty:
            return pd.DataFrame(columns=["officer_name", "officer_position", "update_date"])

        df.columns = [_camel_to_snake(col) for col in df.columns]
        df = _drop_cols_by_pattern(df, ["__typename", "ticker", "en_"])
        df["update_date"] = pd.to_datetime(df["update_date"], unit="ms", errors="coerce").dt.strftime("%Y-%m-%d")
        df = df.rename(columns={
            "full_name": "officer_name",
            "position_name": "officer_position",
            "percentage": "officer_own_percent",
        })
        return df

    def company_news(self, symbol: str, limit: int = 20) -> pd.DataFrame:
        """Fetch company-related news.

        Args:
            symbol: Stock ticker.
            limit: Maximum number of news items to return. Default 20.

        Returns:
            pd.DataFrame with news items.
        """
        raw = self._fetch_data(symbol)
        news_list = raw.get("News", [])

        if not news_list:
            return pd.DataFrame(columns=["title", "short_content", "source_link", "public_date"])

        df = pd.DataFrame(news_list)
        df.columns = [_camel_to_snake(col) for col in df.columns]
        df = _drop_cols_by_pattern(df, ["__typename", "ticker"])
        df = df.rename(columns={
            "news_title": "title",
            "news_short_content": "short_content",
            "news_source_link": "source_link",
        })
        if "public_date" in df.columns:
            df["public_date"] = pd.to_datetime(df["public_date"], unit="ms", errors="coerce").dt.strftime("%Y-%m-%d")

        return df.head(limit)

    def company_events(self, symbol: str) -> pd.DataFrame:
        """Fetch company corporate events.

        Args:
            symbol: Stock ticker.

        Returns:
            pd.DataFrame with corporate events.
        """
        raw = self._fetch_data(symbol)
        events_list = raw.get("OrganizationEvents", [])

        if not events_list:
            return pd.DataFrame(columns=["event_title", "event_list_name", "public_date"])

        df = pd.DataFrame(events_list)
        df.columns = [_camel_to_snake(col) for col in df.columns]
        df = _drop_cols_by_pattern(df, ["__typename", "en_"])
        df = df.rename(columns={"ticker": "symbol"}, errors="ignore")
        df = _drop_cols_by_pattern(df, ["symbol"])

        date_cols = ["public_date", "issue_date", "record_date", "exright_date"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], unit="ms", errors="coerce").dt.strftime("%Y-%m-%d")

        return df
