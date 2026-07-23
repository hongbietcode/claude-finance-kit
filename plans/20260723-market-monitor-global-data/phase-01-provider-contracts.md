---
title: Provider contracts and routing
status: completed
priority: P1
effort: medium
branch: main
tags: [providers, routing]
created: 2026-07-23
---

# Phase 01: Provider contracts and routing

Status: completed

Add market/capability enums, canonical event models, provider descriptors, an
opt-in AUTO router, provenance metadata, and backward-compatible trading
methods. Test capability filtering, fallback classification, and explicit
provider compatibility.

## Requirements

- Preserve explicit provider behavior and existing DataFrame schemas.
- Require `market` for AUTO and attach actual source, attempted chain, fetch
  time, delay and coverage.
- Fallback only for unsupported capability, throttling, transport failure or
  outage; surface authentication, symbol, schema and programming errors.
- Normalize canonical records to UTC while retaining exchange timezone.

## Files

- `src/claude_finance_kit/core/{types,models,exceptions}.py`
- `src/claude_finance_kit/_provider/{_base,_registry,_auto,_market_http}.py`
- `src/claude_finance_kit/stock/{__init__,trading}.py`
- Provider conformance tests under `tests/`.

## Validation

- Capability ordering for VN history, US history and US fundamentals.
- Provenance and hard-error/no-fallback tests.
- Legacy `StreamProvider` contract remains import-compatible.

## Risk and rollback

The primary risk is changing legacy source selection. AUTO remains opt-in, so
rollback is removal of AUTO registration without changing explicit providers.
