"""FMP (Financial Modeling Prep) API constants and field mappings."""

import os

_FMP_DOMAIN = "https://financialmodelingprep.com/stable"
_DEFAULT_TIMEOUT = 30

_ENDPOINTS = {
    "quote": "/quote",
    "quote_short": "/quote-short",
    "historical_price_eod": "/historical-price-eod",
    "historical_chart_1min": "/historical-chart/1min",
    "historical_chart_5min": "/historical-chart/5min",
    "historical_chart_15min": "/historical-chart/15min",
    "historical_chart_30min": "/historical-chart/30min",
    "historical_chart_1hour": "/historical-chart/1hour",
    "historical_chart_4hour": "/historical-chart/4hour",
    "profile": "/profile",
    "key_executives": "/key-executives",
    "income_statement": "/income-statement",
    "balance_sheet": "/balance-sheet-statement",
    "cashflow_statement": "/cash-flow-statement",
    "ratios": "/ratios",
    "search_symbol": "/search-symbol",
}

_INTERVAL_MAP = {
    "1m": "historical_chart_1min",
    "5m": "historical_chart_5min",
    "15m": "historical_chart_15min",
    "30m": "historical_chart_30min",
    "1H": "historical_chart_1hour",
    "1h": "historical_chart_1hour",
    "4H": "historical_chart_4hour",
    "4h": "historical_chart_4hour",
    "1D": "historical_price_eod",
    "1d": "historical_price_eod",
    "1W": "historical_price_eod",
    "1w": "historical_price_eod",
    "1M": "historical_price_eod",
}

_RESAMPLE_MAP = {
    "1W": "W",
    "1w": "W",
    "1M": "ME",
}

_OHLC_MAP = {
    "date": "time",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
}

_OHLC_DTYPE = {
    "time": "datetime64[ns]",
    "open": "float64",
    "high": "float64",
    "low": "float64",
    "close": "float64",
    "volume": "int64",
}

_PERIOD_MAP = {
    "quarter": "quarter",
    "year": "annual",
}


def get_api_key(api_key: str | None = None) -> str:
    key = api_key or os.getenv("FMP_TOKEN") or os.getenv("FMP_API_KEY")
    if not key:
        raise ValueError(
            "FMP API key not found. Set FMP_TOKEN or FMP_API_KEY env var, "
            "or pass api_key to Stock()."
        )
    return key
