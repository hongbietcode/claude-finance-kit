# Technical Analysis Module

The `claude_finance_kit.ta` module provides common technical indicators built on top of numpy and pandas. No external TA library is required.

## Setup

```python
from claude_finance_kit import Stock
from claude_finance_kit.ta import Indicator

stock = Stock("FPT")
df = stock.quote.history(start="2024-01-01")

ind = Indicator(df.set_index('time'))
```

Input DataFrame must have `open`, `high`, `low`, `close`, `volume` columns with a DatetimeIndex.

## Trend Indicators

Access via `ind.trend`.

| Method | Return | Description |
|--------|--------|-------------|
| `sma(length=14)` | Series | Simple Moving Average |
| `ema(length=14)` | Series | Exponential Moving Average |
| `wma(length=14)` | Series | Weighted Moving Average |
| `bbands(length=20, std=2.0)` | DataFrame | Bollinger Bands (BBL, BBM, BBU, BBB, BBP) |
| `ichimoku(tenkan=9, kijun=26, senkou_b=52, displacement=26)` | DataFrame | Ichimoku Cloud (ITS, IKS, ISA, ISB, ICS) |
| `adx(period=14)` | DataFrame | Average Directional Index with DMP and DMN |
| `aroon(period=25)` | DataFrame | Aroon Up/Down (AROONU, AROOND) |
| `psar(af=0.02, max_af=0.2)` | DataFrame | Parabolic SAR (PSARl, PSARs, PSARaf, PSARr) |
| `supertrend(period=10, multiplier=3.0)` | DataFrame | Supertrend (SUPERT, SUPERTd, SUPERTl, SUPERTs) |
| `vwma(period=20)` | Series | Volume Weighted Moving Average |
| `dema(length=14)` | Series | Double Exponential MA (less lag) |
| `tema(length=14)` | Series | Triple Exponential MA (least lag) |
| `donchian(period=20)` | DataFrame | Donchian Channel (DCL, DCM, DCU) |

## Momentum Indicators

Access via `ind.momentum`.

| Method | Return | Description |
|--------|--------|-------------|
| `rsi(length=14)` | Series | Relative Strength Index [0-100] |
| `macd(fast=12, slow=26, signal=9)` | DataFrame | MACD line, signal, histogram (MACD, MACDs, MACDh) |
| `stoch(k=14, d=3, smooth_k=3)` | DataFrame | Stochastic Oscillator (STOCHk, STOCHd) |
| `roc(length=9)` | Series | Rate of Change (%) |
| `willr(length=14)` | Series | Williams %R [-100, 0] |
| `mom(length=10)` | Series | Momentum |
| `cmo(length=14)` | Series | Chande Momentum Oscillator [-100, 100] |
| `cci(length=20)` | Series | Commodity Channel Index (unbounded, ±100 thresholds) |
| `tsi(long=25, short=13)` | Series | True Strength Index [-100, 100] |
| `uo(fast=7, medium=14, slow=28)` | Series | Ultimate Oscillator [0-100] |
| `ao(fast=5, slow=34)` | Series | Awesome Oscillator (unbounded) |

## Volatility Indicators

Access via `ind.volatility`.

| Method | Return | Description |
|--------|--------|-------------|
| `atr(length=14)` | Series | Average True Range |
| `keltner(length=20, scalar=2.0, mamode="ema")` | DataFrame | Keltner Channel (KCLe, KCBe, KCUe) |
| `stdev(period=20)` | Series | Rolling Standard Deviation |
| `linreg(period=14)` | Series | Linear Regression endpoint |
| `hv(period=20)` | Series | Historical Volatility (annualized %) |
| `ulcer(period=14)` | Series | Ulcer Index (downside volatility) |

## Volume Indicators

Access via `ind.volume`.

| Method | Return | Description |
|--------|--------|-------------|
| `obv()` | Series | On-Balance Volume |
| `vwap()` | Series | Volume Weighted Average Price (cumulative) |
| `mfi(length=14)` | Series | Money Flow Index [0-100] |
| `adl()` | Series | Accumulation/Distribution Line (cumulative) |
| `cmf(length=20)` | Series | Chaikin Money Flow [-1, 1] |
| `pvt()` | Series | Price Volume Trend (cumulative) |
| `emv(length=14)` | Series | Ease of Movement (smoothed) |

## Output Column Reference

### Trend Output Columns

| Indicator | Column(s) | Description |
|-----------|-----------|-------------|
| `sma(N)` | `SMA_N` | Simple moving average value |
| `ema(N)` | `EMA_N` | Exponential moving average value |
| `wma(N)` | `WMA_N` | Weighted moving average value |
| `bbands(N, S)` | `BBL_N_S` | Lower band |
| | `BBM_N_S` | Middle band (SMA) |
| | `BBU_N_S` | Upper band |
| | `BBB_N_S` | Bandwidth = (upper - lower) / middle |
| | `BBP_N_S` | %B = (close - lower) / (upper - lower) |
| `ichimoku()` | `ITS` | Tenkan-sen (conversion line) |
| | `IKS` | Kijun-sen (base line) |
| | `ISA` | Senkou Span A (leading span A) |
| | `ISB` | Senkou Span B (leading span B) |
| | `ICS` | Chikou Span (lagging span) |
| `adx(N)` | `ADX_N` | Average Directional Index [0-100] |
| | `DMP_N` | Plus Directional Indicator (+DI) |
| | `DMN_N` | Minus Directional Indicator (-DI) |
| `aroon(N)` | `AROONU_N` | Aroon Up [0-100] |
| | `AROOND_N` | Aroon Down [0-100] |
| `psar()` | `PSARl` | Parabolic SAR long (bullish) value |
| | `PSARs` | Parabolic SAR short (bearish) value |
| | `PSARaf` | Current acceleration factor |
| | `PSARr` | Reversal flag (1.0 = reversal, 0.0 = no) |
| `supertrend(N, M)` | `SUPERT_N_M` | SuperTrend line value |
| | `SUPERTd_N_M` | Direction (1.0 = up/bullish, -1.0 = down/bearish) |
| | `SUPERTl_N_M` | Long signal (value when bullish, NaN otherwise) |
| | `SUPERTs_N_M` | Short signal (value when bearish, NaN otherwise) |
| `vwma(N)` | `VWMA_N` | Volume-weighted moving average value |
| `dema(N)` | `DEMA_N` | Double Exponential MA value |
| `tema(N)` | `TEMA_N` | Triple Exponential MA value |
| `donchian(N)` | `DCL_N` | Donchian Channel lower |
| | `DCM_N` | Donchian Channel midline |
| | `DCU_N` | Donchian Channel upper |

### Momentum Output Columns

| Indicator | Column(s) | Description |
|-----------|-----------|-------------|
| `rsi(N)` | `RSI_N` | Relative Strength Index [0-100] |
| `macd(F, S, Sg)` | `MACD_F_S_Sg` | MACD line (fast EMA - slow EMA) |
| | `MACDs_F_S_Sg` | Signal line (EMA of MACD) |
| | `MACDh_F_S_Sg` | Histogram (MACD - Signal) |
| `stoch(K, D, Sm)` | `STOCHk_K_D_Sm` | %K (smoothed fast stochastic) [0-100] |
| | `STOCHd_K_D_Sm` | %D (slow stochastic) [0-100] |
| `roc(N)` | `ROC_N` | Rate of change (%) |
| `willr(N)` | `WILLR_N` | Williams %R [-100, 0] |
| `mom(N)` | `MOM_N` | Price momentum (close - close_N_periods_ago) |
| `cmo(N)` | `CMO_N` | Chande Momentum Oscillator [-100, 100] |
| `cci(N)` | `CCI_N` | Commodity Channel Index (unbounded) |
| `tsi(L, S)` | `TSI_L_S` | True Strength Index [-100, 100] |
| `uo(F, M, S)` | `UO_F_M_S` | Ultimate Oscillator [0-100] |
| `ao(F, S)` | `AO_F_S` | Awesome Oscillator (unbounded) |

### Volatility Output Columns

| Indicator | Column(s) | Description |
|-----------|-----------|-------------|
| `atr(N)` | `ATR_N` | Average True Range (price units) |
| `keltner(N, S)` | `KCLe_N_S` | Lower Keltner Channel |
| | `KCBe_N_S` | Middle band (EMA or SMA) |
| | `KCUe_N_S` | Upper Keltner Channel |
| `stdev(N)` | `STDEV_N` | Rolling standard deviation of close |
| `linreg(N)` | `LINREG_N` | Linear regression endpoint value |
| `hv(N)` | `HV_N` | Historical Volatility (annualized %) |
| `ulcer(N)` | `UI_N` | Ulcer Index (downside volatility) |

### Volume Output Columns

| Indicator | Column(s) | Description |
|-----------|-----------|-------------|
| `obv()` | `OBV` | On-Balance Volume (cumulative) |
| `vwap()` | `VWAP` | Volume Weighted Average Price (cumulative) |
| `mfi(N)` | `MFI_N` | Money Flow Index [0-100] |
| `adl()` | `ADL` | Accumulation/Distribution Line (cumulative) |
| `cmf(N)` | `CMF_N` | Chaikin Money Flow [-1, 1] |
| `pvt()` | `PVT` | Price Volume Trend (cumulative) |
| `emv(N)` | `EMV_N` | Ease of Movement (smoothed) |

## Examples

### Computing RSI and MACD Together

```python
from claude_finance_kit import Stock
from claude_finance_kit.ta import Indicator

stock = Stock("FPT")
df = stock.quote.history(start="2024-01-01")
ind = Indicator(df.set_index('time'))

rsi = ind.momentum.rsi(length=14)
macd = ind.momentum.macd(fast=12, slow=26, signal=9)
macd_col = "MACD_12_26_9"
signal_col = "MACDs_12_26_9"
hist_col = "MACDh_12_26_9"

df["RSI"] = rsi
df["MACD"] = macd[macd_col]
df["MACD_Signal"] = macd[signal_col]
df["MACD_Hist"] = macd[hist_col]

bullish = df[(df["RSI"] < 30) & (df["MACD_Hist"] > 0)]
print(bullish[["close", "RSI", "MACD", "MACD_Signal"]])
```

### Bollinger Bands with Price Data

```python
ind = Indicator(df.set_index('time'))
bbands = ind.trend.bbands(length=20, std=2.0)
lower_col = "BBL_20_2.0"
middle_col = "BBM_20_2.0"
upper_col = "BBU_20_2.0"
width_col = "BBB_20_2.0"
percent_col = "BBP_20_2.0"

df["BB_Lower"] = bbands[lower_col]
df["BB_Middle"] = bbands[middle_col]
df["BB_Upper"] = bbands[upper_col]
df["BB_Width"] = bbands[width_col]
df["BB_Percent"] = bbands[percent_col]

squeeze = df[df["BB_Width"] < df["BB_Width"].quantile(0.1)]
print(f"Squeeze periods: {len(squeeze)} days")
```

### Multi-Indicator Analysis

```python
ind = Indicator(df.set_index('time'))
df["SMA_20"] = ind.trend.sma(length=20)
df["SMA_50"] = ind.trend.sma(length=50)
df["RSI"] = ind.momentum.rsi(length=14)
df["ATR"] = ind.volatility.atr(length=14)
df["OBV"] = ind.volume.obv()

signals = df[(df["SMA_20"] > df["SMA_50"]) & (df["RSI"] < 70)]
print(signals[["close", "SMA_20", "SMA_50", "RSI", "ATR"]].tail())
```

