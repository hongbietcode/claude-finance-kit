"""
claude-finance-kit: Vietnam and US market data, research signals, and paper monitoring.
"""

__version__ = "0.2.0"

__all__ = [
    "Stock",
    "Bond",
    "Market",
    "Macro",
    "Fund",
    "Commodity",
    "MarketStream",
    "Monitor",
    "BacktestEngine",
    "WalkForwardOptimizer",
]

_LAZY_IMPORTS = {
    "Stock": "claude_finance_kit.stock",
    "Bond": "claude_finance_kit.bond",
    "Market": "claude_finance_kit.market",
    "Macro": "claude_finance_kit.macro",
    "Fund": "claude_finance_kit.fund",
    "Commodity": "claude_finance_kit.commodity",
    "MarketStream": "claude_finance_kit.stream",
    "Monitor": "claude_finance_kit.monitor",
    "BacktestEngine": "claude_finance_kit.strategy",
    "WalkForwardOptimizer": "claude_finance_kit.strategy",
    "ta": "claude_finance_kit.ta",
    "collector": "claude_finance_kit.collector",
    "news": "claude_finance_kit.news",
    "PerplexitySearch": "claude_finance_kit.search",
    "search": "claude_finance_kit.search",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module_path = _LAZY_IMPORTS[name]
        import importlib

        module = importlib.import_module(module_path)
        if hasattr(module, name):
            return getattr(module, name)
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
