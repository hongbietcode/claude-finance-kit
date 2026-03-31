"""MAS (Mirae Asset Securities) API constants and field mappings."""

_CHART_URL = "https://masboard.masvn.com/api/v1/"
_FINANCIAL_URL = "https://masboard.masvn.com/api/v2/vs/"

_INDEX_MAPPING = {
    "VNINDEX": "VN-INDEX",
    "HNXINDEX": "HNXIndex",
    "UPCOMINDEX": "HNXUpcomIndex",
}

_INTERVAL_MAP = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1H": "60",
    "1D": "1D",
    "1W": "1W",
    "1M": "1M",
}

_OHLC_MAP = {
    "t": "time",
    "o": "open",
    "h": "high",
    "l": "low",
    "c": "close",
    "v": "volume",
}

_OHLC_DTYPE = {
    "time": "datetime64[ns]",
    "open": "float64",
    "high": "float64",
    "low": "float64",
    "close": "float64",
    "volume": "int64",
}

_RESAMPLE_MAP = {
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1H": "1H",
    "1W": "W",
    "1M": "ME",
}

_INTRADAY_MAP = {
    "ti": "time",
    "c": "price",
    "mv": "volume",
    "va": "value",
    "mb": "match_type",
    "h": "high",
    "l": "low",
    "ch": "change",
    "r": "change_pct",
    "vo": "agg_volume",
}

_INTRADAY_DTYPE = {
    "time": "datetime64[ns]",
    "price": "float64",
    "volume": "int64",
    "value": "float64",
    "match_type": "str",
    "high": "float64",
    "low": "float64",
    "change": "float64",
    "change_pct": "float64",
    "agg_volume": "int64",
}

_PRICE_DEPTH_MAP = {
    "price": "price",
    "volume": "volume",
    "buyVolume": "buy_volume",
    "sellVolume": "sell_volume",
    "bsVolume": "undefined_volume",
}

_FINANCIAL_REPORT_MAP = {
    "balance_sheet": "CDKT",
    "income_statement": "KQKD",
    "cash_flow": "LCTT",
    "ratio": "CSTC",
}

_FINANCIAL_REPORT_PERIOD_MAP = {
    "year": "Y",
    "quarter": "Q",
}

_FINANCIAL_QUERY_TEMPLATE = (
    'query{vsFinancialReportList(StockCode:"TARGET_SYMBOL",'
    'Type:"TARGET_TYPE",TermType:"TARGET_PERIOD")'
    '{_id,ID,TermCode,YearPeriod,Content{Values{Name,NameEn,Value}}}}'
)
