# Phase 2: Python Source Imports

**Priority:** CRITICAL
**Status:** Pending
**Depends on:** Phase 1

## Tasks

1. Update `src/claude_finance_kit/core/exceptions.py` — rename `OpenStockError` → `ClaudeFinanceKitError`, error codes
2. Update `src/claude_finance_kit/core/__init__.py` — exports
3. Update `src/claude_finance_kit/__init__.py` — docstring, lazy imports
4. Find-replace `open_stock` → `claude_finance_kit` in ALL Python files under `src/`
5. Find-replace `OpenStockError` → `ClaudeFinanceKitError` in ALL Python files
6. Find-replace `open_stock` → `claude_finance_kit` in ALL test files under `tests/`
7. Find-replace `OpenStockError` → `ClaudeFinanceKitError` in ALL test files

## Success Criteria

- `python -c "from claude_finance_kit import Stock"` works
- All imports resolve correctly
