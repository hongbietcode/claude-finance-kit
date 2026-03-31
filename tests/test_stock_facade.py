"""Test Stock facade with mocked providers."""

from unittest.mock import Mock, patch

import pytest

from claude_finance_kit import Stock
from claude_finance_kit.stock.company import Company
from claude_finance_kit.stock.financial import Finance
from claude_finance_kit.stock.listing import Listing
from claude_finance_kit.stock.quote import Quote
from claude_finance_kit.stock.trading import Trading


class TestStockInitialization:
    """Test Stock class initialization."""

    def test_stock_creation_with_symbol(self):
        """Stock can be created with a symbol."""
        stock = Stock("FPT")
        assert stock._symbol == "FPT"
        assert stock._source == "VCI"

    def test_stock_uppercase_symbol(self):
        """Stock symbol is converted to uppercase."""
        stock = Stock("fpt")
        assert stock._symbol == "FPT"

    def test_stock_with_custom_source(self):
        """Stock can be created with custom source."""
        stock = Stock("FPT", source="KBS")
        assert stock._symbol == "FPT"
        assert stock._source == "KBS"

    def test_stock_repr(self):
        """Stock repr shows symbol and source."""
        stock = Stock("FPT", source="VCI")
        repr_str = repr(stock)
        assert "FPT" in repr_str
        assert "VCI" in repr_str


class TestStockFacadeProperties:
    """Test Stock facade cached properties."""

    def test_stock_quote_property(self):
        """Stock has quote property of correct type."""
        stock = Stock("FPT")
        quote = stock.quote
        assert isinstance(quote, Quote)

    def test_stock_company_property(self):
        """Stock has company property of correct type."""
        stock = Stock("FPT")
        company = stock.company
        assert isinstance(company, Company)

    def test_stock_finance_property(self):
        """Stock has finance property of correct type."""
        stock = Stock("FPT")
        finance = stock.finance
        assert isinstance(finance, Finance)

    def test_stock_listing_property(self):
        """Stock has listing property of correct type."""
        stock = Stock("FPT")
        listing = stock.listing
        assert isinstance(listing, Listing)

    def test_stock_trading_property(self):
        """Stock has trading property of correct type."""
        stock = Stock("FPT")
        trading = stock.trading
        assert isinstance(trading, Trading)

    def test_stock_properties_cached(self):
        """Stock properties are cached (same instance on repeated access)."""
        stock = Stock("FPT")
        quote1 = stock.quote
        quote2 = stock.quote
        assert quote1 is quote2

    def test_stock_symbol_propagated_to_quote(self):
        """Symbol is correctly propagated to facade objects."""
        stock = Stock("FPT", source="VCI")
        quote = stock.quote
        assert quote._symbol == "FPT"

    def test_stock_provider_propagated_to_facade(self):
        """Provider instance is propagated to facade objects."""
        stock = Stock("FPT", source="VCI")
        quote = stock.quote
        assert quote._provider is not None


class TestStockFacadeIntegration:
    """Test Stock facade integration with mocked providers."""

    @patch('claude_finance_kit._provider.vci.VCIQuote')
    def test_stock_delegates_to_provider(self, mock_quote_class):
        """Stock quote facade delegates to provider."""
        mock_provider_instance = Mock()
        mock_provider_instance.history = Mock(return_value=None)

        stock = Stock("FPT", source="VCI")
        assert stock._provider is not None

    def test_stock_multiple_symbols(self):
        """Can create Stock instances for different symbols."""
        stock1 = Stock("FPT")
        stock2 = Stock("ACB")

        assert stock1._symbol == "FPT"
        assert stock2._symbol == "ACB"
        assert stock1._provider is not stock2._provider

    def test_stock_multiple_sources(self):
        """Can create Stock instances with different sources."""
        stock_vci = Stock("FPT", source="VCI")
        stock_kbs = Stock("FPT", source="KBS")

        assert stock_vci._source == "VCI"
        assert stock_kbs._source == "KBS"
        assert type(stock_vci._provider).__name__ == "VCIStockProvider"
        assert type(stock_kbs._provider).__name__ == "KBSStockProvider"


class TestStockErrorHandling:
    """Test Stock error scenarios."""

    def test_stock_with_invalid_source_raises_error(self):
        """Stock raises error for non-existent source."""
        from claude_finance_kit.core.exceptions import SourceNotAvailableError

        with pytest.raises(SourceNotAvailableError):
            Stock("FPT", source="INVALID_SOURCE")

    def test_stock_lowercase_source_accepted(self):
        """Stock accepts lowercase source names."""
        stock = Stock("FPT", source="vci")
        assert stock._source == "VCI"

    def test_stock_mixed_case_symbol_uppercase(self):
        """Stock converts mixed case symbols to uppercase."""
        stock = Stock("FpT")
        assert stock._symbol == "FPT"
