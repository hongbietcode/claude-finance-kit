"""SEC EDGAR submissions and XBRL company-facts adapter."""

from __future__ import annotations

import os
import re
import threading
from time import monotonic, sleep
from typing import Any

import pandas as pd

from claude_finance_kit._provider._base import StockProvider
from claude_finance_kit._provider._market_http import MarketHttpClient
from claude_finance_kit._provider._registry import registry
from claude_finance_kit.core.exceptions import AuthenticationError, InvalidSymbolError
from claude_finance_kit.core.models import ProviderDescriptor
from claude_finance_kit.core.types import MarketRegion, ProviderCapability


class SECStockProvider(StockProvider):
    """Keyless EDGAR provider requiring a responsible caller User-Agent."""

    _ticker_map: dict[str, str] | None = None
    _rate_lock = threading.Lock()
    _last_request_at = 0.0
    _minimum_request_interval = 0.11

    def __init__(self, user_agent: str | None = None, timeout: int = 30) -> None:
        self.user_agent = user_agent or os.getenv("CFK_SEC_USER_AGENT") or os.getenv("SEC_USER_AGENT")
        if not self.user_agent or "@" not in self.user_agent:
            raise AuthenticationError(
                "SEC",
                "Set CFK_SEC_USER_AGENT to an application name and contact email",
            )
        self.http = MarketHttpClient(
            "SEC",
            {"www.sec.gov", "data.sec.gov"},
            {"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate", "Accept": "application/json"},
            timeout,
        )

    def _request(self, url: str) -> Any:
        """Keep process-wide EDGAR request starts below ten per second."""

        provider_type = type(self)
        with provider_type._rate_lock:
            now = monotonic()
            wait = provider_type._minimum_request_interval - (
                now - provider_type._last_request_at
            )
            if wait > 0:
                sleep(wait)
            provider_type._last_request_at = monotonic()
        return self.http.request("GET", url)

    def _cik(self, symbol: str) -> str:
        if self.__class__._ticker_map is None:
            payload = self._request("https://www.sec.gov/files/company_tickers.json")
            mapping: dict[str, str] = {}
            for record in payload.values() if isinstance(payload, dict) else []:
                if isinstance(record, dict) and record.get("ticker") is not None:
                    mapping[str(record["ticker"]).upper()] = str(record["cik_str"]).zfill(10)
            self.__class__._ticker_map = mapping
        cik = self.__class__._ticker_map.get(symbol.upper())
        if not cik:
            raise InvalidSymbolError(symbol)
        return cik

    def _submissions(self, symbol: str) -> dict[str, Any]:
        return self._request(
            f"https://data.sec.gov/submissions/CIK{self._cik(symbol)}.json"
        )

    def _company_facts(self, symbol: str) -> dict[str, Any]:
        return self._request(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{self._cik(symbol)}.json"
        )

    def filings(self, symbol: str, limit: int = 40) -> pd.DataFrame:
        payload = self._submissions(symbol)
        recent = payload.get("filings", {}).get("recent", {})
        frame = pd.DataFrame(recent)
        if frame.empty:
            return frame
        frame = frame.head(limit).copy()
        if "accessionNumber" in frame:
            accession = frame["accessionNumber"].astype(str).str.replace("-", "", regex=False)
            cik = str(int(self._cik(symbol)))
            frame["url"] = [
                f"https://www.sec.gov/Archives/edgar/data/{cik}/{number}/{document}"
                for number, document in zip(accession, frame.get("primaryDocument", ""), strict=False)
            ]
        frame.attrs.update(source="SEC", symbol=symbol.upper(), market="US")
        return frame

    def company_overview(self, symbol: str) -> pd.DataFrame:
        payload = self._submissions(symbol)
        fields = {
            "symbol": symbol.upper(),
            "name": payload.get("name"),
            "cik": payload.get("cik"),
            "sic": payload.get("sic"),
            "sic_description": payload.get("sicDescription"),
            "fiscal_year_end": payload.get("fiscalYearEnd"),
            "exchanges": payload.get("exchanges", []),
        }
        frame = pd.DataFrame([fields])
        frame.attrs.update(source="SEC", symbol=symbol.upper(), market="US")
        return frame

    def _statement_from_payload(
        self,
        symbol: str,
        payload: dict[str, Any],
        tags: set[str],
        period: str,
    ) -> pd.DataFrame:
        facts = payload.get("facts", {}).get("us-gaap", {})
        rows: list[dict[str, Any]] = []
        if period not in {"quarter", "year"}:
            raise ValueError("period must be 'quarter' or 'year'")
        for tag in tags:
            fact = facts.get(tag, {})
            for unit, observations in fact.get("units", {}).items():
                for observation in observations:
                    if self._matches_period(observation, period):
                        rows.append(
                            {
                                "metric": tag,
                                "unit": unit,
                                "value": observation.get("val"),
                                "start": observation.get("start"),
                                "end": observation.get("end"),
                                "filed": observation.get("filed"),
                                "form": observation.get("form"),
                                "fiscal_year": observation.get("fy"),
                                "fiscal_period": observation.get("fp"),
                                "frame": observation.get("frame"),
                                "accession": observation.get("accn"),
                            }
                        )
        frame = pd.DataFrame(rows)
        if not frame.empty:
            frame = (
                frame.sort_values(["end", "filed", "accession"])
                .drop_duplicates(
                    ["metric", "unit", "start", "end"],
                    keep="last",
                )
            )
        frame.attrs.update(source="SEC", symbol=symbol.upper(), market="US")
        return frame.reset_index(drop=True)

    @staticmethod
    def _matches_period(observation: dict[str, Any], period: str) -> bool:
        form = observation.get("form")
        start = observation.get("start")
        end = observation.get("end")
        frame = str(observation.get("frame") or "")
        if not end:
            return False
        if start is None:
            if period == "year":
                return form == "10-K"
            return form in {"10-Q", "10-K"} and (
                bool(re.fullmatch(r"CY\d{4}Q[1-4]I", frame))
                or observation.get("fp") in {"Q1", "Q2", "Q3"}
            )
        try:
            duration = (pd.Timestamp(end) - pd.Timestamp(start)).days
        except (TypeError, ValueError):
            return False
        if period == "year":
            return form == "10-K" and (
                bool(re.fullmatch(r"CY\d{4}", frame))
                or 335 <= duration <= 395
            )
        return form in {"10-Q", "10-K"} and (
            bool(re.fullmatch(r"CY\d{4}Q[1-4]", frame))
            or 61 <= duration <= 121
        )

    def _statement(self, symbol: str, tags: set[str], period: str) -> pd.DataFrame:
        return self._statement_from_payload(
            symbol,
            self._company_facts(symbol),
            tags,
            period,
        )

    def income_statement(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._statement(
            symbol,
            {
                "Revenues",
                "SalesRevenueNet",
                "GrossProfit",
                "OperatingIncomeLoss",
                "NetIncomeLoss",
                "EarningsPerShareDiluted",
            },
            period,
        )

    def balance_sheet(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._statement(
            symbol,
            {
                "Assets",
                "AssetsCurrent",
                "CashAndCashEquivalentsAtCarryingValue",
                "Liabilities",
                "LiabilitiesCurrent",
                "StockholdersEquity",
            },
            period,
        )

    def cash_flow(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._statement(
            symbol,
            {
                "NetCashProvidedByUsedInOperatingActivities",
                "NetCashProvidedByUsedInInvestingActivities",
                "NetCashProvidedByUsedInFinancingActivities",
                "PaymentsToAcquirePropertyPlantAndEquipment",
            },
            period,
        )

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        payload = self._company_facts(symbol)
        statements = pd.concat(
            [
                self._statement_from_payload(
                    symbol,
                    payload,
                    {
                        "Revenues",
                        "SalesRevenueNet",
                        "GrossProfit",
                        "OperatingIncomeLoss",
                        "NetIncomeLoss",
                        "EarningsPerShareDiluted",
                    },
                    period,
                ),
                self._statement_from_payload(
                    symbol,
                    payload,
                    {
                        "Assets",
                        "AssetsCurrent",
                        "CashAndCashEquivalentsAtCarryingValue",
                        "Liabilities",
                        "LiabilitiesCurrent",
                        "StockholdersEquity",
                    },
                    period,
                ),
            ],
            ignore_index=True,
        )
        statements.attrs.update(source="SEC", symbol=symbol.upper(), market="US")
        return statements

    def history(self, symbol: str, start: str, end: str | None = None, interval: str = "1D") -> pd.DataFrame:
        raise NotImplementedError("SEC EDGAR does not provide market prices.")

    def intraday(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("SEC EDGAR does not provide intraday data.")

    def price_board(self, symbols: list[str]) -> pd.DataFrame:
        raise NotImplementedError("SEC EDGAR does not provide quotes.")

    def shareholders(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("SEC EDGAR does not provide a normalized shareholder table.")

    def all_symbols(self, exchange: str | None = None) -> pd.DataFrame:
        raise NotImplementedError("Use SEC company_tickers only for CIK resolution.")

    def symbols_by_group(self, group: str) -> pd.DataFrame:
        raise NotImplementedError("SEC EDGAR does not provide index constituents.")

    def symbols_by_industries(self) -> pd.DataFrame:
        raise NotImplementedError("SEC EDGAR does not provide normalized industries.")

    def price_depth(self, symbol: str) -> pd.DataFrame:
        raise NotImplementedError("SEC EDGAR does not provide order books.")


registry.register_stock(
    "SEC",
    SECStockProvider,
    ProviderDescriptor(
        source="SEC",
        markets={MarketRegion.US},
        capabilities={
            ProviderCapability.COMPANY,
            ProviderCapability.FUNDAMENTALS,
            ProviderCapability.FILINGS,
        },
        requires_auth=True,
        auth_type="user_agent",
        coverage="official-filings",
    ),
)
