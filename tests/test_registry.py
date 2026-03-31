"""Test provider registry registration and lookup."""

import pytest

from claude_finance_kit._provider import registry
from claude_finance_kit._provider._base import MarketProvider, StockProvider
from claude_finance_kit.core.exceptions import SourceNotAvailableError


class TestStockProviderRegistry:
    """Test stock provider registration."""

    def test_vci_stock_provider_registered(self):
        """VCI stock provider is registered."""
        provider_cls = registry.get_stock("VCI")
        assert provider_cls is not None
        assert issubclass(provider_cls, StockProvider)

    def test_kbs_stock_provider_registered(self):
        """KBS stock provider is registered."""
        provider_cls = registry.get_stock("KBS")
        assert provider_cls is not None
        assert issubclass(provider_cls, StockProvider)

    def test_default_stock_provider(self):
        """Default stock provider is VCI."""
        provider_cls = registry.get_stock()
        assert provider_cls is not None
        assert issubclass(provider_cls, StockProvider)

    def test_stock_provider_case_insensitive(self):
        """Stock provider lookup is case-insensitive."""
        vci_upper = registry.get_stock("VCI")
        vci_lower = registry.get_stock("vci")
        vci_mixed = registry.get_stock("Vci")
        assert vci_upper is vci_lower
        assert vci_lower is vci_mixed

    def test_unknown_stock_provider_raises_error(self):
        """Unknown stock provider raises SourceNotAvailableError."""
        with pytest.raises(SourceNotAvailableError):
            registry.get_stock("NONEXISTENT")

    def test_stock_provider_instantiation(self):
        """Stock provider can be instantiated."""
        provider_cls = registry.get_stock("VCI")
        provider = provider_cls()
        assert provider is not None


class TestMarketProviderRegistry:
    """Test market provider registration."""

    def test_vnd_market_provider_registered(self):
        """VND market provider is registered."""
        provider_cls = registry.get_market("VND")
        assert provider_cls is not None
        assert issubclass(provider_cls, MarketProvider)

    def test_default_market_provider(self):
        """Default market provider is VND."""
        provider_cls = registry.get_market()
        assert provider_cls is not None
        assert issubclass(provider_cls, MarketProvider)

    def test_market_provider_case_insensitive(self):
        """Market provider lookup is case-insensitive."""
        vnd_upper = registry.get_market("VND")
        vnd_lower = registry.get_market("vnd")
        assert vnd_upper is vnd_lower

    def test_unknown_market_provider_raises_error(self):
        """Unknown market provider raises SourceNotAvailableError."""
        with pytest.raises(SourceNotAvailableError):
            registry.get_market("UNKNOWN_MARKET")


class TestMacroProviderRegistry:
    """Test macro provider registration."""

    def test_mbk_macro_provider_registered(self):
        """MBK macro provider is registered."""
        provider_cls = registry.get_macro("MBK")
        assert provider_cls is not None

    def test_default_macro_provider(self):
        """Default macro provider is MBK."""
        provider_cls = registry.get_macro()
        assert provider_cls is not None


class TestFundProviderRegistry:
    """Test fund provider registration."""

    def test_fmarket_fund_provider_registered(self):
        """FMARKET fund provider is registered."""
        provider_cls = registry.get_fund("FMARKET")
        assert provider_cls is not None

    def test_default_fund_provider(self):
        """Default fund provider is FMARKET."""
        provider_cls = registry.get_fund()
        assert provider_cls is not None


class TestCommodityProviderRegistry:
    """Test commodity provider registration."""

    def test_spl_commodity_provider_registered(self):
        """SPL commodity provider is registered."""
        provider_cls = registry.get_commodity("SPL")
        assert provider_cls is not None

    def test_default_commodity_provider(self):
        """Default commodity provider is SPL."""
        provider_cls = registry.get_commodity()
        assert provider_cls is not None


class TestProviderDefaults:
    """Test registry default provider mappings."""

    def test_stock_default_is_vci(self):
        """Default stock provider is VCI."""
        default = registry.get_stock()
        explicit_vci = registry.get_stock("VCI")
        assert default is explicit_vci

    def test_market_default_is_vnd(self):
        """Default market provider is VND."""
        default = registry.get_market()
        explicit_vnd = registry.get_market("VND")
        assert default is explicit_vnd

    def test_macro_default_is_mbk(self):
        """Default macro provider is MBK."""
        default = registry.get_macro()
        explicit_mbk = registry.get_macro("MBK")
        assert default is explicit_mbk

    def test_fund_default_is_fmarket(self):
        """Default fund provider is FMARKET."""
        default = registry.get_fund()
        explicit_fmarket = registry.get_fund("FMARKET")
        assert default is explicit_fmarket

    def test_commodity_default_is_spl(self):
        """Default commodity provider is SPL."""
        default = registry.get_commodity()
        explicit_spl = registry.get_commodity("SPL")
        assert default is explicit_spl


class TestListSources:
    """Test registry list_sources method."""

    def test_list_stock_sources(self):
        """Can list all stock sources."""
        sources = registry.list_sources("stock")
        assert isinstance(sources, list)
        assert len(sources) > 0
        assert "VCI" in sources
        assert "KBS" in sources

    def test_list_market_sources(self):
        """Can list all market sources."""
        sources = registry.list_sources("market")
        assert isinstance(sources, list)
        assert len(sources) > 0
        assert "VND" in sources
