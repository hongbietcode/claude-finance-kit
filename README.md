# claude-finance-kit

Claude Code plugin for Vietnamese stock market analysis — fundamentals, technicals, macro, news, screening, and fund analysis.

## Install

**Python library:**
```bash
pip install claude-finance-kit
```

**Plugin (multi-platform):**
```bash
npx cfk init --ai claude    # Claude Code
npx cfk init --ai cursor    # Cursor
npx cfk init --ai copilot   # GitHub Copilot
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

cli/                       # npm CLI installer (cfk)
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

## License

MIT
