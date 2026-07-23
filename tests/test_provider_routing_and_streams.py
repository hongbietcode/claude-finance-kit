"""Routing, provider, and stream parsing tests for new VN/US coverage."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime

import pandas as pd
import pytest

from claude_finance_kit import Stock
from claude_finance_kit._provider._auto import AutoStockProvider
from claude_finance_kit._provider._registry import registry
from claude_finance_kit._provider.alpaca.stock import AlpacaStockProvider
from claude_finance_kit._provider.alpaca.stream import AlpacaStreamProvider
from claude_finance_kit._provider.dnse.stock import DNSEStockProvider
from claude_finance_kit._provider.dnse.stream import DNSEStreamProvider
from claude_finance_kit._provider.sec import stock as sec_stock_module
from claude_finance_kit._provider.sec.stock import SECStockProvider
from claude_finance_kit._provider.ssi.stock import SSIStockProvider
from claude_finance_kit._provider.ssi.stream import SSIStreamProvider
from claude_finance_kit.core.exceptions import AuthenticationError, InvalidSymbolError, ProviderCapabilityError
from claude_finance_kit.core.models import (
    Bar,
    MarketEvent,
    OrderBookSnapshot,
    ProviderDescriptor,
    TradeTick,
)
from claude_finance_kit.core.types import FeedHealth, MarketRegion, ProviderCapability
from claude_finance_kit.stream import MarketStream


def _bar_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "time": datetime(2026, 7, 23, 9, 0, tzinfo=UTC),
                "open": 10.0,
                "high": 11.0,
                "low": 9.5,
                "close": 10.5,
                "volume": 1_000.0,
            }
        ]
    )


def _descriptor(source: str, market: MarketRegion, capability: ProviderCapability, delayed_seconds: int = 0):
    from claude_finance_kit.core.models import ProviderDescriptor

    return ProviderDescriptor(
        source=source,
        markets={market},
        capabilities={capability},
        delayed_seconds=delayed_seconds,
        coverage=f"{source.lower()}-coverage",
    )


def _provider_class(name: str, behavior: dict[str, object], calls: list[tuple]):
    class Provider:
        def __init__(self, **kwargs):
            calls.append(("init", name, kwargs))

        def history(self, *args, **kwargs):
            calls.append(("history", name, args, kwargs))
            outcome = behavior["history"]
            if isinstance(outcome, Exception):
                raise outcome
            return outcome.copy()

        def intraday(self, *args, **kwargs):
            calls.append(("intraday", name, args, kwargs))
            outcome = behavior["intraday"]
            if isinstance(outcome, Exception):
                raise outcome
            return outcome.copy()

    return Provider


class DummyRegistry:
    def __init__(self, sources: list[str], providers: dict[str, type], descriptors: dict[str, object]):
        self.sources = sources
        self.providers = {key.upper(): value for key, value in providers.items()}
        self.descriptors = {key.upper(): value for key, value in descriptors.items()}
        self.calls: list[tuple] = []

    def stock_sources_for(self, market, capability, preferred=None):
        self.calls.append(("stock_sources_for", market, capability, preferred))
        return list(self.sources)

    def get_stock(self, source):
        self.calls.append(("get_stock", source))
        return self.providers[source.upper()]

    def get_descriptor(self, source):
        self.calls.append(("get_descriptor", source))
        return self.descriptors[source.upper()]


def test_auto_stock_provider_falls_back_and_records_provenance():
    calls: list[tuple] = []
    primary = _provider_class("PRIMARY", {"history": ConnectionError("primary down"), "intraday": _bar_frame()}, calls)
    secondary_frame = _bar_frame()
    secondary = _provider_class("SECONDARY", {"history": secondary_frame, "intraday": secondary_frame}, calls)
    dummy_registry = DummyRegistry(
        ["PRIMARY", "SECONDARY"],
        {"PRIMARY": primary, "SECONDARY": secondary},
        {
            "PRIMARY": _descriptor("PRIMARY", MarketRegion.VN, ProviderCapability.HISTORICAL_BARS, 30),
            "SECONDARY": _descriptor("SECONDARY", MarketRegion.VN, ProviderCapability.HISTORICAL_BARS, 15),
        },
    )

    provider = AutoStockProvider(
        MarketRegion.VN,
        provider_registry=dummy_registry,
        provider_options={"SECONDARY": {"timeout": 9}},
    )
    frame = provider.history("fpt", "2026-07-01", "2026-07-02")

    assert frame.attrs["source"] == "SECONDARY"
    assert frame.attrs["attempted_sources"] == ["PRIMARY", "SECONDARY"]
    assert frame.attrs["market"] == "VN"
    assert frame.attrs["data_timestamp"] == "2026-07-23T09:00:00+00:00"
    assert frame.attrs["delayed_seconds"] == 15
    assert frame.attrs["coverage"] == "secondary-coverage"
    assert provider.last_provenance == frame.attrs
    assert ("init", "SECONDARY", {"timeout": 9}) in calls
    assert dummy_registry.calls == [
        ("stock_sources_for", MarketRegion.VN, ProviderCapability.HISTORICAL_BARS, None),
        ("get_stock", "PRIMARY"),
        ("get_stock", "SECONDARY"),
        ("get_descriptor", "SECONDARY"),
    ]


def test_auto_stock_provider_propagates_non_fallback_errors():
    calls: list[tuple] = []
    primary = _provider_class("PRIMARY", {"history": ValueError("bad request"), "intraday": _bar_frame()}, calls)
    secondary = _provider_class("SECONDARY", {"history": _bar_frame(), "intraday": _bar_frame()}, calls)
    dummy_registry = DummyRegistry(
        ["PRIMARY", "SECONDARY"],
        {"PRIMARY": primary, "SECONDARY": secondary},
        {
            "PRIMARY": _descriptor("PRIMARY", MarketRegion.VN, ProviderCapability.HISTORICAL_BARS),
            "SECONDARY": _descriptor("SECONDARY", MarketRegion.VN, ProviderCapability.HISTORICAL_BARS),
        },
    )

    provider = AutoStockProvider(MarketRegion.VN, provider_registry=dummy_registry)

    with pytest.raises(ValueError, match="bad request"):
        provider.history("fpt", "2026-07-01", "2026-07-02")

    assert dummy_registry.calls[:2] == [
        ("stock_sources_for", MarketRegion.VN, ProviderCapability.HISTORICAL_BARS, None),
        ("get_stock", "PRIMARY"),
    ]
    assert calls == [("init", "PRIMARY", {}), ("history", "PRIMARY", ("fpt", "2026-07-01", "2026-07-02", "1D"), {})]


def test_auto_stock_provider_raises_capability_error_after_fallback_failures():
    calls: list[tuple] = []
    primary = _provider_class("PRIMARY", {"history": ConnectionError("primary down"), "intraday": _bar_frame()}, calls)
    secondary = _provider_class(
        "SECONDARY", {"history": ConnectionError("secondary down"), "intraday": _bar_frame()}, calls
    )
    dummy_registry = DummyRegistry(
        ["PRIMARY", "SECONDARY"],
        {"PRIMARY": primary, "SECONDARY": secondary},
        {
            "PRIMARY": _descriptor("PRIMARY", MarketRegion.VN, ProviderCapability.HISTORICAL_BARS),
            "SECONDARY": _descriptor("SECONDARY", MarketRegion.VN, ProviderCapability.HISTORICAL_BARS),
        },
    )

    provider = AutoStockProvider(MarketRegion.VN, provider_registry=dummy_registry)

    with pytest.raises(ProviderCapabilityError) as excinfo:
        provider.history("fpt", "2026-07-01", "2026-07-02")

    assert excinfo.value.details["attempted_sources"] == ["PRIMARY", "SECONDARY"]


def test_stock_auto_source_requires_market():
    with pytest.raises(ValueError, match="market='VN' or market='US' is required"):
        Stock("FPT", source="AUTO")


def test_registry_includes_new_realtime_descriptors():
    vn_realtime = {
        item.source for item in registry.list_descriptors(MarketRegion.VN, ProviderCapability.REALTIME_STREAM)
    }
    us_realtime = {
        item.source for item in registry.list_descriptors(MarketRegion.US, ProviderCapability.REALTIME_STREAM)
    }

    assert {"DNSE", "SSI"} <= vn_realtime
    assert "ALPACA" in us_realtime
    assert registry.get_descriptor("SEC").capabilities == {
        ProviderCapability.COMPANY,
        ProviderCapability.FUNDAMENTALS,
        ProviderCapability.FILINGS,
    }
    assert registry.get_descriptor("SEC").auth_type == "user_agent"


def test_registry_prefers_alpaca_for_us_history():
    sources = registry.stock_sources_for(MarketRegion.US, ProviderCapability.HISTORICAL_BARS)

    assert sources[0] == "ALPACA"
    assert "FMP" in sources
    assert "SEC" not in sources


def test_registry_prefers_sec_for_us_fundamentals():
    sources = registry.stock_sources_for(MarketRegion.US, ProviderCapability.FUNDAMENTALS)

    assert sources[:2] == ["SEC", "FMP"]


def test_sec_edgar_enforces_a_process_wide_request_interval(monkeypatch):
    provider = SECStockProvider(user_agent="cfk test@example.com")
    monotonic_values = iter([100.0, 100.0, 100.05, 100.11])
    sleeps: list[float] = []
    provider.__class__._last_request_at = 0.0
    monkeypatch.setattr(sec_stock_module, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(sec_stock_module, "sleep", sleeps.append)
    monkeypatch.setattr(provider.http, "request", lambda *args, **kwargs: {})

    provider._request("https://data.sec.gov/first.json")
    provider._request("https://data.sec.gov/second.json")

    assert sleeps == [pytest.approx(0.06)]


def test_alpaca_rest_pagination_honors_total_limit(monkeypatch):
    provider = AlpacaStockProvider(api_key="alpaca-key", api_secret="alpaca-secret")
    calls: list[str | None] = []

    def fake_get(path, **params):
        calls.append(params["page_token"])
        if params["page_token"] is None:
            return {"trades": [{"i": "1"}, {"i": "2"}], "next_page_token": "next"}
        return {"trades": [{"i": "3"}, {"i": "4"}]}

    monkeypatch.setattr(provider, "_get", fake_get)

    records = provider._paged("/v2/stocks/AAPL/trades", "trades", total_limit=3)

    assert [record["i"] for record in records] == ["1", "2", "3"]
    assert calls == [None, "next"]


def test_alpaca_trades_preserve_distinct_records_with_the_same_timestamp(monkeypatch):
    provider = AlpacaStockProvider(api_key="alpaca-key", api_secret="alpaca-secret")
    timestamp = "2026-07-23T14:30:00.000000000Z"
    monkeypatch.setattr(
        provider,
        "_paged",
        lambda *args, **kwargs: [
            {"t": timestamp, "p": 100, "s": 10, "i": "one"},
            {"t": timestamp, "p": 101, "s": 20, "i": "two"},
        ],
    )

    frame = provider.trades("AAPL")

    assert frame["trade_id"].tolist() == ["one", "two"]
    assert frame["volume"].tolist() == [10, 20]


def test_ssi_rest_pagination_and_exchange_timezone(monkeypatch):
    provider = SSIStockProvider(consumer_id="id", consumer_secret="secret")
    calls: list[int] = []

    def fake_get(endpoint, **params):
        calls.append(params["pageIndex"])
        if params["pageIndex"] == 1:
            return {"data": [{"Symbol": "FPT"}, {"Symbol": "HPG"}]}
        return {"data": [{"Symbol": "SSI"}]}

    monkeypatch.setattr(provider, "_get", fake_get)
    records = provider._paged("Securities", page_size=2)
    normalized = provider._normalize(
        [{"Timestamp": "23/07/2026 09:00:00", "Close": "10"}],
        {"timestamp": "time", "close": "close"},
        numeric=("close",),
    )

    assert [record["Symbol"] for record in records] == ["FPT", "HPG", "SSI"]
    assert calls == [1, 2]
    assert normalized.loc[0, "time"] == pd.Timestamp("2026-07-23 02:00:00+00:00")


def test_dnse_history_normalizes_interval_and_attrs(monkeypatch):
    calls: list[tuple] = []

    def fake_get(path, **params):
        calls.append((path, params))
        return {"data": [{"t": "2026-07-23T09:00:00Z", "o": "10", "h": "11", "l": "9", "c": "10.5", "v": "1000"}]}

    provider = DNSEStockProvider(api_key="dnse-key", api_secret="dnse-secret")
    monkeypatch.setattr(provider, "_get", fake_get)

    frame = provider.history("fpt", "2026-07-01", "2026-07-02", "1m")

    assert calls == [
        (
            "/price/ohlc",
            {
                "symbol": "FPT",
                "type": "STOCK",
                "from": provider._epoch("2026-07-01"),
                "to": provider._epoch("2026-07-02", end=True),
                "resolution": "1",
            },
        )
    ]
    assert list(frame.columns) == ["time", "open", "high", "low", "close", "volume"]
    assert frame.loc[0, "close"] == pytest.approx(10.5)
    assert frame.attrs["source"] == "DNSE"
    assert frame.attrs["symbol"] == "FPT"
    assert frame.attrs["market"] == "VN"
    assert frame.attrs["interval"] == "1m"


def test_dnse_history_marks_known_indices(monkeypatch):
    calls: list[dict[str, object]] = []
    provider = DNSEStockProvider(api_key="dnse-key", api_secret="dnse-secret")

    def fake_get(path, **params):
        calls.append(params)
        return {"t": [1784797200], "o": [100], "h": [101], "l": [99], "c": [100], "v": [1000]}

    monkeypatch.setattr(provider, "_get", fake_get)

    provider.history("VNINDEX", "2026-07-01", "2026-07-02")

    assert calls[0]["type"] == "INDEX"


@pytest.mark.parametrize("interval", ["7m", "2H", "1W"])
def test_dnse_history_rejects_unsupported_interval(interval):
    provider = DNSEStockProvider(api_key="dnse-key", api_secret="dnse-secret")

    with pytest.raises(ValueError, match="does not support interval"):
        provider.history("fpt", "2026-07-01", "2026-07-02", interval)


def test_dnse_stream_parse_message_covers_trade_order_book_foreign_and_bar():
    provider = DNSEStreamProvider(api_key="dnse-key", api_secret="dnse-secret")

    trade = provider.parse_message(
        {
            "T": "te",
            "symbol": "fpt",
            "time": {"Seconds": 1784797200, "Nanos": 0},
            "matchPrice": 123.5,
            "matchQtty": 200,
            "side": 1,
            "tradeId": "t-1",
            "boardId": "G1",
            "isBlockTrade": True,
        }
    )
    order_book = provider.parse_message(
        {
            "T": "q",
            "symbol": "FPT",
            "time": {"Seconds": 1784797201, "Nanos": 0},
            "bid": [{"price": 123, "qtty": 10}],
            "offer": [{"price": 124, "qtty": 12}],
        }
    )
    foreign = provider.parse_message(
        {
            "T": "f",
            "symbol": "FPT",
            "time": {"Seconds": 1784797202, "Nanos": 0},
            "totalBuyVolume": 1_000,
            "totalSellVolume": 250,
            "totalBuyTradedAmount": 10_000,
            "totalSellTradedAmount": 2_500,
            "foreignerBuyPossibleQuantity": 42_000,
            "transactTime": "035200011",
        }
    )
    bar = provider.parse_message(
        {
            "T": "b",
            "symbol": "FPT",
            "time": 1784797203,
            "open": 120,
            "high": 125,
            "low": 119,
            "close": 124,
            "volume": 5_000,
            "resolution": "1m",
        }
    )

    assert trade.event_type == "trade"
    assert isinstance(trade.record, TradeTick)
    assert trade.record.symbol == "FPT"
    assert trade.record.is_block_trade is True
    assert trade.record.exchange_timezone == "Asia/Ho_Chi_Minh"
    assert order_book.event_type == "order_book"
    assert isinstance(order_book.record, OrderBookSnapshot)
    assert len(order_book.record.bids) == 1
    assert foreign.event_type == "foreign_flow"
    assert foreign.metadata["provider_transact_time"] == "035200011"
    assert bar.event_type == "bar"
    assert bar.record.interval == "1m"


def test_dnse_stream_parse_message_ignores_missing_symbols():
    provider = DNSEStreamProvider(api_key="dnse-key", api_secret="dnse-secret")

    assert provider.parse_message({"channel": "tick.G1.json", "data": {"price": 1}}) is None


def test_ssi_stream_parse_message_covers_quote_trade_and_foreign():
    provider = SSIStreamProvider(consumer_id="id", consumer_secret="secret")

    quote = provider.parse_message(
        {
            "DataType": "X-QUOTE",
            "Content": json.dumps({
                "Symbol": "fpt",
                "TradingDate": "23/07/2026",
                "Time": "09:00:00",
                "BidPrice1": 123.0,
                "BidVol1": 10,
                "AskPrice1": 124.0,
                "AskVol1": 12,
            }),
        }
    )
    trade = provider.parse_message(
        {
            "DataType": "X-TRADE",
            "Content": json.dumps({
                "Symbol": "fpt",
                "TradingDate": "23/07/2026",
                "Time": "09:00:01",
                "LastPrice": 123.5,
                "LastVol": 200,
                "Side": "SD",
                "TradeId": "t-2",
                "IsDeal": True,
            }),
        }
    )
    foreign = provider.parse_message(
        {
            "DataType": "R",
            "Content": json.dumps({
                "Symbol": "FPT",
                "TradingDate": "23/07/2026",
                "Time": "09:00:02",
                "BuyVol": 1_000,
                "SellVol": 300,
                "BuyVal": 10_000,
                "SellVal": 3_000,
                "CurrentRoom": 99_000,
            }),
        }
    )
    index = provider.parse_message(
        {
            "DataType": "MI",
            "Content": {
                "IndexId": "VNINDEX",
                "TradingDate": "23/07/2026",
                "Time": "09:00:03",
                "IndexValue": 1500.5,
                "AllQty": 1_000_000,
            },
        }
    )
    next_index = provider.parse_message(
        {
            "DataType": "MI",
            "Content": {
                "IndexId": "VNINDEX",
                "TradingDate": "23/07/2026",
                "Time": "09:00:04",
                "IndexValue": 1501,
                "AllQty": 1_002_500,
            },
        }
    )

    assert quote.event_type == "order_book"
    assert isinstance(quote.record, OrderBookSnapshot)
    assert trade.event_type == "trade"
    assert trade.record.side == "sell"
    assert trade.record.is_block_trade is True
    assert foreign.event_type == "foreign_flow"
    assert foreign.record.buy_volume == 1_000
    assert foreign.record.sell_value == 3_000
    assert foreign.record.room == 99_000
    assert index.event_type == "trade"
    assert index.metadata["index_tick"] is True
    assert index.record.symbol == "VNINDEX"
    assert index.record.volume == 0
    assert next_index.record.volume == 2_500


def test_alpaca_stream_parse_message_and_symbol_cap():
    provider = AlpacaStreamProvider(api_key="alpaca-key", api_secret="alpaca-secret")

    trade = provider.parse_message({"T": "t", "S": "aapl", "t": "2026-07-23T09:30:00Z", "p": 100.5, "s": 50, "i": "x1"})
    quote = provider.parse_message(
        {"T": "q", "S": "aapl", "t": "2026-07-23T09:30:01Z", "bp": 100, "bs": 10, "ap": 101, "as": 12}
    )
    bar = provider.parse_message(
        {"T": "b", "S": "aapl", "t": "2026-07-23T09:30:02Z", "o": 100, "h": 102, "l": 99, "c": 101, "v": 500}
    )

    assert trade.event_type == "trade"
    assert trade.metadata["coverage"] == "iex-partial"
    assert quote.event_type == "order_book"
    assert bar.event_type == "bar"

    with pytest.raises(ValueError, match="limited to 30 symbols"):
        asyncio.run(provider.connect([f"SYM{i:02d}" for i in range(31)]))


def test_alpaca_stream_rejects_invalid_messages():
    provider = AlpacaStreamProvider(api_key="alpaca-key", api_secret="alpaca-secret")

    assert provider.parse_message({"T": "x", "S": "AAPL"}) is None
    assert provider.parse_message({"T": "t", "S": ""}) is None


def test_market_stream_emits_idle_and_drops_extended_hours_event():
    premarket_event = MarketEvent(
        event_type="bar",
        record=Bar(
            symbol="AAPL",
            market=MarketRegion.US,
            timestamp=datetime(2026, 7, 23, 12, 0, tzinfo=UTC),
            source="ALPACA",
            exchange_timezone="America/New_York",
            open=100,
            high=101,
            low=99,
            close=100,
            volume=100,
        ),
    )

    class Provider:
        def __init__(self, **kwargs):
            self.disconnected = False

        async def connect(self, symbols):
            return None

        async def disconnect(self):
            self.disconnected = True

        async def events(self):
            yield premarket_event

    class Registry:
        @staticmethod
        def get_descriptor(source):
            return ProviderDescriptor(
                source="ALPACA",
                markets={MarketRegion.US},
                capabilities={ProviderCapability.REALTIME_STREAM},
            )

        @staticmethod
        def get_stream(source):
            return Provider

    stream = MarketStream(
        MarketRegion.US,
        ["AAPL"],
        "ALPACA",
        provider_registry=Registry(),
    )

    async def collect():
        iterator = stream.events()
        connected = await anext(iterator)
        idle = await anext(iterator)
        await stream.stop()
        await iterator.aclose()
        return connected, idle

    connected, idle = asyncio.run(collect())

    assert connected.health is FeedHealth.HEALTHY
    assert idle.health is FeedHealth.IDLE
    assert idle.metadata["reason"] == "event outside regular market session"


def test_sec_filings_and_company_overview_normalize_data(monkeypatch):
    provider = SECStockProvider(user_agent="cfk@example.com")
    monkeypatch.setattr(SECStockProvider, "_ticker_map", {"AAPL": "0000320193"})
    payload = {
        "name": "Apple Inc.",
        "cik": "0000320193",
        "sic": "3571",
        "sicDescription": "Electronic Computers",
        "fiscalYearEnd": "0930",
        "exchanges": ["Nasdaq"],
        "filings": {
            "recent": {
                "accessionNumber": ["0000320193-26-000001"],
                "primaryDocument": ["a10-k.htm"],
                "form": ["10-K"],
            }
        },
    }
    monkeypatch.setattr(provider, "_submissions", lambda symbol: payload)
    monkeypatch.setattr(provider, "_company_facts", lambda symbol: {"facts": {"us-gaap": {}}})

    overview = provider.company_overview("aapl")
    filings = provider.filings("aapl", limit=1)
    empty_ratio = provider.ratio("aapl")

    assert overview.loc[0, "symbol"] == "AAPL"
    assert overview.loc[0, "name"] == "Apple Inc."
    assert filings.loc[0, "url"].startswith("https://www.sec.gov/Archives/edgar/data/320193/")
    assert filings.attrs["market"] == "US"
    assert empty_ratio.attrs["source"] == "SEC"


def test_sec_rejects_unknown_symbols(monkeypatch):
    provider = SECStockProvider(user_agent="cfk@example.com")
    monkeypatch.setattr(SECStockProvider, "_ticker_map", {"AAPL": "0000320193"})

    with pytest.raises(InvalidSymbolError):
        provider.filings("MSFT")


def test_sec_quarterly_facts_exclude_ytd_and_include_discrete_10k_q4():
    provider = SECStockProvider(user_agent="cfk@example.com")
    payload = {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {
                                "val": 200,
                                "start": "2026-01-01",
                                "end": "2026-06-30",
                                "filed": "2026-07-20",
                                "form": "10-Q",
                                "fy": 2026,
                                "fp": "Q2",
                                "accn": "ytd",
                            },
                            {
                                "val": 110,
                                "start": "2026-04-01",
                                "end": "2026-06-30",
                                "filed": "2026-07-20",
                                "form": "10-Q",
                                "fy": 2026,
                                "fp": "Q2",
                                "frame": "CY2026Q2",
                                "accn": "q2-old",
                            },
                            {
                                "val": 111,
                                "start": "2026-04-01",
                                "end": "2026-06-30",
                                "filed": "2026-07-21",
                                "form": "10-Q",
                                "fy": 2026,
                                "fp": "Q2",
                                "frame": "CY2026Q2",
                                "accn": "q2-restated",
                            },
                            {
                                "val": 120,
                                "start": "2026-10-01",
                                "end": "2026-12-31",
                                "filed": "2027-02-01",
                                "form": "10-K",
                                "fy": 2026,
                                "fp": "FY",
                                "frame": "CY2026Q4",
                                "accn": "q4",
                            },
                        ]
                    }
                }
            }
        }
    }

    frame = provider._statement_from_payload("AAPL", payload, {"Revenues"}, "quarter")

    assert frame["value"].tolist() == [111, 120]
    assert frame["accession"].tolist() == ["q2-restated", "q4"]


def test_sec_requires_responsible_user_agent():
    with pytest.raises(AuthenticationError, match="contact email"):
        SECStockProvider(user_agent="not-an-email")
