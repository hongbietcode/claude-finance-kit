"""Bias-aware long-only next-bar backtesting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from claude_finance_kit.core.types import MarketRegion, SignalAction
from claude_finance_kit.strategy.execution import long_exit_trigger
from claude_finance_kit.strategy.rules import Strategy, _validate_bars


@dataclass(slots=True)
class BacktestConfig:
    starting_cash: float = 1_000_000_000
    commission_per_side: float | None = None
    sell_tax: float | None = None
    slippage_per_side: float | None = None
    regulatory_sell_fee: float = 0
    periods_per_year: float | None = None

    def costs(self, market: MarketRegion) -> tuple[float, float, float, float]:
        if market is MarketRegion.VN:
            return (
                0.0015 if self.commission_per_side is None else self.commission_per_side,
                0.001 if self.sell_tax is None else self.sell_tax,
                0.0005 if self.slippage_per_side is None else self.slippage_per_side,
                self.regulatory_sell_fee,
            )
        return (
            0 if self.commission_per_side is None else self.commission_per_side,
            0 if self.sell_tax is None else self.sell_tax,
            0.0002 if self.slippage_per_side is None else self.slippage_per_side,
            self.regulatory_sell_fee,
        )


@dataclass(slots=True)
class BacktestResult:
    strategy: str
    market: MarketRegion
    trades: pd.DataFrame
    equity: pd.DataFrame
    metrics: dict[str, float]
    benchmark_return: float | None = None

    def to_html(self, path: str | Path, title: str | None = None) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        display_title = escape(title or self.strategy)
        metric_rows = "".join(
            f"<tr><th>{key}</th><td>{value:.4f}</td></tr>"
            for key, value in self.metrics.items()
        )
        trade_table = (
            self.trades.tail(100).to_html(index=False, border=0)
            if not self.trades.empty
            else "<p>No trades.</p>"
        )
        equity_table = (
            self.equity.tail(100).to_html(index=False, border=0)
            if not self.equity.empty
            else "<p>No equity observations.</p>"
        )
        html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{display_title}</title>
<style>body{{font:15px system-ui;max-width:1100px;margin:40px auto;padding:0 20px;color:#172033}}
table{{border-collapse:collapse;width:100%;margin:16px 0}}
th,td{{padding:8px;border-bottom:1px solid #dfe5ee;text-align:right}}
th:first-child,td:first-child{{text-align:left}}.warning{{background:#fff4d6;padding:12px;border-radius:8px}}</style></head>
<body><h1>{display_title}</h1>
<p class="warning">Research-only backtest. Next-bar fills, explicit costs,
selection bias and survivorship bias apply.</p>
<h2>Metrics</h2><table>{metric_rows}</table>
<h2>Equity and drawdown</h2>{equity_table}<h2>Trades</h2>{trade_table}
<p>Generated {datetime.now(UTC).isoformat()}</p></body></html>"""
        output.write_text(html, encoding="utf-8")
        return output


class BacktestEngine:
    """Execute signals at the next bar open with explicit friction."""

    def __init__(self, config: BacktestConfig | None = None) -> None:
        self.config = config or BacktestConfig()

    def run(
        self,
        bars: pd.DataFrame,
        strategy: Strategy,
        market: MarketRegion | str,
        *,
        benchmark: pd.DataFrame | None = None,
        evaluation_start: pd.Timestamp | datetime | str | None = None,
    ) -> BacktestResult:
        market_value = MarketRegion(market)
        frame = _validate_bars(bars)
        generated = strategy.generate(frame, market_value, benchmark)
        if len(frame) < 2:
            raise ValueError("Backtest requires at least two bars")
        start_index = 1
        if evaluation_start is not None:
            if "time" not in frame:
                raise ValueError("evaluation_start requires a time column")
            start_time = pd.Timestamp(evaluation_start)
            if start_time.tzinfo is None:
                start_time = start_time.tz_localize(UTC)
            eligible = frame.index[frame["time"] >= start_time]
            if not len(eligible):
                raise ValueError("evaluation_start is after available data")
            start_index = max(1, int(eligible[0]))

        commission, sell_tax, slippage, regulatory_fee = self.config.costs(market_value)
        cash = self.config.starting_cash
        quantity = 0.0
        entry_cost = 0.0
        stop_loss: float | None = None
        take_profit: float | None = None
        rows: list[dict[str, object]] = []
        equity_rows: list[dict[str, object]] = []

        for index in range(start_index, len(frame)):
            signal = SignalAction(generated.iloc[index - 1]["action"])
            open_price = float(frame.iloc[index]["open"])
            high_price = float(frame.iloc[index]["high"])
            low_price = float(frame.iloc[index]["low"])
            timestamp = frame.iloc[index].get("time", index)
            trigger = (
                long_exit_trigger(
                    open_price=open_price,
                    high=high_price,
                    low=low_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )
                if quantity > 0
                else None
            )
            if trigger is not None:
                reason, raw_fill = trigger
                fill = raw_fill * (1 - slippage)
                gross = quantity * fill
                fees = gross * (commission + sell_tax + regulatory_fee)
                proceeds = gross - fees
                pnl = proceeds - entry_cost
                cash += proceeds
                rows.append(
                    {
                        "time": timestamp,
                        "side": "SELL",
                        "price": fill,
                        "quantity": quantity,
                        "fees": fees,
                        "pnl": pnl,
                        "reason": reason,
                    }
                )
                quantity = 0.0
                entry_cost = 0.0
                stop_loss = None
                take_profit = None
            elif signal is SignalAction.BUY and quantity == 0 and open_price > 0:
                fill = open_price * (1 + slippage)
                quantity = cash / (fill * (1 + commission))
                gross = quantity * fill
                fee = gross * commission
                cash -= gross + fee
                entry_cost = gross + fee
                rows.append(
                    {
                        "time": timestamp,
                        "side": "BUY",
                        "price": fill,
                        "quantity": quantity,
                        "fees": fee,
                        "pnl": np.nan,
                        "reason": "next_bar_open",
                    }
                )
                signal_row = generated.iloc[index - 1]
                stop_loss = (
                    float(signal_row["stop_loss"])
                    if pd.notna(signal_row.get("stop_loss"))
                    else None
                )
                take_profit = (
                    float(signal_row["take_profit"])
                    if pd.notna(signal_row.get("take_profit"))
                    else None
                )
            elif signal is SignalAction.EXIT and quantity > 0:
                fill = open_price * (1 - slippage)
                gross = quantity * fill
                fees = gross * (commission + sell_tax + regulatory_fee)
                proceeds = gross - fees
                pnl = proceeds - entry_cost
                cash += proceeds
                rows.append(
                    {
                        "time": timestamp,
                        "side": "SELL",
                        "price": fill,
                        "quantity": quantity,
                        "fees": fees,
                        "pnl": pnl,
                        "reason": "signal_exit",
                    }
                )
                quantity = 0.0
                entry_cost = 0.0
                stop_loss = None
                take_profit = None
            close = float(frame.iloc[index]["close"])
            equity_rows.append(
                {
                    "time": timestamp,
                    "cash": cash,
                    "position_value": quantity * close,
                    "equity": cash + quantity * close,
                }
            )

        equity = pd.DataFrame(equity_rows)
        if not equity.empty:
            values = equity["equity"].astype(float)
            equity["drawdown"] = values / values.cummax() - 1
        trades = pd.DataFrame(rows)
        benchmark_return = None
        if benchmark is not None and not benchmark.empty:
            benchmark_frame = _validate_bars(benchmark)
            if "time" in frame and "time" in benchmark_frame:
                benchmark_start = frame.iloc[start_index]["time"]
                benchmark_end = frame.iloc[-1]["time"]
                benchmark_frame = benchmark_frame.loc[
                    (benchmark_frame["time"] >= benchmark_start)
                    & (benchmark_frame["time"] <= benchmark_end)
                ]
            if len(benchmark_frame) >= 2:
                benchmark_return = float(
                    benchmark_frame.iloc[-1]["close"] / benchmark_frame.iloc[0]["close"] - 1
                )
        metrics = self._metrics(equity, trades, self._periods_per_year(frame, market_value))
        if benchmark_return is not None:
            metrics["benchmark_return"] = benchmark_return
            metrics["excess_return"] = metrics["total_return"] - benchmark_return
        return BacktestResult(strategy.name, market_value, trades, equity, metrics, benchmark_return)

    def _periods_per_year(self, frame: pd.DataFrame, market: MarketRegion) -> float:
        if self.config.periods_per_year is not None:
            if self.config.periods_per_year <= 0:
                raise ValueError("periods_per_year must be positive")
            return self.config.periods_per_year
        if "time" not in frame or len(frame) < 2:
            return 252.0
        deltas = frame["time"].sort_values().diff().dropna().dt.total_seconds()
        if deltas.empty:
            return 252.0
        seconds = float(deltas.median())
        if seconds >= 20 * 86400:
            return 12.0
        if seconds >= 5 * 86400:
            return 52.0
        if seconds >= 20 * 3600:
            return 252.0
        session_seconds = 4.5 * 3600 if market is MarketRegion.VN else 6.5 * 3600
        return 252.0 * session_seconds / max(seconds, 1.0)

    def _metrics(
        self,
        equity: pd.DataFrame,
        trades: pd.DataFrame,
        periods_per_year: float,
    ) -> dict[str, float]:
        if equity.empty:
            return {
                "total_return": 0,
                "annual_return": 0,
                "sharpe": 0,
                "calmar": 0,
                "max_drawdown": 0,
                "profit_factor": 0,
                "expectancy": 0,
                "trades": 0,
                "turnover": 0,
            }
        values = equity["equity"].astype(float)
        returns = values.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
        total_return = float(values.iloc[-1] / self.config.starting_cash - 1)
        periods = max(1, len(values))
        annual_return = (
            float((1 + total_return) ** (periods_per_year / periods) - 1)
            if 1 + total_return > 0
            else -1.0
        )
        volatility = float(returns.std(ddof=1)) if len(returns) > 1 else 0.0
        sharpe = (
            float(returns.mean() / volatility * sqrt(periods_per_year))
            if volatility > 0
            else 0.0
        )
        drawdown = values / values.cummax() - 1
        max_drawdown = abs(float(drawdown.min()))
        calmar = annual_return / max_drawdown if max_drawdown > 0 else 0.0
        closed = trades.loc[trades.get("side", pd.Series(dtype=str)) == "SELL"] if not trades.empty else trades
        pnl = closed["pnl"].dropna().astype(float) if not closed.empty else pd.Series(dtype=float)
        profits = float(pnl[pnl > 0].sum())
        losses = abs(float(pnl[pnl < 0].sum()))
        profit_factor = profits / losses if losses else (float("inf") if profits else 0.0)
        expectancy = float(pnl.mean()) if len(pnl) else 0.0
        fees = float(trades["fees"].sum()) if not trades.empty else 0.0
        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "sharpe": sharpe,
            "calmar": calmar,
            "max_drawdown": max_drawdown,
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "trades": float(len(pnl)),
            "turnover": fees / self.config.starting_cash,
        }
