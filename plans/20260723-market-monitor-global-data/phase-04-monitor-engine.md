---
title: Monitor engine
status: completed
priority: P1
effort: large
branch: main
tags: [stream, unusual-flow, health]
created: 2026-07-23
---

# Phase 04: Monitor engine

Status: completed

Build the bounded asynchronous pipeline, feed health and staleness gates,
checkpoint/deduplication storage, graceful shutdown, and evidence-based
unusual-flow scoring. Executed trades are primary; quotes are secondary and
block trades are classified separately.

## Requirements

- Reject stale, future, duplicated and out-of-order exchange timestamps.
- Quarantine incoming records outside known regular weekday sessions before
  strategy evaluation or paper execution.
- Distinguish healthy, degraded, stale, idle and disconnected states.
- Score rolling notional, z-score, ADV, OFI, clusters, sweeps, VWAP impact,
  book imbalance and available foreign flow.
- Exclude block trades and prevent quote-only spoof patterns from confirming.
- Persist aggregates, dedupe keys and health without storing full raw tick
  history.
- Build the configured VN benchmark from SSI index ticks and restore bounded
  completed-minute aggregates after restart.

## Files

- `src/claude_finance_kit/stream.py`
- `src/claude_finance_kit/monitor/{engine,flow,storage,config,polling}.py`
- Runtime and detector tests.

## Validation

- Reconnect/resubscribe, bounded queue, stale/future quarantine and shutdown.
- Warmup, zero volume, unknown side, block exclusion, sweep and foreign-flow
  tests.
- Restart-safe signal/alert dedupe and checkpoint recovery.
- Default SSI `ALL` benchmark warmup, aggregate restart recovery and bounded
  cooldown-deduplicated daily flow reports.

## Risk and rollback

Session hours do not invent holiday calendars. Outside known weekday sessions
the runtime reports idle; timestamp freshness still fails closed.
