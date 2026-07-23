---
title: Runtime delivery
status: completed
priority: P1
effort: large
branch: main
tags: [paper, telegram, docker, cli]
created: 2026-07-23
---

# Phase 06: Runtime delivery

Status: completed

Add paper execution, SQLite persistence, Telegram outbound alerts, `cfk`
commands, configuration templates, Docker/Compose, health checks, retry,
chunking, cooldown, and secret redaction.

## Requirements

- Persist paper cash, open positions, pending signals, fills, P&L and dedupe
  state across restart.
- Provide `providers`, `backtest`, `monitor init`, `doctor`, `run` and `health`.
- Doctor checks local constraints and, by default, probes data, stream auth and
  Telegram without sending a message.
- Telegram is outbound-only, 4096-safe, rate-limit aware and token-safe.
- Suppress recurring HOLD messages and retain a bounded durable alert/report
  workload.
- Docker runs non-root with read-only config and persistent SQLite.

## Files

- `src/claude_finance_kit/{cli.py,monitor/}`
- `monitor.example.toml`, `.dockerignore`, `Dockerfile`, `compose.yaml`
- CLI, Telegram, paper and end-to-end runtime tests.

## Validation

- Restart and next-bar/gap fills, degraded-feed BUY cancellation and health.
- Telegram chunking, escaping, retry-after and transport redaction.
- Package CLI smoke, Docker build, non-root runtime and persistent volume.

## Risk and rollback

No broker adapter exists, so runtime mutations are limited to local SQLite,
reports and outbound Telegram. Stop the container and retain the volume for
recovery.
