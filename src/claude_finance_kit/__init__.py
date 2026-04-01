"""
claude-finance-kit: Vietnamese stock market data & analysis library.
"""

__version__ = "0.1.14"

__all__ = [
    "Stock",
    "Market",
    "Macro",
    "Fund",
    "Commodity",
]

_LAZY_IMPORTS = {
    "Stock": "claude_finance_kit.stock",
    "Market": "claude_finance_kit.market",
    "Macro": "claude_finance_kit.macro",
    "Fund": "claude_finance_kit.fund",
    "Commodity": "claude_finance_kit.commodity",
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
