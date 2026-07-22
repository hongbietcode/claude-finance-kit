"""MSN Finance endpoint and field constants."""

_BASE_URL = "https://assets.msn.com/service/Finance"
_SEARCH_URL = "https://services.bingapis.com/contentservices-finance.csautosuggest/api/v1/Query"
_CONFIG_URL = "https://assets.msn.com/resolver/api/resolve/v3/config/"
_MSN_ALLOWED_HOSTS = {"assets.msn.com", "services.bingapis.com"}

_SYMBOL_MAP = {
    "RT00S": "symbol",
    "SecId": "symbol_id",
    "AC040": "exchange_name",
    "LS01Z": "exchange_code_mic",
    "AC042": "short_name",
    "FriendlyName": "friendly_name",
    "RT0SN": "eng_name",
    "Description": "description",
    "OS0LN": "local_name",
    "locale": "locale",
}

_STATIC_SEC_IDS = {
    "VNI": "aqk2nm",
    "VNINDEX": "aqk2nm",
    "BTC": "c2111",
    "BTCUSDT": "c2111",
    "ETH": "c2112",
    "ETHUSDT": "c2112",
    "USDVND": "avyufr",
}

_OHLC_MAP = {
    "timeStamps": "time",
    "openPrices": "open",
    "pricesHigh": "high",
    "pricesLow": "low",
    "prices": "close",
    "volumes": "volume",
}

_RESAMPLE_MAP = {"1D": "1D", "1W": "1W", "1M": "ME"}
