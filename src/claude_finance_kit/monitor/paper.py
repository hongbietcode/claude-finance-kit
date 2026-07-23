"""Minimal research-only paper execution simulator."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

from claude_finance_kit.core.models import Bar, Signal
from claude_finance_kit.core.types import MarketRegion, SignalAction
from claude_finance_kit.monitor.storage import MonitorStore
from claude_finance_kit.strategy.backtest import BacktestConfig
from claude_finance_kit.strategy.execution import long_exit_trigger


@dataclass(slots=True)
class PaperPosition:
    symbol: str
    quantity: float
    entry_price: float
    entry_cost: float
    stop_loss: float | None
    take_profit: float | None


class PaperBroker:
    """Fixed-notional next-bar fills; never sends a brokerage order."""

    def __init__(
        self,
        market: MarketRegion | str,
        store: MonitorStore,
        starting_cash: float = 1_000_000_000,
        notional: float = 50_000_000,
        backtest_config: BacktestConfig | None = None,
    ) -> None:
        self.market = MarketRegion(market)
        self.store = store
        self.cash = starting_cash
        self.notional = notional
        self.backtest_config = backtest_config or BacktestConfig()
        self.positions: dict[str, PaperPosition] = {}
        self.pending: dict[str, Signal] = {}
        self.last_prices: dict[str, float] = {}
        self._last_equity_bucket: datetime | None = None
        self._state_key = f"paper:{self.market.value}"
        self._restore()

    def _restore(self) -> None:
        state = self.store.get_checkpoint(self._state_key)
        if not state:
            return
        try:
            self.cash = float(state["cash"])
            self.positions = {
                symbol: PaperPosition(**payload)
                for symbol, payload in state.get("positions", {}).items()
            }
            self.pending = {
                symbol: Signal.model_validate(payload)
                for symbol, payload in state.get("pending", {}).items()
            }
            self.last_prices = {
                symbol: float(price)
                for symbol, price in state.get("last_prices", {}).items()
            }
        except (KeyError, TypeError, ValueError):
            self.cash = float(self.cash)
            self.positions = {}
            self.pending = {}
            self.last_prices = {}

    def _persist(self) -> None:
        self.store.checkpoint(self._state_key, self.state_payload())

    @property
    def state_key(self) -> str:
        return self._state_key

    def state_payload(self) -> dict[str, object]:
        return {
            "cash": self.cash,
            "positions": {
                symbol: asdict(position)
                for symbol, position in self.positions.items()
            },
            "pending": {
                symbol: signal.model_dump(mode="json")
                for symbol, signal in self.pending.items()
            },
            "last_prices": self.last_prices,
        }

    def on_signal(self, signal: Signal, *, persist: bool = True) -> None:
        if signal.action is SignalAction.BUY and signal.symbol not in self.positions:
            self.pending[signal.symbol] = signal
        elif signal.action is SignalAction.EXIT and signal.symbol in self.positions:
            self.pending[signal.symbol] = signal
        else:
            return
        if persist:
            self._persist()

    def on_bar(self, bar: Bar, *, allow_entry: bool = True) -> dict[str, float | str] | None:
        self.last_prices[bar.symbol] = bar.close
        result: dict[str, float | str] | None = None
        state_changed = False
        position = self.positions.get(bar.symbol)
        if position:
            trigger = long_exit_trigger(
                open_price=bar.open,
                high=bar.high,
                low=bar.low,
                stop_loss=position.stop_loss,
                take_profit=position.take_profit,
            )
            if trigger is not None:
                reason, price = trigger
                self.pending.pop(bar.symbol, None)
                result = self._sell(bar, price, reason)

        if result is None:
            signal = self.pending.get(bar.symbol)
            if signal is not None and bar.timestamp > signal.timestamp:
                self.pending.pop(bar.symbol, None)
                state_changed = True
                if signal.action is SignalAction.BUY and bar.symbol not in self.positions:
                    if allow_entry:
                        result = self._buy(bar, signal)
                elif signal.action is SignalAction.EXIT and bar.symbol in self.positions:
                    result = self._sell(bar, bar.open, "signal_exit")
        if state_changed and result is None:
            self._persist()
        self._record_equity(bar, force=result is not None or state_changed)
        return result

    def _record_equity(self, bar: Bar, *, force: bool = False) -> None:
        if not force and bar.symbol not in self.positions:
            return
        bucket = bar.timestamp.replace(second=0, microsecond=0)
        if not force and bucket == self._last_equity_bucket:
            return
        position_value = sum(
            position.quantity
            * self.last_prices.get(symbol, position.entry_price)
            for symbol, position in self.positions.items()
        )
        equity = self.cash + position_value
        self.store.save_paper_equity(
            bar.timestamp,
            self.cash,
            position_value,
            equity,
            {"symbol": bar.symbol, "market": self.market.value},
        )
        self._last_equity_bucket = bucket

    def _buy(self, bar: Bar, signal: Signal) -> dict[str, float | str] | None:
        commission, _, slippage, _ = self.backtest_config.costs(self.market)
        fill = bar.open * (1 + slippage)
        allocation = min(self.notional, self.cash)
        quantity = allocation / (fill * (1 + commission)) if fill > 0 else 0
        if quantity <= 0:
            self._persist()
            return None
        gross = quantity * fill
        fees = gross * commission
        self.cash -= gross + fees
        self.positions[bar.symbol] = PaperPosition(
            bar.symbol,
            quantity,
            fill,
            gross + fees,
            signal.stop_loss,
            signal.take_profit,
        )
        payload = {"reason": "next_bar_open", "cash_after": self.cash}
        self.store.save_paper_trade_and_checkpoint(
            bar.symbol,
            "BUY",
            quantity,
            fill,
            fees,
            bar.timestamp,
            payload,
            self._state_key,
            self.state_payload(),
        )
        return {"symbol": bar.symbol, "side": "BUY", "price": fill, "quantity": quantity}

    def _sell(self, bar: Bar, raw_price: float, reason: str) -> dict[str, float | str]:
        position = self.positions.pop(bar.symbol)
        commission, sell_tax, slippage, regulatory = self.backtest_config.costs(self.market)
        fill = raw_price * (1 - slippage)
        gross = position.quantity * fill
        fees = gross * (commission + sell_tax + regulatory)
        proceeds = gross - fees
        pnl = proceeds - position.entry_cost
        self.cash += proceeds
        payload = {"reason": reason, "pnl": pnl, "cash_after": self.cash}
        self.store.save_paper_trade_and_checkpoint(
            bar.symbol,
            "SELL",
            position.quantity,
            fill,
            fees,
            bar.timestamp,
            payload,
            self._state_key,
            self.state_payload(),
        )
        return {
            "symbol": bar.symbol,
            "side": "SELL",
            "price": fill,
            "quantity": position.quantity,
            "pnl": pnl,
        }

    @property
    def equity(self) -> float:
        return self.cash + sum(
            position.quantity
            * self.last_prices.get(symbol, position.entry_price)
            for symbol, position in self.positions.items()
        )
