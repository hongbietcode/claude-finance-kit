"""KBS (KB Securities) API constants: URLs, interval maps, field mappings."""

_IIS_BASE_URL = "https://kbbuddywts.kbsec.com.vn/iis-server/investment"
_SAS_BASE_URL = "https://kbbuddywts.kbsec.com.vn/sas"

_SEARCH_URL = f"{_IIS_BASE_URL}/stock/search/data"
_SECTOR_ALL_URL = f"{_IIS_BASE_URL}/sector/all"
_SECTOR_STOCK_URL = f"{_IIS_BASE_URL}/sector/stock"
_STOCK_INFO_URL = f"{_IIS_BASE_URL}/stockinfo"
_INDEX_URL = f"{_IIS_BASE_URL}/index"
_STOCK_ISS_URL = f"{_IIS_BASE_URL}/stock/iss"

_SAS_STOCK_URL = f"{_SAS_BASE_URL}/kbsv-stock-data-store/stock"
_SAS_FINANCE_INFO_URL = f"{_SAS_STOCK_URL}/finance-info"

_INDEX_MAPPING = {
    "VNINDEX": "VNINDEX",
    "HNXINDEX": "HNXINDEX",
    "UPCOMINDEX": "UPCOMINDEX",
    "VN30": "VN30",
    "HNX30": "HNX30",
    "VN100": "VN100",
}

_GROUP_CODE = {
    "HOSE": "HOSE",
    "HNX": "HNX",
    "UPCOM": "UPCOM",
    "VN30": "30",
    "VN100": "100",
    "VNMidCap": "MID",
    "VNSmallCap": "SML",
    "VNSI": "SI",
    "VNX50": "X50",
    "VNXALL": "XALL",
    "VNALL": "ALL",
    "HNX30": "HNX30",
    "ETF": "FUND",
    "CW": "CW",
    "BOND": "BOND",
    "FU_INDEX": "DER",
}

_INTERVAL_MAP = {
    "1m": "1P",
    "5m": "5P",
    "15m": "15P",
    "30m": "30P",
    "1h": "60P",
    "1H": "60P",
    "1d": "day",
    "1D": "day",
    "1w": "week",
    "1W": "week",
    "1M": "month",
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

_INTRADAY_MAP = {
    "t": "timestamp",
    "TD": "trading_date",
    "SB": "symbol",
    "FT": "time",
    "LC": "side",
    "FMP": "price",
    "FCV": "price_change",
    "FV": "match_volume",
    "AVO": "accumulated_volume",
    "AVA": "accumulated_value",
}

_INTRADAY_DTYPE = {
    "timestamp": "object",
    "trading_date": "object",
    "symbol": "object",
    "time": "object",
    "side": "object",
    "price": "float64",
    "price_change": "float64",
    "match_volume": "int64",
    "accumulated_volume": "int64",
    "accumulated_value": "float64",
}

_PRICE_BOARD_MAP = {
    "TT": "total_trades",
    "HI": "high_price",
    "TV": "total_value",
    "LO": "low_price",
    "CHP": "percent_change",
    "V1": "bid_vol_1",
    "V2": "bid_vol_2",
    "V3": "bid_vol_3",
    "B1": "bid_price_1",
    "AP": "average_price",
    "B2": "bid_price_2",
    "B3": "bid_price_3",
    "RE": "reference_price",
    "EX": "exchange",
    "FB": "foreign_buy_volume",
    "S1": "ask_price_1",
    "S2": "ask_price_2",
    "S3": "ask_price_3",
    "FL": "floor_price",
    "FO": "foreign_ownership_ratio",
    "FR": "foreign_sell_volume",
    "SB": "symbol",
    "OP": "open_price",
    "CH": "price_change",
    "CL": "ceiling_price",
    "CP": "close_price",
    "t": "time",
    "U1": "ask_vol_1",
    "U2": "ask_vol_2",
    "U3": "ask_vol_3",
}

_PRICE_BOARD_STANDARD_COLUMNS = [
    "symbol", "time", "exchange", "ceiling_price", "floor_price",
    "reference_price", "open_price", "high_price", "low_price",
    "close_price", "average_price", "total_trades", "total_value",
    "price_change", "percent_change",
    "bid_price_1", "bid_vol_1", "bid_price_2", "bid_vol_2",
    "bid_price_3", "bid_vol_3", "ask_price_1", "ask_vol_1",
    "ask_price_2", "ask_vol_2", "ask_price_3", "ask_vol_3",
    "foreign_buy_volume", "foreign_sell_volume",
]

_EXCLUDED_COLUMNS = {
    "ULS", "IN", "OIC", "TSI", "EP", "ER", "FTY", "P1", "P2",
    "price_points", "total_buy_vol", "total_offer_vol",
    "previous_match_price", "previous_match_qty", "current_vol", "market_status",
}

_EXCHANGE_CODE_MAP = {
    "HOSE": "HOSE",
    "HSX": "HOSE",
    "HNX": "HNX",
    "UPCOM": "UPCOM",
}

_COMPANY_PROFILE_MAP = {
    "SM": "business_model",
    "SB": "symbol",
    "FD": "founded_date",
    "CC": "charter_capital",
    "HM": "number_of_employees",
    "LD": "listing_date",
    "FV": "par_value",
    "EX": "exchange",
    "LP": "listing_price",
    "VL": "listed_volume",
    "CTP": "ceo_name",
    "CTPP": "ceo_position",
    "IS": "inspector_name",
    "ISP": "inspector_position",
    "FP": "establishment_license",
    "BP": "business_code",
    "TC": "tax_id",
    "KT": "auditor",
    "TY": "company_type",
    "ADD": "address",
    "PHONE": "phone",
    "FAX": "fax",
    "EMAIL": "email",
    "URL": "website",
    "BRANCH": "branches",
    "HS": "history",
    "KLCPNY": "free_float_percentage",
    "SFV": "free_float",
    "KLCPLH": "outstanding_shares",
    "AD": "as_of_date",
}

_SUBSIDIARIES_MAP = {
    "D": "update_date",
    "NM": "name",
    "CC": "charter_capital",
    "OR": "ownership_percent",
    "CR": "currency",
}

_SHAREHOLDERS_MAP = {
    "NM": "name",
    "D": "update_date",
    "V": "shares_owned",
    "OR": "ownership_percentage",
}
