"""Test that all public APIs can be imported successfully."""



def test_main_facades_import():
    """Test importing main facade classes."""
    from claude_finance_kit import Commodity, Fund, Macro, Market, Stock

    assert Stock is not None
    assert Market is not None
    assert Macro is not None
    assert Fund is not None
    assert Commodity is not None


def test_ta_import():
    """Test importing technical analysis module."""
    from claude_finance_kit.ta import Indicator

    assert Indicator is not None


def test_news_import():
    """Test importing news crawlers."""
    from claude_finance_kit.news import BatchCrawler, Crawler

    assert Crawler is not None
    assert BatchCrawler is not None


def test_core_import():
    """Test importing core module components."""
    from claude_finance_kit.core import (
        DataNotFoundError,
        DataSource,
        Exchange,
        Interval,
        InvalidDateRangeError,
        InvalidSymbolError,
        ClaudeFinanceKitError,
        RateLimitError,
        SourceNotAvailableError,
    )

    assert DataSource is not None
    assert Interval is not None
    assert Exchange is not None
    assert ClaudeFinanceKitError is not None
    assert SourceNotAvailableError is not None
    assert InvalidSymbolError is not None
    assert DataNotFoundError is not None
    assert RateLimitError is not None
    assert InvalidDateRangeError is not None


def test_provider_import():
    """Test importing provider base classes and registry."""
    from claude_finance_kit._provider import StockProvider, registry

    assert StockProvider is not None
    assert registry is not None


def test_collector_import():
    """Test importing collector module."""
    from claude_finance_kit import collector

    assert collector is not None
