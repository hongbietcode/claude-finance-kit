"""VCI (Vietcap) API constants: URLs, interval maps, field mappings."""

_TRADING_URL = "https://trading.vietcap.com.vn/api/"
_VCIQ_URL = "https://iq.vietcap.com.vn/api/iq-insight-service"
_VCI_COMPANY_URL = f"{_VCIQ_URL}/v1/company"
_VCI_ALLOWED_HOSTS = {"trading.vietcap.com.vn", "iq.vietcap.com.vn"}

_FINANCIAL_SECTIONS = {
    "balance_sheet": "BALANCE_SHEET",
    "income_statement": "INCOME_STATEMENT",
    "cash_flow": "CASH_FLOW",
}

_INTERVAL_MAP = {
    "1m": "ONE_MINUTE",
    "5m": "ONE_MINUTE",
    "15m": "ONE_MINUTE",
    "30m": "ONE_MINUTE",
    "1H": "ONE_HOUR",
    "1D": "ONE_DAY",
    "1W": "ONE_DAY",
    "1M": "ONE_DAY",
}

_RESAMPLE_MAP = {
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1H": "1H",
    "1W": "1W",
    "1M": "ME",
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

_GROUP_CODE = [
    "HOSE", "VN30", "VNMidCap", "VNSmallCap", "VNAllShare", "VN100",
    "ETF", "HNX", "HNX30", "HNXCon", "HNXFin", "HNXLCap", "HNXMSCap",
    "HNXMan", "UPCOM", "FU_INDEX", "FU_BOND", "BOND", "CW",
]

_GROUP_CODE_MAPPING = {
    "HOSE": "HOSE",
    "HNX": "HNX",
    "UPCOM": "UPCOM",
    "ETF": "ETF",
    "FUTURE": "FU_INDEX",
    "FU_INDEX": "FU_INDEX",
    "WARRANT": "CW",
    "CW": "CW",
    "BOND": "BOND",
    "FU_BOND": "FU_BOND",
    "FUND_BOND": "FU_BOND",
}

_INTRADAY_MAP = {
    "truncTime": "time",
    "matchPrice": "price",
    "matchVol": "volume",
    "matchType": "match_type",
    "id": "id",
}

_INTRADAY_DTYPE = {
    "time": "datetime64[ns]",
    "price": "float64",
    "volume": "int64",
    "match_type": "str",
    "id": "str",
}

_FINANCIAL_REPORT_PERIOD_MAP = {"year": "Y", "quarter": "Q"}

_UNIT_MAP = {"BILLION": "tỷ", "PERCENT": "%", "INDEX": "index", "MILLION": "triệu"}

SUPPORTED_LANGUAGES = ["vi", "en"]

_INDEX_MAPPING = {
    "VNINDEX": "VNINDEX",
    "VNI": "VNINDEX",
    "HNX": "HNXIndex",
    "HNXINDEX": "HNXIndex",
    "UPCOM": "HNXUpcomIndex",
    "UPCOMINDEX": "HNXUpcomIndex",
    "VN30": "VN30",
    "VNMID": "VNMIDCAP",
    "VNMIDCAP": "VNMIDCAP",
    "VNSML": "VNSMALLCAP",
    "VNSMALLCAP": "VNSMALLCAP",
    "VN100": "VN100",
    "VNALL": "VNALLSHARE",
    "VNALLSHARE": "VNALLSHARE",
    "VNSI": "VNSI",
    "VNIT": "VNIT",
    "VNIND": "VNIND",
    "VNCONS": "VNCONS",
    "VNCOND": "VNCOND",
    "VNHEAL": "VNHEAL",
    "VNENE": "VNENE",
    "VNUTI": "VNUTI",
    "VNREAL": "VNREAL",
    "VNFIN": "VNFIN",
    "VNMAT": "VNMAT",
    "VNDIAMOND": "VNDIAMOND",
    "VNFINLEAD": "VNFINLEAD",
    "VNFINSELECT": "VNFINSELECT",
    "VNX50": "VNX50",
    "VNXALL": "VNXALL",
    "HNX30": "HNX30",
    "HNXFIN": "HNX Financials Index",
    "HNXFINANCIALS": "HNX Financials Index",
    "HNXCON": "HNX Construction Index",
    "HNXCONSTRUCTION": "HNX Construction Index",
    "HNXLCAP": "HNX Large Cap Index",
    "HNXLARGECAP": "HNX Large Cap Index",
    "HNXMAN": "HNX Manufacturing Index",
    "HNXMANUFACTURING": "HNX Manufacturing Index",
    "HNXMSCAP": "HNX Mid/Small Cap Index",
    "HNXMIDSMALLCAP": "HNX Mid/Small Cap Index",
    "UPCOMLAR": "UPCOM Large Index",
    "UPCOMMID": "UPCOM Medium Index",
    "UPCOMSML": "UPCOM Small Index",
}
