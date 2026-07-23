---
title: VN/US Market Data and Signal Monitor
description: Free-tier data routing, unusual-flow monitoring, strategy validation, and paper alerts
status: completed
priority: P1
effort: large
branch: main
tags: [market-data, monitor, backtest, vn, us]
created: 2026-07-23
---

# VN/US Market Data and Signal Monitor

Status: completed

Progress: all phases and release gates completed

## Phases

1. [x] [Provider contracts and routing](phase-01-provider-contracts.md)
2. [x] [Vietnam data providers](phase-02-vietnam-providers.md)
3. [x] [US data providers](phase-03-us-providers.md)
4. [x] [Monitor and unusual-flow detection](phase-04-monitor-engine.md)
5. [x] [Strategies and backtesting](phase-05-strategy-backtest.md)
6. [x] [Paper trading, Telegram, and deployment](phase-06-runtime-delivery.md)
7. [x] [Documentation and release](phase-07-release.md)

## Dependencies

- Python 3.10+
- Free-tier credentials supplied only through environment variables
- SSI all-market scanning depends on the user's FastConnect permissions
- Alpaca Basic realtime coverage is IEX-only and limited to 30 symbols

## Acceptance criteria

- Existing explicit providers and their public DataFrame schemas remain compatible.
- AUTO routing reports actual source, attempts, freshness, and coverage.
- Monitor fails closed to `NO_TRADE` when feeds or validation are stale.
- Backtests use next-bar fills and share strategy logic with live evaluation.
- The runtime can be initialized, diagnosed, and run locally or with Docker.
- No brokerage order execution or new AI-agent workflow is introduced.
