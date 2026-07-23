"""TOML-backed monitor configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from claude_finance_kit.core.types import MarketRegion


@dataclass(slots=True)
class MonitorConfig:
    """Single-user self-hosted monitor settings."""

    market: MarketRegion = MarketRegion.VN
    source: str = "SSI"
    symbols: list[str] = field(default_factory=lambda: ["ALL"])
    benchmark_symbol: str | None = None
    database_path: Path = Path("data/monitor.db")
    reports_dir: Path = Path("reports")
    stale_after_seconds: float = 90.0
    future_skew_seconds: float = 10.0
    poll_interval_seconds: float = 60.0
    health_heartbeat_seconds: float = 30.0
    queue_size: int = 10_000
    alert_threshold: float = 75.0
    flow_quantile: float = 0.995
    flow_imbalance_threshold: float = 0.6
    cluster_window_seconds: int = 300
    alert_cooldown_seconds: int = 900
    daily_report_event_limit: int = 5000
    paper_starting_cash: float = 1_000_000_000
    paper_notional: float = 50_000_000
    strategy: str = "trend-momentum"
    strategy_parameters: dict[str, Any] = field(default_factory=dict)
    require_strategy_validation: bool = True
    strategy_validation_path: Path = Path("data/strategy-validation.json")
    validation_max_age_days: float = 30.0
    validation_data_max_age_days: float = 7.0
    telegram_enabled: bool = True
    provider_options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.market = MarketRegion(self.market)
        self.source = self.source.upper()
        self.symbols = [symbol.upper() for symbol in self.symbols]
        self.benchmark_symbol = (
            self.benchmark_symbol.upper()
            if self.benchmark_symbol
            else ("VNINDEX" if self.market is MarketRegion.VN else "SPY")
        )
        self.database_path = Path(self.database_path)
        self.reports_dir = Path(self.reports_dir)
        self.strategy_validation_path = Path(self.strategy_validation_path)
        forbidden_secret_keys = {
            "api_key",
            "api_secret",
            "consumer_id",
            "consumer_secret",
            "token",
            "chat_id",
        }
        configured_secrets = forbidden_secret_keys.intersection(
            key.lower() for key in self.provider_options
        )
        if configured_secrets:
            raise ValueError(
                "Provider and Telegram secrets must come from environment variables, "
                f"not monitor.toml: {sorted(configured_secrets)}"
            )
        stream_symbols = set(self.symbols)
        if "ALL" not in stream_symbols and self.benchmark_symbol:
            stream_symbols.add(self.benchmark_symbol)
        if self.market is MarketRegion.US and len(stream_symbols) > 30:
            raise ValueError("Alpaca Basic realtime watchlist is limited to 30 symbols")
        if self.market is MarketRegion.US and self.source != "ALPACA":
            raise ValueError("US realtime monitoring currently requires source='ALPACA'")
        if self.market is MarketRegion.VN and "ALL" in self.symbols and self.source != "SSI":
            raise ValueError("All-market VN scanning requires source='SSI'")
        if (
            self.stale_after_seconds <= 0
            or self.future_skew_seconds < 0
            or self.poll_interval_seconds <= 0
            or self.health_heartbeat_seconds <= 0
        ):
            raise ValueError(
                "stale_after_seconds and poll_interval_seconds must be positive; "
                "health_heartbeat_seconds must be positive; future_skew_seconds cannot be negative"
            )
        if self.queue_size <= 0:
            raise ValueError("queue_size must be positive")
        if not 0 <= self.alert_threshold <= 100:
            raise ValueError("alert_threshold must be between 0 and 100")
        if not 0 < self.flow_quantile <= 1:
            raise ValueError("flow_quantile must be in the interval (0, 1]")
        if not 0 <= self.flow_imbalance_threshold <= 1:
            raise ValueError("flow_imbalance_threshold must be between 0 and 1")
        if self.cluster_window_seconds <= 0 or self.alert_cooldown_seconds <= 0:
            raise ValueError("cluster and cooldown windows must be positive")
        if self.daily_report_event_limit <= 0:
            raise ValueError("daily_report_event_limit must be positive")
        if self.paper_starting_cash <= 0 or self.paper_notional <= 0:
            raise ValueError("paper capital and notional must be positive")
        if self.validation_max_age_days <= 0 or self.validation_data_max_age_days <= 0:
            raise ValueError("strategy validation age limits must be positive")

    @classmethod
    def from_toml(cls, path: str | Path) -> "MonitorConfig":
        try:
            import tomllib
        except ImportError:  # pragma: no cover - Python 3.10
            import tomli as tomllib  # type: ignore[no-redef]
        config_path = Path(path)
        with config_path.open("rb") as handle:
            raw = tomllib.load(handle)
        monitor = raw.get("monitor", {})
        paper = raw.get("paper", {})
        strategy = raw.get("strategy", {})
        telegram = raw.get("telegram", {})
        return cls(
            market=monitor.get("market", "VN"),
            source=monitor.get("source", "SSI"),
            symbols=monitor.get("symbols", ["ALL"]),
            benchmark_symbol=monitor.get("benchmark_symbol"),
            database_path=Path(monitor.get("database_path", "data/monitor.db")),
            reports_dir=Path(monitor.get("reports_dir", "reports")),
            stale_after_seconds=float(monitor.get("stale_after_seconds", 90)),
            future_skew_seconds=float(monitor.get("future_skew_seconds", 10)),
            poll_interval_seconds=float(monitor.get("poll_interval_seconds", 60)),
            health_heartbeat_seconds=float(monitor.get("health_heartbeat_seconds", 30)),
            queue_size=int(monitor.get("queue_size", 10_000)),
            alert_threshold=float(monitor.get("alert_threshold", 75)),
            flow_quantile=float(monitor.get("flow_quantile", 0.995)),
            flow_imbalance_threshold=float(monitor.get("flow_imbalance_threshold", 0.6)),
            cluster_window_seconds=int(monitor.get("cluster_window_seconds", 300)),
            alert_cooldown_seconds=int(monitor.get("alert_cooldown_seconds", 900)),
            daily_report_event_limit=int(
                monitor.get("daily_report_event_limit", 5000)
            ),
            paper_starting_cash=float(paper.get("starting_cash", 1_000_000_000)),
            paper_notional=float(paper.get("notional", 50_000_000)),
            strategy=strategy.get("name", "trend-momentum"),
            strategy_parameters=dict(strategy.get("parameters", {})),
            require_strategy_validation=bool(strategy.get("require_validation", True)),
            strategy_validation_path=Path(
                strategy.get("validation_path", "data/strategy-validation.json")
            ),
            validation_max_age_days=float(strategy.get("validation_max_age_days", 30)),
            validation_data_max_age_days=float(
                strategy.get("validation_data_max_age_days", 7)
            ),
            telegram_enabled=bool(telegram.get("enabled", True)),
            provider_options=raw.get("providers", {}).get(monitor.get("source", "SSI").lower(), {}),
        )


DEFAULT_CONFIG = """[monitor]
market = "VN"
source = "SSI"
symbols = ["ALL"]
benchmark_symbol = "VNINDEX"
database_path = "data/monitor.db"
reports_dir = "reports"
stale_after_seconds = 90
future_skew_seconds = 10
poll_interval_seconds = 60
health_heartbeat_seconds = 30
queue_size = 10000
alert_threshold = 75
flow_quantile = 0.995
flow_imbalance_threshold = 0.6
cluster_window_seconds = 300
alert_cooldown_seconds = 900
daily_report_event_limit = 5000

[strategy]
name = "trend-momentum"
require_validation = true
validation_path = "data/strategy-validation.json"
validation_max_age_days = 30
validation_data_max_age_days = 7

[paper]
starting_cash = 1000000000
notional = 50000000

[telegram]
enabled = true
"""


ENV_EXAMPLE = """# Provider credentials; keep real values outside source control.
SSI_CONSUMER_ID=
SSI_CONSUMER_SECRET=
DNSE_API_KEY=
DNSE_API_SECRET=
ALPACA_API_KEY=
ALPACA_API_SECRET=
FMP_API_KEY=
CFK_SEC_USER_AGENT="your-app your-email@example.com"

# Outbound-only Telegram bot.
CFK_TELEGRAM_BOT_TOKEN=
CFK_TELEGRAM_CHAT_ID=
"""
