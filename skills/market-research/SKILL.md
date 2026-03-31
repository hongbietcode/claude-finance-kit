---
name: market-research
description: Vietnamese market overview — VNINDEX valuation, macro indicators, sector comparison, fund analysis, commodity prices. Activate for market conditions, macro economy, sector comparison, fund performance, commodity prices, or VNINDEX valuation. Routes to appropriate agent structure based on complexity.
---

# Market Research

> **Install:** `claude-finance-kit` must be installed — see [`references/claude-finance-kit-install-guide.md`](../../references/claude-finance-kit-install-guide.md) for setup command.

## Workflow Router

| Trigger                                                 | Tier | Agents                                          |
| ------------------------------------------------------- | ---- | ----------------------------------------------- |
| "VNINDEX P/E", "current CPI", single metric             | T1   | macro-researcher                                |
| "market briefing", "thị trường hôm nay"                 | T2   | macro-researcher + fundamental-analyst parallel |
| "sector comparison", "sector rotation", "so sánh ngành" | T3   | macro + fundamental → lead-analyst              |
| "full macro outlook + portfolio impact"                 | T4   | lead-analyst → macro + fundamental + technical  |

See [`references/orchestration-protocol.md`](../../references/orchestration-protocol.md) for full tier definitions.

## Market Valuation

```python
from claude_finance_kit import Market

market = Market("VNINDEX")
pe_hist = market.pe(duration="5Y")
pb_hist = market.pb(duration="5Y")
gainers = market.top_gainer(limit=10)
losers = market.top_loser(limit=10)
liquidity = market.top_liquidity(limit=10)
```

### VNINDEX P/E Zones

| P/E   | Interpretation     | Action          |
| ----- | ------------------ | --------------- |
| <12   | Historically cheap | Accumulate      |
| 12-16 | Fair value         | Selective       |
| 16-20 | Getting expensive  | Reduce exposure |
| >20   | Overvalued         | Defensive       |

## Macro Research

```python
from claude_finance_kit import Macro

macro = Macro()
gdp = macro.gdp(start="2023-01", period="quarter")
cpi = macro.cpi(length="2Y", period="month")
rates = macro.interest_rate()
fx = macro.exchange_rate()
fdi = macro.fdi(period="month")
trade = macro.trade_balance(period="month")
```

### Macro Signals

| Indicator      | Bullish    | Bearish          |
| -------------- | ---------- | ---------------- |
| GDP growth     | >6% YoY    | <4%              |
| CPI            | <4%        | >6%              |
| Interest rates | Decreasing | Increasing       |
| USD/VND        | Stable     | >3% depreciation |
| FDI            | Increasing | Declining        |

## Sector Comparison

```python
from claude_finance_kit import Stock

stock = Stock("FPT")
by_industry = stock.listing.symbols_by_industries()
vn30 = stock.listing.symbols_by_group("VN30")
```

Compare financials across symbols in same industry for relative valuation.

## Fund Analysis

```python
from claude_finance_kit import Fund

fund = Fund()
funds = fund.listing(fund_type="STOCK")
fund_id = fund.fund_filter(symbol="SSISCA")['id'].iloc[0]
holdings = fund.top_holding(fund_id=fund_id)
sectors = fund.industry_holding(fund_id=fund_id)
nav = fund.nav_report(fund_id=fund_id)
```

## Commodity Prices

```python
from claude_finance_kit import Commodity

commodity = Commodity()
gold = commodity.gold()
oil = commodity.oil()
steel = commodity.steel()
gas = commodity.gas()
```

## Report Structure

> **IMPORTANT:** Always write the report in the user's language (Vietnamese if user writes in Vietnamese, English if user writes in English).
> **HTML reports:** Follow styles and layout in [`references/html-report-styles.md`](../../references/html-report-styles.md).

Dàn ý báo cáo thị trường đạt yêu cầu (5 sections):

1. **Thị trường chứng khoán** — VNINDEX + VN30 (điểm, % ngày), thanh khoản toàn thị trường so với TB 30 phiên, P/E VNINDEX vs TB 5 năm (vùng: rẻ / hợp lý / đắt / quá đắt); biểu đồ P/E lịch sử
2. **Cổ phiếu nổi bật** — Top 5 tăng mạnh (mã + % tăng), Top 5 giảm mạnh (mã + % giảm), Top 5 thanh khoản cao (mã + giá trị tỷ đồng)
3. **Kinh tế vĩ mô** — GDP tăng trưởng, CPI (lạm phát), lãi suất SBV, USD/VND, FDI — mỗi chỉ số: giá trị hiện tại + xu hướng (↑/↓/→) + tác động ngắn hạn lên thị trường
4. **Hàng hoá & Quỹ** — Vàng (USD/oz), Dầu Brent (USD/bbl), Thép (USD/tấn) + YTD%; 3 quỹ mở nổi bật (NAV/ccq + YTD%)
5. **Nhận định thị trường** — Xu hướng tổng thể (TÍCH CỰC / TRUNG LẬP / TIÊU CỰC), đoạn nhận định 2–3 câu, ngành hưởng lợi vs ngành chịu áp lực

**Required data per section:**

- S1: `Market("VNINDEX").pe(duration="5Y")`, `market.top_gainer/loser/liquidity()`
- S2: `market.top_gainer(10)`, `market.top_loser(10)`, `market.top_liquidity(10)`
- S3: `Macro().gdp()`, `.cpi()`, `.interest_rate()`, `.exchange_rate()`, `.fdi()`
- S4: `Commodity().gold()`, `.oil()`, `.steel()`; `Fund().listing(fund_type="STOCK")`
- S5: derived synthesis from S1–S4
- **Disclaimer** (footer): "Báo cáo chỉ mang tính tham khảo, không phải khuyến nghị đầu tư. Nhà đầu tư tự chịu trách nhiệm về quyết định của mình."

## Reference Index

⚠️ **READ THESE WHEN:** You need detailed API documentation, valuation zones, or macro thresholds beyond what SKILL.md provides.

| File | Content |
|------|---------|
| [`references/claude-finance-kit-install-guide.md`](../../references/claude-finance-kit-install-guide.md) | Installation instructions, requirements, environment variables |
| [`references/common-patterns.md`](../../references/common-patterns.md) | Common coding patterns for data fetching, error handling, batch processing |
| [`references/api-market-macro-fund.md`](../../references/api-market-macro-fund.md) | Market, Macro, Fund, Commodity APIs |
| [`references/analysis-methodology.md`](../../references/analysis-methodology.md) | Valuation zones, macro thresholds |
| [`references/orchestration-protocol.md`](../../references/orchestration-protocol.md) | Complexity routing, agent communication |
| [`references/html-report-styles.md`](../../references/html-report-styles.md) | HTML report design system: Tailwind config, components, placeholders |
