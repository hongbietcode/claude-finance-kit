"""Capability-aware opt-in provider routing."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from claude_finance_kit._provider._base import StockProvider
from claude_finance_kit._provider._registry import ProviderRegistry, registry
from claude_finance_kit.core.exceptions import ProviderCapabilityError, RateLimitError
from claude_finance_kit.core.types import MarketRegion, ProviderCapability

_FALLBACK_ERRORS = (ConnectionError, TimeoutError, RateLimitError, NotImplementedError)

_METHOD_CAPABILITIES = {
    "history": ProviderCapability.HISTORICAL_BARS,
    "intraday": ProviderCapability.INTRADAY,
    "price_board": ProviderCapability.PRICE_BOARD,
    "company_overview": ProviderCapability.COMPANY,
    "shareholders": ProviderCapability.COMPANY,
    "officers": ProviderCapability.COMPANY,
    "company_news": ProviderCapability.COMPANY,
    "company_events": ProviderCapability.COMPANY,
    "income_statement": ProviderCapability.FUNDAMENTALS,
    "balance_sheet": ProviderCapability.FUNDAMENTALS,
    "cash_flow": ProviderCapability.FUNDAMENTALS,
    "ratio": ProviderCapability.FUNDAMENTALS,
    "all_symbols": ProviderCapability.LISTING,
    "symbols_by_group": ProviderCapability.LISTING,
    "symbols_by_industries": ProviderCapability.LISTING,
    "price_depth": ProviderCapability.ORDER_BOOK,
    "trades": ProviderCapability.TRADES,
    "order_book": ProviderCapability.ORDER_BOOK,
    "foreign_flow": ProviderCapability.FOREIGN_FLOW,
    "filings": ProviderCapability.FILINGS,
}


class AutoStockProvider(StockProvider):
    """Dispatch each stock operation to a compatible provider.

    Authentication and validation errors intentionally propagate. Only
    transport/rate-limit/unsupported-operation failures advance the chain.
    """

    def __init__(
        self,
        market: MarketRegion | str,
        fallback_sources: list[str] | None = None,
        provider_options: dict[str, dict[str, Any]] | None = None,
        provider_registry: ProviderRegistry | None = None,
    ) -> None:
        self.market = MarketRegion(market)
        self.fallback_sources = [source.upper() for source in fallback_sources] if fallback_sources else None
        self.provider_options = {key.upper(): value for key, value in (provider_options or {}).items()}
        self.registry = provider_registry or registry
        self.last_provenance: dict[str, Any] | None = None

    def _configured(self, source: str) -> bool:
        options = self.provider_options.get(source, {})
        if source == "DNSE":
            return bool(
                (options.get("api_key") or os.getenv("DNSE_API_KEY"))
                and (options.get("api_secret") or os.getenv("DNSE_API_SECRET"))
            )
        if source == "SSI":
            return bool(
                (options.get("consumer_id") or os.getenv("SSI_CONSUMER_ID") or os.getenv("FC_DATA_CONSUMER_ID"))
                and (
                    options.get("consumer_secret")
                    or os.getenv("SSI_CONSUMER_SECRET")
                    or os.getenv("FC_DATA_CONSUMER_SECRET")
                )
            )
        if source == "ALPACA":
            return bool(
                (options.get("api_key") or os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID"))
                and (
                    options.get("api_secret")
                    or os.getenv("ALPACA_API_SECRET")
                    or os.getenv("APCA_API_SECRET_KEY")
                )
            )
        if source == "FMP":
            return bool(options.get("api_key") or os.getenv("FMP_TOKEN") or os.getenv("FMP_API_KEY"))
        if source == "SEC":
            return bool(
                options.get("user_agent")
                or os.getenv("CFK_SEC_USER_AGENT")
                or os.getenv("SEC_USER_AGENT")
            )
        return True

    def _call(self, method: str, *args: Any, **kwargs: Any) -> pd.DataFrame:
        capability = _METHOD_CAPABILITIES[method]
        sources = self.registry.stock_sources_for(
            self.market,
            capability,
            preferred=self.fallback_sources,
        )
        attempted: list[str] = []
        last_error: Exception | None = None

        for source in sources:
            if not self._configured(source):
                continue
            attempted.append(source)
            try:
                provider_cls = self.registry.get_stock(source)
                provider = provider_cls(**self.provider_options.get(source, {}))
                result = getattr(provider, method)(*args, **kwargs)
            except _FALLBACK_ERRORS as exc:
                last_error = exc
                continue

            descriptor = self.registry.get_descriptor(source)
            data_timestamp = None
            if "time" in result and not result.empty:
                parsed = pd.to_datetime(result["time"], utc=True, errors="coerce").dropna()
                if not parsed.empty:
                    data_timestamp = parsed.max().isoformat()
            provenance = {
                "source": source,
                "attempted_sources": attempted.copy(),
                "market": self.market.value,
                "fetched_at": datetime.now(UTC).isoformat(),
                "data_timestamp": data_timestamp,
                "delayed_seconds": descriptor.delayed_seconds,
                "coverage": descriptor.coverage,
            }
            result.attrs.update(provenance)
            self.last_provenance = provenance
            return result

        if last_error is not None:
            raise ProviderCapabilityError(capability.value, self.market.value, attempted) from last_error
        raise ProviderCapabilityError(capability.value, self.market.value, attempted)

    def history(self, symbol: str, start: str, end: str | None = None, interval: str = "1D") -> pd.DataFrame:
        return self._call("history", symbol, start, end, interval)

    def intraday(self, symbol: str) -> pd.DataFrame:
        return self._call("intraday", symbol)

    def price_board(self, symbols: list[str]) -> pd.DataFrame:
        return self._call("price_board", symbols)

    def company_overview(self, symbol: str) -> pd.DataFrame:
        return self._call("company_overview", symbol)

    def shareholders(self, symbol: str) -> pd.DataFrame:
        return self._call("shareholders", symbol)

    def officers(self, symbol: str, **kwargs: Any) -> pd.DataFrame:
        return self._call("officers", symbol, **kwargs)

    def company_news(self, symbol: str, **kwargs: Any) -> pd.DataFrame:
        return self._call("company_news", symbol, **kwargs)

    def company_events(self, symbol: str, **kwargs: Any) -> pd.DataFrame:
        return self._call("company_events", symbol, **kwargs)

    def income_statement(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._call("income_statement", symbol, period)

    def balance_sheet(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._call("balance_sheet", symbol, period)

    def cash_flow(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._call("cash_flow", symbol, period)

    def ratio(self, symbol: str, period: str = "quarter") -> pd.DataFrame:
        return self._call("ratio", symbol, period)

    def all_symbols(self, exchange: str | None = None) -> pd.DataFrame:
        return self._call("all_symbols", exchange)

    def symbols_by_group(self, group: str) -> pd.DataFrame:
        return self._call("symbols_by_group", group)

    def symbols_by_industries(self) -> pd.DataFrame:
        return self._call("symbols_by_industries")

    def price_depth(self, symbol: str) -> pd.DataFrame:
        return self._call("price_depth", symbol)

    def trades(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        return self._call("trades", symbol, start, end, limit)

    def order_book(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        return self._call("order_book", symbol, start, end, limit)

    def foreign_flow(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        return self._call("foreign_flow", symbol, start, end)

    def filings(self, symbol: str, limit: int = 40) -> pd.DataFrame:
        return self._call("filings", symbol, limit)
