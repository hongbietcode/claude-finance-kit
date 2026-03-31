import numpy as np
import pandas as pd


class TrendIndicators:
    """Trend technical indicators implemented with numpy/pandas."""

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def sma(self, length: int = 14) -> pd.Series:
        """Simple Moving Average (SMA).

        Args:
            length: Rolling window period. Default 14.

        Returns:
            pd.Series with SMA values.
        """
        sma = self._df["close"].rolling(window=length).mean()
        sma.name = f"SMA_{length}"
        return sma

    def ema(self, length: int = 14) -> pd.Series:
        """Exponential Moving Average (EMA).

        Args:
            length: Span period. Default 14.

        Returns:
            pd.Series with EMA values.
        """
        ema = self._df["close"].ewm(span=length, adjust=False).mean()
        ema.name = f"EMA_{length}"
        return ema

    def wma(self, length: int = 14) -> pd.Series:
        """Weighted Moving Average (WMA).

        Args:
            length: Rolling window period. Default 14.

        Returns:
            pd.Series with WMA values.
        """
        weights = np.arange(1, length + 1, dtype=float)

        def _wma(x: np.ndarray) -> float:
            if len(x) < length:
                return np.nan
            return float(np.dot(x, weights) / weights.sum())

        wma = self._df["close"].rolling(window=length).apply(_wma, raw=True)
        wma.name = f"WMA_{length}"
        return wma

    def bbands(self, length: int = 20, std: float = 2.0) -> pd.DataFrame:
        """Bollinger Bands.

        Args:
            length: Rolling window period. Default 20.
            std: Number of standard deviations. Default 2.0.

        Returns:
            pd.DataFrame with columns: BBL (lower), BBM (middle), BBU (upper), BBB (bandwidth), BBP (percent).
        """
        close = self._df["close"]
        mid = close.rolling(window=length).mean()
        stdev = close.rolling(window=length).std(ddof=0)
        upper = mid + std * stdev
        lower = mid - std * stdev
        bandwidth = (upper - lower) / mid.replace(0, np.nan)
        percent = (close - lower) / (upper - lower).replace(0, np.nan)

        return pd.DataFrame(
            {
                f"BBL_{length}_{std}": lower,
                f"BBM_{length}_{std}": mid,
                f"BBU_{length}_{std}": upper,
                f"BBB_{length}_{std}": bandwidth,
                f"BBP_{length}_{std}": percent,
            }
        )

    def ichimoku(
        self,
        tenkan: int = 9,
        kijun: int = 26,
        senkou_b: int = 52,
        displacement: int = 26,
    ) -> pd.DataFrame:
        """Ichimoku Cloud.

        Args:
            tenkan: Tenkan-sen (conversion line) period. Default 9.
            kijun: Kijun-sen (base line) period. Default 26.
            senkou_b: Senkou Span B period. Default 52.
            displacement: Cloud displacement (chikou offset). Default 26.

        Returns:
            pd.DataFrame with Ichimoku components.
        """
        high = self._df["high"]
        low = self._df["low"]
        close = self._df["close"]

        def _midpoint(h: pd.Series, lo: pd.Series, period: int) -> pd.Series:
            return (h.rolling(period).max() + lo.rolling(period).min()) / 2

        tenkan_sen = _midpoint(high, low, tenkan)
        kijun_sen = _midpoint(high, low, kijun)
        senkou_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
        senkou_b_line = _midpoint(high, low, senkou_b).shift(displacement)
        chikou = close.shift(-displacement)

        return pd.DataFrame(
            {
                "ITS": tenkan_sen,
                "IKS": kijun_sen,
                "ISA": senkou_a,
                "ISB": senkou_b_line,
                "ICS": chikou,
            }
        )

    def adx(self, period: int = 14) -> pd.DataFrame:
        """Average Directional Index (ADX) with +DI and -DI.

        Args:
            period: Smoothing period. Default 14.

        Returns:
            pd.DataFrame with columns: ADX, DMP (Plus DI), DMN (Minus DI).
        """
        high = self._df["high"]
        low = self._df["low"]
        close = self._df["close"]

        prev_high = high.shift(1)
        prev_low = low.shift(1)
        prev_close = close.shift(1)

        up_move = high - prev_high
        down_move = prev_low - low

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        tr = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
            axis=1,
        ).max(axis=1)

        atr = tr.ewm(com=period - 1, min_periods=period).mean()
        safe_atr = atr.replace(0, np.nan)
        plus_dm_s = pd.Series(plus_dm, index=close.index)
        minus_dm_s = pd.Series(minus_dm, index=close.index)
        plus_di = 100 * plus_dm_s.ewm(com=period - 1, min_periods=period).mean() / safe_atr
        minus_di = 100 * minus_dm_s.ewm(com=period - 1, min_periods=period).mean() / safe_atr

        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.ewm(com=period - 1, min_periods=period).mean()

        return pd.DataFrame(
            {
                f"ADX_{period}": adx,
                f"DMP_{period}": plus_di,
                f"DMN_{period}": minus_di,
            }
        )

    def aroon(self, period: int = 25) -> pd.DataFrame:
        """Aroon Up/Down indicator.

        Args:
            period: Lookback period. Default 25.

        Returns:
            pd.DataFrame with columns: AROONU (Up), AROOND (Down).
        """
        high = self._df["high"]
        low = self._df["low"]

        aroon_up = high.rolling(period + 1).apply(
            lambda x: float(np.argmax(x)) / period * 100, raw=True
        )
        aroon_down = low.rolling(period + 1).apply(
            lambda x: float(np.argmin(x)) / period * 100, raw=True
        )

        return pd.DataFrame(
            {
                f"AROONU_{period}": aroon_up,
                f"AROOND_{period}": aroon_down,
            }
        )

    def psar(self, af: float = 0.02, max_af: float = 0.2) -> pd.DataFrame:
        """Parabolic SAR.

        Args:
            af: Acceleration factor starting value. Default 0.02.
            max_af: Maximum acceleration factor. Default 0.2.

        Returns:
            pd.DataFrame with columns: PSARl (long/bullish), PSARs (short/bearish), PSARaf, PSARr (reversal flag).
        """
        high = self._df["high"].values
        low = self._df["low"].values
        n = len(high)

        psar = np.full(n, np.nan)
        psar_af = np.full(n, np.nan)
        psar_reversal = np.zeros(n, dtype=int)
        long_vals = np.full(n, np.nan)
        short_vals = np.full(n, np.nan)

        bull = True
        current_af = af
        ep = low[0]
        hp = high[0]
        lp = low[0]

        psar[0] = lp
        psar_af[0] = current_af

        for i in range(1, n):
            if bull:
                psar[i] = psar[i - 1] + current_af * (hp - psar[i - 1])
                psar[i] = min(psar[i], low[i - 1], low[max(0, i - 2)])

                if low[i] < psar[i]:
                    bull = False
                    psar[i] = hp
                    lp = low[i]
                    ep = lp
                    current_af = af
                    psar_reversal[i] = 1
                else:
                    if high[i] > ep:
                        ep = high[i]
                        current_af = min(current_af + af, max_af)
                    hp = max(hp, high[i])
                    long_vals[i] = psar[i]
            else:
                psar[i] = psar[i - 1] - current_af * (psar[i - 1] - lp)
                psar[i] = max(psar[i], high[i - 1], high[max(0, i - 2)])

                if high[i] > psar[i]:
                    bull = True
                    psar[i] = lp
                    hp = high[i]
                    ep = hp
                    current_af = af
                    psar_reversal[i] = 1
                else:
                    if low[i] < ep:
                        ep = low[i]
                        current_af = min(current_af + af, max_af)
                    lp = min(lp, low[i])
                    short_vals[i] = psar[i]

            psar_af[i] = current_af

        idx = self._df.index
        return pd.DataFrame(
            {
                "PSARl": long_vals,
                "PSARs": short_vals,
                "PSARaf": psar_af,
                "PSARr": psar_reversal.astype(float),
            },
            index=idx,
        )

    def supertrend(self, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
        """SuperTrend indicator.

        Args:
            period: ATR period. Default 10.
            multiplier: ATR band multiplier. Default 3.0.

        Returns:
            pd.DataFrame with columns: SUPERT (line), SUPERTd (direction: 1 up, -1 down),
                SUPERTl (long signal), SUPERTs (short signal).
        """
        high = self._df["high"]
        low = self._df["low"]
        close = self._df["close"]

        prev_close = close.shift(1)
        tr = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
            axis=1,
        ).max(axis=1)
        atr = tr.ewm(com=period - 1, min_periods=period).mean()

        hl2 = (high + low) / 2
        upper_band = hl2 + multiplier * atr
        lower_band = hl2 - multiplier * atr

        n = len(close)
        supertrend = np.full(n, np.nan)
        direction = np.zeros(n, dtype=int)
        final_upper = upper_band.values.copy()
        final_lower = lower_band.values.copy()
        close_arr = close.values

        for i in range(1, n):
            if np.isnan(atr.iloc[i]):
                continue

            prev_upper = final_upper[i - 1]
            prev_lower = final_lower[i - 1]
            prev_close_val = close_arr[i - 1]
            final_upper[i] = (
                upper_band.iloc[i]
                if upper_band.iloc[i] < prev_upper or prev_close_val > prev_upper
                else prev_upper
            )
            final_lower[i] = (
                lower_band.iloc[i]
                if lower_band.iloc[i] > prev_lower or prev_close_val < prev_lower
                else prev_lower
            )

            if np.isnan(supertrend[i - 1]):
                direction[i] = 1
                supertrend[i] = final_lower[i]
            elif supertrend[i - 1] == final_upper[i - 1]:
                direction[i] = 1 if close_arr[i] > final_upper[i] else -1
            else:
                direction[i] = -1 if close_arr[i] < final_lower[i] else 1

            supertrend[i] = final_lower[i] if direction[i] == 1 else final_upper[i]

        idx = self._df.index
        col_base = f"{period}_{multiplier}"
        supert_series = pd.Series(supertrend, index=idx, name=f"SUPERT_{col_base}")
        dir_series = pd.Series(direction.astype(float), index=idx, name=f"SUPERTd_{col_base}")
        long_vals = np.where(direction == 1, supertrend, np.nan)
        short_vals = np.where(direction == -1, supertrend, np.nan)
        long_series = pd.Series(long_vals, index=idx, name=f"SUPERTl_{col_base}")
        short_series = pd.Series(short_vals, index=idx, name=f"SUPERTs_{col_base}")

        return pd.DataFrame(
            {
                supert_series.name: supert_series,
                dir_series.name: dir_series,
                long_series.name: long_series,
                short_series.name: short_series,
            }
        )

    def vwma(self, period: int = 20) -> pd.Series:
        """Volume Weighted Moving Average (VWMA).

        Args:
            period: Rolling window period. Default 20.

        Returns:
            pd.Series with VWMA values.
        """
        close = self._df["close"]
        volume = self._df["volume"]

        pv = close * volume
        vwma = pv.rolling(window=period).sum() / volume.rolling(window=period).sum().replace(0, np.nan)
        vwma.name = f"VWMA_{period}"
        return vwma

    def dema(self, length: int = 14) -> pd.Series:
        """Double Exponential Moving Average (DEMA).

        Reduces lag compared to standard EMA: 2*EMA - EMA(EMA).

        Args:
            length: EMA period. Default 14.

        Returns:
            pd.Series with DEMA values.
        """
        close = self._df["close"]
        ema1 = close.ewm(span=length, adjust=False).mean()
        ema2 = ema1.ewm(span=length, adjust=False).mean()
        dema = 2 * ema1 - ema2
        dema.name = f"DEMA_{length}"
        return dema

    def tema(self, length: int = 14) -> pd.Series:
        """Triple Exponential Moving Average (TEMA).

        Further lag reduction: 3*EMA - 3*EMA(EMA) + EMA(EMA(EMA)).

        Args:
            length: EMA period. Default 14.

        Returns:
            pd.Series with TEMA values.
        """
        close = self._df["close"]
        ema1 = close.ewm(span=length, adjust=False).mean()
        ema2 = ema1.ewm(span=length, adjust=False).mean()
        ema3 = ema2.ewm(span=length, adjust=False).mean()
        tema = 3 * ema1 - 3 * ema2 + ema3
        tema.name = f"TEMA_{length}"
        return tema

    def donchian(self, period: int = 20) -> pd.DataFrame:
        """Donchian Channel.

        Highest high and lowest low over N periods, with midline.

        Args:
            period: Lookback period. Default 20.

        Returns:
            pd.DataFrame with columns: DCL (lower), DCM (mid), DCU (upper).
        """
        upper = self._df["high"].rolling(window=period).max()
        lower = self._df["low"].rolling(window=period).min()
        mid = (upper + lower) / 2

        return pd.DataFrame(
            {
                f"DCL_{period}": lower,
                f"DCM_{period}": mid,
                f"DCU_{period}": upper,
            }
        )
