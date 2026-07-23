"""Walk-forward strategy selection with untouched final holdout."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from hashlib import sha256
from math import log, sqrt
from statistics import NormalDist, median

import pandas as pd

from claude_finance_kit.core.types import MarketRegime, MarketRegion, SignalAction
from claude_finance_kit.strategy.backtest import BacktestEngine
from claude_finance_kit.strategy.rules import Strategy, StrategyRegistry, _validate_bars


@dataclass(slots=True)
class WalkForwardConfig:
    train_bars: int = 504
    test_bars: int = 126
    holdout_bars: int = 252
    minimum_folds: int = 4
    minimum_oos_trades: int = 30
    minimum_profit_factor: float = 1.1
    maximum_drawdown: float = 0.2
    minimum_dsr_probability: float = 0.95


@dataclass(slots=True)
class OptimizationResult:
    market: MarketRegion
    regime: MarketRegime
    selected_strategy: str | None
    action: SignalAction
    passed: bool
    selected_parameters: dict[str, str | int | float | bool] = field(default_factory=dict)
    data_fingerprint: str | None = None
    data_end: str | None = None
    fold_parameters: list[dict[str, str | int | float | bool]] = field(default_factory=list)
    fold_metrics: list[dict[str, float]] = field(default_factory=list)
    holdout_metrics: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(
        default_factory=lambda: [
            "Current-constituent data may contain survivorship bias.",
            "Selection is bounded and is not a universally optimal strategy.",
        ]
    )


class WalkForwardOptimizer:
    """Choose one strategy per market/regime, never per symbol."""

    def __init__(
        self,
        engine: BacktestEngine | None = None,
        config: WalkForwardConfig | None = None,
        candidates: list[Strategy] | None = None,
    ) -> None:
        self.engine = engine or BacktestEngine()
        self.config = config or WalkForwardConfig()
        self.candidates = candidates or StrategyRegistry.candidates()

    @staticmethod
    def _candidate_key(strategy: Strategy) -> str:
        params = sorted(strategy.parameters().items())
        return f"{strategy.name}:{params}"

    @staticmethod
    def _fingerprint(frame: pd.DataFrame, benchmark: pd.DataFrame | None = None) -> str:
        columns = [column for column in ("time", "open", "high", "low", "close", "volume") if column in frame]
        digest = sha256(pd.util.hash_pandas_object(frame.loc[:, columns], index=False).values.tobytes())
        if benchmark is not None and not benchmark.empty:
            benchmark_frame = _validate_bars(benchmark)
            benchmark_columns = [
                column
                for column in ("time", "open", "high", "low", "close", "volume")
                if column in benchmark_frame
            ]
            digest.update(
                pd.util.hash_pandas_object(
                    benchmark_frame.loc[:, benchmark_columns],
                    index=False,
                ).values.tobytes()
            )
        return digest.hexdigest()

    @staticmethod
    def _dsr_probability(returns: pd.Series, trials: int) -> float:
        """Deflated probabilistic Sharpe using only realized OOS returns."""

        clean = pd.Series(returns, dtype=float).replace(
            [float("inf"), float("-inf")],
            pd.NA,
        ).dropna()
        observations = len(clean)
        if observations < 3:
            return 0.0
        volatility = float(clean.std(ddof=1))
        if volatility <= 0:
            return 0.0
        sharpe = float(clean.mean() / volatility)
        selection_threshold = sqrt(
            max(0.0, 2 * log(max(1, trials))) / max(1, observations - 1)
        )
        skew = float(clean.skew()) if observations > 2 else 0.0
        kurtosis = float(clean.kurt()) + 3 if observations > 3 else 3.0
        denominator = sqrt(
            max(
                1e-12,
                1
                - skew * sharpe
                + ((kurtosis - 1) / 4) * sharpe**2,
            )
        )
        z_score = (
            (sharpe - selection_threshold)
            * sqrt(observations - 1)
            / denominator
        )
        return NormalDist().cdf(z_score)

    @staticmethod
    def _result_returns(result: object) -> pd.Series:
        equity = getattr(result, "equity", None)
        if not isinstance(equity, pd.DataFrame) or "equity" not in equity:
            return pd.Series(dtype=float)
        return (
            equity["equity"]
            .astype(float)
            .pct_change()
            .replace([float("inf"), float("-inf")], pd.NA)
            .dropna()
        )

    def optimize(
        self,
        bars: pd.DataFrame,
        market: MarketRegion | str,
        regime: MarketRegime | str,
        *,
        benchmark: pd.DataFrame | None = None,
    ) -> OptimizationResult:
        market_value = MarketRegion(market)
        regime_value = MarketRegime(regime)
        frame = _validate_bars(bars)
        if "time" not in frame:
            raise ValueError("Walk-forward optimization requires timezone-aware time bars")
        data_fingerprint = self._fingerprint(frame, benchmark)
        data_end = pd.Timestamp(frame.iloc[-1]["time"]).isoformat()
        if regime_value is MarketRegime.BEAR:
            return OptimizationResult(
                market_value,
                regime_value,
                None,
                SignalAction.NO_TRADE,
                False,
                data_fingerprint=data_fingerprint,
                data_end=data_end,
                reasons=["Long-only strategies are disabled in bear regime"],
            )
        candidates = [
            candidate
            for candidate in self.candidates
            if (
                regime_value is MarketRegime.RANGE
                and candidate.name == "mean-reversion"
                or regime_value is MarketRegime.BULL
                and candidate.name != "mean-reversion"
            )
        ]
        if not candidates:
            return OptimizationResult(
                market_value,
                regime_value,
                None,
                SignalAction.NO_TRADE,
                False,
                data_fingerprint=data_fingerprint,
                data_end=data_end,
                reasons=[f"No bounded strategies are configured for {regime_value.value} regime"],
            )
        required = (
            self.config.train_bars
            + self.config.minimum_folds * self.config.test_bars
            + self.config.holdout_bars
        )
        if len(frame) < required:
            return OptimizationResult(
                market_value,
                regime_value,
                None,
                SignalAction.NO_TRADE,
                False,
                data_fingerprint=data_fingerprint,
                data_end=data_end,
                reasons=[f"Need at least {required} bars for four folds plus untouched holdout"],
            )

        holdout_start = len(frame) - self.config.holdout_bars
        fold_starts = list(
            range(
                0,
                holdout_start - self.config.train_bars - self.config.test_bars + 1,
                self.config.test_bars,
            )
        )[-self.config.minimum_folds :]
        selections: Counter[str] = Counter()
        candidate_map = {self._candidate_key(candidate): candidate for candidate in candidates}
        training_metrics: dict[str, list[dict[str, float]]] = defaultdict(list)
        fold_metrics: list[dict[str, float]] = []
        fold_parameters: list[dict[str, str | int | float | bool]] = []
        oos_returns: list[pd.Series] = []

        for start in fold_starts:
            train_end = start + self.config.train_bars
            test_end = train_end + self.config.test_bars
            train = frame.iloc[start:train_end].reset_index(drop=True)
            ranked: list[tuple[float, float, float, str, Strategy]] = []
            for candidate in candidates:
                result = self.engine.run(train, candidate, market_value, benchmark=benchmark)
                metrics = result.metrics
                training_metrics[self._candidate_key(candidate)].append(metrics)
                stability_penalty = metrics["turnover"] + metrics["max_drawdown"]
                ranked.append(
                    (
                        metrics["calmar"],
                        metrics["sharpe"],
                        -stability_penalty,
                        self._candidate_key(candidate),
                        candidate,
                    )
                )
            selected = max(ranked, key=lambda item: item[:4])[4]
            selected_key = self._candidate_key(selected)
            selections[selected_key] += 1
            test_with_context = frame.iloc[max(0, train_end - 252):test_end].reset_index(drop=True)
            evaluation_start = frame.iloc[train_end]["time"]
            result = self.engine.run(
                test_with_context,
                selected,
                market_value,
                benchmark=benchmark,
                evaluation_start=evaluation_start,
            )
            fold_metrics.append(result.metrics)
            fold_parameters.append(selected.parameters())
            oos_returns.append(self._result_returns(result))

        def score(key: str) -> tuple[int, float, float, float]:
            metrics = training_metrics[key]
            return (
                selections[key],
                median(item["calmar"] for item in metrics),
                median(item["sharpe"] for item in metrics),
                -median(item["turnover"] + item["max_drawdown"] for item in metrics),
            )

        selected_key = max(candidate_map, key=score)
        selected = candidate_map[selected_key]

        holdout_with_context = frame.iloc[max(0, holdout_start - 252):].reset_index(drop=True)
        evaluation_start = frame.iloc[holdout_start]["time"]
        holdout = self.engine.run(
            holdout_with_context,
            selected,
            market_value,
            benchmark=benchmark,
            evaluation_start=evaluation_start,
        )
        total_trades = sum(int(item["trades"]) for item in fold_metrics)
        positive_folds = sum(item["expectancy"] > 0 for item in fold_metrics)
        majority_positive = positive_folds > len(fold_metrics) / 2
        median_profit_factor = median(item["profit_factor"] for item in fold_metrics)
        worst_drawdown = max(item["max_drawdown"] for item in fold_metrics)
        realized_oos_returns = (
            pd.concat(oos_returns, ignore_index=True)
            if oos_returns
            else pd.Series(dtype=float)
        )
        dsr = self._dsr_probability(realized_oos_returns, len(candidates))
        passed = all(
            [
                majority_positive,
                total_trades >= self.config.minimum_oos_trades,
                median_profit_factor >= self.config.minimum_profit_factor,
                worst_drawdown <= self.config.maximum_drawdown,
                dsr >= self.config.minimum_dsr_probability,
                holdout.metrics["expectancy"] > 0,
                holdout.metrics["profit_factor"] >= self.config.minimum_profit_factor,
                holdout.metrics["max_drawdown"] <= self.config.maximum_drawdown,
            ]
        )
        reasons = [
            f"positive_folds={positive_folds}/{len(fold_metrics)}",
            f"oos_trades={total_trades}",
            f"parameter_selection_folds={selections[selected_key]}/{len(fold_metrics)}",
            f"median_profit_factor={median_profit_factor:.3f}",
            f"worst_drawdown={worst_drawdown:.3f}",
            f"deflated_sharpe_probability={dsr:.3f}",
            f"holdout_expectancy={holdout.metrics['expectancy']:.3f}",
        ]
        return OptimizationResult(
            market=market_value,
            regime=regime_value,
            selected_strategy=selected.name,
            action=SignalAction.HOLD if passed else SignalAction.NO_TRADE,
            passed=passed,
            selected_parameters=selected.parameters(),
            data_fingerprint=data_fingerprint,
            data_end=data_end,
            fold_parameters=fold_parameters,
            fold_metrics=fold_metrics,
            holdout_metrics=holdout.metrics,
            reasons=reasons,
        )
