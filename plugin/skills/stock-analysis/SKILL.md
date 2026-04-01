---
name: stock-analysis
description: Orchestration skill for Vietnamese stock market analysis. Activate for deep dives, valuation, financial health, technical analysis, screening, sentiment, macro, sector analysis, or market briefings. Routes to appropriate agent structure based on task complexity.
---

# Stock Analysis — Vietnamese Market

> **Install:** `claude-finance-kit` must be installed — see [`references/finance-kit-install-guide.md`](./references/finance-kit-install-guide.md) for setup command.

Orchestration skill: uses `claude-finance-kit` as data layer, Claude's reasoning as analysis layer. Routes queries to the right agent structure based on complexity.

> **Code patterns & error handling:** See [`references/common-patterns.md`](./references/common-patterns.md).

## Operating Principles

- **Data-First:** thesis → data → reasoning → conclusion. State assumptions when data unavailable. Never hallucinate.
- **No Bias:** If risk > reward, recommend staying out. If setup unclear, say "No trade setup".
- **Concise & Actionable:** Bullet points and data tables over paragraphs.
- **Real-Time Data Only:** Market indices MUST be fetched live — never fabricated. Flag if delayed/unavailable.
- **Context-Aware:** Tailor analysis depth and style to user's timeframe and experience level. Always clarify if ambiguous.

## Scope

**Handles:** Stock valuation, financial health scoring, technical analysis, screening, news sentiment, macro research, sector analysis, fund flows — all for Vietnamese market via claude-finance-kit.
**Does NOT handle:** Portfolio management systems, trading bots, brokerage integrations, live order execution, non-Vietnamese markets.

## Workflow Router

| Trigger                                                             | Workflow           | Tier | Agents                                         |
| ------------------------------------------------------------------- | ------------------ | ---- | ---------------------------------------------- |
| "P/E of X", single metric, "giá"                                    | Single Metric      | T1   | fundamental-analyst OR technical-analyst       |
| "DCF", "valuation", "fair value", "định giá"                        | Valuation          | T1   | fundamental-analyst                            |
| "health", "Z-score", "F-score", "DuPont", "sức khỏe"                | Financial Health   | T1   | fundamental-analyst                            |
| "technical", "kỹ thuật", "trend", "RSI", "MACD"                     | Technical Analysis | T1   | technical-analyst                              |
| "analyze {TICKER}", "deep dive {TICKER}"                            | Stock Deep Dive    | T2   | fundamental + technical parallel               |
| "briefing", "market today", "thị trường"                            | Daily Briefing     | T2   | macro + fundamental parallel                   |
| "banking", "NIM", "NPL" / "real estate", "NAV" / "consumer", "ROIC" | Sector Analysis    | T2   | fundamental-analyst with sector context        |
| "news", "sentiment", "tin tức"                                      | Sentiment          | T1   | Delegate to news-sentiment skill               |
| "screen", "sàng lọc", "magic formula", "CAN SLIM"                   | Screener + Rank    | T3   | fundamental + technical → lead-analyst ranks   |
| "compare", "so sánh", "buy/sell", "mua/bán"                         | Comparative        | T3   | specialists → lead-analyst decides             |
| "portfolio", "danh mục", "holdings"                                 | Portfolio Check    | T4   | lead-analyst → fundamental + technical + macro |
| "macro outlook + recommendation", "sector rotation"                 | Macro + Rotation   | T4   | lead-analyst → macro + fundamental             |

See [`references/orchestration-protocol.md`](./references/orchestration-protocol.md) for full tier definitions and communication rules.

## Composite Workflows

### 1. Stock Deep Dive — T2 (`analyze {TICKER}`)

1. Company overview: `stock.company.overview()`
2. Fundamentals (fundamental-analyst): relative valuation (P/E, P/B vs peers) + Piotroski F-score + DuPont
3. Technicals (technical-analyst): composite score (trend + momentum + volume) from last 200 days
4. Recent news: crawl last 10 articles mentioning ticker, classify sentiment
5. **Verdict:** Bull/bear case, confidence level (0-100), key risks

- Agents run in parallel, sections merged — no cross-talk needed

### 2. Daily Market Briefing — T2

1. Market valuation: `Market("VNINDEX").pe()` vs 5Y average
2. Top movers: `Market("VNINDEX").top_gainer(10)` + `top_loser(10)`
3. Macro snapshot: latest CPI, interest rate, exchange rate from `Macro()`
4. News headlines: top 10 from cafef + vnexpress
5. **Output:** 5-bullet summary + sector bias for the day

### 3. Multi-Criteria Screener — T3

1. Universe: VN30 or user-specified group via `stock.listing.symbols_by_group()`
2. Fundamental filter (fundamental-analyst): P/E < median, ROE > 15%, F-score >= 6
3. Technical filter (technical-analyst): composite score > 60, price above SMA200
4. lead-analyst: rank by composite score, issue top 10 with score breakdown

- Specialists run parallel → lead-analyst synthesizes ranking

### 4. Portfolio Health Check — T4

lead-analyst coordinates sequentially:

1. fundamental-analyst: Piotroski F-score + Altman Z-score per holding
2. technical-analyst: trend + momentum signal per holding
3. macro-researcher: macro headwinds/tailwinds for held sectors
4. lead-analyst: aggregate portfolio risk score, weakest positions, rebalance suggestions

### 5. Macro Outlook & Sector Rotation — T4

lead-analyst coordinates:

1. macro-researcher: GDP, CPI, interest rate trends + commodity prices
2. fundamental-analyst: sector valuation comparison
3. lead-analyst: map macro conditions to sector impact → top 3 sector picks

## Report Structure

> **IMPORTANT:** Always write the report in the user's language (Vietnamese if user writes in Vietnamese, English if user writes in English).
> **MANDATORY:** Every analysis MUST produce a self-contained HTML report file. Follow styles and layout in [`references/html-report-styles.md`](./references/html-report-styles.md).

Strictly follow 8 sections with clear headings, bullet points, bold key figures:

1. **Executive Summary** — Rating (Bullish/Bearish/Neutral), current price & target price, 3-4 sentence thesis, confidence level (0-100)
2. **Macro & Sector Context** — VNINDEX P/E zone (rẻ/hợp lý/đắt), interest rate trend, USD/VND, sector performance vs market; how macro conditions impact this specific stock
3. **Catalysts & Growth Drivers** — Company-specific catalysts, competitive advantages & economic moat, upcoming events (earnings, dividends, M&A)
4. **Financial Health & Valuation** — Debt, margins, FCF; P/E, P/B vs. sector avg & history — over/undervalued? Piotroski F-score, DuPont breakdown
5. **Technical View** — Daily/Weekly trend, Support/Resistance zones, momentum (RSI, BB, MACD), volume profile; Plotly price chart with S/R levels
6. **Recent Events & News Impact** — 3-5 recent news/events affecting the stock, sentiment classification (bullish/bearish/neutral), corporate actions, regulatory changes
7. **Key Risks** — Top 2-3 risks breaking thesis (regulatory, management, interest rate, sector-specific...)
8. **Actionable Plan** — Strategy per user's timeframe: entry zone, hard stop-loss, partial take-profit levels, position sizing suggestion
9. **Disclaimer** — "This report is based on market data for informational purposes only and does not constitute mandatory investment advice. You are solely responsible for your own capital allocation and risk management decisions."

**Required data sources per section:**

- S1: synthesis from S2–S8
- S2: `Market("VNINDEX").pe()`, `Macro().interest_rate()`, `Macro().exchange_rate()`, sector P/E comparison
- S3: `stock.company.overview()`, `stock.company.events()`, `stock.company.news()`
- S4: `stock.finance.balance_sheet()`, `.income_statement()`, `.ratio()`, peer comparison
- S5: `stock.quote.history()` → `Indicator(df)` for RSI, MACD, BB, SMA; Plotly candlestick chart
- S6: `Crawler("cafef").get_latest_articles()` filtered by ticker, sentiment classification
- S7–S8: derived from S2–S6

### HTML Output Rules

1. **Format:** Self-contained HTML file — Tailwind CDN + Plotly.js CDN, no external dependencies
2. **Save path:** `{CWD}/plans/reports/{slug}-report.html` (e.g., `fpt-analysis-2026-04-01-report.html`, `vn30-screening-2026-04-01-report.html`)
3. **Open:** After writing the file, run `open {file_path}` to auto-open in browser
4. **Charts:** Plotly.js with data embedded as inline JS variables
5. **Deliver in chat:** summary + file path link

## Rules

- Source fallback: VCI → KBS. Always `try-except` + check `df.empty`.
- Date format: `YYYY-MM-DD`
- TA requires `df.set_index('time')` before `Indicator()`
- TA indicators produce NaN for first N-1 rows — drop or ignore warmup period
- Always show data sources, date ranges, and assumptions
- Never fabricate data — if API returns empty, state "data unavailable"
- Vietnamese context: VN30 concentration (4 banks ~30%), FOL limits, margin rules
- Data errors/empty/stale → flag explicitly, never silently fill gaps
- Technical vs fundamental conflict → present both sides, never cherry-pick bullish
- Insufficient data for DCF/peers → say so, don't force a target price
- claude-finance-kit API down → alert user, suggest trying later or switch source (VCI → KBS)

## Reference Index

⚠️ **READ THESE WHEN:** You need detailed API documentation, methodology, or code patterns beyond what SKILL.md provides.

| File                                                                                             | Content                                                                                                |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| [`references/finance-kit-install-guide.md`](./references/finance-kit-install-guide.md)           | Installation instructions, requirements, environment variables                                         |
| [`references/common-patterns.md`](./references/common-patterns.md)                               | Common coding patterns for data fetching, TA, news crawling, error handling, caching, batch processing |
| [`references/api-stock-and-company.md`](./references/api-stock-and-company.md)                   | Stock, Quote, Company, Finance, Listing, Trading APIs                                                  |
| [`references/api-technical-analysis.md`](./references/api-technical-analysis.md)                 | All TA indicators with params                                                                          |
| [`references/api-market-macro-fund.md`](./references/api-market-macro-fund.md)                   | Market, Macro, Fund, Commodity APIs                                                                    |
| [`references/api-news-and-collector.md`](./references/api-news-and-collector.md)                 | News crawlers, Collector tasks                                                                         |
| [`references/analysis-methodology.md`](./references/analysis-methodology.md)                     | Valuation, financial health, TA signals                                                                |
| [`references/orchestration-protocol.md`](./references/orchestration-protocol.md)                 | Complexity routing, agent communication tiers                                                          |
| [`references/html-report-styles.md`](./references/html-report-styles.md)                         | HTML report design system: Tailwind config, components, placeholders                                   |
| [`references/fundamental-analysis-workflows.md`](./references/fundamental-analysis-workflows.md) | DCF, DDM, DuPont, Z-score, F-score                                                                     |
| [`references/technical-analysis-workflows.md`](./references/technical-analysis-workflows.md)     | Composite scoring system                                                                               |
| [`references/screening-strategies.md`](./references/screening-strategies.md)                     | Magic Formula, CAN SLIM, multi-factor                                                                  |
| [`references/sentiment-macro-workflows.md`](./references/sentiment-macro-workflows.md)           | News classification, macro dashboard, fund flows                                                       |
| [`references/sector-specific-analysis.md`](./references/sector-specific-analysis.md)             | Banking, real estate, consumer metrics                                                                 |
