# claude-finance-kit

Claude Code plugin for Vietnamese stock market analysis — fundamentals, technicals, macro, news, screening, and fund analysis.

## Install

### Prerequisites

Install the Python library first:

```bash
pip install claude-finance-kit
```

### Claude Code (via Marketplace)

**1. Add the marketplace**

From within Claude Code, add the marketplace:

```
/plugin marketplace add hongbietcode/claude-finance-kit
```

**2. Browse and install**

Run `/plugin` to open the plugin manager. Go to the **Discover** tab to find `claude-finance-kit`.

Select it and choose an installation scope:
- **User scope** — install for yourself across all projects
- **Project scope** — install for all collaborators on this repository
- **Local scope** — install for yourself in this repository only

Or install directly from the command line:

```
/plugin install claude-finance-kit@hongbietcode-claude-finance-kit
```

**3. Activate and use**

Run `/reload-plugins` to activate. Plugin skills are auto-invoked by context — just ask:

```
"Analyze FPT stock"
"Market overview today"
"Latest news sentiment for VNM"
```

### Other AI Assistants (via CLI)

```bash
npx claude-finance-kit-cli init --ai cursor    # Cursor
npx claude-finance-kit-cli init --ai copilot   # GitHub Copilot
```

## What's Included

**Skills** (auto-invoked by context): marcus-vance, stock-analysis, market-research, news-sentiment

**Agents**: lead-analyst, fundamental-analyst, technical-analyst, macro-researcher

**References**: API docs, analysis methodology, common patterns, orchestration protocol

## Data Sources

| Source  | Type             | Coverage                                                     |
| ------- | ---------------- | ------------------------------------------------------------ |
| VCI     | Stock (default)  | Quote, company, finance, listing, trading — full VN coverage |
| KBS     | Stock (fallback) | Same as VCI — full VN coverage                               |
| MAS     | Stock            | Quote, intraday, financials, price depth                     |
| TVS     | Stock            | Company overview only                                        |
| VDS     | Stock            | Intraday only                                                |
| FMP     | Stock (global)   | Quote, company, financials — requires `FMP_API_KEY`          |
| BINANCE | Crypto           | History, intraday, depth — no API key                        |
| VND     | Market           | P/E, P/B, top movers                                         |
| MBK     | Macro            | GDP, CPI, interest rates, FDI, trade balance                 |
| FMARKET | Fund             | Mutual fund data (58+ funds)                                 |
| SPL     | Commodity        | Gold, oil, steel, gas, fertilizer, agricultural              |
| Perplexity | Search        | Web search via Perplexity API — requires `PERPLEXITY_API_KEY` |

## Project Structure

```
src/claude_finance_kit/    # Python library
cli/                       # npm CLI installer (claude-finance-kit-cli)
├── assets/                # Plugin source of truth
│   ├── skills/            # marcus-vance, stock-analysis, market-research, news-sentiment
│   ├── agents/            # fundamental-analyst, technical-analyst, macro-researcher, lead-analyst
│   ├── references/        # API docs, methodology, patterns
│   └── templates/         # Platform configs (claude, cursor, copilot)
├── src/                   # CLI source code
└── dist/                  # Built CLI
.claude-plugin/            # Claude Marketplace manifest
```

## Claude Marketplace

The plugin manifest lives in `.claude-plugin/`:

- **`marketplace.json`** — listing metadata, `source` points to `./cli/assets`
- **`plugin.json`** — plugin identity, version, keywords

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
| `.claude-plugin/plugin.json` | `version` |
| `.claude-plugin/marketplace.json` | `metadata.version` + `plugins[0].version` |

### Publishing

```bash
npm run bump -- patch
git commit -am "chore: bump version to X.Y.Z"
git tag vX.Y.Z
git push origin main --tags    # Triggers CI: PyPI + npm publish
```

## Documentation

- [Getting Started](docs/01-getting-started.md)
- [Stock Module](docs/02-stock-module.md)
- [Market Module](docs/03-market-module.md)
- [Macro Module](docs/04-macro-module.md)
- [Fund Module](docs/05-fund-module.md)
- [Commodity Module](docs/06-commodity-module.md)
- [Technical Analysis](docs/07-technical-analysis.md)
- [Collector Module](docs/08-collector-module.md)
- [News Module](docs/09-news-module.md)
- [Advanced Topics](docs/10-advanced-topics.md)
- [Search Module](docs/11-search-module.md)

## License

MIT
