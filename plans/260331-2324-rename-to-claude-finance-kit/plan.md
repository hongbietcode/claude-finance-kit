# Rename: open-stock → claude-finance-kit

**Status:** Complete
**Created:** 2026-03-31
**Mode:** Parallel execution

## Overview

Rename entire project from `open-stock` / `open_stock` / `OpenStock` to `claude-finance-kit` / `claude_finance_kit` / `ClaudeFinanceKitError`. ~498 occurrences across ~140 files.

## Phases

| # | Phase | Status | Owner |
|---|-------|--------|-------|
| 1 | [Directory rename + config](phase-01-structure-and-config.md) | Complete | Main |
| 2 | [Python source imports](phase-02-python-imports.md) | Complete | Agent |
| 3 | [Documentation + metadata](phase-03-docs-and-metadata.md) | Complete | Agent |
| 4 | [Verification + testing](phase-04-verification.md) | Complete | Main |

## Dependencies

- Phase 1 MUST complete before Phase 2 (imports depend on directory rename)
- Phase 2 and Phase 3 can run in parallel after Phase 1
- Phase 4 runs after Phase 2 + 3 complete

## Mapping

| From | To |
|------|-----|
| `open-stock` | `claude-finance-kit` |
| `open_stock` | `claude_finance_kit` |
| `OpenStock` | `ClaudeFinanceKit` |
| `OpenStockError` | `ClaudeFinanceKitError` |
| `OPEN_STOCK_` | `CLAUDE_FINANCE_KIT_` |
