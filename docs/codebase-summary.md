# Codebase Summary

Snapshot of `claude-finance-kit` generated from the current repository state and
the `repomix-output.xml` pack.

## Purpose

`claude-finance-kit` is a Python library and CLI for Vietnam and US market data,
research signals, backtesting, and a self-hosted paper-monitor runtime.

## Current State

| Area | What lives here |
|------|------------------|
| Python library | `src/claude_finance_kit/` with facades for stock, market, macro, fund, commodity, bond, search, monitor, and strategies |
| CLI | `src/claude_finance_kit/cli.py` exposes `cfk providers`, `cfk backtest`, and `cfk monitor {init,doctor,run,health}` |
| Providers | `_provider/` contains source-specific implementations and the capability-aware AUTO router |
| Strategies | `strategy/` contains the deterministic long-only rules, backtest engine, and walk-forward optimizer |
| Monitor | `monitor/` contains config loading, flow detection, paper execution, Telegram alerts, reporting, and storage |
| Docs | `docs/` contains user-facing module guides plus this repository summary |

## Verified Behavior

- `Stock(..., source="AUTO")` requires `market="VN"` or `market="US"`.
- AUTO results attach provenance in `DataFrame.attrs` via `source`,
  `attempted_sources`, `market`, `fetched_at`, `data_timestamp`,
  `delayed_seconds`, and `coverage`.
- AUTO fallback only advances on transport, throttling, outage, or unsupported-operation failures.
- The monitor is paper-only and does not connect to a brokerage order API.
- VN all-market monitoring requires SSI FastConnect entitlement; explicit
  watchlists can use degraded AUTO polling if realtime credentials are absent.
- US monitoring uses Alpaca Basic/IEX and counts the benchmark toward the 30-symbol free-tier cap.
- Strategy validation is fail-closed: missing or mismatched validation artifacts downgrade BUY to `NO_TRADE`.
- Validation binds market, regime, benchmark, exact parameters, source-data
  fingerprint, and freshness. Each fold selects only from its training window
  and tests that selection on the next OOS window; the final stable parameter
  set is evaluated on an untouched holdout.
- Signal dedupe, paper state, and outbound notifications use an atomic SQLite
  transaction; failed Telegram delivery stays in a durable retry outbox.
- SSI `MI:ALL` provides the VN benchmark path; completed minute aggregates are
  bounded and restored from SQLite after restart.
- Runtime validation is reloaded immediately before BUY, recurring HOLD states
  are suppressed, and daily unusual-flow report buffers are bounded.
- Both stream and monitor layers quarantine records outside known regular
  sessions before strategy evaluation or paper fills.
- Backtests and daily monitor summaries are written as HTML reports under `reports/`.

## Documentation Map

- [Getting Started](./01-getting-started.md)
- [Stock Module](./02-stock-module.md)
- [Market Module](./03-market-module.md)
- [Macro Module](./04-macro-module.md)
- [Fund Module](./05-fund-module.md)
- [Commodity Module](./06-commodity-module.md)
- [Technical Analysis](./07-technical-analysis.md)
- [Collector Module](./08-collector-module.md)
- [News Module](./09-news-module.md)
- [Advanced Topics](./10-advanced-topics.md)
- [Search Module](./11-search-module.md)
- [Bond Module](./12-bond-module.md)
- [Market Monitor](./13-market-monitor.md)

## Scope Notes

- This repo is centered on Vietnamese market workflows; US coverage is present
  where the verified provider layer supports it.
- Documentation should prefer explicit command names, exact env vars, and
  provider-specific limitations over general statements.
- Realtime and monitor docs should stay aligned with `pyproject.toml`,
  `monitor.example.toml`, and `src/claude_finance_kit/cli.py`.
