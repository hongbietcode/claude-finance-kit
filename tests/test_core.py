"""Test core module components: enums, constants, exceptions, models."""


from claude_finance_kit.core import (
    EXCHANGES,
    INDEX_GROUPS,
    INDICES_INFO,
    INDICES_MAP,
    SECTOR_IDS,
    AssetType,
    DataSource,
    DateRange,
    Exchange,
    Interval,
    StockInfo,
)
from claude_finance_kit.core.exceptions import (
    DataNotFoundError,
    InvalidDateRangeError,
    InvalidSymbolError,
    ClaudeFinanceKitError,
    ProviderError,
    RateLimitError,
    SourceNotAvailableError,
)


class TestIntervalEnum:
    """Test Interval enum values."""

    def test_interval_values_exist(self):
        """All standard intervals have expected values."""
        assert Interval.MINUTE_1.value == "1m"
        assert Interval.MINUTE_5.value == "5m"
        assert Interval.MINUTE_15.value == "15m"
        assert Interval.MINUTE_30.value == "30m"
        assert Interval.HOUR_1.value == "1H"
        assert Interval.DAY_1.value == "1D"
        assert Interval.WEEK_1.value == "1W"
        assert Interval.MONTH_1.value == "1M"

    def test_interval_count(self):
        """Correct number of intervals defined."""
        assert len(Interval) == 8


class TestExchangeEnum:
    """Test Exchange enum values."""

    def test_exchange_values_exist(self):
        """All Vietnamese exchanges present."""
        assert Exchange.HOSE.value == "HOSE"
        assert Exchange.HNX.value == "HNX"
        assert Exchange.UPCOM.value == "UPCOM"

    def test_exchange_count(self):
        """Correct number of exchanges defined."""
        assert len(Exchange) == 3


class TestAssetTypeEnum:
    """Test AssetType enum values."""

    def test_asset_type_values(self):
        """All asset types defined."""
        assert AssetType.STOCK.value == "STOCK"
        assert AssetType.ETF.value == "ETF"
        assert AssetType.BOND.value == "BOND"
        assert AssetType.FUND.value == "FUND"
        assert AssetType.INDEX.value == "INDEX"

    def test_asset_type_count(self):
        """Correct number of asset types."""
        assert len(AssetType) >= 5


class TestDataSourceEnum:
    """Test DataSource enum."""

    def test_common_sources_exist(self):
        """Common data sources are available."""
        assert DataSource.VCI.value == "VCI"
        assert DataSource.KBS.value == "KBS"
        assert DataSource.VND.value == "VND"
        assert DataSource.MBK.value == "MBK"
        assert DataSource.FMARKET.value == "FMARKET"
        assert DataSource.SPL.value == "SPL"

    def test_all_sources_method(self):
        """all_sources() returns list of all sources."""
        sources = DataSource.all_sources()
        assert isinstance(sources, list)
        assert len(sources) > 0
        assert "VCI" in sources
        assert "KBS" in sources


class TestConstants:
    """Test core constants."""

    def test_indices_info_populated(self):
        """INDICES_INFO has expected structure and entries."""
        assert isinstance(INDICES_INFO, dict)
        assert len(INDICES_INFO) > 0
        assert "VN30" in INDICES_INFO
        assert INDICES_INFO["VN30"]["name"] == "VN30"

    def test_indices_map_populated(self):
        """INDICES_MAP is populated."""
        assert isinstance(INDICES_MAP, dict)
        assert len(INDICES_MAP) > 0

    def test_index_groups_populated(self):
        """INDEX_GROUPS exists and is populated."""
        assert isinstance(INDEX_GROUPS, dict)
        assert len(INDEX_GROUPS) > 0

    def test_sector_ids_populated(self):
        """SECTOR_IDS is populated."""
        assert isinstance(SECTOR_IDS, dict)
        assert len(SECTOR_IDS) > 0

    def test_exchanges_populated(self):
        """EXCHANGES constant is populated."""
        assert isinstance(EXCHANGES, (list, dict))
        if isinstance(EXCHANGES, list):
            assert len(EXCHANGES) > 0


class TestExceptionHierarchy:
    """Test exception classes and hierarchy."""

    def test_claude_finance_kit_error_base(self):
        """ClaudeFinanceKitError is base exception."""
        err = ClaudeFinanceKitError("test message")
        assert isinstance(err, Exception)
        assert "test message" in str(err)
        assert err.error_code == "CLAUDE_FINANCE_KIT_000"

    def test_claude_finance_kit_error_with_details(self):
        """ClaudeFinanceKitError supports error codes and details."""
        err = ClaudeFinanceKitError(
            "test",
            error_code="TEST_001",
            details={"key": "value"}
        )
        assert err.error_code == "TEST_001"
        assert err.details == {"key": "value"}
        assert err.to_dict()["error_code"] == "TEST_001"

    def test_provider_error(self):
        """ProviderError inherits from ClaudeFinanceKitError."""
        err = ProviderError("API failed", provider="VCI")
        assert isinstance(err, ClaudeFinanceKitError)
        assert err.details["provider"] == "VCI"

    def test_invalid_symbol_error(self):
        """InvalidSymbolError creates with symbol."""
        err = InvalidSymbolError("INVALID")
        assert isinstance(err, ClaudeFinanceKitError)
        assert "INVALID" in err.details["symbol"]

    def test_data_not_found_error(self):
        """DataNotFoundError can include symbol."""
        err = DataNotFoundError("No data found", symbol="FPT")
        assert isinstance(err, ClaudeFinanceKitError)
        assert err.details["symbol"] == "FPT"

    def test_rate_limit_error(self):
        """RateLimitError stores provider and retry_after."""
        err = RateLimitError("VCI", retry_after=60)
        assert err.details["provider"] == "VCI"
        assert err.details["retry_after"] == 60

    def test_source_not_available_error(self):
        """SourceNotAvailableError lists available sources."""
        available = ["VCI", "KBS"]
        err = SourceNotAvailableError("UNKNOWN", available=available)
        assert err.details["source"] == "UNKNOWN"
        assert err.details["available_sources"] == available

    def test_invalid_date_range_error(self):
        """InvalidDateRangeError stores dates."""
        err = InvalidDateRangeError("2024-01-02", "2024-01-01")
        assert err.details["start"] == "2024-01-02"
        assert err.details["end"] == "2024-01-01"


class TestPydanticModels:
    """Test Pydantic data models."""

    def test_date_range_model(self):
        """DateRange model can be created."""
        from datetime import date
        dr = DateRange(start=date(2024, 1, 1), end=date(2024, 12, 31))
        assert dr.start == date(2024, 1, 1)
        assert dr.end == date(2024, 12, 31)

    def test_stock_info_model(self):
        """StockInfo model can be created."""
        info = StockInfo(
            symbol="FPT",
            exchange=Exchange.HOSE,
            name="FPT Corporation"
        )
        assert info.symbol == "FPT"
        assert info.exchange == Exchange.HOSE
        assert info.name == "FPT Corporation"
