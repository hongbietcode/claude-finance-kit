"""FundProvider implementation using Fmarket API."""

import logging
from datetime import datetime

import pandas as pd
from pandas import json_normalize

from claude_finance_kit._internal.http_client import send_request
from claude_finance_kit._provider._base import FundProvider
from claude_finance_kit._provider._registry import registry

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.fmarket.vn/res/products"

_FUND_TYPE_MAPPING: dict[str, list[str]] = {
    "": [],
    "BALANCED": ["BALANCED"],
    "BOND": ["BOND"],
    "STOCK": ["STOCK"],
}

_FUND_LIST_COLUMNS = [
    "shortName",
    "name",
    "dataFundAssetType.name",
    "owner.name",
    "managementFee",
    "firstIssueAt",
    "nav",
    "productNavChange.navTo36Months",
    "productNavChange.annualizedReturn36Months",
    "productNavChange.updateAt",
    "id",
    "code",
]

_FUND_LIST_MAPPING = {
    "shortName": "short_name",
    "name": "name",
    "dataFundAssetType.name": "fund_type",
    "owner.name": "fund_owner_name",
    "managementFee": "management_fee",
    "firstIssueAt": "inception_date",
    "nav": "nav",
    "productNavChange.navTo36Months": "nav_change_36m",
    "productNavChange.annualizedReturn36Months": "nav_change_36m_annualized",
    "productNavChange.updateAt": "nav_update_at",
    "id": "fund_id_fmarket",
    "code": "fund_code",
}

_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "user-agent": "claude-finance-kit/1.0",
}


def _convert_unix_to_date(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], unit="ms", utc=True, errors="coerce").dt.strftime("%Y-%m-%d")
    return df


class FmarketProvider(FundProvider):
    """Mutual fund data provider backed by Fmarket API."""

    def listing(self, fund_type: str = "STOCK") -> pd.DataFrame:
        """List funds filtered by type. fund_type: '', 'BALANCED', 'BOND', 'STOCK'."""
        fund_type = fund_type.upper()
        fund_asset_types = _FUND_TYPE_MAPPING.get(fund_type, [])
        payload = {
            "types": ["NEW_FUND", "TRADING_FUND"],
            "issuerIds": [],
            "sortOrder": "DESC",
            "sortField": "navTo6Months",
            "page": 1,
            "pageSize": 100,
            "isIpo": False,
            "fundAssetTypes": fund_asset_types,
            "bondRemainPeriods": [],
            "searchField": "",
            "isBuyByReward": False,
            "thirdAppIds": [],
        }
        try:
            data = send_request(url=f"{_BASE_URL}/filter", headers=_HEADERS, method="POST", payload=payload)
            df = json_normalize(data, record_path=["data", "rows"])
            existing_cols = [c for c in _FUND_LIST_COLUMNS if c in df.columns]
            df = df[existing_cols]
            df = _convert_unix_to_date(df, ["firstIssueAt", "productNavChange.updateAt"])
            sort_col = "productNavChange.navTo36Months"
            if sort_col in df.columns:
                df = df.sort_values(by=sort_col, ascending=False)
            existing_map = {k: v for k, v in _FUND_LIST_MAPPING.items() if k in df.columns}
            df.rename(columns=existing_map, inplace=True)
            return df.reset_index(drop=True)
        except Exception as exc:
            logger.error("listing() failed: %s", exc)
            raise

    def fund_filter(self, symbol: str) -> pd.DataFrame:
        """Search funds by short name, returns id and shortName."""
        symbol = symbol.upper()
        payload = {
            "searchField": symbol,
            "types": ["NEW_FUND", "TRADING_FUND"],
            "pageSize": 100,
        }
        try:
            data = send_request(url=f"{_BASE_URL}/filter", headers=_HEADERS, method="POST", payload=payload)
            df = json_normalize(data, record_path=["data", "rows"])
            if df.empty:
                raise ValueError(f"No fund found with symbol '{symbol}'")
            cols = [c for c in ["id", "shortName"] if c in df.columns]
            return df[cols]
        except Exception as exc:
            logger.error("fund_filter() failed: %s", exc)
            raise

    def top_holding(self, fund_id: str) -> pd.DataFrame:
        """Top holdings for given fund_id (int or str)."""
        fid = int(fund_id)
        try:
            data = send_request(url=f"{_BASE_URL}/{fid}", headers=_HEADERS, method="GET")
            df = pd.DataFrame()
            equity = json_normalize(data, record_path=["data", "productTopHoldingList"], errors="ignore")
            if not equity.empty:
                equity = _convert_unix_to_date(equity, ["updateAt"])
                df = pd.concat([df, equity])
            bond = json_normalize(data, record_path=["data", "productTopHoldingBondList"], errors="ignore")
            if not bond.empty:
                bond = _convert_unix_to_date(bond, ["updateAt"])
                df = pd.concat([df, bond])
            if df.empty:
                return pd.DataFrame()
            df["fundId"] = fid
            cols_want = ["stockCode", "industry", "netAssetPercent", "type", "updateAt", "fundId"]
            existing = [c for c in cols_want if c in df.columns]
            df = df[existing]
            rename_map = {
                "stockCode": "stock_code",
                "industry": "industry",
                "netAssetPercent": "net_asset_percent",
                "type": "type_asset",
                "updateAt": "update_at",
            }
            df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
            return df.reset_index(drop=True)
        except Exception as exc:
            logger.error("top_holding() failed: %s", exc)
            raise

    def industry_holding(self, fund_id: str) -> pd.DataFrame:
        """Industry allocation for given fund_id."""
        fid = int(fund_id)
        try:
            data = send_request(url=f"{_BASE_URL}/{fid}", headers=_HEADERS, method="GET")
            df = json_normalize(data, record_path=["data", "productIndustriesHoldingList"], errors="ignore")
            if df.empty:
                return pd.DataFrame()
            cols_want = ["industry", "assetPercent"]
            existing = [c for c in cols_want if c in df.columns]
            df = df[existing]
            df.rename(columns={"assetPercent": "net_asset_percent"}, inplace=True)
            return df.reset_index(drop=True)
        except Exception as exc:
            logger.error("industry_holding() failed: %s", exc)
            raise

    def nav_report(self, fund_id: str) -> pd.DataFrame:
        """Full NAV history for given fund_id."""
        fid = int(fund_id)
        current_date = datetime.now().strftime("%Y%m%d")
        nav_url = _BASE_URL.replace("products", "product/get-nav-history")
        payload = {
            "isAllData": 1,
            "productId": fid,
            "fromDate": None,
            "toDate": current_date,
        }
        try:
            data = send_request(url=nav_url, headers=_HEADERS, method="POST", payload=payload)
            df = json_normalize(data, record_path=["data"], errors="ignore")
            if df.empty:
                raise ValueError(f"No NAV data for fund_id={fid}")
            cols_want = ["navDate", "nav"]
            existing = [c for c in cols_want if c in df.columns]
            df = df[existing]
            df.rename(columns={"navDate": "date", "nav": "nav_per_unit"}, inplace=True)
            return df.reset_index(drop=True)
        except Exception as exc:
            logger.error("nav_report() failed: %s", exc)
            raise

    def asset_holding(self, fund_id: str) -> pd.DataFrame:
        """Asset allocation breakdown for given fund_id."""
        fid = int(fund_id)
        try:
            data = send_request(url=f"{_BASE_URL}/{fid}", headers=_HEADERS, method="GET")
            df = json_normalize(data, record_path=["data", "productAssetHoldingList"], errors="ignore")
            if df.empty:
                return pd.DataFrame()
            cols_want = ["assetPercent", "assetType.name"]
            existing = [c for c in cols_want if c in df.columns]
            df = df[existing]
            df.rename(columns={"assetPercent": "asset_percent", "assetType.name": "asset_type"}, inplace=True)
            return df.reset_index(drop=True)
        except Exception as exc:
            logger.error("asset_holding() failed: %s", exc)
            raise


registry.register_fund("FMARKET", FmarketProvider)
