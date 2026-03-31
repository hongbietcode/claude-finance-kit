"""Binance public API constants and field mappings."""

_BASE_URL = "https://api.binance.com/api/v3"

_INTERVAL_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1H": "1h",
    "1h": "1h",
    "4H": "4h",
    "4h": "4h",
    "1D": "1d",
    "1d": "1d",
    "1W": "1w",
    "1w": "1w",
    "1M": "1M",
}

_KLINE_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_volume", "trades", "taker_buy_volume",
    "taker_buy_quote_volume", "ignore",
]
