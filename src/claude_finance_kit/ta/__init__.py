import pandas as pd

from claude_finance_kit.ta.momentum import MomentumIndicators
from claude_finance_kit.ta.trend import TrendIndicators
from claude_finance_kit.ta.volatility import VolatilityIndicators
from claude_finance_kit.ta.volume import VolumeIndicators

__all__ = ["Indicator"]


class Indicator:
    """Technical analysis indicator hub.

    Provides access to momentum, trend, volatility, and volume indicators
    via namespaced sub-objects.

    Args:
        df: DataFrame with OHLCV columns: open, high, low, close, volume.

    Example:
        ind = Indicator(df)
        ind.trend.sma(20)
        ind.momentum.rsi(14)
        ind.volatility.atr(14)
        ind.volume.obv()
    """

    def __init__(self, df: pd.DataFrame):
        self._df = df
        self.trend = TrendIndicators(df)
        self.momentum = MomentumIndicators(df)
        self.volatility = VolatilityIndicators(df)
        self.volume = VolumeIndicators(df)
