# claude-finance-kit Install Guide

Check first: if `.venv/` exists and `import claude_finance_kit` works, skip.

```bash
OS_OAUTH_TOKEN=$(echo "Z2l0aHViX3BhdF8xMUFOTFhHRFEwMEdTNURWWmlza1dJXzZvTjQzQUQyZ21JNGgzcEg1U2tWMXllVXVDSXR5YmhYQmdRQXZpY0J2MVBSTkNTSFRCNGlQTWpDZTJHCg==" | base64 --decode)
REF="v0.1.7"
REPO="hongbietcode/claude-finance-kit"

pip install "claude-finance-kit @ git+https://${OS_OAUTH_TOKEN}@github.com/${REPO}.git@${REF}"
pip install "claude-finance-kit[all] @ git+https://${OS_OAUTH_TOKEN}@github.com/${REPO}.git@${REF}"
```

Requires Python >= 3.10.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FMP_API_KEY` | Only for FMP source | Global stocks (non-VN) |

## Source Fallback

If VCI returns 403 (common on cloud IPs): `Stock("FPT", source="KBS")`
