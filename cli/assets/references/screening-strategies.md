# Stock Screening Strategies (Vietnamese Market)

All data sourced from `claude-finance-kit` library only.

---

## 1. Magic Formula (Greenblatt)

**Concept:** Rank stocks by earnings yield + return on capital; buy top combined rank.
**Rebalance:** Quarterly

**Data:**
- Universe: `stock.listing.symbols_by_group("VN30")`
- `stock.finance.income_statement(period="year")` → operatingProfit (EBIT)
- `stock.finance.balance_sheet(period="year")` → shortTermAssets, shortTermLiabilities, fixedAssets, debt, cash
- `stock.company.overview()` → marketCap

**Steps:**
1. Working Capital = shortTermAssets − shortTermLiabilities
2. EV = marketCap + debt − cash
3. ROC = EBIT / (Working Capital + Fixed Assets)
4. Earnings Yield = EBIT / EV
5. Rank by ROC (desc) + rank by EY (desc) → combined rank
6. Buy top 10% by combined rank

---

## 2. CAN SLIM Adaptation

**Concept:** Score 0–7; buy if score >= 5.

**Factor → Data Mapping:**
- **C** (Current EPS growth): `stock.finance.ratio(period="quarter")` → EPS QoQ > 25%
- **A** (Annual EPS growth): `stock.finance.ratio(period="year")` → EPS YoY > 25%
- **N** (New high): `stock.quote.history()` → price >= 95% of 52-week high
- **L** (Relative strength): compare stock return vs VNINDEX return
- **I** (Institutional): `Fund().top_holding()` → fund ownership
- **M** (Market direction): VNINDEX above SMA200

**Steps:**
1. Score each factor as binary (0 or 1)
2. Sum all factors
3. Buy if score >= 5

---

## 3. Multi-Factor Model

**Factors:** Value (P/E, P/B rank) + Quality (ROE, D/E, Piotroski) + Momentum (6M RS)
**Composite:** equal-weight normalized z-scores

**Data per stock:**
- `stock.finance.ratio(period="year")` → P/E, P/B, ROE
- `stock.finance.balance_sheet(period="year")` → debt, equity for D/E
- `stock.quote.history()` → 6-month return for momentum

**Steps:**
1. For value metrics (P/E, P/B, D/E): z-score, invert (lower = better)
2. For quality/momentum (ROE, momentum): z-score (higher = better)
3. Composite = mean of all z-scores
4. Buy top 10 by composite

---

## 4. Relative Strength Ranking

**Concept:** RS = stock 6M return / VNINDEX 6M return. Buy top quintile.

**Data:**
- `stock.quote.history(start, end)` → compute 6M return per stock
- `Market("VNINDEX")` → compute VNINDEX 6M return

**Steps:**
1. For each stock: return_6m = (close_end / close_start) − 1
2. RS = stock_return / vnindex_return
3. Rank by RS descending
4. Buy top 20% (top quintile)

**Output format:** symbol | 6M return | RS ratio | rank
