import numpy as np
import pandas as pd


class VolatilityIndicators:
    """Volatility technical indicators implemented with numpy/pandas."""

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def atr(self, length: int = 14) -> pd.Series:
        """Average True Range (ATR).

        Args:
            length: Smoothing period. Default 14.

        Returns:
            pd.Series with ATR values.
        """
        high = self._df["high"]
        low = self._df["low"]
        close = self._df["close"]

        prev_close = close.shift(1)
        tr = pd.concat(
            [
                high - low,
                (high - prev_close).abs(),
                (low - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        atr = tr.ewm(com=length - 1, min_periods=length).mean()
        atr.name = f"ATR_{length}"
        return atr

    def keltner(
        self, length: int = 20, scalar: float = 2.0, mamode: str = "ema"
    ) -> pd.DataFrame:
        """Keltner Channel.

        Args:
            length: Period for the middle band MA and ATR. Default 20.
            scalar: ATR multiplier. Default 2.0.
            mamode: Middle band MA type: 'ema' or 'sma'. Default 'ema'.

        Returns:
            pd.DataFrame with columns: KCLe (lower), KCBe (middle), KCUe (upper).
        """
        close = self._df["close"]

        if mamode.lower() == "sma":
            mid = close.rolling(window=length).mean()
        else:
            mid = close.ewm(span=length, adjust=False).mean()

        atr_series = self.atr(length)
        upper = mid + scalar * atr_series
        lower = mid - scalar * atr_series

        return pd.DataFrame(
            {
                f"KCLe_{length}_{scalar}": lower,
                f"KCBe_{length}_{scalar}": mid,
                f"KCUe_{length}_{scalar}": upper,
            }
        )

    def stdev(self, period: int = 20) -> pd.Series:
        """Rolling Standard Deviation of close prices.

        Args:
            period: Rolling window period. Default 20.

        Returns:
            pd.Series with standard deviation values.
        """
        stdev = self._df["close"].rolling(window=period).std(ddof=1)
        stdev.name = f"STDEV_{period}"
        return stdev

    def linreg(self, period: int = 14) -> pd.Series:
        """Linear Regression value (end-point of OLS line over window).

        Args:
            period: Rolling window period. Default 14.

        Returns:
            pd.Series with linear regression endpoint values.
        """
        close = self._df["close"]
        x = np.arange(period, dtype=float)
        x_mean = x.mean()
        x_var = ((x - x_mean) ** 2).sum()

        def _linreg_val(y: np.ndarray) -> float:
            if len(y) < period or np.isnan(y).any():
                return np.nan
            y_mean = y.mean()
            slope = ((x - x_mean) * (y - y_mean)).sum() / x_var
            intercept = y_mean - slope * x_mean
            return float(slope * (period - 1) + intercept)

        linreg = close.rolling(window=period).apply(_linreg_val, raw=True)
        linreg.name = f"LINREG_{period}"
        return linreg
