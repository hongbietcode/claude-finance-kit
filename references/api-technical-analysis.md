# API Reference — Technical Analysis

Requires `pip install claude-finance-kit[ta]`.

## Setup

```python
from claude_finance_kit import Stock
from claude_finance_kit.ta import Indicator

df = Stock("FPT").quote.history(start="2025-01-01", end="2025-03-15")
ind = Indicator(df.set_index('time'))   # REQUIRED: set DatetimeIndex
```

## Trend Indicators

```python
ind.trend.sma(length=20)                          # Series — Simple Moving Average
ind.trend.ema(length=20)                          # Series — Exponential MA
ind.trend.wma(length=20)                          # Series — Weighted MA
ind.trend.vwma(period=20)                         # Series — Volume-Weighted MA
ind.trend.adx(period=14)                          # DataFrame: ADX, DMP, DMN (0-100)
ind.trend.aroon(period=25)                        # DataFrame: AROONU, AROOND (0-100)
ind.trend.psar(af=0.02, max_af=0.2)               # DataFrame: PSARl, PSARs, PSARaf, PSARr
ind.trend.supertrend(period=10, multiplier=3.0)   # DataFrame: SUPERT, SUPERTd, SUPERTl, SUPERTs
ind.trend.bbands(length=20, std=2.0)              # DataFrame: BBL, BBM, BBU, BBB, BBP
ind.trend.ichimoku(tenkan=9, kijun=26, senkou_b=52, displacement=26)  # DataFrame: ITS, IKS, ISA, ISB, ICS
```

## Momentum Indicators

```python
ind.momentum.rsi(length=14)                          # Series, 0-100
ind.momentum.macd(fast=12, slow=26, signal=9)        # DataFrame: MACD, MACDs, MACDh
ind.momentum.stoch(k=14, d=3, smooth_k=3)            # DataFrame: STOCHk, STOCHd (0-100)
ind.momentum.willr(length=14)                        # Series, -100 to 0
ind.momentum.roc(length=9)                           # Series, percentage
ind.momentum.mom(length=10)                          # Series, float
ind.momentum.cmo(length=14)                          # Series, -100 to 100
```

## Volatility Indicators

```python
ind.volatility.atr(length=14)                        # Series, float
ind.volatility.keltner(length=20, scalar=2.0, mamode="ema")  # DataFrame: KCLe, KCBe, KCUe
ind.volatility.stdev(period=20)                      # Series, float — Rolling Standard Deviation
ind.volatility.linreg(period=14)                     # Series, float — Linear Regression endpoint
```

Note: `bbands` lives under `ind.trend.bbands()` — not `ind.volatility`.

## Volume Indicators

```python
ind.volume.obv()              # Series — On Balance Volume (cumulative)
ind.volume.vwap()             # Series — Volume Weighted Average Price
ind.volume.mfi(length=14)     # Series — Money Flow Index, 0-100
```

## Column Name Patterns

| Indicator | Output column names |
|-----------|---------------------|
| SMA(20) | `SMA_20` |
| EMA(20) | `EMA_20` |
| RSI(14) | `RSI_14` |
| MACD(12,26,9) | `MACD_12_26_9`, `MACDs_12_26_9`, `MACDh_12_26_9` |
| ADX(14) | `ADX_14`, `DMP_14`, `DMN_14` |
| Supertrend(10,3.0) | `SUPERT_10_3.0`, `SUPERTd_10_3.0`, `SUPERTl_10_3.0`, `SUPERTs_10_3.0` |
| BBands(20,2.0) | `BBL_20_2.0`, `BBM_20_2.0`, `BBU_20_2.0`, `BBB_20_2.0`, `BBP_20_2.0` |

## Notes

- First N-1 values are NaN (warmup period)
- All timeframes supported: 1m, 5m, 15m, 30m, 1H, 1D, 1W, 1M
- `Indicator` requires DataFrame with columns: open, high, low, close, volume + DatetimeIndex
- `SUPERTd`: 1 = uptrend, -1 = downtrend
- `PSARr`: 1 = reversal signal
