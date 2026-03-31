# claude-finance-kit Python Package Installation Guide

Check first: if `.venv/` exists and `import claude_finance_kit` works, skip.

```bash
GITHUB_TOKEN=$(echo "<YOUR_BASE64_ENCODED_GITHUB_TOKEN>" | base64 --decode)
PACKGE_URL=@git+https://${GITHUB_TOKEN}@github.com/hongbietcode/claude-finance-kit.git

pip install "claude-finance-kit             @${PACKGE_URL}@main"  # Latest stable release
pip install "claude-finance-kit[all]        @${PACKGE_URL}@main"  # Latest stable release with all optional dependencies

pip install "claude-finance-kit[ta]         @${PACKGE_URL}@main"              # + Technical analysis
pip install "claude-finance-kit[collector]  @${PACKGE_URL}@main"    # + Batch data collector
pip install "claude-finance-kit[news]       @${PACKGE_URL}@main"        # + News crawlers
pip install "claude-finance-kit[all]        @${PACKGE_URL}@main"         # Everything
```

Requires Python >= 3.10.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FMP_API_KEY` | Only for FMP source | Global stocks (non-VN) |

## Source Fallback

If VCI returns 403 (common on cloud IPs): `Stock("FPT", source="KBS")`
