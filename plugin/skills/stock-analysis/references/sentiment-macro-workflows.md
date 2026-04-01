# Sentiment, Macro & Fund Flow Workflows

## 1. News Sentiment Analysis

**Concept:** Crawl Vietnamese financial news, classify each article via Claude reasoning.

**Data sources:**
- `Crawler(source)` for: cafef, vnexpress, vietstock, vneconomy, baodautu
- `BatchCrawler(sources=sites).latest(limit=50)` for bulk fetch
- `Crawler(source).get(url=article_url)` → full article content

**Sentiment Classification (Claude reasoning — not API call):**
- Bullish signals: revenue growth, profit beat, expansion, FDI inflow, rate cut
- Bearish signals: loss, scandal, regulatory penalty, rate hike, supply shock
- Neutral: routine disclosure, AGM notice, dividend announcement

**Per article, classify:**
- sentiment: bullish | bearish | neutral
- event_type: earnings | M&A | regulatory | macro
- confidence: 0.0–1.0
- tickers: list of mentioned tickers

**Aggregate per ticker:**
- Count bullish / bearish / neutral articles
- Net Score = bullish_count − bearish_count

**Output:** Table with columns: Ticker | Bullish | Bearish | Neutral | Net Score | Dominant Sentiment

---

## 2. Macro Dashboard

**Concept:** Fetch key macro indicators, score them, map sector impact.

**Data:**
- `Macro().gdp(start, period="quarter")`
- `Macro().cpi(length="2Y", period="month")`
- `Macro().interest_rate()`
- `Macro().exchange_rate()`
- `Macro().fdi(period="month")`
- `Macro().trade_balance(period="month")`

**Interpretation Thresholds:**

| Indicator | Bullish | Neutral | Bearish |
|-----------|---------|---------|---------|
| GDP YoY | >6% | 4-6% | <4% |
| CPI YoY | <2% | 2-4% | >6% (SBV tightening risk) |
| Policy rate | Decreasing | Stable | Increasing |
| VND/USD chg | <1% depreciation | 1-2% | >3% depreciation |
| FDI | Rising MoM | Stable | Declining 3M trend |

**Sector Impact Mapping:**

| Macro Driver | Sensitive Sectors | Key Tickers |
|-------------|------------------|-------------|
| Rate decrease | Banks, Real estate | VCB, TCB, VHM, NVL |
| CPI spike | Consumer staples | VNM, MSN, SAB |
| FDI surge | Industrials, Logistics | KBC, SZC, GMD |
| Oil price up | Energy | PVD, GAS, PLX |
| Steel price up | Steel producers | HPG, HSG, NKG |

**Macro Scorecard:**
- Score each indicator: +1 bullish, 0 neutral, −1 bearish
- Sum → overall macro bias (bullish / neutral / bearish)

**Output:** Macro Scorecard (score per indicator + overall bias) + Sector Rotation Recommendation

---

## 3. Fund Flow Analysis

**Concept:** Track mutual fund holdings and commodity prices to identify smart money positioning.

**Mutual Fund Data:**
- `Fund().listing(fund_type="STOCK")` → list stock funds
- `Fund().fund_filter(symbol)` → get fund_id
- `Fund().top_holding(fund_id)` → top holdings
- `Fund().industry_holding(fund_id)` → sector allocation
- `Fund().nav_report(fund_id)` → NAV history

**Smart Money Signals:**
- Aggregate all fund holdings → count how many funds hold each ticker
- Tickers held by 3+ funds = high conviction

**Commodity Correlation:**
- `Commodity().gold()`, `.oil()`, `.steel()`, `.gas()`

| Commodity | Direction | Impacted Tickers |
|-----------|-----------|-----------------|
| Oil up | Bullish | PVD, GAS, PLX |
| Oil down | Bearish | PVD, GAS |
| Steel up | Bullish | HPG, HSG, NKG |
| Gold up | Defensive | SJC-linked, safe haven rotation |
| Gas up | Bullish | GAS, PGV |

**Output:**
- Fund Flow Table: Ticker | # Funds Holding | Total AUM Exposure | MoM Change
- Smart Money Signals: tickers held by 3+ funds = high conviction
- Commodity Impact: current price trend → affected tickers + direction
