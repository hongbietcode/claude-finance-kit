---
title: Strategy and backtest
status: completed
priority: P1
effort: large
branch: main
tags: [strategy, backtest, walk-forward]
created: 2026-07-23
---

# Phase 05: Strategy and backtest

Status: completed

Implement deterministic long-only strategies, market regime detection,
next-bar backtesting, conservative costs, walk-forward selection by
market/regime, untouched holdout validation, and strict `NO_TRADE` gates.

## Requirements

- Keep one pure strategy contract for live evaluation and backtests.
- Use benchmark SMA50/SMA200/ADX regime, range-only mean reversion and no
  long entry in bear regimes.
- Fill at next-bar open; use shared stop/target gap behavior and explicit VN/US
  costs.
- In each fold, select parameters using only the training window and evaluate
  them on the immediately following OOS window.
- Choose the final parameter set from training-selection stability, test it
  once on an untouched holdout, then apply strict gates.
- Bind validation to market, regime, benchmark, exact parameters, data
  fingerprint and freshness.
- Compute the strict Deflated/Probabilistic Sharpe gate from OOS return
  observations and moments with a fixed-family trial penalty.

## Files

- `src/claude_finance_kit/strategy/{rules,execution,backtest,walk_forward}.py`
- CLI validation artifact writer.
- Golden backtest and walk-forward tests.

## Validation

- No look-ahead, ordered/unique timestamps, benchmark alignment and inferred
  annualization.
- OOS windows, fold-local selection, exact deployed parameters, untouched
  holdout, deterministic selection and failed-gate `NO_TRADE`.
- Shared live/backtest/paper stop, target, commission, tax and slippage logic.

## Risk and rollback

Walk-forward reduces but cannot eliminate selection and survivorship bias.
Failing any gate disables BUY; rollback can retain reports while disabling
runtime validation artifacts.
