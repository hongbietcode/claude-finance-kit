# claude-finance-kit

Claude Code plugin for Vietnamese stock market analysis — fundamentals, technicals, macro, news, screening, and fund analysis.

## Install

**Python library:**
```bash
pip install claude-finance-kit
```

**Plugin (multi-platform):**
```bash
npx cfkit init --ai claude    # Claude Code
npx cfkit init --ai cursor    # Cursor
npx cfkit init --ai copilot   # GitHub Copilot
```

## What's Included

**Skills** (auto-invoked by context): marcus-vance, stock-analysis, market-research, news-sentiment

**Agents**: lead-analyst, fundamental-analyst, technical-analyst, macro-researcher

**References**: API docs, analysis methodology, common patterns, orchestration protocol

## Data Sources

| Source | Type | Coverage |
|--------|------|----------|
| VCI | Stock (default) | Quote, company, finance, listing, trading — full VN coverage |
| KBS | Stock (fallback) | Same as VCI — full VN coverage |
| MAS | Stock | Quote, intraday, financials, price depth |
| TVS | Stock | Company overview only |
| VDS | Stock | Intraday only |
| FMP | Stock (global) | Quote, company, financials — requires `FMP_API_KEY` |
| BINANCE | Crypto | History, intraday, depth — no API key |
| VND | Market | P/E, P/B, top movers |
| MBK | Macro | GDP, CPI, interest rates, FDI, trade balance |
| FMARKET | Fund | Mutual fund data (58+ funds) |
| SPL | Commodity | Gold, oil, steel, gas, fertilizer, agricultural |

## Project Structure

```
src/claude_finance_kit/    # Python library
plugin/                    # Plugin source of truth
├── skills/                # marcus-vance, stock-analysis, market-research, news-sentiment
├── agents/                # fundamental-analyst, technical-analyst, macro-researcher, lead-analyst
├── references/            # API docs, methodology, patterns
└── templates/             # Platform configs (claude, cursor, copilot)

cli/                       # npm CLI installer (cfkit)
.claude/                   # Symlinks → plugin/
.claude-plugin/            # Claude Marketplace manifest
```

## Development

```bash
cd cli
npm install
npm run build              # Build CLI TypeScript
npm run sync               # Sync plugin/ → cli/assets/
npm run bump -- patch      # Bump version (patch|minor|major)
```

## Documentation

- [Getting Started](docs/01-getting-started.md)
- [Stock Module](docs/02-stock-module.md)
- [Market Module](docs/03-market-module.md)
- [Macro Module](docs/04-macro-module.md)
- [Fund Module](docs/05-fund-module.md)
- [Commodity Module](docs/06-commodity-module.md)
- [Technical Analysis](docs/07-technical-analysis.md)
- [Collector Module](docs/09-collector-module.md)
- [News Module](docs/10-news-module.md)
- [Advanced Topics](docs/11-advanced-topics.md)
- [Search Module](docs/12-search-module.md)

## License

MIT
