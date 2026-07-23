"""Monitor config, storage, paper, Telegram, engine, and CLI tests."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from argparse import Namespace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from claude_finance_kit._provider.ssi.stream import SSIStreamProvider
from claude_finance_kit.cli import (
    _monitor_doctor,
    _monitor_health,
    _monitor_init,
    _write_validation,
)
from claude_finance_kit.core.models import (
    Bar,
    MarketEvent,
    Signal,
    TradeTick,
    UnusualFlowEvent,
)
from claude_finance_kit.core.types import FeedHealth, MarketRegime, MarketRegion, SignalAction
from claude_finance_kit.monitor import engine as engine_module
from claude_finance_kit.monitor import polling as polling_module
from claude_finance_kit.monitor.config import MonitorConfig
from claude_finance_kit.monitor.engine import Monitor
from claude_finance_kit.monitor.paper import PaperBroker
from claude_finance_kit.monitor.polling import PollingMarketStream
from claude_finance_kit.monitor.storage import MonitorStore
from claude_finance_kit.monitor.telegram import TelegramNotifier
from claude_finance_kit.strategy import (
    BacktestConfig,
    BacktestEngine,
    WalkForwardConfig,
    WalkForwardOptimizer,
)
from claude_finance_kit.strategy.rules import Strategy as RulesStrategy


@pytest.fixture(autouse=True)
def _regular_session_for_runtime_tests(monkeypatch):
    monkeypatch.setattr(engine_module, "market_session_open", lambda *args: True)


def _bars(count: int = 3) -> pd.DataFrame:
    times = pd.date_range("2026-07-23 09:00", periods=count, freq="D", tz="UTC")
    return pd.DataFrame(
        {
            "time": times,
            "open": [100 + i * 10 for i in range(count)],
            "high": [101 + i * 10 for i in range(count)],
            "low": [99 + i * 10 for i in range(count)],
            "close": [100.5 + i * 10 for i in range(count)],
            "volume": [1_000 + i * 100 for i in range(count)],
        }
    )


class ScheduledStrategy(RulesStrategy):
    name = "scheduled"

    def __init__(self, actions: list[str]):
        self.actions = actions

    def generate(
        self, bars: pd.DataFrame, market: MarketRegion | str, benchmark: pd.DataFrame | None = None
    ) -> pd.DataFrame:
        frame = bars.reset_index(drop=True)
        actions = (self.actions + [SignalAction.NO_TRADE.value] * len(frame))[: len(frame)]
        return pd.DataFrame(
            {
                "action": actions,
                "confidence": [80.0] * len(frame),
                "regime": [MarketRegime.BULL.value] * len(frame),
                "stop_loss": frame["close"] - 2,
                "take_profit": frame["close"] + 2,
                "reason": ["test"] * len(frame),
            }
        )


class ParameterStrategy(RulesStrategy):
    name = "parameter-strategy"

    def __init__(self, scale: int):
        self.scale = scale

    def generate(
        self, bars: pd.DataFrame, market: MarketRegion | str, benchmark: pd.DataFrame | None = None
    ) -> pd.DataFrame:
        return ScheduledStrategy([SignalAction.NO_TRADE.value]).generate(bars, market, benchmark)


class CountingStrategy(ScheduledStrategy):
    name = "counting"

    def __init__(self):
        super().__init__([SignalAction.HOLD.value] * 300)
        self.calls = 0

    def evaluate(self, *args, **kwargs):
        self.calls += 1
        return super().evaluate(*args, **kwargs)


class RecordingBacktestEngine:
    def __init__(self) -> None:
        self.calls: list[tuple[int, bool]] = []

    def run(self, bars, strategy, market, *, benchmark=None, evaluation_start=None):
        self.calls.append((strategy.scale, evaluation_start is not None))
        score = float(strategy.scale)
        return SimpleNamespace(
            metrics={
                "calmar": score,
                "sharpe": score,
                "turnover": 0.01,
                "max_drawdown": 0.05,
                "trades": 20.0,
                "expectancy": 1.0,
                "profit_factor": 2.0,
            }
        )


class FoldChangingBacktestEngine:
    """Select a different candidate when a later training window changes."""

    def __init__(self) -> None:
        self.oos_scales: list[int] = []

    def run(self, bars, strategy, market, *, benchmark=None, evaluation_start=None):
        if evaluation_start is None:
            preferred = 1 if float(bars["open"].max()) < 220 else 2
            score = 10.0 if strategy.scale == preferred else 1.0
        else:
            self.oos_scales.append(strategy.scale)
            score = 2.0
        return SimpleNamespace(
            metrics={
                "calmar": score,
                "sharpe": score,
                "turnover": 0.01,
                "max_drawdown": 0.05,
                "trades": 20.0,
                "expectancy": 1.0,
                "profit_factor": 2.0,
            }
        )


class DummyStream:
    def __init__(self) -> None:
        self.stopped = False

    async def stop(self) -> None:
        self.stopped = True


class DummyResponse:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload


def test_monitor_config_validation_rules(tmp_path):
    with pytest.raises(ValueError, match="limited to 30 symbols"):
        MonitorConfig(market="US", source="ALPACA", symbols=[f"SYM{i:02d}" for i in range(31)])

    with pytest.raises(ValueError, match="requires source='ALPACA'"):
        MonitorConfig(market="US", source="SSI", symbols=["AAPL"])

    with pytest.raises(ValueError, match="requires source='SSI'"):
        MonitorConfig(market="VN", source="DNSE", symbols=["ALL"])
    with pytest.raises(ValueError, match="cooldown"):
        MonitorConfig(
            market="US",
            source="ALPACA",
            symbols=["AAPL"],
            alert_cooldown_seconds=0,
        )
    with pytest.raises(ValueError, match="flow_quantile"):
        MonitorConfig(
            market="US",
            source="ALPACA",
            symbols=["AAPL"],
            flow_quantile=1.1,
        )
    with pytest.raises(ValueError, match="must come from environment"):
        MonitorConfig(
            market="VN",
            source="DNSE",
            symbols=["FPT"],
            provider_options={"api_key": "not-allowed"},
        )

    config_path = tmp_path / "monitor.toml"
    config_path.write_text(
        """
[monitor]
market = "US"
source = "ALPACA"
symbols = ["AAPL"]
database_path = "data/monitor.db"
reports_dir = "reports"

[strategy]
name = "trend-momentum"
require_validation = false
validation_path = "data/strategy-validation.json"

[paper]
starting_cash = 250000000
notional = 25000000

[telegram]
enabled = false
""".strip(),
        encoding="utf-8",
    )
    parsed = MonitorConfig.from_toml(config_path)

    assert parsed.market is MarketRegion.US
    assert parsed.source == "ALPACA"
    assert parsed.symbols == ["AAPL"]
    assert parsed.paper_notional == 25_000_000


def test_backtest_uses_next_bar_open_and_explicit_costs():
    engine = BacktestEngine(
        BacktestConfig(
            starting_cash=1_000.0,
            commission_per_side=0.01,
            sell_tax=0.02,
            slippage_per_side=0.05,
        )
    )
    result = engine.run(_bars(3), ScheduledStrategy(["BUY", "EXIT", "NO_TRADE"]), MarketRegion.US)

    assert result.trades.shape[0] == 2
    assert result.trades.iloc[0]["time"] == pd.Timestamp("2026-07-24 09:00:00+0000", tz="UTC")
    assert result.trades.iloc[0]["price"] == pytest.approx(110.0 * (1 + 0.05))
    assert result.trades.iloc[1]["time"] == pd.Timestamp("2026-07-25 09:00:00+0000", tz="UTC")
    assert result.trades.iloc[1]["price"] == pytest.approx(120.0 * (1 - 0.05))
    assert result.metrics["trades"] == 1.0
    assert "drawdown" in result.equity


def test_backtest_report_escapes_user_supplied_title(tmp_path):
    result = BacktestEngine().run(
        _bars(3),
        ScheduledStrategy(["BUY", "EXIT", "NO_TRADE"]),
        MarketRegion.US,
    )

    report = result.to_html(tmp_path / "report.html", title="<script>alert(1)</script>")
    html = report.read_text(encoding="utf-8")

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_walk_forward_returns_no_trade_when_data_is_insufficient():
    optimizer = WalkForwardOptimizer(candidates=[ScheduledStrategy(["BUY", "EXIT", "NO_TRADE"])])
    result = optimizer.optimize(_bars(100), MarketRegion.US, MarketRegime.BULL)

    assert result.action is SignalAction.NO_TRADE
    assert result.selected_strategy is None
    assert not result.passed
    assert "Need at least" in result.reasons[0]


def test_walk_forward_validates_each_fold_selection_on_its_immediate_oos_window():
    engine = RecordingBacktestEngine()
    optimizer = WalkForwardOptimizer(
        engine=engine,
        config=WalkForwardConfig(
            train_bars=10,
            test_bars=5,
            holdout_bars=5,
            minimum_folds=2,
            minimum_oos_trades=1,
            minimum_dsr_probability=0,
        ),
        candidates=[ParameterStrategy(1), ParameterStrategy(2)],
    )

    result = optimizer.optimize(_bars(25), MarketRegion.US, MarketRegime.BULL)
    evaluated_parameters = [scale for scale, is_oos in engine.calls if is_oos]

    assert result.selected_strategy == "parameter-strategy"
    assert result.selected_parameters == {"scale": 2}
    assert evaluated_parameters == [2, 2, 2]
    assert len(result.fold_metrics) == 2


def test_walk_forward_does_not_use_later_training_windows_for_earlier_fold_selection():
    engine = FoldChangingBacktestEngine()
    optimizer = WalkForwardOptimizer(
        engine=engine,
        config=WalkForwardConfig(
            train_bars=10,
            test_bars=5,
            holdout_bars=5,
            minimum_folds=2,
            minimum_oos_trades=1,
            minimum_dsr_probability=0,
        ),
        candidates=[ParameterStrategy(1), ParameterStrategy(2)],
    )

    result = optimizer.optimize(_bars(25), MarketRegion.US, MarketRegime.BULL)

    assert result.fold_parameters == [{"scale": 1}, {"scale": 2}]
    assert engine.oos_scales[:2] == [1, 2]
    assert len(engine.oos_scales) == 3  # two folds plus untouched holdout


def test_walk_forward_requires_explicit_temporal_bars():
    optimizer = WalkForwardOptimizer(candidates=[ParameterStrategy(1)])

    with pytest.raises(ValueError, match="requires timezone-aware time bars"):
        optimizer.optimize(
            _bars(25).drop(columns=["time"]),
            MarketRegion.US,
            MarketRegime.BULL,
        )


def test_deflated_sharpe_uses_oos_scale_and_penalizes_many_trials():
    returns = pd.Series([0.002, -0.001] * 100)

    one_trial = WalkForwardOptimizer._dsr_probability(returns, trials=1)
    many_trials = WalkForwardOptimizer._dsr_probability(returns, trials=10_000)

    assert one_trial > 0.95
    assert many_trials < one_trial


def test_validation_artifact_is_market_benchmark_scoped(tmp_path):
    result = SimpleNamespace(
        market=MarketRegion.US,
        regime=MarketRegime.BULL,
        selected_strategy="trend-momentum",
        selected_parameters={"fast": 20},
        data_fingerprint="a" * 64,
        data_end=datetime.now(UTC).isoformat(),
        fold_parameters=[{"fast": 20}],
        passed=True,
        action=SignalAction.HOLD,
        holdout_metrics={"expectancy": 1.0},
        reasons=["passed"],
    )
    path = tmp_path / "validation.json"

    _write_validation(path, result, "SPY")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["validation_scope"] == "market_regime_benchmark"
    assert payload["benchmark_symbol"] == "SPY"
    assert payload["data_end"] == result.data_end


def test_paper_broker_executes_next_bar_and_persists_trades(tmp_path):
    store = MonitorStore(tmp_path / "monitor.db")
    broker = PaperBroker(
        MarketRegion.US,
        store,
        starting_cash=1_000.0,
        notional=500.0,
        backtest_config=BacktestConfig(
            starting_cash=1_000.0,
            commission_per_side=0.01,
            sell_tax=0.02,
            slippage_per_side=0.05,
        ),
    )
    signal = Signal(
        symbol="aapl",
        market=MarketRegion.US,
        timestamp=datetime(2026, 7, 23, 9, 0, tzinfo=UTC),
        action=SignalAction.BUY,
        confidence=80,
        regime=MarketRegime.BULL,
        strategy="trend-momentum",
        stop_loss=90.0,
        take_profit=130.0,
    )
    broker.on_signal(signal)

    buy = broker.on_bar(
        Bar(
            symbol="aapl",
            market=MarketRegion.US,
            timestamp=datetime(2026, 7, 23, 9, 1, tzinfo=UTC),
            source="ALPACA",
            exchange_timezone="America/New_York",
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.0,
            volume=100.0,
        )
    )
    sell = broker.on_bar(
        Bar(
            symbol="aapl",
            market=MarketRegion.US,
            timestamp=datetime(2026, 7, 23, 9, 2, tzinfo=UTC),
            source="ALPACA",
            exchange_timezone="America/New_York",
            open=110.0,
            high=111.0,
            low=89.0,
            close=105.0,
            volume=100.0,
        )
    )

    rows = store.connection.execute("SELECT side, payload FROM paper_trades ORDER BY id").fetchall()
    equity_rows = store.connection.execute(
        "SELECT cash, position_value, equity FROM paper_equity ORDER BY id"
    ).fetchall()

    assert buy["side"] == "BUY"
    assert buy["price"] == pytest.approx(105.0)
    assert sell["side"] == "SELL"
    assert sell["price"] == pytest.approx(90.0 * (1 - 0.05))
    assert [row[0] for row in rows] == ["BUY", "SELL"]
    assert len(equity_rows) == 2
    assert equity_rows[-1][2] == pytest.approx(broker.equity)
    store.close()


def test_signal_state_and_notification_are_rolled_back_together(tmp_path):
    store = MonitorStore(tmp_path / "monitor.db")
    store.connection.executescript(
        """
        CREATE TRIGGER reject_signal_checkpoint
        BEFORE INSERT ON checkpoints
        WHEN NEW.key = 'paper:US'
        BEGIN
            SELECT RAISE(ABORT, 'checkpoint rejected');
        END;
        """
    )
    signal = Signal(
        symbol="AAPL",
        market=MarketRegion.US,
        timestamp=datetime(2026, 7, 23, 9, 0, tzinfo=UTC),
        action=SignalAction.BUY,
        confidence=80,
        regime=MarketRegime.BULL,
        strategy="trend-momentum",
    )

    with pytest.raises(sqlite3.IntegrityError, match="checkpoint rejected"):
        store.save_signal_state_and_notification(
            "signal-key",
            signal,
            "paper:US",
            {"cash": 1_000},
            "telegram",
            "BUY AAPL",
        )

    assert not store.signal_seen("signal-key")
    assert store.get_notification("signal-key") is None
    store.close()


def test_paper_broker_restores_cash_positions_and_uses_gap_stop(tmp_path):
    database = tmp_path / "monitor.db"
    store = MonitorStore(database)
    config = BacktestConfig(
        starting_cash=1_000.0,
        commission_per_side=0,
        sell_tax=0,
        slippage_per_side=0,
    )
    broker = PaperBroker(
        MarketRegion.US,
        store,
        starting_cash=1_000.0,
        notional=500.0,
        backtest_config=config,
    )
    broker.on_signal(
        Signal(
            symbol="AAPL",
            market=MarketRegion.US,
            timestamp=datetime(2026, 7, 23, 9, 0, tzinfo=UTC),
            action=SignalAction.BUY,
            confidence=80,
            regime=MarketRegime.BULL,
            strategy="trend-momentum",
            stop_loss=90,
        )
    )
    broker.on_bar(
        Bar(
            symbol="AAPL",
            market=MarketRegion.US,
            timestamp=datetime(2026, 7, 23, 9, 1, tzinfo=UTC),
            source="ALPACA",
            exchange_timezone="America/New_York",
            open=100,
            high=101,
            low=99,
            close=100,
            volume=100,
        )
    )
    expected_cash = broker.cash
    store.close()

    restored_store = MonitorStore(database)
    restored = PaperBroker(
        MarketRegion.US,
        restored_store,
        starting_cash=1_000.0,
        notional=500.0,
        backtest_config=config,
    )
    assert restored.cash == pytest.approx(expected_cash)
    assert restored.positions["AAPL"].quantity == pytest.approx(5)

    fill = restored.on_bar(
        Bar(
            symbol="AAPL",
            market=MarketRegion.US,
            timestamp=datetime(2026, 7, 23, 9, 2, tzinfo=UTC),
            source="ALPACA",
            exchange_timezone="America/New_York",
            open=80,
            high=82,
            low=79,
            close=81,
            volume=100,
        )
    )
    assert fill["price"] == pytest.approx(80)
    assert "AAPL" not in restored.positions
    restored_store.close()


def test_paper_equity_skips_unrelated_all_market_bars(tmp_path):
    store = MonitorStore(tmp_path / "monitor.db")
    broker = PaperBroker(
        MarketRegion.VN,
        store,
        starting_cash=1_000,
        notional=500,
    )
    timestamp = datetime(2026, 7, 23, 2, 0, tzinfo=UTC)

    for index in range(100):
        broker.on_bar(
            Bar(
                symbol=f"SYM{index}",
                market=MarketRegion.VN,
                timestamp=timestamp,
                source="SSI",
                exchange_timezone="Asia/Ho_Chi_Minh",
                open=10,
                high=10,
                low=10,
                close=10,
                volume=100,
            )
        )

    rows = store.connection.execute("SELECT COUNT(*) FROM paper_equity").fetchone()
    assert rows[0] == 0
    store.close()


def test_paper_broker_drops_pending_buy_when_feed_is_degraded(tmp_path):
    store = MonitorStore(tmp_path / "monitor.db")
    broker = PaperBroker(
        MarketRegion.US,
        store,
        starting_cash=1_000,
        notional=500,
    )
    broker.on_signal(
        Signal(
            symbol="AAPL",
            market=MarketRegion.US,
            timestamp=datetime(2026, 7, 23, 9, 0, tzinfo=UTC),
            action=SignalAction.BUY,
            confidence=80,
            regime=MarketRegime.BULL,
            strategy="trend-momentum",
        )
    )

    fill = broker.on_bar(
        Bar(
            symbol="AAPL",
            market=MarketRegion.US,
            timestamp=datetime(2026, 7, 23, 9, 1, tzinfo=UTC),
            source="FMP",
            exchange_timezone="America/New_York",
            open=100,
            high=101,
            low=99,
            close=100,
            volume=100,
        ),
        allow_entry=False,
    )

    assert fill is None
    assert "AAPL" not in broker.pending
    assert "AAPL" not in broker.positions
    store.close()


def test_monitor_uses_degraded_polling_for_watchlist_without_stream_credentials(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("DNSE_API_KEY", raising=False)
    monkeypatch.delenv("DNSE_API_SECRET", raising=False)
    config = MonitorConfig(
        market="VN",
        source="DNSE",
        symbols=["FPT"],
        database_path=tmp_path / "monitor.db",
        reports_dir=tmp_path / "reports",
        require_strategy_validation=False,
        telegram_enabled=False,
    )

    monitor = Monitor(config)

    assert isinstance(monitor.stream, PollingMarketStream)
    assert monitor.stream.symbols == ["FPT", "VNINDEX"]
    asyncio.run(monitor.stop())


def test_degraded_polling_aggregates_ticks_and_localizes_exchange_time(monkeypatch):
    frame = pd.DataFrame(
        {
            "time": ["2026-07-23 09:00:01", "2026-07-23 09:00:40"],
            "price": [10.0, 11.0],
            "volume": [100, 200],
        }
    )
    frame.attrs.update(source="VCI", attempted_sources=["VCI"], interval="1m")

    class FakeQuote:
        def intraday(self):
            return frame

    class FakeStock:
        def __init__(self, *args, **kwargs):
            self.quote = FakeQuote()

    monkeypatch.setattr(polling_module, "Stock", FakeStock)
    poller = PollingMarketStream(MarketRegion.VN, ["FPT"])

    event = poller._latest_bar("FPT")

    assert event.record.timestamp == datetime(2026, 7, 23, 2, 0, tzinfo=UTC)
    assert (event.record.open, event.record.high, event.record.close) == (10, 11, 11)
    assert event.record.volume == 300
    assert event.metadata["actual_source"] == "VCI"


def test_degraded_polling_uses_intraday_history_for_vn_index(monkeypatch):
    frame = pd.DataFrame(
        {
            "time": [datetime.now(UTC).replace(second=0, microsecond=0)],
            "open": [1500],
            "high": [1502],
            "low": [1499],
            "close": [1501],
            "volume": [1_000_000],
        }
    )
    frame.attrs.update(source="VCI", attempted_sources=["VCI"], interval="1m")
    calls: list[tuple[str, object]] = []

    class FakeQuote:
        def intraday(self):
            raise ValueError("Intraday data not supported for index 'VNINDEX'.")

        def history(self, *, start, interval):
            calls.append((start, interval))
            return frame

    class FakeStock:
        def __init__(self, *args, **kwargs):
            self.quote = FakeQuote()

    monkeypatch.setattr(polling_module, "Stock", FakeStock)
    poller = PollingMarketStream(MarketRegion.VN, ["VNINDEX"])

    event = poller._latest_bar("VNINDEX")

    assert calls[0][1] == "1m"
    assert event.record.symbol == "VNINDEX"
    assert event.record.close == 1501


def test_monitor_loads_validation_and_records_health(tmp_path):
    validation_path = tmp_path / "validation.json"
    validation_path.write_text(
        json.dumps(
                {
                    "passed": True,
                    "market": "US",
                    "regime": "bull",
                    "validation_scope": "market_regime_benchmark",
                    "benchmark_symbol": "SPY",
                    "selected_strategy": "trend-momentum",
                    "strategy_parameters": {
                        "fast": 20,
                        "slow": 50,
                        "adx_threshold": 20,
                        "volume_length": 20,
                    },
                    "data_fingerprint": "a" * 64,
                    "data_end": datetime.now(UTC).isoformat(),
                    "created_at": datetime.now(UTC).isoformat(),
                }
        ),
        encoding="utf-8",
    )
    config = MonitorConfig(
        market="US",
        source="ALPACA",
        symbols=["AAPL"],
        database_path=tmp_path / "monitor.db",
        reports_dir=tmp_path / "reports",
        strategy_validation_path=validation_path,
        require_strategy_validation=True,
        telegram_enabled=False,
    )
    monitor = Monitor(config, stream=DummyStream(), store=MonitorStore(config.database_path))
    event = MarketEvent(
        event_type="health",
        health=FeedHealth.STALE,
        metadata={"source": "ALPACA", "reason": "test"},
        received_at=datetime(2026, 7, 23, 9, 0, tzinfo=UTC),
    )

    asyncio.run(monitor.process(event))
    health = monitor.store.get_health("alpaca")

    assert monitor.strategy_validation is not None
    assert monitor.feed_health is FeedHealth.STALE
    assert health["status"] == "stale"
    assert health["metadata"] == {"source": "ALPACA", "reason": "test"}

    asyncio.run(monitor.stop())


def test_monitor_rejects_stale_strategy_validation(tmp_path):
    validation_path = tmp_path / "validation.json"
    validation_path.write_text(
        json.dumps(
            {
                "passed": True,
                "market": "US",
                "regime": "bull",
                "validation_scope": "market_regime_benchmark",
                "benchmark_symbol": "SPY",
                "selected_strategy": "trend-momentum",
                "strategy_parameters": {
                    "fast": 20,
                    "slow": 50,
                    "adx_threshold": 20,
                    "volume_length": 20,
                },
                "data_fingerprint": "a" * 64,
                "data_end": datetime.now(UTC).isoformat(),
                "created_at": (datetime.now(UTC) - timedelta(days=31)).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    config = MonitorConfig(
        market="US",
        source="ALPACA",
        symbols=["AAPL"],
        database_path=tmp_path / "monitor.db",
        reports_dir=tmp_path / "reports",
        strategy_validation_path=validation_path,
        telegram_enabled=False,
    )
    monitor = Monitor(config, stream=DummyStream(), store=MonitorStore(config.database_path))

    assert monitor.strategy_validation is None
    asyncio.run(monitor.stop())


def test_monitor_revalidates_artifact_freshness_before_buy(tmp_path):
    validation_path = tmp_path / "validation.json"
    payload = {
        "passed": True,
        "market": "US",
        "regime": "bull",
        "validation_scope": "market_regime_benchmark",
        "benchmark_symbol": "SPY",
        "selected_strategy": "trend-momentum",
        "strategy_parameters": {
            "fast": 20,
            "slow": 50,
            "adx_threshold": 20,
            "volume_length": 20,
        },
        "data_fingerprint": "a" * 64,
        "data_end": datetime.now(UTC).isoformat(),
        "created_at": datetime.now(UTC).isoformat(),
    }
    validation_path.write_text(json.dumps(payload), encoding="utf-8")
    config = MonitorConfig(
        market="US",
        source="ALPACA",
        symbols=["AAPL"],
        database_path=tmp_path / "monitor.db",
        reports_dir=tmp_path / "reports",
        strategy_validation_path=validation_path,
        telegram_enabled=False,
    )
    monitor = Monitor(config, stream=DummyStream(), store=MonitorStore(config.database_path))
    assert monitor.strategy_validation is not None
    payload["created_at"] = (datetime.now(UTC) - timedelta(days=31)).isoformat()
    validation_path.write_text(json.dumps(payload), encoding="utf-8")
    buy = Signal(
        symbol="AAPL",
        market=MarketRegion.US,
        timestamp=datetime.now(UTC),
        action=SignalAction.BUY,
        confidence=80,
        regime=MarketRegime.BULL,
        strategy="trend-momentum",
    )

    assert monitor._signal_validated(buy) is False
    assert monitor.strategy_validation is None
    asyncio.run(monitor.stop())


def test_default_ssi_monitor_warms_benchmark_and_restores_aggregates(tmp_path):
    config = MonitorConfig(
        market="VN",
        source="SSI",
        symbols=["ALL"],
        database_path=tmp_path / "monitor.db",
        reports_dir=tmp_path / "reports",
        stale_after_seconds=20_000,
        require_strategy_validation=False,
        telegram_enabled=False,
    )
    strategy = CountingStrategy()
    monitor = Monitor(
        config,
        stream=DummyStream(),
        store=MonitorStore(config.database_path),
        strategy=strategy,
    )
    provider = SSIStreamProvider(consumer_id="id", consumer_secret="secret")
    local_timezone = ZoneInfo("Asia/Ho_Chi_Minh")
    start = datetime.now(UTC).replace(second=0, microsecond=0) - timedelta(minutes=201)

    async def warm() -> None:
        for offset in range(202):
            timestamp = start + timedelta(minutes=offset)
            local = timestamp.astimezone(local_timezone)
            common = {
                "TradingDate": local.strftime("%d/%m/%Y"),
                "Time": local.strftime("%H:%M:%S"),
            }
            stock = provider.parse_message(
                {
                    "DataType": "X-TRADE",
                    "Content": {
                        **common,
                        "Symbol": "FPT",
                        "LastPrice": 100 + offset / 10,
                        "LastVol": 100,
                        "TradeId": f"stock-{offset}",
                    },
                }
            )
            index = provider.parse_message(
                {
                    "DataType": "MI",
                    "Content": {
                        **common,
                        "IndexId": "VNINDEX",
                        "IndexValue": 1_500 + offset / 10,
                        "AllQty": 1_000_000 + offset * 100,
                    },
                }
            )
            await monitor.process(stock)
            await monitor.process(index)

    asyncio.run(warm())

    assert len(monitor.raw_bars["FPT"]) >= 200
    assert len(monitor.raw_bars["VNINDEX"]) >= 200
    assert strategy.calls >= 1
    assert monitor.store.connection.execute("SELECT COUNT(*) FROM signals").fetchone()[0] == 0
    assert (
        monitor.store.connection.execute(
            "SELECT COUNT(*) FROM notification_outbox"
        ).fetchone()[0]
        == 0
    )
    asyncio.run(monitor.stop())

    restored = Monitor(
        config,
        stream=DummyStream(),
        store=MonitorStore(config.database_path),
        strategy=CountingStrategy(),
    )
    assert len(restored.raw_bars["FPT"]) >= 200
    assert len(restored.raw_bars["VNINDEX"]) >= 200
    asyncio.run(restored.stop())


def test_daily_flow_report_is_cooldown_deduplicated_and_bounded(tmp_path):
    config = MonitorConfig(
        market="VN",
        source="DNSE",
        symbols=["FPT"],
        database_path=tmp_path / "monitor.db",
        reports_dir=tmp_path / "reports",
        stale_after_seconds=60,
        alert_cooldown_seconds=1,
        daily_report_event_limit=2,
        require_strategy_validation=False,
        telegram_enabled=False,
    )
    monitor = Monitor(config, stream=DummyStream(), store=MonitorStore(config.database_path))

    class FlowDetector:
        def update_trade(self, trade):
            return UnusualFlowEvent(
                symbol=trade.symbol,
                market=trade.market,
                timestamp=trade.timestamp,
                score=90,
                direction="buy",
                confirmed=False,
                source=trade.source,
            )

    monitor.detector = FlowDetector()
    now = datetime.now(UTC).replace(microsecond=0)

    async def feed() -> None:
        for offset in (-2, -1, 0):
            timestamp = now + timedelta(seconds=offset)
            await monitor.process(
                MarketEvent(
                    event_type="trade",
                    record=TradeTick(
                        symbol="FPT",
                        market=MarketRegion.VN,
                        timestamp=timestamp,
                        source="DNSE",
                        exchange_timezone="Asia/Ho_Chi_Minh",
                        price=10,
                        volume=100,
                        side="buy",
                        trade_id=f"flow-{offset}",
                    ),
                )
            )
        await monitor.process(
            MarketEvent(
                event_type="trade",
                record=TradeTick(
                    symbol="FPT",
                    market=MarketRegion.VN,
                    timestamp=now,
                    source="DNSE",
                    exchange_timezone="Asia/Ho_Chi_Minh",
                    price=10,
                    volume=101,
                    side="buy",
                    trade_id="same-bucket",
                ),
            )
        )

    asyncio.run(feed())

    assert len(monitor.flows_today) == 2
    assert len(monitor.reported_flow_buckets) == 2
    assert len(monitor.reported_flow_bucket_order) == 2
    asyncio.run(monitor.stop())


def test_monitor_builds_completed_minute_bars_from_ssi_trades(tmp_path):
    config = MonitorConfig(
        market="VN",
        source="DNSE",
        symbols=["FPT"],
        database_path=tmp_path / "monitor.db",
        reports_dir=tmp_path / "reports",
        require_strategy_validation=False,
        telegram_enabled=False,
    )
    monitor = Monitor(config, stream=DummyStream(), store=MonitorStore(config.database_path))

    def trade(second: int, price: float, volume: float) -> TradeTick:
        return TradeTick(
            symbol="FPT",
            market=MarketRegion.VN,
            timestamp=datetime(2026, 7, 23, 2, 0, tzinfo=UTC) + timedelta(seconds=second),
            source="SSI",
            exchange_timezone="Asia/Ho_Chi_Minh",
            price=price,
            volume=volume,
            side="buy",
            trade_id=f"t-{second}",
        )

    asyncio.run(monitor._aggregate_trade_bar(trade(0, 10, 100)))
    asyncio.run(monitor._aggregate_trade_bar(trade(20, 11, 200)))
    asyncio.run(monitor._aggregate_trade_bar(trade(60, 12, 50)))

    completed = monitor.raw_bars["FPT"][0]
    assert (completed.open, completed.high, completed.low, completed.close) == (10, 11, 10, 11)
    assert completed.volume == 300
    monitor.store.close()


def test_monitor_quarantines_stale_exchange_timestamps(tmp_path):
    config = MonitorConfig(
        market="US",
        source="ALPACA",
        symbols=["AAPL"],
        database_path=tmp_path / "monitor.db",
        reports_dir=tmp_path / "reports",
        require_strategy_validation=False,
        telegram_enabled=False,
        stale_after_seconds=30,
    )
    monitor = Monitor(config, stream=DummyStream(), store=MonitorStore(config.database_path))
    stale_bar = Bar(
        symbol="AAPL",
        market=MarketRegion.US,
        timestamp=datetime.now(UTC) - timedelta(minutes=5),
        source="ALPACA",
        exchange_timezone="America/New_York",
        open=100,
        high=101,
        low=99,
        close=100,
        volume=100,
    )

    asyncio.run(monitor.process(MarketEvent(event_type="bar", record=stale_bar)))

    assert monitor.feed_health is FeedHealth.STALE
    assert not monitor.raw_bars["AAPL"]
    monitor.store.close()


def test_monitor_quarantines_extended_hours_event_before_paper_fill(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(engine_module, "market_session_open", lambda *args: False)
    config = MonitorConfig(
        market="US",
        source="ALPACA",
        symbols=["AAPL"],
        database_path=tmp_path / "monitor.db",
        reports_dir=tmp_path / "reports",
        require_strategy_validation=False,
        telegram_enabled=False,
    )
    monitor = Monitor(config, stream=DummyStream(), store=MonitorStore(config.database_path))
    premarket = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)
    monitor.paper.on_signal(
        Signal(
            symbol="AAPL",
            market=MarketRegion.US,
            timestamp=premarket - timedelta(minutes=1),
            action=SignalAction.BUY,
            confidence=80,
            regime=MarketRegime.BULL,
            strategy="trend-momentum",
        )
    )
    bar = Bar(
        symbol="AAPL",
        market=MarketRegion.US,
        timestamp=premarket,
        source="ALPACA",
        exchange_timezone="America/New_York",
        open=100,
        high=101,
        low=99,
        close=100,
        volume=100,
    )

    asyncio.run(monitor.process(MarketEvent(event_type="bar", record=bar)))

    assert monitor.feed_health is FeedHealth.IDLE
    assert "AAPL" not in monitor.paper.positions
    assert not monitor.raw_bars["AAPL"]
    assert (
        monitor.store.connection.execute(
            "SELECT COUNT(*) FROM paper_trades"
        ).fetchone()[0]
        == 0
    )
    asyncio.run(monitor.stop())


def test_monitor_accepts_distinct_same_second_trades_and_rejects_exact_duplicates(tmp_path):
    config = MonitorConfig(
        market="VN",
        source="DNSE",
        symbols=["FPT"],
        database_path=tmp_path / "monitor.db",
        reports_dir=tmp_path / "reports",
        require_strategy_validation=False,
        telegram_enabled=False,
    )
    monitor = Monitor(config, stream=DummyStream(), store=MonitorStore(config.database_path))
    timestamp = datetime.now(UTC)

    def event(trade_id: str, volume: float) -> MarketEvent:
        return MarketEvent(
            event_type="trade",
            record=TradeTick(
                symbol="FPT",
                market=MarketRegion.VN,
                timestamp=timestamp,
                source="SSI",
                exchange_timezone="Asia/Ho_Chi_Minh",
                price=10,
                volume=volume,
                side="buy",
                trade_id=trade_id,
            ),
        )

    first = event("one", 100)
    second = event("two", 200)

    assert monitor._record_is_fresh(first)
    assert monitor._record_is_fresh(second)
    assert not monitor._record_is_fresh(second)
    monitor.store.close()


def test_monitor_throttles_healthy_storage_heartbeats(tmp_path, monkeypatch):
    config = MonitorConfig(
        market="US",
        source="ALPACA",
        symbols=["AAPL"],
        database_path=tmp_path / "monitor.db",
        reports_dir=tmp_path / "reports",
        require_strategy_validation=False,
        telegram_enabled=False,
        health_heartbeat_seconds=60,
    )
    store = MonitorStore(config.database_path)
    monitor = Monitor(config, stream=DummyStream(), store=store)
    calls = 0
    original = store.update_health

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(store, "update_health", counted)
    now = datetime.now(UTC)
    for offset in range(2):
        asyncio.run(
            monitor.process(
                MarketEvent(
                    event_type="bar",
                    record=Bar(
                        symbol="AAPL",
                        market=MarketRegion.US,
                        timestamp=now + timedelta(seconds=offset),
                        source="ALPACA",
                        exchange_timezone="America/New_York",
                        open=100,
                        high=101,
                        low=99,
                        close=100,
                        volume=100,
                    ),
                )
            )
        )

    assert calls == 1
    asyncio.run(monitor.stop())


def test_ssi_partial_minute_is_discarded_across_session_gap(tmp_path):
    config = MonitorConfig(
        market="VN",
        source="DNSE",
        symbols=["FPT"],
        database_path=tmp_path / "monitor.db",
        reports_dir=tmp_path / "reports",
        require_strategy_validation=False,
        telegram_enabled=False,
    )
    monitor = Monitor(config, stream=DummyStream(), store=MonitorStore(config.database_path))

    def trade(timestamp: datetime, trade_id: str) -> TradeTick:
        return TradeTick(
            symbol="FPT",
            market=MarketRegion.VN,
            timestamp=timestamp,
            source="SSI",
            exchange_timezone="Asia/Ho_Chi_Minh",
            price=10,
            volume=100,
            side="buy",
            trade_id=trade_id,
        )

    asyncio.run(monitor._aggregate_trade_bar(trade(datetime(2026, 7, 22, 7, 0, tzinfo=UTC), "old")))
    asyncio.run(monitor._aggregate_trade_bar(trade(datetime(2026, 7, 23, 2, 0, tzinfo=UTC), "new")))

    assert not monitor.raw_bars["FPT"]
    assert monitor.minute_trade_bars["FPT"].timestamp == datetime(2026, 7, 23, 2, 0, tzinfo=UTC)
    monitor.store.close()


def test_telegram_chunks_and_retry(monkeypatch):
    chunks = TelegramNotifier.chunks("a" * 3500 + "\n" + "b" * 5000)

    assert len(chunks) >= 2
    assert chunks[0] == "a" * 3500
    assert "".join(chunks) == "a" * 3500 + "b" * 5000
    assert all(len(chunk) <= TelegramNotifier.MAX_LENGTH for chunk in chunks)

    calls: list[str] = []
    responses = iter([DummyResponse(429, {"parameters": {"retry_after": 1}}), DummyResponse(200)])

    def transport(*args, json, timeout, **kwargs):
        calls.append(json["text"])
        return next(responses)

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(asyncio, "sleep", no_sleep)

    notifier = TelegramNotifier(token="bot", chat_id="chat", transport=transport)
    asyncio.run(notifier.send("hello world"))

    assert calls == ["hello world", "hello world"]


def test_telegram_transport_error_redacts_bot_token():
    secret = "super-secret-token"

    def transport(*args, **kwargs):
        raise RuntimeError(f"failed URL {args[0]}")

    notifier = TelegramNotifier(token=secret, chat_id="chat", transport=transport)
    with pytest.raises(ConnectionError) as captured:
        asyncio.run(notifier.send("hello"))

    assert secret not in str(captured.value)


def test_telegram_check_authenticates_without_sending_message():
    calls: list[tuple[str, dict]] = []

    def transport(endpoint, **kwargs):
        calls.append((endpoint, kwargs))
        return DummyResponse(200)

    notifier = TelegramNotifier(token="bot", chat_id="chat", transport=transport)
    asyncio.run(notifier.check())

    assert calls[0][0].endswith("/getMe")
    assert "json" not in calls[0][1]


def test_notification_failure_stays_in_outbox_and_can_retry(tmp_path):
    class FailingNotifier:
        async def send(self, text):
            raise ConnectionError("telegram unavailable")

    class WorkingNotifier:
        async def send(self, text):
            return None

    config = MonitorConfig(
        market="VN",
        source="DNSE",
        symbols=["FPT"],
        database_path=tmp_path / "monitor.db",
        reports_dir=tmp_path / "reports",
        require_strategy_validation=False,
        telegram_enabled=False,
    )
    monitor = Monitor(
        config,
        stream=DummyStream(),
        store=MonitorStore(config.database_path),
        notifier=FailingNotifier(),
    )
    flow = UnusualFlowEvent(
        symbol="FPT",
        market=MarketRegion.VN,
        timestamp=datetime.now(UTC),
        score=90,
        direction="buy",
        confirmed=True,
        source="SSI",
    )

    asyncio.run(monitor._notify_flow(flow))
    key = next(iter(monitor.store.pending_notifications()))["dedupe_key"]
    pending = monitor.store.get_notification(key)

    assert pending["attempts"] == 1
    assert not monitor.store.alert_seen(key)

    monitor.notifier = WorkingNotifier()
    asyncio.run(monitor._deliver_notification(key))

    assert monitor.store.get_notification(key) is None
    assert monitor.store.alert_seen(key)
    asyncio.run(monitor.stop())


def test_monitor_init_and_doctor(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / "monitor.toml"
    args = Namespace(config=str(config_path), market="US", source=None, symbols="aapl,msft", force=False)

    assert _monitor_init(args) == 0
    config_text = config_path.read_text(encoding="utf-8")
    env_text = (config_path.parent / ".env.example").read_text(encoding="utf-8")
    assert 'market = "US"' in config_text
    assert 'source = "ALPACA"' in config_text
    assert 'symbols = ["AAPL", "MSFT"]' in config_text
    assert "CFK_TELEGRAM_BOT_TOKEN" in env_text

    strategy_validation = tmp_path / "strategy-validation.json"
    strategy_validation.write_text(
        json.dumps(
            {
                "passed": True,
                "market": "US",
                "selected_strategy": "trend-momentum",
            }
        ),
        encoding="utf-8",
    )
    doctor_config = tmp_path / "doctor.toml"
    doctor_config.write_text(
        f"""
[monitor]
market = "US"
source = "ALPACA"
symbols = ["AAPL"]
database_path = "{(tmp_path / "monitor.db").as_posix()}"
reports_dir = "{(tmp_path / "reports").as_posix()}"
stale_after_seconds = 90

[strategy]
name = "trend-momentum"
require_validation = false
validation_path = "{strategy_validation.as_posix()}"

[paper]
starting_cash = 1000000000
notional = 50000000

[telegram]
enabled = false
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_API_SECRET", "secret")

    capsys.readouterr()
    assert _monitor_doctor(Namespace(config=str(doctor_config), offline=True)) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "ready"
    assert output["source"] == "ALPACA"
    assert output["telegram"] is False


def test_monitor_health_rejects_an_old_idle_checkpoint(tmp_path, capsys):
    config_path = tmp_path / "monitor.toml"
    database_path = tmp_path / "monitor.db"
    config_path.write_text(
        f"""
[monitor]
market = "US"
source = "ALPACA"
symbols = ["AAPL"]
database_path = "{database_path.as_posix()}"
reports_dir = "{(tmp_path / "reports").as_posix()}"
stale_after_seconds = 30
health_heartbeat_seconds = 30

[strategy]
name = "trend-momentum"
require_validation = false

[telegram]
enabled = false
""".strip(),
        encoding="utf-8",
    )
    store = MonitorStore(database_path)
    store.update_health(
        "ALPACA",
        FeedHealth.IDLE,
        event_at=datetime.now(UTC) - timedelta(minutes=10),
    )
    store.close()

    assert _monitor_health(Namespace(config=str(config_path))) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "idle"
    assert payload["healthy"] is False


def test_monitor_doctor_reports_degraded_watchlist_polling(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("DNSE_API_KEY", raising=False)
    monkeypatch.delenv("DNSE_API_SECRET", raising=False)
    config_path = tmp_path / "monitor.toml"
    config_path.write_text(
        f"""
[monitor]
market = "VN"
source = "DNSE"
symbols = ["FPT"]
database_path = "{(tmp_path / "monitor.db").as_posix()}"
reports_dir = "{(tmp_path / "reports").as_posix()}"

[strategy]
name = "trend-momentum"
require_validation = false

[telegram]
enabled = false
""".strip(),
        encoding="utf-8",
    )

    assert _monitor_doctor(Namespace(config=str(config_path), offline=True)) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["status"] == "degraded"
    assert "polling" in output["warnings"][0]
