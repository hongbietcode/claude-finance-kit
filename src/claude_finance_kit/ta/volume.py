import numpy as np
import pandas as pd


class VolumeIndicators:
    """Volume technical indicators implemented with numpy/pandas."""

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def obv(self) -> pd.Series:
        """On-Balance Volume (OBV).

        Returns:
            pd.Series with cumulative OBV values.
        """
        close = self._df["close"]
        volume = self._df["volume"]

        direction = np.sign(close.diff()).fillna(0)
        obv = (direction * volume).cumsum()
        obv.name = "OBV"
        return obv

    def vwap(self) -> pd.Series:
        """Volume Weighted Average Price (VWAP).

        Calculated as a cumulative VWAP over the entire series.

        Returns:
            pd.Series with VWAP values.
        """
        high = self._df["high"]
        low = self._df["low"]
        close = self._df["close"]
        volume = self._df["volume"]

        typical_price = (high + low + close) / 3
        cum_tp_vol = (typical_price * volume).cumsum()
        cum_vol = volume.cumsum()
        vwap = cum_tp_vol / cum_vol.replace(0, np.nan)
        vwap.name = "VWAP"
        return vwap

    def mfi(self, length: int = 14) -> pd.Series:
        """Money Flow Index (MFI).

        Args:
            length: Lookback period. Default 14.

        Returns:
            pd.Series with MFI values in [0, 100].
        """
        high = self._df["high"]
        low = self._df["low"]
        close = self._df["close"]
        volume = self._df["volume"]

        typical_price = (high + low + close) / 3
        raw_money_flow = typical_price * volume

        tp_diff = typical_price.diff()
        pos_flow = raw_money_flow.where(tp_diff > 0, 0.0)
        neg_flow = raw_money_flow.where(tp_diff < 0, 0.0)

        pos_sum = pos_flow.rolling(length).sum()
        neg_sum = neg_flow.rolling(length).sum()

        mfr = pos_sum / neg_sum.replace(0, np.nan)
        mfi = 100 - (100 / (1 + mfr))
        mfi.name = f"MFI_{length}"
        return mfi
