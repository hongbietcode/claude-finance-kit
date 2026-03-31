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

    def adl(self) -> pd.Series:
        """Accumulation/Distribution Line (ADL).

        Combines price and volume to show money flow direction.

        Returns:
            pd.Series with cumulative ADL values.
        """
        high = self._df["high"]
        low = self._df["low"]
        close = self._df["close"]
        volume = self._df["volume"]

        hl_range = (high - low).replace(0, np.nan)
        clv = ((close - low) - (high - close)) / hl_range
        adl = (clv * volume).cumsum()
        adl.name = "ADL"
        return adl

    def cmf(self, length: int = 20) -> pd.Series:
        """Chaikin Money Flow (CMF).

        Rolling sum of money flow volume / rolling sum of volume. Range: [-1, 1].

        Args:
            length: Lookback period. Default 20.

        Returns:
            pd.Series with CMF values.
        """
        high = self._df["high"]
        low = self._df["low"]
        close = self._df["close"]
        volume = self._df["volume"]

        hl_range = (high - low).replace(0, np.nan)
        clv = ((close - low) - (high - close)) / hl_range
        mfv = clv * volume

        cmf = mfv.rolling(length).sum() / volume.rolling(length).sum().replace(0, np.nan)
        cmf.name = f"CMF_{length}"
        return cmf

    def pvt(self) -> pd.Series:
        """Price Volume Trend (PVT).

        Cumulative volume weighted by percentage price change.

        Returns:
            pd.Series with cumulative PVT values.
        """
        close = self._df["close"]
        volume = self._df["volume"]

        pct = close.pct_change()
        pvt = (pct * volume).cumsum()
        pvt.name = "PVT"
        return pvt

    def emv(self, length: int = 14) -> pd.Series:
        """Ease of Movement (EMV).

        Relates price change to volume, smoothed by SMA.

        Args:
            length: Smoothing period. Default 14.

        Returns:
            pd.Series with EMV values.
        """
        high = self._df["high"]
        low = self._df["low"]
        volume = self._df["volume"]

        distance = ((high + low) / 2) - ((high.shift(1) + low.shift(1)) / 2)
        box_ratio = (volume / 1e6) / (high - low).replace(0, np.nan)
        emv_raw = distance / box_ratio.replace(0, np.nan)
        emv = emv_raw.rolling(window=length).mean()
        emv.name = f"EMV_{length}"
        return emv
