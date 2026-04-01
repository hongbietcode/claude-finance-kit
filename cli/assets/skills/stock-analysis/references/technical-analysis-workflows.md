# Technical Analysis Workflows — claude-finance-kit Library

## Data Fetching Pattern

```
stock = Stock(TICKER, source="VCI")
df = stock.quote.history(start, end).set_index('time')
ind = Indicator(df)
```

---

## 1. Trend Analysis

**Indicators:** SMA(50/200), EMA(20), ADX(14), Supertrend(10,3), Ichimoku, PSAR

**API calls:**
- `ind.trend.sma(50)`, `ind.trend.sma(200)`, `ind.trend.ema(20)`
- `ind.trend.adx(14)` → returns `ADX` column
- `ind.trend.supertrend(10, 3)` → returns `direction` (1=up, -1=down)
- `ind.trend.ichimoku()` → returns `cloud_top`
- `ind.trend.psar()`

**Signal Rules:**
- Golden cross: SMA50 crosses above SMA200 → bullish
- Death cross: SMA50 crosses below SMA200 → bearish
- Price above Ichimoku cloud → bullish; below cloud → bearish
- ADX > 25 = strong trend; ADX < 20 = weak/ranging
- Supertrend direction: 1 = up, -1 = down
- PSAR below price = uptrend; above = downtrend

**Scoring:** Each bullish signal = +1; sum / total × 100 → trend_score (0–100)

---

## 2. Momentum Analysis

**Indicators:** RSI(14), MACD(12,26,9), Stochastic(14,3,3), Williams %R(14), MFI(14)

**API calls:**
- `ind.momentum.rsi(14)`
- `ind.momentum.macd()` → returns `MACD`, `Signal` columns
- `ind.momentum.stoch()` → returns `%K`, `%D` columns
- `ind.momentum.willr(14)`
- `ind.volume.mfi(14)`

**Signal Rules:**
- RSI > 70 = overbought; RSI < 30 = oversold; 40–60 = neutral bullish
- MACD line crosses above signal line → bullish
- Stochastic %K > %D and both < 80 → bullish entry
- Williams %R > -20 = overbought; < -80 = oversold
- MFI > 50 = buying pressure

**Divergence:** Price makes new high but RSI makes lower high → bearish divergence

**Scoring:** Each bullish signal = +1; sum / total × 100 → momentum_score (0–100)

---

## 3. Volume Analysis

**Indicators:** OBV, VWAP, MFI(14), A/D Line

**API calls:**
- `ind.volume.obv()`
- `ind.volume.vwap()`
- `ind.volume.mfi(14)`
- `ind.volume.ad()`

**Signal Rules:**
- OBV rising with price rising → volume confirms uptrend
- OBV rising while price falling → bullish divergence (accumulation)
- Price above VWAP → institutional buying pressure
- A/D line trending up = accumulation phase

**Scoring:** 4 signals, each +1 if bullish; sum / 4 × 100 → volume_score (0–100)

---

## 4. Volatility Assessment

**Indicators:** Bollinger Bands(20,2), ATR(14), Keltner Channel(20)

**API calls:**
- `ind.volatility.bbands(20)` → returns `BBU`, `BBL`, `BBM`
- `ind.volatility.atr(14)`
- `ind.volatility.kc(20)`

**Signal Rules:**
- BB squeeze (bands narrowing) → breakout imminent
- Price at BBL + RSI < 35 → mean reversion long setup
- Price at BBU + RSI > 65 → mean reversion short setup
- ATR used for position sizing and stop placement

**Position Sizing:** `position_size = risk_amount / ATR`
**Stop distance:** ATR × 2

---

## 5. Composite Technical Score

**Formula:** `score = trend(35%) + momentum(30%) + volume(20%) + volatility(15%)`

**Scale:** > 70 = Bullish | 40–70 = Neutral | < 40 = Bearish

**Levels:**
- Stop Loss = price − ATR × 2
- Target = price + ATR × 3

**Output Template:**
```
Ticker : FPT       Price: 120.5
Signal : BULLISH   Score: 74.2/100

Category Scores:
  Trend      35% weight → 80.0
  Momentum   30% weight → 70.0
  Volume     20% weight → 75.0
  Volatility 15% weight → 60.0

Key Indicators:
  ADX: 28.4 (strong trend)   RSI: 55.2   ATR: 3.1

Levels:
  Stop Loss : 114.3
  Target    : 129.8
```
