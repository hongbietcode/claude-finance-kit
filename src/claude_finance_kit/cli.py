"""`cfk` runtime CLI for providers, backtests, and the self-hosted monitor."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from claude_finance_kit.core.types import MarketRegime, MarketRegion
from claude_finance_kit.monitor.config import DEFAULT_CONFIG, ENV_EXAMPLE, MonitorConfig
from claude_finance_kit.monitor.engine import Monitor
from claude_finance_kit.monitor.storage import MonitorStore
from claude_finance_kit.monitor.telegram import TelegramNotifier
from claude_finance_kit.monitor.validation import valid_strategy_artifact
from claude_finance_kit.stock import Stock
from claude_finance_kit.strategy import BacktestEngine, StrategyRegistry, WalkForwardOptimizer


def _providers(_: argparse.Namespace) -> int:
    from claude_finance_kit._provider._registry import registry

    rows = []
    for descriptor in sorted(registry.list_descriptors(), key=lambda item: item.source):
        rows.append(
            {
                "source": descriptor.source,
                "markets": ",".join(sorted(item.value for item in descriptor.markets)),
                "capabilities": ",".join(sorted(item.value for item in descriptor.capabilities)),
                "coverage": descriptor.coverage,
                "auth": descriptor.requires_auth,
                "auth_type": descriptor.auth_type,
                "max_stream_symbols": descriptor.max_stream_symbols,
            }
        )
    print(json.dumps(rows, indent=2))
    return 0


def _write_validation(path: Path, result: Any, benchmark_symbol: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "market": result.market.value,
        "regime": result.regime.value,
        "validation_scope": "market_regime_benchmark",
        "benchmark_symbol": benchmark_symbol,
        "selected_strategy": result.selected_strategy,
        "strategy_parameters": result.selected_parameters,
        "data_fingerprint": result.data_fingerprint,
        "data_end": result.data_end,
        "fold_parameters": result.fold_parameters,
        "passed": result.passed,
        "action": result.action.value,
        "holdout_metrics": result.holdout_metrics,
        "reasons": result.reasons,
        "created_at": datetime.now(UTC).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _backtest(args: argparse.Namespace) -> int:
    market = MarketRegion(args.market)
    stock = Stock(args.symbol, source=args.source, market=market)
    bars = stock.quote.history(args.start, args.end, args.interval)
    if bars.empty:
        print("No price data returned.", file=sys.stderr)
        return 2
    benchmark_symbol = "VNINDEX" if market is MarketRegion.VN else "SPY"
    benchmark = Stock(
        benchmark_symbol,
        source="AUTO",
        market=market,
    ).quote.history(args.start, args.end, args.interval)
    if benchmark.empty:
        print(f"No benchmark data returned for {benchmark_symbol}.", file=sys.stderr)
        return 2
    output = Path(args.output or f"reports/{args.symbol.lower()}-{args.strategy}-backtest-report.html")
    if args.optimize:
        optimizer = WalkForwardOptimizer()
        result = optimizer.optimize(
            benchmark,
            market,
            MarketRegime(args.regime),
            benchmark=benchmark,
        )
        _write_validation(Path(args.validation_path), result, benchmark_symbol)
        summary = {
            "passed": result.passed,
            "selected_strategy": result.selected_strategy,
            "strategy_parameters": result.selected_parameters,
            "action": result.action.value,
            "reasons": result.reasons,
            "validation_path": args.validation_path,
        }
        print(json.dumps(summary, indent=2))
        if not result.selected_strategy:
            return 3
        strategy = StrategyRegistry.create(result.selected_strategy, **result.selected_parameters)
    else:
        strategy = StrategyRegistry.create(args.strategy)
    backtest = BacktestEngine().run(bars, strategy, market, benchmark=benchmark)
    backtest.to_html(output, f"{args.symbol.upper()} — {strategy.name}")
    print(str(output.resolve()))
    return 0 if (not args.optimize or result.passed) else 3


def _monitor_init(args: argparse.Namespace) -> int:
    config_path = Path(args.config)
    env_path = config_path.parent / ".env.example"
    if config_path.exists() and not args.force:
        print(f"{config_path} already exists; use --force to replace it.", file=sys.stderr)
        return 2
    source = args.source or ("SSI" if args.market == "VN" else "ALPACA")
    symbols = args.symbols or ("ALL" if args.market == "VN" else "AAPL,MSFT")
    config_text = DEFAULT_CONFIG.replace('market = "VN"', f'market = "{args.market}"')
    config_text = config_text.replace('source = "SSI"', f'source = "{source.upper()}"')
    config_text = config_text.replace('symbols = ["ALL"]', f"symbols = {json.dumps(symbols.upper().split(','))}")
    benchmark = "VNINDEX" if args.market == "VN" else "SPY"
    config_text = config_text.replace('benchmark_symbol = "VNINDEX"', f'benchmark_symbol = "{benchmark}"')
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(config_text, encoding="utf-8")
    if not env_path.exists():
        env_path.write_text(ENV_EXAMPLE, encoding="utf-8")
    print(f"Created {config_path} and {env_path}")
    print("Run `cfk monitor doctor --config <path>` before starting the bot.")
    return 0


def _credential_diagnostics(config: MonitorConfig) -> tuple[list[str], list[str]]:
    requirements = {
        "SSI": (
            ("SSI_CONSUMER_ID", "FC_DATA_CONSUMER_ID"),
            ("SSI_CONSUMER_SECRET", "FC_DATA_CONSUMER_SECRET"),
        ),
        "DNSE": (("DNSE_API_KEY",), ("DNSE_API_SECRET",)),
        "ALPACA": (
            ("ALPACA_API_KEY", "APCA_API_KEY_ID"),
            ("ALPACA_API_SECRET", "APCA_API_SECRET_KEY"),
        ),
    }
    missing_provider = [
        names[0]
        for names in requirements.get(config.source, ())
        if not any(os.getenv(name) for name in names)
    ]
    errors: list[str] = []
    warnings: list[str] = []
    if missing_provider:
        if "ALL" in config.symbols:
            errors.extend(f"Missing {name}" for name in missing_provider)
        elif (
            config.market is MarketRegion.US
            and not (os.getenv("FMP_API_KEY") or os.getenv("FMP_TOKEN"))
        ):
            errors.append(
                "Missing Alpaca realtime credentials and FMP_API_KEY for degraded US polling"
            )
        else:
            warnings.append(
                f"Missing {', '.join(missing_provider)}; monitor will use degraded AUTO watchlist polling"
            )
    if config.telegram_enabled:
        errors.extend(
            f"Missing {name}"
            for name in ("CFK_TELEGRAM_BOT_TOKEN", "CFK_TELEGRAM_CHAT_ID")
            if not os.getenv(name)
        )
    if config.require_strategy_validation and not config.strategy_validation_path.exists():
        errors.append(
            f"Missing passing strategy validation at {config.strategy_validation_path}; run `cfk backtest --optimize`"
        )
    elif config.require_strategy_validation:
        try:
            payload = json.loads(config.strategy_validation_path.read_text(encoding="utf-8"))
            strategy = StrategyRegistry.create(
                config.strategy,
                **config.strategy_parameters,
            )
            valid = valid_strategy_artifact(payload, config, strategy)
        except (OSError, ValueError, TypeError):
            valid = False
        if not valid:
            errors.append("Strategy validation artifact does not match market, strategy parameters, or data identity")
    return errors, warnings


def _credential_errors(config: MonitorConfig) -> list[str]:
    errors, _ = _credential_diagnostics(config)
    return errors


async def _probe_runtime(config: MonitorConfig, *, degraded: bool) -> dict[str, str]:
    symbol = next(
        (item for item in config.symbols if item != "ALL"),
        config.benchmark_symbol,
    )
    if symbol is None:
        raise ValueError("No symbol is available for the data probe")
    source = "AUTO" if degraded else config.source
    end = datetime.now(UTC).date()
    start = end - timedelta(days=14)
    stock = Stock(symbol, source=source, market=config.market)
    bars = await asyncio.to_thread(
        stock.quote.history,
        start.isoformat(),
        end.isoformat(),
        "1D",
    )
    if bars.empty:
        raise ConnectionError(f"{source} returned no history for the doctor probe")
    checks = {
        "data": str(bars.attrs.get("source", source)),
        "stream": "degraded-polling" if degraded else "connected",
        "telegram": "disabled",
    }
    if not degraded:
        from claude_finance_kit._provider._registry import registry

        provider_options = {
            key: value
            for key, value in config.provider_options.items()
            if key not in {"queue_size"}
        }
        stream = registry.get_stream(config.source)(**provider_options)
        stream_symbols = list(config.symbols)
        if (
            "ALL" not in stream_symbols
            and config.benchmark_symbol
            and config.benchmark_symbol not in stream_symbols
        ):
            stream_symbols.append(config.benchmark_symbol)
        try:
            await asyncio.wait_for(stream.connect(stream_symbols), timeout=15)
            await asyncio.sleep(1)
            queue = getattr(stream, "queue", None)
            if queue is not None and not queue.empty():
                candidate = queue.get_nowait()
                queue.task_done()
                if isinstance(candidate, Exception):
                    raise candidate
        finally:
            await stream.disconnect()
    if config.telegram_enabled:
        await TelegramNotifier().check()
        checks["telegram"] = "authenticated"
    return checks


def _monitor_doctor(args: argparse.Namespace) -> int:
    try:
        config = MonitorConfig.from_toml(args.config)
    except Exception as exc:
        print(f"Invalid monitor config: {exc}", file=sys.stderr)
        return 2
    errors, warnings = _credential_diagnostics(config)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    checks = {
        "configuration": "valid",
        "credentials": "degraded-fallback" if warnings else "present",
        "data": "not-probed",
        "stream": "not-probed",
        "telegram": "configured" if config.telegram_enabled else "disabled",
    }
    if not getattr(args, "offline", False):
        try:
            checks.update(asyncio.run(_probe_runtime(config, degraded=bool(warnings))))
        except Exception as exc:
            print(
                f"ERROR: online provider probe failed ({type(exc).__name__})",
                file=sys.stderr,
            )
            return 2
    print(
        json.dumps(
            {
                "status": "degraded" if warnings else "ready",
                "market": config.market.value,
                "source": config.source,
                "symbols": config.symbols,
                "benchmark_symbol": config.benchmark_symbol,
                "telegram": config.telegram_enabled,
                "strategy_validation": str(config.strategy_validation_path),
                "warnings": warnings,
                "checks": checks,
            },
            indent=2,
        )
    )
    return 0


async def _run_monitor(config_path: str) -> int:
    config = MonitorConfig.from_toml(config_path)
    monitor = Monitor(config)
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def request_stop() -> None:
        stop_event.set()

    for signal_name in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signal_name, request_stop)
        except NotImplementedError:  # pragma: no cover - Windows
            pass
    task = asyncio.create_task(monitor.run())
    stop_task = asyncio.create_task(stop_event.wait())
    done, _ = await asyncio.wait({task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
    if task in done:
        stop_task.cancel()
        await asyncio.gather(stop_task, return_exceptions=True)
        task.result()
        return 0
    await monitor.stop()
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    return 0


def _monitor_run(args: argparse.Namespace) -> int:
    return asyncio.run(_run_monitor(args.config))


def _monitor_health(args: argparse.Namespace) -> int:
    config = MonitorConfig.from_toml(args.config)
    if not config.database_path.exists():
        print("Monitor database does not exist.", file=sys.stderr)
        return 2
    store = MonitorStore(config.database_path)
    try:
        health = store.get_health(config.source)
    finally:
        store.close()
    if not health:
        print("No feed health checkpoint found.", file=sys.stderr)
        return 2
    last_event = datetime.fromisoformat(health["last_event_at"])
    age = (datetime.now(UTC) - last_event.astimezone(UTC)).total_seconds()
    maximum_age = max(
        config.stale_after_seconds * 2,
        config.health_heartbeat_seconds * 3,
    )
    healthy = (
        health["status"] in {"healthy", "idle"}
        and age <= maximum_age
    )
    print(json.dumps({**health, "age_seconds": age, "healthy": healthy}, indent=2))
    return 0 if healthy else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cfk", description="Claude Finance Kit runtime")
    subcommands = parser.add_subparsers(dest="command", required=True)

    providers = subcommands.add_parser("providers", help="List provider capabilities")
    providers.set_defaults(func=_providers)

    backtest = subcommands.add_parser("backtest", help="Backtest or optimize a bounded strategy family")
    backtest.add_argument("symbol")
    backtest.add_argument("--market", choices=["VN", "US"], required=True)
    backtest.add_argument("--source", default="AUTO")
    backtest.add_argument("--start", required=True)
    backtest.add_argument("--end")
    backtest.add_argument("--interval", default="1D")
    backtest.add_argument("--strategy", default="trend-momentum", choices=StrategyRegistry.names())
    backtest.add_argument("--regime", default="bull", choices=["bull", "range", "bear"])
    backtest.add_argument("--optimize", action="store_true")
    backtest.add_argument("--validation-path", default="data/strategy-validation.json")
    backtest.add_argument("--output")
    backtest.set_defaults(func=_backtest)

    monitor = subcommands.add_parser("monitor", help="Configure and run the signal monitor")
    monitor_commands = monitor.add_subparsers(dest="monitor_command", required=True)

    init = monitor_commands.add_parser("init")
    init.add_argument("--config", default="monitor.toml")
    init.add_argument("--market", choices=["VN", "US"], default="VN")
    init.add_argument("--source")
    init.add_argument("--symbols")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=_monitor_init)

    doctor = monitor_commands.add_parser("doctor")
    doctor.add_argument("--config", default="monitor.toml")
    doctor.add_argument(
        "--offline",
        action="store_true",
        help="Validate local configuration without provider or Telegram probes",
    )
    doctor.set_defaults(func=_monitor_doctor)

    run = monitor_commands.add_parser("run")
    run.add_argument("--config", default="monitor.toml")
    run.set_defaults(func=_monitor_run)

    health = monitor_commands.add_parser("health")
    health.add_argument("--config", default="monitor.toml")
    health.set_defaults(func=_monitor_health)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
