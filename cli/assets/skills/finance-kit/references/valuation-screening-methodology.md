# Analysis Methodology — Vietnamese Stock Market

## Contents
- Valuation ratios & thresholds
- Financial health signals
- Technical analysis signals & composite scoring
- Market valuation zones (VNINDEX)
- Macro context & sector impact
- Fundamental workflows (DCF, DDM, DuPont, Z-score, F-score)
- Technical workflows (trend, momentum, volume, volatility scoring)
- Screening strategies (Magic Formula, CAN SLIM, Multi-factor)
- Sentiment classification
- Macro dashboard & fund flow analysis

---

## Valuation Ratios

| Ratio | Cheap | Fair | Expensive | Notes |
|-------|-------|------|-----------|-------|
| P/E | <10 | 10-20 | >20 | Compare within same industry |
| P/B | <1 | 1-3 | >3 | Banks typically 1-2x |
| EV/EBITDA | <8 | 8-15 | >15 | Better for capital-heavy sectors |
| PEG | <1 | 1-1.5 | >1.5 | Only valid when earnings growing |

## Profitability

| Metric | Good | Excellent | Watch out |
|--------|------|-----------|-----------|
| ROE | >15% | >20% | Declining trend, leverage inflating |
| ROA | >5% | >10% | Low ROA + high ROE = too much debt |
| Gross margin | Stable | Expanding | Shrinking = pricing power loss |
| Net margin | >5% | >15% | One-time gains inflating |

## Financial Health

| Signal | Healthy | Warning |
|--------|---------|---------|
| Debt/Equity | <1.0 | >2.0 (non-banks) |
| Current ratio | >1.5 | <1.0 |
| Interest coverage | >3x | <1.5x |
| Operating CF | Positive, growing | Negative while profitable |
| Free CF | Positive | Persistent negative |

## Technical Signals

### Trend
| Signal | Bullish | Bearish |
|--------|---------|---------|
| SMA crossover | SMA20 > SMA50 | SMA20 < SMA50 |
| SMA200 | Price above | Price below |
| ADX | >25 strong trend | <20 range-bound |
| Supertrend | SUPERTd = 1 | SUPERTd = -1 |
| Ichimoku | Price above cloud | Price below cloud |

### Momentum
| Indicator | Overbought | Oversold | Signal |
|-----------|------------|----------|--------|
| RSI(14) | >70 | <30 | Divergence = reversal |
| Stochastic | >80 | <20 | K crosses D from below = buy |
| MACD | — | — | MACD > signal = buy |
| MFI | >80 | <20 | Money flow confirmation |

### Volume
- Price up + volume up = confirmed
- OBV rising + price flat = accumulation (bullish)
- Price above VWAP = institutional buying

### Volatility
- BB squeeze (bands narrowing) → breakout imminent
- Price at BBL + RSI < 35 → mean reversion long
- ATR for position sizing: `shares = risk / ATR`, stop = entry ± 2×ATR

## Composite Technical Score

`score = trend(35%) + momentum(30%) + volume(20%) + volatility(15%)`

| Score | Signal |
|-------|--------|
| >70 | Bullish |
| 40-70 | Neutral |
| <40 | Bearish |

Levels: Stop = price − ATR×2 | Target = price + ATR×3

---

## VNINDEX Valuation Zones

| P/E | Interpretation | Action |
|-----|---------------|--------|
| <12 | Historically cheap | Accumulate |
| 12-16 | Fair value | Selective |
| 16-20 | Getting expensive | Reduce exposure |
| >20 | Overvalued | Defensive |

Compare current vs 5Y avg. >1σ above = expensive, >1σ below = cheap.

## Macro Context (Vietnam)

| Indicator | Bullish | Bearish |
|-----------|---------|---------|
| GDP growth | >6% YoY | <4% |
| CPI | <4% | >6% (SBV tightening) |
| Interest rates | Decreasing | Increasing |
| USD/VND | Stable (<2%) | >3% depreciation |
| FDI | Increasing | Declining |

### Sector Impact Mapping

| Macro Driver | Sensitive Sectors | Key Tickers |
|-------------|------------------|-------------|
| Rate decrease | Banks, Real estate | VCB, TCB, VHM, NVL |
| CPI spike | Consumer staples | VNM, MSN, SAB |
| FDI surge | Industrials | KBC, SZC, GMD |
| Oil price up | Energy | PVD, GAS, PLX |
| Steel price up | Steel | HPG, HSG, NKG |

---

## Fundamental Workflows

### DCF Valuation
1. FCF = operatingCashFlow − abs(capitalExpenditure)
2. WACC = risk-free rate + 9% equity premium
3. Project FCF 5 years at growth_rate (default 10%)
4. Terminal = FCF₅ × (1+g) / (WACC−g), g=2.5%
5. PV = sum discounted FCFs + discounted terminal
6. **BUY** if price < 0.8× fair value | **SELL** if > 1.2×

### DDM (Dividend Discount)
1. g = ROE × (1 − payoutRatio)
2. r = risk-free + 9% equity premium
3. Intrinsic = DPS × (1+g) / (r−g)
4. **BUY** if price < 85% intrinsic | **SELL** if > 115%

### DuPont Analysis
ROE = Net Margin × Asset Turnover × Equity Multiplier
Rising net margin + stable leverage = quality improvement.

### Altman Z-Score
Z = 1.2×X1 + 1.4×X2 + 3.3×X3 + 0.6×X4 + 1.0×X5
- X1=(CA−CL)/TA, X2=RE/TA, X3=EBIT/TA, X4=MktEquity/TL, X5=Rev/TA
- **>2.99** Safe | **1.81–2.99** Gray | **<1.81** Distress

### Piotroski F-Score (9 binary signals)
1. ROA > 0
2. Operating CF > 0
3. ROA improving YoY
4. CF > ROA (accrual quality)
5. Long-term leverage decreasing
6. Current ratio improving
7. No share dilution
8. Gross margin improving
9. Asset turnover improving
- **8-9** High quality | **5-7** Neutral | **<5** Avoid

### Relative Valuation
Compare P/E, P/B, EV/EBITDA vs peer median.
**BUY** if < 0.9× peer median | **SELL** if > 1.3×

---

## Screening Strategies

### Magic Formula (Greenblatt)
1. Working Capital = shortTermAssets − shortTermLiabilities
2. EV = marketCap + debt − cash
3. ROC = EBIT / (WC + Fixed Assets)
4. Earnings Yield = EBIT / EV
5. Rank by ROC + EY combined; buy top 10%

### CAN SLIM Adaptation (score 0–7)
- **C**: EPS QoQ > 25%
- **A**: EPS YoY > 25%
- **N**: Price ≥ 95% of 52-week high
- **L**: Stock return > VNINDEX return
- **I**: Fund ownership (from `Fund().top_holding()`)
- **M**: VNINDEX above SMA200
- Buy if score ≥ 5

### Multi-Factor Model
- Value: P/E, P/B z-scores (inverted)
- Quality: ROE, D/E z-scores
- Momentum: 6-month relative strength
- Composite = mean of all z-scores; buy top 10

---

## Sentiment Classification

Per article, classify via Claude reasoning:
- **Sentiment:** bullish / bearish / neutral
- **Event type:** earnings, M&A, regulatory, macro
- **Confidence:** 0.0–1.0
- **Tickers mentioned**

Bullish signals: revenue growth, profit beat, expansion, FDI inflow, rate cut
Bearish signals: loss, scandal, penalty, rate hike, supply shock

Aggregate per ticker: Net Score = bullish_count − bearish_count

## Macro Scorecard
Score each indicator: +1 bullish, 0 neutral, −1 bearish. Sum → overall bias.

## Fund Flow Signals
- Aggregate fund holdings → tickers held by 3+ funds = high conviction
- Commodity correlation: oil up → PVD/GAS bullish, steel up → HPG/HSG bullish, gold up → defensive rotation

## Analysis Checklist
1. **Macro**: GDP, CPI, rates → environment favorable?
2. **Market**: VNINDEX P/E vs history → cheap/fair/expensive?
3. **Sector**: Target vs industry peers (P/E, ROE, growth)
4. **Fundamentals**: Revenue growth, margins, ROE, debt, CF quality
5. **Technicals**: Trend, momentum, volume confirmation
6. **News**: Recent catalysts, events, insider activity
7. **Conclusion**: Bull/bear case with price targets
