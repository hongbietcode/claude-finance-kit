# claude-finance-kit Python Package Installation Guide

Always install **latest version**. Check first: if `.venv/` exists and `import claude_finance_kit` works, upgrade instead.

```bash
pip install -U claude-finance-kit              # Core (upgrade to latest)
pip install -U "claude-finance-kit[all]"       # All optional dependencies
pip install -U "claude-finance-kit[ta]"        # + Technical analysis
pip install -U "claude-finance-kit[collector]" # + Batch data collector
pip install -U "claude-finance-kit[news]"      # + News crawlers
pip install -U "claude-finance-kit[search]"    # + Perplexity web search
```

Requires Python >= 3.10.

## Environment Variables

| Variable             | Required               | Description            |
| -------------------- | ---------------------- | ---------------------- |
| `FMP_API_KEY`        | Only for FMP source    | Global stocks (non-VN) |
| `PERPLEXITY_API_KEY` | Only for Search module | Perplexity web search  |

## Source Fallback

If VCI returns 403 (common on cloud IPs): `Stock("FPT", source="KBS")`
