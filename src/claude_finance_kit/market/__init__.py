"""User-facing market data API."""

import pandas as pd

from claude_finance_kit._provider import fmarket, mbk, spl, vnd  # noqa: F401 — trigger provider registration
from claude_finance_kit._provider._registry import registry


class Market:
    """High-level market data interface delegating to a MarketProvider."""

    def __init__(self, index: str = "VNINDEX", source: str = "VND") -> None:
        self._index = index
        self._provider = registry.get_market(source)()

    def pe(self, duration: str = "5Y") -> pd.DataFrame:
        """P/E ratio history."""
        return self._provider.pe(self._index, duration)

    def pb(self, duration: str = "5Y") -> pd.DataFrame:
        """P/B ratio history."""
        return self._provider.pb(self._index, duration)

    def top_gainer(self, limit: int = 10) -> pd.DataFrame:
        """Top gaining stocks."""
        return self._provider.top_gainer(self._index, limit)

    def top_loser(self, limit: int = 10) -> pd.DataFrame:
        """Top losing stocks."""
        return self._provider.top_loser(self._index, limit)

    def top_liquidity(self, limit: int = 10) -> pd.DataFrame:
        """Top stocks by trading value (liquidity)."""
        return self._provider.top_liquidity(self._index, limit)
