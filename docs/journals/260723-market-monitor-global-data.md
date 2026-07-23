---
title: "VN/US market monitor release"
date: "2026-07-23 17:30"
severity: "High"
component: "provider routing, market stream, unusual-flow monitor, backtest"
status: "Resolved"
---

# VN/US market monitor release

## Context

We shipped the VN/US market monitor stack with capability-aware provider
routing, reconnectable streams, unusual-flow detection, deterministic
backtesting, and walk-forward strategy selection. The release spans
`AutoStockProvider`, `MarketStream`, the monitor runtime, and the shared
strategy/backtest stack.

## What happened

The monitor is fail-closed: BUY stays `NO_TRADE` until the selected strategy
has a passing walk-forward artifact for the same market and regime. The
optimizer can still refuse a setup when trade count, profit factor, drawdown,
Deflated Sharpe, or holdout gates fail. Runtime remains paper-only and never
connects to broker order APIs. US realtime accepts partial IEX coverage,
disables “whale confirmed,” and counts the `SPY` benchmark in the same
free-tier symbol budget as the watchlist.

The release review exposed contract drift in the first DNSE/SSI adapters,
over-trusting exchange timestamps, and a walk-forward result that did not
uniquely identify the deployed parameters. Those issues were corrected before
release: official message envelopes are normalized, stale/future/out-of-order
records are quarantined, each fold selects from its own training window and
tests on the immediately following OOS window, and the final stable parameters
are evaluated on an untouched holdout. Parameters, benchmark scope, data
fingerprint, and freshness are recorded for runtime validation.

## Reflection

The implementation chooses correctness over alert volume. Routed data carries
provenance, stale feeds degrade instead of pretending to be current, and
regime handling uses an explicit benchmark. More `NO_TRADE` outcomes are a
feature when data or validation quality is insufficient.

## Decisions

- Keep `NO_TRADE` as the default failure mode for invalid or unvalidated setups.
- Keep execution paper-only and exclude broker integrations.
- Expose partial IEX coverage instead of masking the gap.
- Treat the benchmark as part of the live subscription budget.
- Prefer free-tier compatibility over hidden paid assumptions.
- Allow explicit watchlists to degrade to polling, but never equate that mode
  with an entitled realtime or all-market feed.
- Persist signals, paper state, and the notification outbox atomically so
  restart and Telegram failures do not silently lose an alert.
- Restore completed-minute aggregates after restart, source `VNINDEX` from the
  official SSI index channel, and suppress recurring HOLD notification noise.
- Calculate the Deflated/Probabilistic Sharpe gate from realized OOS returns
  and their moments rather than annualized in-sample summary metrics.
- Quarantine extended-hours events at both the stream and monitor boundaries
  so regular-session paper semantics cannot be bypassed.

## Next

Preserve the release quality gates and watch for regressions in provider
routing, feed freshness, paper-state recovery, and walk-forward validation
before expanding venue or symbol coverage.
