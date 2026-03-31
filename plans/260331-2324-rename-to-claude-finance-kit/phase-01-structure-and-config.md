# Phase 1: Structure & Configuration

**Priority:** CRITICAL — blocks all other phases
**Status:** Pending

## Tasks

1. Rename directory `src/open_stock/` → `src/claude_finance_kit/`
2. Update `pyproject.toml` — name, packages, optional-deps, URLs, authors
3. Update `.claude-plugin/plugin.json` — name, description
4. Update `Makefile` — plugin artifact names
5. Update `scripts/package-plugin.sh` — artifact names
6. Update `requirements.txt` — package name
7. Update `LICENSE` — copyright holder name

## Success Criteria

- Directory exists at `src/claude_finance_kit/`
- `pyproject.toml` references `claude-finance-kit` everywhere
