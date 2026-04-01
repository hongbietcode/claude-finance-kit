# claude-finance-kit Python Package Installation Guide

Check first: if `.venv/` exists and `import claude_finance_kit` works, skip.

```bash
pip install claude-finance-kit              # Core
pip install "claude-finance-kit[all]"       # All optional dependencies
pip install "claude-finance-kit[ta]"        # + Technical analysis
pip install "claude-finance-kit[collector]" # + Batch data collector
pip install "claude-finance-kit[news]"      # + News crawlers
pip install "claude-finance-kit[search]"    # + Perplexity web search
```

Requires Python >= 3.10.

## Environment Variables

| Variable             | Required               | Description            |
| -------------------- | ---------------------- | ---------------------- |
| `FMP_API_KEY`        | Only for FMP source    | Global stocks (non-VN) |
| `PERPLEXITY_API_KEY` | Only for Search module | Perplexity web search  |

## Source Fallback

If VCI returns 403 (common on cloud IPs): `Stock("FPT", source="KBS")`
