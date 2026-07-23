---
title: Vietnam providers
status: completed
priority: P1
effort: large
branch: main
tags: [dnse, ssi, vn]
created: 2026-07-23
---

# Phase 02: Vietnam providers

Status: completed

Add DNSE REST/WebSocket and SSI REST/official SDK stream adapters. Normalize
OHLCV, trades, order book, and foreign-flow records. Support SSI `ALL` only
when credentials and entitlements permit; otherwise expose degraded watchlist
mode.

## Requirements

- DNSE: signed REST requests, OHLCV, paged trades/quotes/foreign data,
  ping/pong, reconnect before eight hours and resubscription.
- SSI: official `ssi-fc-data` REST/stream envelopes, pagination, VN timezone,
  `X-TRADE`, `X-QUOTE`, `R`, and entitlement-dependent `ALL`.
- Classify block/deal trades separately and never embed credentials in errors.
- Use explicit watchlist AUTO polling in degraded mode; never emulate `ALL`.

## Files

- `src/claude_finance_kit/_provider/dnse/`
- `src/claude_finance_kit/_provider/ssi/`
- `src/claude_finance_kit/monitor/polling.py`
- VN provider/stream fixtures in `tests/test_provider_routing_and_streams.py`.

## Validation

- Official message-envelope parsing, HMAC/header shape, page traversal and UTC
  conversion.
- Reader failure propagation, bounded queues and symbol/index OHLC typing.
- Missing realtime credentials produce degraded polling only for watchlists.

## Risk and rollback

Entitlements vary by account. Runtime health and doctor expose degradation;
users can select an existing explicit provider if an official feed is
temporarily unavailable.
