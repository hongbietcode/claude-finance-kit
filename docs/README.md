# claude-finance-kit Documentation

claude-finance-kit is an open-source Vietnamese stock market data & analysis library with an Interface-first architecture.

## Quick Start

```bash
pip install claude-finance-kit[all]
```

```python
from claude_finance_kit import Stock, Market, Macro, Fund, Commodity
from claude_finance_kit.ta import Indicator

stock = Stock("FPT", source="VCI")
df = stock.quote.history(start="2024-01-01", end="2025-03-15")
```

## Skill Files (primary reference)

| File | Purpose |
|------|---------|
| `../SKILL.md` | Main skill — workflows, quick lookup, rules |
| `../CLAUDE.md` | Skill activation trigger |

## Reference Files (detailed API)

| File | Content |
|------|---------|
| `../references/api-stock-and-company.md` | Stock, Quote, Company, Finance, Listing, Trading APIs |
| `../references/api-market-macro-fund.md` | Market, Macro, Fund, Commodity APIs |
| `../references/api-technical-analysis.md` | All TA indicators: trend, momentum, volatility, volume |
| `../references/api-news-and-collector.md` | News crawlers, Collector tasks, exporters, scheduler, Perplexity Search |
| `../references/analysis-methodology.md` | Valuation ratios, financial health, TA signals, checklist |
| `../references/common-patterns.md` | Error handling, caching, batch processing, gotchas |

## Package Structure

```
claude_finance_kit/
├── stock/       # Stock, Quote, Company, Finance, Listing, Trading
├── market/      # Market (P/E, P/B, top movers)
├── macro/       # Macro (GDP, CPI, rates, FDI)
├── fund/        # Fund (listing, holdings, NAV)
├── commodity/   # Commodity (gold, oil, steel, gas)
├── ta/          # Indicator (trend, momentum, volatility, volume)
├── news/        # Crawler, BatchCrawler
├── search/      # PerplexitySearch (web search via Perplexity API)
├── collector/    # Batch tasks, exporters, scheduler
└── _provider/   # Data source adapters (VCI, KBS, MAS, TVS, VDS, FMP, BINANCE, VND, MBK, SPL, FMARKET)
```

## Optional Extras

| Extra | Installs | Enables |
|-------|----------|---------|
| `[ta]` | pandas-ta | Technical analysis indicators |
| `[collector]` | duckdb, pyarrow, aiohttp | Batch data collector |
| `[news]` | scipy, pyarrow | News crawlers |
| `[all]` | all above | Everything |
