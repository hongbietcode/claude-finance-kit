"""Unified public facade for Vietnamese bond market data."""

from typing import Any

import pandas as pd

from claude_finance_kit._internal.parser import get_asset_type
from claude_finance_kit._provider import kbs, vci  # noqa: F401 -- trigger provider registration
from claude_finance_kit._provider._registry import registry


def _symbols(value: Any) -> pd.Series:
    if isinstance(value, pd.Series):
        series = value
    elif isinstance(value, pd.DataFrame) and "symbol" in value.columns:
        series = value["symbol"]
    else:
        series = pd.Series(value, dtype="object")
    return series.dropna().astype(str).str.upper().drop_duplicates().reset_index(drop=True)


class Bond:
    """Bond listing and market-data facade using existing stock providers."""

    def __init__(self, symbol: str | None = None, source: str = "VCI", **kwargs) -> None:
        self._symbol = symbol.upper() if symbol else None
        self._source = source.upper()
        self._provider = registry.get_stock(self._source)(**kwargs)
        if self._symbol is not None:
            self._validate_symbol(self._symbol)

    @staticmethod
    def _validate_symbol(symbol: str) -> str:
        normalized = symbol.upper()
        if get_asset_type(normalized) != "bond":
            raise ValueError(f"'{symbol}' is not a recognized bond symbol.")
        return normalized

    def _target(self, symbol: str | None) -> str:
        target = symbol or self._symbol
        if target is None:
            raise ValueError("A bond symbol is required for this operation.")
        return self._validate_symbol(target)

    def list(self, bond_type: str = "all") -> pd.DataFrame:
        """List corporate, government, or all bonds supported by the provider."""
        if bond_type not in {"all", "corporate", "government"}:
            raise ValueError("bond_type must be 'all', 'corporate', or 'government'.")

        frames: list[pd.DataFrame] = []
        unsupported_types: list[str] = []
        if bond_type in {"all", "corporate"}:
            corporate = _symbols(self._provider.symbols_by_group("BOND"))
            frames.append(pd.DataFrame({"symbol": corporate, "type": "corporate"}))
        if bond_type in {"all", "government"}:
            try:
                government = _symbols(self._provider.symbols_by_group("FU_BOND"))
            except NotImplementedError:
                if bond_type == "government":
                    raise
                unsupported_types.append("government")
                government = pd.Series(dtype="object")
            frames.append(pd.DataFrame({"symbol": government, "type": "government"}))

        result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["symbol", "type"])
        result.attrs["source"] = self._source
        result.attrs["unsupported_types"] = unsupported_types
        return result

    def ohlcv(
        self,
        symbol: str | None = None,
        start: str | None = None,
        end: str | None = None,
        interval: str = "1D",
    ) -> pd.DataFrame:
        """Return historical OHLCV for a bond."""
        if start is None:
            raise ValueError("start is required and must use YYYY-MM-DD format.")
        return self._provider.history(self._target(symbol), start, end, interval)

    def trades(self, symbol: str | None = None) -> pd.DataFrame:
        """Return recent matched trades for a bond."""
        return self._provider.intraday(self._target(symbol))

    def quote(self, symbol: str | None = None) -> pd.DataFrame:
        """Return the current quote row for a bond."""
        return self._provider.price_board([self._target(symbol)])

    def __repr__(self) -> str:
        return f"Bond(symbol={self._symbol!r}, source={self._source!r})"


__all__ = ["Bond"]
