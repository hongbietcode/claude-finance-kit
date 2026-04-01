# claude-finance-kit

Claude Code plugin for Vietnamese stock market analysis — fundamentals, technicals, macro, news, screening, and fund analysis.

## Install Plugin

```bash
curl -fsSL https://finhay.huutri2208.uk/install.sh | GITHUB_TOKEN=github_pat_xxx  bash
```

## What's Included

**Skills** (auto-invoked by context): stock-analysis, market-research, news-sentiment

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

## Multi-Platform Install

```bash
npx cfk init --ai claude    # Claude Code
npx cfk init --ai cursor    # Cursor
npx cfk init --ai copilot   # GitHub Copilot
```

## Development

```bash
cd cli
npm run build                # Build CLI TypeScript
npm run sync                 # Sync src/plugin/ -> cli/assets/
npm run export-requirements  # Export requirements.txt from pyproject.toml
npm run package-plugin       # Package plugin files into zip
npm run bump -- patch        # Bump version (patch|minor|major)
npm run release              # Package plugin + build wheel
```

## License

MIT
