"""Enums and type aliases for claude-finance-kit."""

from enum import Enum


class Interval(str, Enum):
    """Supported time intervals for historical data."""

    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1H"
    DAY_1 = "1D"
    WEEK_1 = "1W"
    MONTH_1 = "1M"


class Exchange(str, Enum):
    """Vietnamese stock exchanges."""

    HOSE = "HOSE"
    HNX = "HNX"
    UPCOM = "UPCOM"


class AssetType(str, Enum):
    """Asset categories supported by the library."""

    STOCK = "STOCK"
    ETF = "ETF"
    BOND = "BOND"
    DERIVATIVE = "DERIVATIVE"
    FUND = "FUND"
    INDEX = "INDEX"
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"
    COMMODITY = "COMMODITY"


class DataSource(str, Enum):
    """Data source identifiers used in the provider registry."""

    VCI = "VCI"
    KBS = "KBS"
    MAS = "MAS"
    TVS = "TVS"
    VND = "VND"
    VDS = "VDS"
    CAFEF = "CAFEF"
    FMARKET = "FMARKET"
    SPL = "SPL"
    MBK = "MBK"
    MSN = "MSN"
    DNSE = "DNSE"
    SSI = "SSI"
    FMP = "FMP"
    BINANCE = "BINANCE"

    @classmethod
    def all_sources(cls) -> list[str]:
        return [s.value for s in cls]
