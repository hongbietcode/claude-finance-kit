# Sector-Specific Analysis — Vietnamese Stock Market

## 1. Banking Sector

### Key Metrics & Thresholds
| Metric | Good | Concern | Distress |
|--------|------|---------|---------|
| NIM | 2.5–3.5% | <2.5% | declining trend |
| NPL ratio | <2% | 2–3% | >3% |
| CASA ratio | >35% | 25–35% | <25% |
| Cost-to-Income | <35% | 35–40% | >40% |
| ROA | >1.2% | 0.8–1.2% | <0.8% |
| CAR | >10% | 9–10% | <9% |

### Data Mapping
- `stock.finance.ratio()` → ROA, CAR approximations
- `stock.finance.income_statement()` → interest_income, interest_expense, provision_expense
- `stock.finance.balance_sheet()` → total_assets, total_deposits
- NIM proxy = (interest_income − interest_expense) / total_assets × 100
- **Limitations:** CASA not directly available; NPL not in public financials — estimate from provision trends

### Key Tickers
VCB, BID, CTG, TCB, MBB, ACB, VPB, TPB, STB, HDB

### Signals
- **Buy:** NIM stable/expanding + NPL declining + ROA >1.5%
- **Sell:** NPL surging + NIM compression + Cost-to-Income rising

---

## 2. Real Estate Sector

### Key Metrics & Thresholds
| Metric | Healthy | Watch | Risk |
|--------|---------|-------|------|
| P/B (NAV proxy) | <0.8× | 0.8–1.2× | >1.2× |
| Inventory years | >3 yrs | 1–3 yrs | <1 yr |
| Debt/Equity | <1.5 | 1.5–2.0 | >2.0 |
| Gross margin | project-mix | stable | compressing |

### Data Mapping
- `stock.finance.balance_sheet()` → assets, liabilities, inventory, equity
- `stock.finance.income_statement()` → cost_of_goods_sold, revenue, gross_profit
- `stock.finance.ratio()` → P/B
- Inventory years = inventory / COGS
- D/E = total_liabilities / equity

### Key Tickers
VHM, VRE, NVL, KDH, DXG, PDR, NLG, HDG

### Signals
- **Buy:** P/B <0.8× + inventory >3 years + Debt/Equity <1.5
- **Sell:** P/B >1.2× + inventory <1 year + Debt/Equity >2.0

---

## 3. Consumer Goods Sector

### Key Metrics & Thresholds
| Metric | Strong | Acceptable | Weak |
|--------|--------|-----------|------|
| Revenue CAGR (3yr) | >8% | 5–8% | <5% |
| Gross margin | >35% | 25–35% | <25% |
| ROIC | >12% | 8–12% | <8% |
| Debt/EBITDA | <2.0 | 2.0–3.0 | >3.0 |
| Dividend yield | >2% | 1–2% | <1% |

### Data Mapping
- `stock.finance.income_statement(period="year")` → revenue (multi-year for CAGR), EBIT, gross_profit
- `stock.finance.balance_sheet(period="year")` → equity, total_debt, cash
- `stock.finance.ratio(period="year")` → gross_margin, dividend_yield
- Revenue CAGR = (rev_now / rev_3y_ago)^(1/3) − 1
- ROIC = NOPAT / invested_capital; NOPAT = EBIT × (1 − tax_rate); invested_capital = equity + debt − cash

### Key Tickers
VNM, MSN, MWG, PNJ, SAB, BHN

### Signals
- **Buy:** CAGR >10% + gross margin stable/expanding + ROIC >15%
- **Sell:** margin compression + revenue growth <5% + Debt/EBITDA >3.0
