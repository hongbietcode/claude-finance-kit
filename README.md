<p align="center">
  <h1 align="center">claude-finance-kit</h1>
  <p align="center">
    Vietnamese stock market analysis toolkit for AI coding assistants.
    <br />
    Fundamentals &bull; Technicals &bull; Macro &bull; News &bull; Screening &bull; Fund Analysis
  </p>
</p>

<p align="center">
  <a href="https://pypi.org/project/claude-finance-kit/"><img src="https://img.shields.io/pypi/v/claude-finance-kit?color=blue&label=PyPI" alt="PyPI Version" /></a>
  <a href="https://www.npmjs.com/package/claude-finance-kit-cli"><img src="https://img.shields.io/npm/v/claude-finance-kit-cli?color=green&label=npm" alt="npm Version" /></a>
  <a href="https://pypi.org/project/claude-finance-kit/"><img src="https://img.shields.io/pypi/pyversions/claude-finance-kit" alt="Python Versions" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/hongbietcode/claude-finance-kit" alt="License" /></a>
</p>

---

## Overview

**claude-finance-kit** is a Python library + AI plugin that gives your coding assistant deep access to Vietnamese stock market data and analysis tools. It ships valid plugin manifests for **Codex** and **Claude Code**, and also supports **Cursor** and **GitHub Copilot** through the CLI installer.

Ask natural language questions — the plugin auto-routes to the right analysis workflow:

```
"Analyze FPT stock"
"Market overview today"
"Compare VNM vs MSN"
"Latest news sentiment for HPG"
```

### Example: Stock Analysis in Action

<p align="center">
  <a href="https://github.com/hongbietcode/claude-finance-kit/releases/latest">
    <img src="assets/image.png" alt="Claude Finance Kit analyzing HPG stock" width="800" />
  </a>
  <br />
  <em>Claude Code analyzing HPG stock — orchestrating fundamental and technical agents in parallel. <a href="https://github.com/hongbietcode/claude-finance-kit/releases/latest">Download plugin →</a></em>
</p>

## Features

- **Stock Analysis** — valuation, financial health, technical indicators, screening, sentiment, sector analysis
- **Market Research** — market valuation (P/E, P/B), sector comparison, fund analysis, commodities
- **Technical Analysis** — 30+ indicators: SMA, EMA, RSI, MACD, Bollinger Bands, ATR, OBV, and more
- **Macro Research** — GDP, CPI, interest rates, exchange rates, FDI, trade balance
- **News & Sentiment** — crawl and classify news from Vietnamese financial sites (CafeF, VnExpress, etc.)
- **Fund Analysis** — 58+ mutual funds: NAV, holdings, industry allocation, performance
- **Bond Analysis** — corporate and government bond discovery plus OHLCV, trades, and quotes
- **Batch Collection** — scheduled OHLCV, financial, and intraday data collection tasks
- **Multi-Source** — automatic fallback across 12 data providers

## Installation

### 1. Install the Python library

```bash
pip install claude-finance-kit
```

### 2. Install the AI plugin

<details>
<summary><strong>Codex</strong></summary>

Install the repo-local skill into Codex's documented `.agents/skills/` location:

```bash
npx claude-finance-kit-cli init --ai codex
```

Restart Codex if the skill does not appear immediately, then invoke `$finance-kit` or ask a Vietnamese-market analysis question naturally. Release ZIPs also contain the required `.codex-plugin/plugin.json` manifest for plugin distribution.

See OpenAI's [Codex plugin structure](https://learn.chatgpt.com/docs/build-plugins#plugin-structure) and [skill locations](https://learn.chatgpt.com/docs/build-skills#where-to-save-skills).

</details>

<details>
<summary><strong>Claude Code (via Marketplace)</strong></summary>

**Add the marketplace:**

```
/plugin marketplace add hongbietcode/claude-finance-kit
```

**Browse and install:**

Run `/plugin` to open the plugin manager. Go to the **Discover** tab to find `claude-finance-kit`.

Select it and choose an installation scope:
- **User scope** — available across all projects
- **Project scope** — available for all collaborators on this repository
- **Local scope** — available only for you in this repository

Or install directly:

```
/plugin install claude-finance-kit@hongbietcode-claude-finance-kit
```

Run `/reload-plugins` to activate.

</details>

<details>
<summary><strong>CLI alternatives (Claude Code, Cursor, Copilot)</strong></summary>

```bash
npx claude-finance-kit-cli init --ai cursor    # Cursor
npx claude-finance-kit-cli init --ai copilot   # GitHub Copilot
npx claude-finance-kit-cli init --ai claude    # Claude Code (CLI alternative)
```

</details>

## Quick Start

Once installed, just ask naturally — the plugin auto-invokes the right skill:

```
"Analyze FPT stock"                                        → finance-kit (stock deep dive)
"Market overview today"                                    → finance-kit (market briefing)
"Compare VNM vs MSN"                                       → finance-kit (comparative)
"Latest news sentiment for HPG"                            → finance-kit (news sentiment)
/finance-kit "tôi mua HPG ở giá 26.6k, có nên bán không" → finance-kit (full analysis)
```

### Python Library Usage

```python
from claude_finance_kit import Bond, Stock, Market, Macro, Commodity, Fund

# Stock data
stock = Stock("FPT")
stock.quote.history(start="2025-01-01", end="2025-12-31")
stock.finance.income_statement(period="quarter")
stock.company.overview()

# Bond data
bond = Bond("BAB123032")
bond.ohlcv(start="2025-01-01")
bond.trades()
bond.quote()

# Market valuation
market = Market("VNINDEX")
market.pe(duration="5Y")
market.top_gainer(limit=10)

# Macro indicators
macro = Macro()
macro.gdp()
macro.cpi()
macro.interest_rate()

# Commodities
commodity = Commodity()
commodity.gold()
commodity.oil()

# Fund analysis
fund = Fund()
fund.listing("STOCK")
```

### Technical Analysis

```python
from claude_finance_kit import Stock, Indicator

stock = Stock("FPT")
df = stock.quote.history(start="2025-01-01", end="2025-12-31")
df = df.set_index("time")

ind = Indicator(df)
ind.trend.sma(length=20)
ind.trend.ema(length=50)
ind.momentum.rsi(length=14)
ind.momentum.macd(fast=12, slow=26, signal=9)
ind.volatility.atr(length=14)
ind.volume.obv()
```

## Data Sources

| Source | Type | Coverage |
|--------|------|----------|
| **VCI** | Stock (default) | Quote, company, finance, listing, trading via REST — full VN coverage |
| **KBS** | Stock (fallback) | Same normalized stock coverage as VCI — full VN coverage |
| **MSN** | Stock | Historical OHLCV with dynamic MSN SecId resolution |
| **VCI** | Bond | Corporate/government listing, OHLCV, matched trades, current quote |
| **KBS** | Bond | Corporate listing and market data; no government-group discovery |
| **MAS** | Stock | Quote, intraday, financials, price depth |
| **TVS** | Stock | Company overview only |
| **VDS** | Stock | Intraday only |
| **FMP** | Stock (global) | Quote, company, financials — requires `FMP_API_KEY` |
| **BINANCE** | Crypto | History, intraday, depth — no API key |
| **VND** | Market | P/E, P/B, top movers |
| **MBK** | Macro | GDP, CPI, interest rates, FDI, trade balance |
| **FMARKET** | Fund | Mutual fund data (58+ funds) |
| **SPL** | Commodity | Gold, oil, steel, gas, fertilizer, agricultural |
| **Perplexity** | Search | Web search — requires `PERPLEXITY_API_KEY` |

> **Source fallback:** If VCI returns 403 (common on cloud IPs), the library automatically falls back to KBS. You can also specify manually: `Stock("FPT", source="KBS")`.

## Plugin Architecture

```
src/claude_finance_kit/       # Python library (PyPI)
cli/                          # npm CLI installer (claude-finance-kit-cli)
├── assets/
│   ├── skills/finance-kit/ # Single skill with references + scripts
│   ├── agents/               # fundamental-analyst, technical-analyst, macro-researcher, lead-analyst
│   ├── .codex-plugin/        # Codex plugin manifest
│   └── templates/            # Platform configs (claude, codex, cursor, copilot)
├── src/                      # CLI source code
└── dist/                     # Built CLI
.claude-plugin/               # Claude Marketplace manifest
```

### Skills & Agents

| Component | Type | Role |
|-----------|------|------|
| `finance-kit` | Skill | Senior analyst orchestrator (Marcus Vance). Single entry point — routes by complexity, spawns specialists, produces reports |
| `fundamental-analyst` | Agent | Financials, valuation, earnings (spawned by skill) |
| `technical-analyst` | Agent | Price trends, momentum, S/R levels (spawned by skill) |
| `macro-researcher` | Agent | GDP, CPI, rates, FX, commodities (spawned by skill) |
| `lead-analyst` | Agent | Synthesis + decision for T3/T4 analysis (spawned by skill) |
| `html-report-writer` | Agent | Self-contained HTML report generation for Claude Code; Codex falls back to the active agent |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FMP_API_KEY` | Optional | For global stock data via Financial Modeling Prep |
| `PERPLEXITY_API_KEY` | Optional | For web search via Perplexity API |

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/01-getting-started.md) | Installation, quickstart, architecture |
| [Stock Module](docs/02-stock-module.md) | Stock API with data models |
| [Market Module](docs/03-market-module.md) | Market valuation API |
| [Macro Module](docs/04-macro-module.md) | Macro indicators API |
| [Fund Module](docs/05-fund-module.md) | Fund analysis API |
| [Commodity Module](docs/06-commodity-module.md) | Commodity API |
| [Technical Analysis](docs/07-technical-analysis.md) | TA indicators reference |
| [Collector Module](docs/08-collector-module.md) | Collector tasks, scheduler |
| [News Module](docs/09-news-module.md) | News crawlers, sites |
| [Advanced Topics](docs/10-advanced-topics.md) | Provider registry, error handling |
| [Search Module](docs/11-search-module.md) | Perplexity Search API |
| [Bond Module](docs/12-bond-module.md) | Bond listing, OHLCV, trades, and quotes |

## Development

```bash
cd cli
npm install
npm run build              # Build CLI TypeScript
npm run bump -- patch      # Bump version (patch|minor|major)
```

### Version Sync

`npm run bump` updates version across all files:

| File | Field |
|------|-------|
| `pyproject.toml` | `version` |
| `src/claude_finance_kit/__init__.py` | `__version__` |
| `cli/package.json` | `version` |
| `cli/assets/.claude-plugin/plugin.json` | `version` |
| `cli/assets/.codex-plugin/plugin.json` | `version` |
| `.claude-plugin/marketplace.json` | `plugins[0].version` |

### Publishing

```bash
npm run bump -- patch
git commit -am "chore: bump version to X.Y.Z"
git tag vX.Y.Z
git push origin main --tags    # Triggers CI: PyPI + npm publish
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Commit your changes (`git commit -m 'feat: add my feature'`)
4. Push to the branch (`git push origin feat/my-feature`)
5. Open a Pull Request

## License

[MIT](LICENSE)

## Disclaimer

Reports generated by this toolkit are for **reference only** and do not constitute investment advice. You are responsible for your own capital allocation and risk management.
