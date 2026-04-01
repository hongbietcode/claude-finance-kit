# Stock Analysis Methodology

Guide for interpreting financial data, technical signals, and market valuation from claude-finance-kit data.

## Fundamental Analysis

### Valuation Ratios

| Ratio | Formula | Cheap | Fair | Expensive | Notes |
|-------|---------|-------|------|-----------|-------|
| P/E | Price / EPS | <10 | 10-20 | >20 | Compare within same industry |
| P/B | Price / Book Value | <1 | 1-3 | >3 | Banks typically 1-2x |
| EV/EBITDA | Enterprise Value / EBITDA | <8 | 8-15 | >15 | Better than P/E for capital-heavy sectors |
| PEG | P/E / EPS Growth Rate | <1 | 1-1.5 | >1.5 | Only valid when earnings growing |

### Profitability

| Metric | Good | Excellent | Watch out |
|--------|------|-----------|-----------|
| ROE | >15% | >20% | Declining trend, high leverage inflating ROE |
| ROA | >5% | >10% | Low ROA + high ROE = too much debt |
| Gross margin | Stable | Expanding | Shrinking = pricing power loss |
| Net margin | >5% | >15% | One-time gains inflating margin |

### Financial Health

| Signal | Healthy | Warning |
|--------|---------|---------|
| Debt/Equity | <1.0 | >2.0 (non-banks) |
| Current ratio | >1.5 | <1.0 |
| Interest coverage | >3x | <1.5x |
| Operating cash flow | Positive, growing | Negative while profitable (earnings quality issue) |
| Free cash flow | Positive | Persistent negative = cash burn |

### Growth Assessment

Compare YoY and QoQ for: revenue, net income, EPS, total assets.
Look for: acceleration (growth rate increasing), consistency (3+ quarters), quality (revenue-driven, not one-offs).

## Technical Analysis Signals

### Trend Identification

| Signal | Bullish | Bearish |
|--------|---------|---------|
| SMA crossover | SMA20 > SMA50 (golden cross) | SMA20 < SMA50 (death cross) |
| SMA200 | Price above SMA200 | Price below SMA200 |
| ADX | ADX > 25 = strong trend | ADX < 20 = no trend (range-bound) |
| Supertrend | SUPERTd = 1 | SUPERTd = -1 |
| PSAR | PSARl active (dots below price) | PSARs active (dots above price) |
| Ichimoku | Price above cloud (ISA/ISB) | Price below cloud |

### Momentum & Reversal

| Indicator | Overbought | Oversold | Signal |
|-----------|------------|----------|--------|
| RSI(14) | >70 | <30 | Divergence with price = reversal |
| Stochastic | >80 | <20 | K crosses D from below = buy |
| Williams %R | >-20 | <-80 | Similar to stochastic |
| MACD | — | — | MACD crosses above signal line = buy |
| CMO | >50 | <-50 | Extreme readings = exhaustion |
| MFI | >80 | <20 | Money flow confirmation |

### Volatility

| Tool | Usage |
|------|-------|
| Bollinger Bands | Price at BBL + RSI oversold = mean reversion buy |
| ATR | Position sizing: risk per trade / ATR = shares. Stop = entry ± 2×ATR |
| Keltner Channel | BB squeeze inside KC → breakout expected |

### Volume Confirmation

- Price up + volume up = confirmed move
- Price up + volume down = weak move, possible reversal
- OBV rising while price flat = accumulation (bullish)
- OBV falling while price flat = distribution (bearish)
- VWAP: price above VWAP = bullish intraday bias

## Market Valuation (VNINDEX)

Use `Market("VNINDEX").pe(duration="5Y")` to assess market-wide valuation.

| P/E Zone | Interpretation | Action bias |
|----------|---------------|-------------|
| <12 | Historically cheap | Accumulate quality stocks |
| 12-16 | Fair value zone | Selective, focus on growth |
| 16-20 | Getting expensive | Reduce exposure, raise cash |
| >20 | Overvalued territory | Defensive, take profits |

Compare current P/E vs 5Y average. >1 std above = expensive, >1 std below = cheap.

## Macro Context (Vietnam)

| Indicator | Bullish for stocks | Bearish |
|-----------|-------------------|---------|
| GDP growth | >6% YoY | <4% |
| CPI | <4% (stable) | >6% (SBV may tighten) |
| Interest rates | Decreasing | Increasing |
| USD/VND | Stable (<2% depreciation) | >3% depreciation |
| FDI inflows | Increasing | Declining |

## Analysis Checklist

1. **Macro**: GDP trend, CPI, interest rates → is environment favorable?
2. **Market**: VNINDEX P/E vs history → is market cheap/fair/expensive?
3. **Sector**: Compare target stock vs industry peers (P/E, ROE, growth)
4. **Fundamentals**: Revenue growth, margins, ROE, debt levels, cash flow quality
5. **Technicals**: Trend (SMA/Supertrend), momentum (RSI/MACD), volume confirmation
6. **News**: Recent catalysts, corporate events, insider activity
7. **Conclusion**: Bull/bear case with price targets based on valuation
