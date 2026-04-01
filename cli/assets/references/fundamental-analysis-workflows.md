# Fundamental Analysis Workflows

Reference for Vietnamese stock fundamental analysis using `claude-finance-kit` library.

---

## 1. DCF Valuation

Fetch cash flows, project FCF, discount to present value.

**Data:**
- `stock.finance.cash_flow(period="year")` → `operatingCashFlow`, `capitalExpenditure`
- `Macro().interest_rate()` → risk-free rate
- `stock.quote.history(count=1)` → current price

**Steps:**
1. FCF = operatingCashFlow − abs(capitalExpenditure)
2. WACC = risk-free rate + 9% equity premium
3. Project FCF for 5 years at `growth_rate` (default 10%)
4. Terminal value = FCF₅ × (1 + terminal_g) / (WACC − terminal_g), terminal_g default 2.5%
5. PV = sum of discounted projected FCFs + discounted terminal value
6. Ratio = current price / (PV / 1e9)

**Decision:** BUY if price < 0.8× fair value | SELL if > 1.2× | HOLD otherwise

---

## 2. Relative Valuation

Compare target valuation multiples vs peer median.

**Data:**
- `stock.listing.symbols_by_industries()` → find peers in same industry
- `stock.finance.ratio(period="quarter")` → P/E, P/B, EV/EBITDA for target + up to 10 peers

**Steps:**
1. Get industry peers, fetch ratio for each
2. Compute peer median for P/E, P/B, EV/EBITDA
3. For each metric: ratio = target_value / peer_median, percentile rank

**Decision:** BUY if < 0.9× peer median | SELL if > 1.3× peer median

---

## 3. DDM — Dividend Discount Model

Gordon Growth: intrinsic = DPS × (1+g) / (r − g)

**Data:**
- `stock.company.events()` → filter `eventType` contains "dividend" → latest DPS
- `stock.finance.ratio(period="quarter")` → ROE, payoutRatio
- `Macro().interest_rate()` → risk-free rate

**Steps:**
1. g = ROE × (1 − payoutRatio)
2. r = risk-free rate + 9% equity premium
3. Intrinsic = DPS × (1 + g) / (r − g)
4. Compare vs current price

**Decision:** BUY if price < 85% intrinsic | SELL if > 115% | HOLD otherwise

---

## 4. DuPont Analysis

ROE = Net Margin × Asset Turnover × Equity Multiplier

**Data:**
- `stock.finance.income_statement(period="quarter").head(4)` → revenue, netIncome
- `stock.finance.balance_sheet(period="quarter").head(4)` → totalAssets, equity

**Steps per quarter:**
1. Net Margin = netIncome / revenue
2. Asset Turnover = revenue / totalAssets
3. Equity Multiplier = totalAssets / equity
4. ROE = product of above three

**Output:** 4-quarter trend of ROE decomposition — rising net margin + stable leverage = quality improvement

---

## 5. Altman Z-Score

Z = 1.2×X1 + 1.4×X2 + 3.3×X3 + 0.6×X4 + 1.0×X5

**Data:**
- `stock.finance.balance_sheet(period="year")` → totalAssets, shortTermAssets, shortTermLiabilities, retainedEarnings, totalLiabilities, sharesOutstanding
- `stock.finance.income_statement(period="year")` → operatingProfit, revenue
- `stock.quote.history(count=1)` → current price for market value of equity

**Components:**
- X1 = (current assets − current liabilities) / total assets
- X2 = retained earnings / total assets
- X3 = EBIT / total assets
- X4 = market value equity / total liabilities
- X5 = revenue / total assets

**Thresholds:** > 2.99 Safe | 1.81–2.99 Gray zone | < 1.81 Distress

---

## 6. Piotroski F-Score

9 binary signals across profitability, leverage, and efficiency. Requires 2 years of data.

**Data:**
- `stock.finance.income_statement(period="year").head(2)`
- `stock.finance.balance_sheet(period="year").head(2)`
- `stock.finance.cash_flow(period="year").head(2)`

**9 Criteria (1 point each if true):**
1. **F1** ROA > 0
2. **F2** Operating cash flow > 0
3. **F3** ROA improving YoY
4. **F4** Cash flow > ROA (accrual quality)
5. **F5** Long-term leverage decreasing YoY
6. **F6** Current ratio improving YoY
7. **F7** No share dilution (shares outstanding ≤ prior year)
8. **F8** Gross margin improving YoY
9. **F9** Asset turnover improving YoY

**Thresholds:** 8–9 High quality | 5–7 Neutral | < 5 Avoid
