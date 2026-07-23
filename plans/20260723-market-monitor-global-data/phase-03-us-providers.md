---
title: US providers
status: completed
priority: P1
effort: medium
branch: main
tags: [alpaca, sec, us]
created: 2026-07-23
---

# Phase 03: US providers

Status: completed

Add Alpaca IEX REST/WebSocket market data and SEC EDGAR filings/company facts.
Enforce the 30-symbol realtime limit and label IEX coverage as partial. Retain
FMP as the limited EOD/fundamental fallback.

## Requirements

- Alpaca bars/trades/quotes use IEX, enforce total REST limits and a 30-symbol
  stream budget including `SPY`.
- SEC submissions and company facts use a responsible User-Agent and bounded
  request rate.
- Route US history `Alpaca → FMP` and company/fundamental/filing operations
  `SEC → FMP`.
- Never issue “whale confirmed” from partial IEX coverage.

## Files

- `src/claude_finance_kit/_provider/alpaca/`
- `src/claude_finance_kit/_provider/sec/`
- Existing FMP adapter and provider registry metadata.

## Validation

- Pagination, normalization, stream cap, coverage metadata and reader errors.
- SEC ticker resolution, filings URLs, XBRL statements and single-fetch ratios.
- AUTO ordering and rejected-auth/no-fallback behavior.

## Risk and rollback

Free feeds are incomplete and rate limited. Coverage labels remain mandatory;
explicit FMP and existing VN providers remain unaffected by rollback.
