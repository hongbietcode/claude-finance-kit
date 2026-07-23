"""Fail-closed strategy validation artifact checks."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from claude_finance_kit.monitor.config import MonitorConfig
from claude_finance_kit.strategy.rules import Strategy

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _fresh_timestamp(value: Any, maximum_age_days: float) -> bool:
    if not isinstance(value, str):
        return False
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    if timestamp.tzinfo is None:
        return False
    age_seconds = (datetime.now(UTC) - timestamp.astimezone(UTC)).total_seconds()
    return -300 <= age_seconds <= maximum_age_days * 86400


def valid_strategy_artifact(
    payload: dict[str, Any],
    config: MonitorConfig,
    strategy: Strategy,
) -> bool:
    """Validate market/regime deployment identity and freshness."""

    fingerprint = payload.get("data_fingerprint")
    return bool(
        payload.get("passed")
        and payload.get("validation_scope") == "market_regime_benchmark"
        and payload.get("market") == config.market.value
        and payload.get("benchmark_symbol") == config.benchmark_symbol
        and payload.get("selected_strategy") == strategy.name
        and payload.get("strategy_parameters", {}) == strategy.parameters()
        and isinstance(fingerprint, str)
        and _SHA256.fullmatch(fingerprint)
        and _fresh_timestamp(
            payload.get("created_at"),
            config.validation_max_age_days,
        )
        and _fresh_timestamp(
            payload.get("data_end"),
            config.validation_data_max_age_days,
        )
    )

