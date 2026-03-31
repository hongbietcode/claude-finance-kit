import numpy as np
import pandas as pd


class MomentumIndicators:
    """Momentum technical indicators implemented with numpy/pandas."""

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def rsi(self, length: int = 14) -> pd.Series:
        """Relative Strength Index (RSI).

        Args:
            length: Lookback period. Default 14.

        Returns:
            pd.Series with RSI values in [0, 100].
        """
        close = self._df["close"]
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(com=length - 1, min_periods=length).mean()
        avg_loss = loss.ewm(com=length - 1, min_periods=length).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi.name = f"RSI_{length}"
        return rsi

    def macd(
        self, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.DataFrame:
        """Moving Average Convergence Divergence (MACD).

        Args:
            fast: Fast EMA period. Default 12.
            slow: Slow EMA period. Default 26.
            signal: Signal line EMA period. Default 9.

        Returns:
            pd.DataFrame with columns: MACD, MACD_signal, MACD_hist.
        """
        close = self._df["close"]
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return pd.DataFrame(
            {
                f"MACD_{fast}_{slow}_{signal}": macd_line,
                f"MACDs_{fast}_{slow}_{signal}": signal_line,
                f"MACDh_{fast}_{slow}_{signal}": histogram,
            }
        )

    def stoch(
        self, k: int = 14, d: int = 3, smooth_k: int = 3
    ) -> pd.DataFrame:
        """Stochastic Oscillator.

        Args:
            k: %K lookback period. Default 14.
            d: %D smoothing period. Default 3.
            smooth_k: %K smoothing period. Default 3.

        Returns:
            pd.DataFrame with columns: STOCHk, STOCHd.
        """
        high = self._df["high"]
        low = self._df["low"]
        close = self._df["close"]

        lowest_low = low.rolling(k).min()
        highest_high = high.rolling(k).max()
        raw_k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)

        smooth_k_series = raw_k.rolling(smooth_k).mean()
        d_series = smooth_k_series.rolling(d).mean()

        return pd.DataFrame(
            {
                f"STOCHk_{k}_{d}_{smooth_k}": smooth_k_series,
                f"STOCHd_{k}_{d}_{smooth_k}": d_series,
            }
        )

    def roc(self, length: int = 9) -> pd.Series:
        """Rate of Change (ROC).

        Args:
            length: Lookback period. Default 9.

        Returns:
            pd.Series with ROC values as percentage.
        """
        close = self._df["close"]
        roc = close.pct_change(periods=length) * 100
        roc.name = f"ROC_{length}"
        return roc

    def willr(self, length: int = 14) -> pd.Series:
        """Williams %R.

        Args:
            length: Lookback period. Default 14.

        Returns:
            pd.Series with Williams %R values in [-100, 0].
        """
        high = self._df["high"]
        low = self._df["low"]
        close = self._df["close"]

        highest_high = high.rolling(length).max()
        lowest_low = low.rolling(length).min()

        willr = -100 * (highest_high - close) / (highest_high - lowest_low).replace(0, np.nan)
        willr.name = f"WILLR_{length}"
        return willr

    def mom(self, length: int = 10) -> pd.Series:
        """Momentum (MOM).

        Args:
            length: Lookback period. Default 10.

        Returns:
            pd.Series with momentum values.
        """
        close = self._df["close"]
        mom = close.diff(length)
        mom.name = f"MOM_{length}"
        return mom

    def cmo(self, length: int = 14) -> pd.Series:
        """Chande Momentum Oscillator (CMO).

        Measures the sum of recent gains minus recent losses divided by
        sum of all recent price movement, scaled to [-100, 100].

        Args:
            length: Lookback period. Default 14.

        Returns:
            pd.Series with CMO values in [-100, 100].
        """
        close = self._df["close"]
        delta = close.diff()
        gains = delta.clip(lower=0)
        losses = (-delta).clip(lower=0)

        sum_gains = gains.rolling(window=length).sum()
        sum_losses = losses.rolling(window=length).sum()

        denom = (sum_gains + sum_losses).replace(0, np.nan)
        cmo = 100 * (sum_gains - sum_losses) / denom
        cmo.name = f"CMO_{length}"
        return cmo

    def cci(self, length: int = 20) -> pd.Series:
        """Commodity Channel Index (CCI).

        Measures deviation of typical price from its SMA,
        normalized by mean absolute deviation. Range: unbounded, ±100 as thresholds.

        Args:
            length: Lookback period. Default 20.

        Returns:
            pd.Series with CCI values.
        """
        tp = (self._df["high"] + self._df["low"] + self._df["close"]) / 3
        sma = tp.rolling(window=length).mean()
        mad = tp.rolling(window=length).apply(
            lambda x: np.mean(np.abs(x - np.mean(x))), raw=True
        )
        cci = (tp - sma) / (0.015 * mad.replace(0, np.nan))
        cci.name = f"CCI_{length}"
        return cci

    def tsi(self, long: int = 25, short: int = 13) -> pd.Series:
        """True Strength Index (TSI).

        Double-smoothed momentum oscillator. Range: [-100, 100].

        Args:
            long: Long EMA period. Default 25.
            short: Short EMA period. Default 13.

        Returns:
            pd.Series with TSI values.
        """
        delta = self._df["close"].diff()
        smooth1 = delta.ewm(span=long, adjust=False).mean().ewm(span=short, adjust=False).mean()
        smooth2 = delta.abs().ewm(span=long, adjust=False).mean().ewm(span=short, adjust=False).mean()
        tsi = 100 * smooth1 / smooth2.replace(0, np.nan)
        tsi.name = f"TSI_{long}_{short}"
        return tsi

    def uo(self, fast: int = 7, medium: int = 14, slow: int = 28) -> pd.Series:
        """Ultimate Oscillator (UO).

        Multi-timeframe momentum combining 3 periods. Range: [0, 100].

        Args:
            fast: Short period. Default 7.
            medium: Medium period. Default 14.
            slow: Long period. Default 28.

        Returns:
            pd.Series with UO values.
        """
        close = self._df["close"]
        high = self._df["high"]
        low = self._df["low"]

        prev_close = close.shift(1)
        true_low = pd.concat([low, prev_close], axis=1).min(axis=1)
        true_high = pd.concat([high, prev_close], axis=1).max(axis=1)

        bp = close - true_low
        tr = true_high - true_low

        avg_fast = bp.rolling(fast).sum() / tr.rolling(fast).sum().replace(0, np.nan)
        avg_medium = bp.rolling(medium).sum() / tr.rolling(medium).sum().replace(0, np.nan)
        avg_slow = bp.rolling(slow).sum() / tr.rolling(slow).sum().replace(0, np.nan)

        uo = 100 * (4 * avg_fast + 2 * avg_medium + avg_slow) / 7
        uo.name = f"UO_{fast}_{medium}_{slow}"
        return uo

    def ao(self, fast: int = 5, slow: int = 34) -> pd.Series:
        """Awesome Oscillator (AO).

        Difference between fast and slow SMA of midpoint price.

        Args:
            fast: Fast SMA period. Default 5.
            slow: Slow SMA period. Default 34.

        Returns:
            pd.Series with AO values.
        """
        midpoint = (self._df["high"] + self._df["low"]) / 2
        ao = midpoint.rolling(fast).mean() - midpoint.rolling(slow).mean()
        ao.name = f"AO_{fast}_{slow}"
        return ao
