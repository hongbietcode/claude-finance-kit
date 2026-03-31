# claude-finance-kit

Vietnamese stock market data & analysis library.

Unified interface for stock data, market analytics, technical analysis, batch collection, and news — covering 15+ data sources.

## Install

```bash
pip install claude-finance-kit              # Core only
pip install claude-finance-kit[ta]          # + Technical analysis
pip install claude-finance-kit[collector]    # + Batch data collector
pip install claude-finance-kit[news]        # + News crawlers
pip install claude-finance-kit[all]         # Everything
```

## Quick Start

```python
from claude_finance_kit import Stock, Market, Macro, Fund, Commodity

# Stock data
stock = Stock("FPT")
stock.quote.history(start="2024-01-01")
stock.company.overview()
stock.finance.balance_sheet(period="quarter")

# Market overview
market = Market("VNINDEX")
market.pe(duration="5Y")

# Macro economics
macro = Macro()
macro.gdp(start="2023-01", period="quarter")

# Mutual funds
fund = Fund()
fund.listing(fund_type="STOCK")

# Commodities
commodity = Commodity()
commodity.gold()
```

## Data Sources

| Source | Type | Coverage |
|--------|------|----------|
| VCI | Stock (default) | Quote, company, finance, listing, trading — full VN coverage |
| KBS | Stock (fallback) | Same as VCI — full VN coverage |
| MAS | Stock | Quote, intraday, financials, price depth (Mirae Asset) |
| TVS | Stock | Company overview only (Thien Viet Securities) |
| VDS | Stock | Intraday only (Viet Dragon Securities, auto-cookie) |
| FMP | Stock (global) | Quote, company, financials — requires `FMP_API_KEY` env var |
| BINANCE | Crypto | History, intraday, depth — no API key (BTCUSDT, ETHUSDT, etc.) |
| VND | Market | P/E, P/B, top movers |
| MBK | Macro | GDP, CPI, interest rates, FDI, trade balance |
| FMARKET | Fund | Mutual fund data (58+ funds) |
| SPL | Commodity | Gold, oil, steel, gas, fertilizer, agricultural |

## Claude Code Plugin

This repo is also a Claude Code plugin with skills, commands, and agents.

```bash
# Test locally
claude --plugin-dir .

# Commands
/claude-finance-kit:analyze FPT              # Deep-dive stock analysis
/claude-finance-kit:market-overview          # VNINDEX + macro snapshot
/claude-finance-kit:compare FPT,VNM,VCB     # Side-by-side comparison
/claude-finance-kit:screen VN30 P/E<15      # Screen stocks by criteria
/claude-finance-kit:news                     # Financial news + sentiment
/claude-finance-kit:fund-analysis SSISCA     # Mutual fund analysis
```

**Skills** (auto-invoked): stock-analysis, market-research, news-sentiment

**Agents**: fundamental-analyst, technical-analyst, macro-researcher

## Development

```bash
make help             # Show all commands
make requirements     # Export requirements.txt from pyproject.toml
make package-skill    # Package skill files into zip
make bump TYPE=patch  # Bump version (patch|minor|major)
make release          # Bump → package → git tag → GitHub release
```

## Test
```
claude --plugin-dir <claude-finance-kit>
```

### Release

```bash
make bump TYPE=patch   # 0.1.0 -> 0.1.1
make release           # Creates tag, pushes, uploads skill zip to GitHub Releases
```

## License

MIT
