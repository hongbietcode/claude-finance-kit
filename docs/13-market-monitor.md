# VN/US Market Monitor

Research-only realtime monitoring with unusual-flow evidence, deterministic
long-only strategies, next-bar backtests, paper fills, and outbound Telegram
alerts. It never connects to a brokerage order API.

This page reflects the `0.2.0` runtime.

## Install

```bash
pip install "claude-finance-kit[monitor]"
cfk monitor init --config monitor.toml
```

`monitor init` also creates a local `.env.example`. Copy it to `.env`, insert
credentials, keep `.env` out of source control, then run:

```bash
cfk monitor doctor --config monitor.toml
cfk monitor run --config monitor.toml
```

Doctor performs an online history request, a stream authentication/connection
probe, and Telegram `getMe` by default. Provider entitlement can still change
after the probe, so runtime health and coverage labels remain authoritative.
For CI or an offline configuration audit:

```bash
cfk monitor doctor --config monitor.toml --offline
```

Required environment secrets:

```text
SSI_CONSUMER_ID
SSI_CONSUMER_SECRET
DNSE_API_KEY
DNSE_API_SECRET
ALPACA_API_KEY
ALPACA_API_SECRET
FMP_API_KEY
CFK_SEC_USER_AGENT
CFK_TELEGRAM_BOT_TOKEN
CFK_TELEGRAM_CHAT_ID
```

The default VN `ALL` configuration requires SSI FastConnect credentials and
permission. Use an explicit watchlist when all-market entitlement is
unavailable:

```toml
[monitor]
market = "VN"
source = "DNSE"
symbols = ["FPT", "HPG", "SSI"]
benchmark_symbol = "VNINDEX"
poll_interval_seconds = 60
```

When DNSE/SSI realtime credentials are absent, an explicit VN watchlist uses
AUTO intraday polling and reports `degraded`. This fallback never expands to
`ALL`, cannot open paper BUY positions, and retains actual source/fallback
metadata. A full-market request without SSI credentials fails doctor instead
of pretending to provide equivalent coverage.

US realtime uses Alpaca Basic/IEX:

```toml
[monitor]
market = "US"
source = "ALPACA"
symbols = ["AAPL", "MSFT", "NVDA"]
benchmark_symbol = "SPY"
```

The free IEX feed is partial-market coverage and accepts no more than 30
realtime symbols. The monitor therefore disables “whale confirmed” for US
events and includes a coverage warning in signals.

The configured benchmark is subscribed with each watchlist and drives regime
classification (`VNINDEX` for VN and `SPY` for US). It counts toward Alpaca's
30-symbol free-tier limit. SSI subscribes to the official `MI:ALL` index
channel, filters the configured benchmark, and builds completed minute bars
from index ticks.

## Validate a strategy first

BUY is fail-closed until the selected strategy has a passing walk-forward
artifact for the same market, current regime, exact strategy parameter set,
and a recorded 64-character source-data fingerprint:

```bash
cfk backtest FPT \
  --market VN \
  --source AUTO \
  --start 2021-01-01 \
  --optimize \
  --regime bull \
  --validation-path data/strategy-validation.json
```

Selection is performed per market/regime from a fixed family:

- EMA/ADX/volume trend momentum
- Donchian breakout with ATR
- RSI/Bollinger mean reversion in range regimes

The optimizer uses rolling two-year training, six-month out-of-sample tests,
four folds when enough history exists, and an untouched one-year holdout.
Failure of trade-count, expectancy, profit-factor, drawdown, deflated-Sharpe,
or holdout gates produces `NO_TRADE`.

Each fold selects parameters using only its own training window, then evaluates
that selection on the immediately following out-of-sample window. The final
runtime parameter set is chosen from training-selection stability and is
evaluated once on the untouched holdout. The artifact records every fold
selection, the final parameters, benchmark scope, data end time, and source
fingerprint; parameter, scope, or freshness drift invalidates it. By default,
an artifact older than 30 days or market data ending more than 7 days ago is
rejected. The Deflated/Probabilistic Sharpe gate uses only realized OOS equity
returns, their skew/kurtosis, and a fixed-family trial penalty—not in-sample or
holdout observations.

If the validation artifact is missing, mismatched, or the feed is not healthy,
the monitor also downgrades live BUY signals to `NO_TRADE`.

Backtests use signal-at-close and next-bar-open fills. Defaults are:

| Market | Commission | Sell tax | Slippage |
|--------|------------|----------|----------|
| VN | 0.15% each side | 0.10% | 0.05% each side |
| US | 0 | Configurable regulatory fee | 0.02% each side |

These are conservative research defaults, not broker quotations. Current
constituent lists can introduce survivorship bias.

The `cfk backtest` command writes an HTML report to
`reports/{symbol}-{strategy}-backtest-report.html`. The live monitor writes a
daily HTML report to `reports/monitor-YYYY-MM-DD-report.html`.

## Unusual-flow semantics

The detector reports “unusual/institutional-like flow”, not the identity of a
beneficial owner. Its evidence combines:

- relative trade notional and rolling percentile/z-score
- signed executed-trade imbalance
- five-minute same-side clustering
- participation versus configured average daily volume
- quote imbalance, VWAP price impact, and foreign flow

Executed trades are primary evidence. Quote imbalance alone cannot confirm a
signal because displayed orders can be cancelled. Put-through/block trades are
excluded from directional accumulation unless ordinary matched trades confirm
the direction.

Default confirmation requires score `75/100`, rolling `q99.5` notional and
absolute order-flow imbalance of at least `0.6`.

## Runtime safety

- Bounded queues drop the oldest item under pressure.
- Streams reconnect with jittered exponential backoff and resubscribe.
- DNSE reconnects before the documented eight-hour connection limit.
- Stale, future-dated, duplicated, out-of-order, disconnected, and degraded
  feeds cannot emit BUY.
- Pending paper BUY signals are discarded if feed health degrades before the
  next-bar fill.
- Repeated HOLD states are not persisted or sent to Telegram; alerts focus on
  actionable transitions and fail-closed `NO_TRADE` vetoes.
- Weekday exchange hours distinguish `idle` from `stale`; the built-in session
  check intentionally does not invent exchange-holiday data. Incoming
  pre-market and after-hours records are quarantined before strategy or paper
  execution.
- SQLite persists signals, alert dedupe, paper trades, mark-to-market equity,
  bounded completed-minute aggregates, checkpoints, health, and a durable
  Telegram outbox; raw all-market ticks are not persisted. Aggregate warmup is
  restored after restart. Signal dedupe, pending paper state, and the
  notification outbox are committed atomically.
- Daily unusual-flow summaries use the same cooldown buckets as alerts and
  retain a bounded number of events.
- Telegram is outbound-only, chunks at 4096 characters, retries server errors,
  honors `retry_after`, and leaves failed messages in the outbox for retry.
- Credentials are environment-only and are not included in logs or reports.
- Individual Telegram alerts do not create HTML files.

## Docker

```bash
cp monitor.example.toml monitor.toml
docker compose up --build -d
docker compose ps
```

Compose mounts configuration read-only, persists SQLite in a named volume,
runs as a non-root user, and checks feed freshness with:

```bash
cfk monitor health --config monitor.toml
```

## Provider constraints

| Provider | Market | Main capabilities | Limitation |
|----------|--------|-------------------|------------|
| DNSE | VN | OHLCV, trades, bid/ask, foreign flow, stream | API credentials; subscription quota |
| SSI | VN | OHLCV, listings, foreign daily data, `ALL` stream | Coverage depends on entitlement |
| VCI/KBS/MAS | VN | Existing history/fundamental fallbacks | Not the realtime backbone |
| Alpaca | US | Adjusted bars, IEX trades/quotes, stream | Partial IEX; 30 realtime symbols |
| SEC | US | Filings, submissions, XBRL facts | Responsible User-Agent required |
| FMP | US/global | EOD/fundamental fallback | Free-tier daily limits and delay |

AUTO routing records the selected source and attempted chain in
`DataFrame.attrs`. It never falls back on invalid symbols or rejected
credentials. US company facts and filings prefer `SEC → FMP`; US history
prefers `Alpaca → FMP`; VN history prefers `DNSE → SSI → VCI → KBS → MAS`.

## Security and methodology limitations

- Secrets are accepted only from environment variables. Secret-looking keys in
  `monitor.toml` are rejected.
- Authenticated URLs, tokens and provider exception bodies are not written to
  health checkpoints or alerts.
- The detector identifies unusual/institutional-like activity, not a beneficial
  owner. Quote imbalance is secondary to executed trades.
- Alpaca Basic is partial IEX coverage, so US “whale confirmed” remains
  disabled even when the stream is healthy.
- Walk-forward and a final holdout reduce, but do not eliminate, selection,
  survivorship and regime-shift bias. The result is never described as
  universally optimal.
- Paper fills are research simulations. There is no broker adapter, live order,
  margin, shorting or account synchronization.
