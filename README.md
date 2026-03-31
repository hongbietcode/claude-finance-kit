# claude-finance-kit

Claude Code plugin for Vietnamese stock market analysis — fundamentals, technicals, macro, news, screening, and fund analysis.

## Install Plugin

```bash
GITHUB_TOKEN=ghp_xxx curl -fsSL https://gist.githubusercontent.com/hongbietcode/0b7845aedc0018c7ce551746c696811a/raw/9eb0536e37061faf7834e9ada8aea1e796f803ac/finance-kit-install.sh | bash
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

## Development

```bash
make help              # Show all commands
make requirements      # Export requirements.txt from pyproject.toml 
make package-plugin    # Package plugin files into zip
make build             # Build Python wheel + sdist
make bump TYPE=patch   # Bump version (patch|minor|major)
make release           # Tag + GitHub release with plugin zip + wheel
```

## License

MIT
