"""User-facing commodity price API."""

import pandas as pd

from claude_finance_kit._provider import spl  # noqa: F401 — trigger provider registration
from claude_finance_kit._provider._registry import registry


class Commodity:
    """High-level commodity price interface delegating to a CommodityProvider."""

    def __init__(self, source: str = "SPL") -> None:
        self._provider = registry.get_commodity(source)()

    def gold(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        """Vietnamese and global gold prices."""
        return self._provider.gold(start, end, length)

    def oil(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        """Crude oil and Vietnam gas prices."""
        return self._provider.oil(start, end, length)

    def steel(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        """Steel and iron ore prices."""
        return self._provider.steel(start, end, length)

    def gas(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        """Natural gas and crude oil prices."""
        return self._provider.gas(start, end, length)

    def fertilizer(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        """Fertilizer (urea) prices."""
        return self._provider.fertilizer(start, end, length)

    def agricultural(self, start: str | None = None, end: str | None = None, length: str = "1Y") -> pd.DataFrame:
        """Agricultural commodity prices: soybean, corn, sugar."""
        return self._provider.agricultural(start, end, length)
