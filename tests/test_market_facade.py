"""Test Market facade with mocked providers."""

from unittest.mock import patch

import pandas as pd
import pytest

from claude_finance_kit import Market
from claude_finance_kit.core.exceptions import SourceNotAvailableError


class TestMarketInitialization:
    """Test Market class initialization."""

    def test_market_creation_default(self):
        """Market can be created with defaults."""
        market = Market()
        assert market._index == "VNINDEX"
        assert market._provider is not None

    def test_market_with_custom_index(self):
        """Market can be created with custom index."""
        market = Market(index="VN30")
        assert market._index == "VN30"

    def test_market_with_custom_source(self):
        """Market can be created with custom source."""
        market = Market(source="VND")
        assert market._provider is not None

    def test_market_uppercase_index(self):
        """Market accepts any case index."""
        market1 = Market(index="VNINDEX")
        market2 = Market(index="vnindex")
        assert market1._index == "VNINDEX"
        assert market2._index == "vnindex"


class TestMarketProviderIntegration:
    """Test Market provider delegation."""

    def test_market_has_provider(self):
        """Market instance has a provider."""
        market = Market()
        assert market._provider is not None

    def test_market_provider_has_pe_method(self):
        """Market provider has pe method."""
        market = Market()
        assert hasattr(market._provider, 'pe')

    def test_market_provider_has_pb_method(self):
        """Market provider has pb method."""
        market = Market()
        assert hasattr(market._provider, 'pb')

    def test_market_provider_has_top_gainer(self):
        """Market provider has top_gainer method."""
        market = Market()
        assert hasattr(market._provider, 'top_gainer')

    def test_market_provider_has_top_loser(self):
        """Market provider has top_loser method."""
        market = Market()
        assert hasattr(market._provider, 'top_loser')


class TestMarketFacadeMethods:
    """Test Market facade methods."""

    @patch('claude_finance_kit._provider.vnd.VNDProvider.pe')
    def test_market_pe_method(self, mock_pe):
        """Market.pe() delegates to provider."""
        mock_pe.return_value = pd.DataFrame()
        market = Market()
        market.pe()
        mock_pe.assert_called_once()

    @patch('claude_finance_kit._provider.vnd.VNDProvider.pb')
    def test_market_pb_method(self, mock_pb):
        """Market.pb() delegates to provider."""
        mock_pb.return_value = pd.DataFrame()
        market = Market()
        market.pb()
        mock_pb.assert_called_once()

    @patch('claude_finance_kit._provider.vnd.VNDProvider.top_gainer')
    def test_market_top_gainer_method(self, mock_gainer):
        """Market.top_gainer() delegates to provider."""
        mock_gainer.return_value = pd.DataFrame()
        market = Market()
        market.top_gainer()
        mock_gainer.assert_called_once()

    @patch('claude_finance_kit._provider.vnd.VNDProvider.top_loser')
    def test_market_top_loser_method(self, mock_loser):
        """Market.top_loser() delegates to provider."""
        mock_loser.return_value = pd.DataFrame()
        market = Market()
        market.top_loser()
        mock_loser.assert_called_once()


class TestMarketDifferentSources:
    """Test Market with different sources."""

    def test_market_vnd_source(self):
        """Market works with VND source."""
        market = Market(source="VND")
        assert market._provider is not None

    def test_market_invalid_source_raises(self):
        """Market raises error for invalid source."""
        with pytest.raises(SourceNotAvailableError):
            Market(source="INVALID")

    def test_market_case_insensitive_source(self):
        """Market source is case-insensitive."""
        market1 = Market(source="VND")
        market2 = Market(source="vnd")
        assert type(market1._provider).__name__ == type(market2._provider).__name__


class TestMarketMethodSignatures:
    """Test Market method signatures."""

    def test_market_pe_accepts_duration(self):
        """Market.pe accepts duration parameter."""
        market = Market()
        assert hasattr(market, 'pe')

    def test_market_top_gainer_accepts_limit(self):
        """Market.top_gainer accepts limit parameter."""
        market = Market()
        assert hasattr(market, 'top_gainer')

    def test_market_top_loser_accepts_limit(self):
        """Market.top_loser accepts limit parameter."""
        market = Market()
        assert hasattr(market, 'top_loser')
