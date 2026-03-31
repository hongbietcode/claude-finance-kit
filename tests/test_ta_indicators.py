"""Test technical analysis indicators with pure math (no mocks)."""

import numpy as np
import pandas as pd
import pytest

from claude_finance_kit.ta import Indicator


@pytest.fixture
def sample_ohlcv_df():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    data = {
        "open": np.random.uniform(100, 110, 100),
        "high": np.random.uniform(110, 120, 100),
        "low": np.random.uniform(90, 100, 100),
        "close": np.random.uniform(100, 110, 100),
        "volume": np.random.uniform(1000000, 5000000, 100),
    }
    df = pd.DataFrame(data, index=dates)
    df = df.sort_index()
    df["close"] = df["close"].astype(float)
    return df


@pytest.fixture
def known_trend_data():
    """Create data with known trend for testing."""
    n = 50
    close_prices = np.arange(100, 100 + n, dtype=float)
    data = {
        "open": close_prices - 0.5,
        "high": close_prices + 1,
        "low": close_prices - 1,
        "close": close_prices,
        "volume": np.full(n, 1000000),
    }
    return pd.DataFrame(data)


class TestIndicatorInitialization:
    """Test Indicator class initialization."""

    def test_indicator_creation(self, sample_ohlcv_df):
        """Indicator can be created with OHLCV DataFrame."""
        ind = Indicator(sample_ohlcv_df)
        assert ind is not None
        assert hasattr(ind, 'trend')
        assert hasattr(ind, 'momentum')
        assert hasattr(ind, 'volatility')
        assert hasattr(ind, 'volume')

    def test_indicator_sub_objects_exist(self, sample_ohlcv_df):
        """Indicator has sub-objects for each indicator type."""
        ind = Indicator(sample_ohlcv_df)
        assert ind.trend is not None
        assert ind.momentum is not None
        assert ind.volatility is not None
        assert ind.volume is not None


class TestTrendIndicators:
    """Test trend indicators."""

    def test_sma_calculation(self, sample_ohlcv_df):
        """SMA can be calculated."""
        ind = Indicator(sample_ohlcv_df)
        sma = ind.trend.sma(20)

        assert isinstance(sma, pd.Series)
        assert len(sma) == len(sample_ohlcv_df)
        assert sma.name == "SMA_20"

    def test_sma_first_values_nan(self, sample_ohlcv_df):
        """SMA has NaN for first period - 1 rows."""
        ind = Indicator(sample_ohlcv_df)
        sma = ind.trend.sma(20)

        assert pd.isna(sma.iloc[0:19]).all()

    def test_sma_different_periods(self, sample_ohlcv_df):
        """SMA with different periods produces different results."""
        ind = Indicator(sample_ohlcv_df)
        sma_10 = ind.trend.sma(10)
        sma_20 = ind.trend.sma(20)

        not_equal = (sma_10 != sma_20).sum()
        assert not_equal > 0

    def test_ema_calculation(self, sample_ohlcv_df):
        """EMA can be calculated."""
        ind = Indicator(sample_ohlcv_df)
        ema = ind.trend.ema(14)

        assert isinstance(ema, pd.Series)
        assert len(ema) == len(sample_ohlcv_df)
        assert ema.name == "EMA_14"

    def test_ema_has_valid_values(self, sample_ohlcv_df):
        """EMA produces valid numeric values."""
        ind = Indicator(sample_ohlcv_df)
        ema = ind.trend.ema(14)

        valid_values = ema[~pd.isna(ema)]
        assert len(valid_values) > 0
        assert all(np.isfinite(valid_values))

    def test_wma_calculation(self, sample_ohlcv_df):
        """WMA can be calculated."""
        ind = Indicator(sample_ohlcv_df)
        wma = ind.trend.wma(14)

        assert isinstance(wma, pd.Series)
        assert len(wma) == len(sample_ohlcv_df)


class TestMomentumIndicators:
    """Test momentum indicators."""

    def test_rsi_calculation(self, sample_ohlcv_df):
        """RSI can be calculated."""
        ind = Indicator(sample_ohlcv_df)
        rsi = ind.momentum.rsi(14)

        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(sample_ohlcv_df)
        assert rsi.name == "RSI_14"

    def test_rsi_bounds(self, sample_ohlcv_df):
        """RSI values are in valid range [0, 100]."""
        ind = Indicator(sample_ohlcv_df)
        rsi = ind.momentum.rsi(14)

        valid_rsi = rsi[~pd.isna(rsi)]
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_rsi_different_periods(self, sample_ohlcv_df):
        """RSI with different periods produces different results."""
        ind = Indicator(sample_ohlcv_df)
        rsi_7 = ind.momentum.rsi(7)
        rsi_14 = ind.momentum.rsi(14)

        not_equal = (rsi_7 != rsi_14).sum()
        assert not_equal > 0

    def test_macd_calculation(self, sample_ohlcv_df):
        """MACD can be calculated."""
        ind = Indicator(sample_ohlcv_df)
        macd = ind.momentum.macd()

        assert isinstance(macd, pd.DataFrame)
        assert len(macd) == len(sample_ohlcv_df)
        assert macd.shape[1] == 3

    def test_macd_columns(self, sample_ohlcv_df):
        """MACD has three columns: line, signal, histogram."""
        ind = Indicator(sample_ohlcv_df)
        macd = ind.momentum.macd()

        columns = macd.columns.tolist()
        assert any("MACD_" in str(col) for col in columns)
        assert any("MACDs_" in str(col) for col in columns)
        assert any("MACDh_" in str(col) for col in columns)

    def test_stoch_calculation(self, sample_ohlcv_df):
        """Stochastic Oscillator can be calculated."""
        ind = Indicator(sample_ohlcv_df)
        stoch = ind.momentum.stoch()

        assert isinstance(stoch, pd.DataFrame)
        assert len(stoch) == len(sample_ohlcv_df)


class TestVolatilityIndicators:
    """Test volatility indicators."""

    def test_atr_calculation(self, sample_ohlcv_df):
        """ATR can be calculated."""
        ind = Indicator(sample_ohlcv_df)
        atr = ind.volatility.atr(14)

        assert isinstance(atr, pd.Series)
        assert len(atr) == len(sample_ohlcv_df)

    def test_atr_positive_values(self, sample_ohlcv_df):
        """ATR values are non-negative."""
        ind = Indicator(sample_ohlcv_df)
        atr = ind.volatility.atr(14)

        valid_atr = atr[~pd.isna(atr)]
        assert (valid_atr >= 0).all()

    def test_keltner_bands_calculation(self, sample_ohlcv_df):
        """Keltner Bands can be calculated."""
        ind = Indicator(sample_ohlcv_df)
        kc = ind.volatility.keltner(20, 2)

        assert isinstance(kc, pd.DataFrame)
        assert len(kc) == len(sample_ohlcv_df)


class TestVolumeIndicators:
    """Test volume indicators."""

    def test_obv_calculation(self, sample_ohlcv_df):
        """OBV can be calculated."""
        ind = Indicator(sample_ohlcv_df)
        obv = ind.volume.obv()

        assert isinstance(obv, pd.Series)
        assert len(obv) == len(sample_ohlcv_df)

    def test_obv_returns_numbers(self, sample_ohlcv_df):
        """OBV returns numeric values."""
        ind = Indicator(sample_ohlcv_df)
        obv = ind.volume.obv()

        valid_obv = obv[~pd.isna(obv)]
        assert len(valid_obv) > 0
        assert all(np.isfinite(valid_obv))

    def test_mfi_calculation(self, sample_ohlcv_df):
        """Money Flow Index can be calculated."""
        ind = Indicator(sample_ohlcv_df)
        mfi = ind.volume.mfi()

        assert isinstance(mfi, pd.Series)
        assert len(mfi) == len(sample_ohlcv_df)


class TestIndicatorEdgeCases:
    """Test indicator edge cases and error handling."""

    def test_indicator_with_missing_values(self):
        """Indicator handles DataFrames with some NaN values."""
        df = pd.DataFrame({
            "open": [100, 101, np.nan, 103],
            "high": [102, 103, 104, np.nan],
            "low": [99, 100, 101, 102],
            "close": [101, 102, 103, 104],
            "volume": [1000000, 1100000, 1200000, 1300000],
        })
        ind = Indicator(df)
        sma = ind.trend.sma(2)
        assert isinstance(sma, pd.Series)

    def test_indicator_with_small_dataset(self):
        """Indicator works with small datasets."""
        df = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 102, 103],
            "volume": [1000000, 1100000, 1200000],
        })
        ind = Indicator(df)
        sma = ind.trend.sma(2)
        assert len(sma) == 3
