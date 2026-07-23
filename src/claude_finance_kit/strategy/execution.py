"""Shared long-only execution rules for historical and paper simulation."""

from __future__ import annotations


def long_exit_trigger(
    *,
    open_price: float,
    high: float,
    low: float,
    stop_loss: float | None,
    take_profit: float | None,
) -> tuple[str, float] | None:
    """Return a conservative raw exit price when a stop or target is crossed."""

    if stop_loss is not None and low <= stop_loss:
        return "stop_loss", min(open_price, stop_loss)
    if take_profit is not None and high >= take_profit:
        return "take_profit", max(open_price, take_profit)
    return None
