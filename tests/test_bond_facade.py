"""Tests for the additive Bond facade."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from claude_finance_kit import Bond


@pytest.fixture
def provider():
    instance = Mock()
    instance.symbols_by_group.side_effect = lambda group: (
        pd.Series(["BAB122032"]) if group == "BOND" else pd.Series(["GB10F2024"])
    )
    instance.history.return_value = pd.DataFrame([{"close": 100}])
    instance.intraday.return_value = pd.DataFrame([{"price": 100}])
    instance.price_board.return_value = pd.DataFrame([{"symbol": "BAB122032"}])
    return instance


@pytest.fixture
def bond(provider):
    with patch("claude_finance_kit.bond.registry.get_stock", return_value=lambda **kwargs: provider):
        yield Bond("BAB122032", source="VCI")


def test_bond_is_available_from_top_level_package(bond):
    assert repr(bond) == "Bond(symbol='BAB122032', source='VCI')"


def test_bond_list_combines_corporate_and_government_symbols(bond):
    result = bond.list()

    assert result.to_dict("records") == [
        {"symbol": "BAB122032", "type": "corporate"},
        {"symbol": "GB10F2024", "type": "government"},
    ]


def test_bond_ohlcv_reuses_constructor_symbol(bond, provider):
    result = bond.ohlcv(start="2026-01-01", end="2026-02-01")

    provider.history.assert_called_once_with("BAB122032", "2026-01-01", "2026-02-01", "1D")
    assert result.loc[0, "close"] == 100


def test_bond_trades_and_quote_delegate_to_provider(bond, provider):
    bond.trades()
    bond.quote()

    provider.intraday.assert_called_once_with("BAB122032")
    provider.price_board.assert_called_once_with(["BAB122032"])


def test_bond_accepts_per_call_symbol_without_constructor_symbol(provider):
    with patch("claude_finance_kit.bond.registry.get_stock", return_value=lambda **kwargs: provider):
        bond = Bond()

    bond.ohlcv(symbol="GB10F2024", start="2026-01-01")
    provider.history.assert_called_once_with("GB10F2024", "2026-01-01", None, "1D")


@pytest.mark.parametrize("symbol", ["FPT", "VNINDEX", "INVALID"])
def test_bond_rejects_non_bond_symbols(symbol, provider):
    with patch("claude_finance_kit.bond.registry.get_stock", return_value=lambda **kwargs: provider):
        with pytest.raises(ValueError):
            Bond(symbol)


def test_bond_requires_start_and_symbol(bond):
    with pytest.raises(ValueError, match="start is required"):
        bond.ohlcv()


def test_bond_validates_listing_type(bond):
    with pytest.raises(ValueError, match="bond_type"):
        bond.list("municipal")


def test_bond_all_marks_government_listing_as_unsupported(provider):
    provider.symbols_by_group.side_effect = lambda group: (
        pd.Series(["BAB122032"])
        if group == "BOND"
        else (_ for _ in ()).throw(NotImplementedError("FU_BOND unsupported"))
    )
    with patch("claude_finance_kit.bond.registry.get_stock", return_value=lambda **kwargs: provider):
        bond = Bond(source="KBS")

    result = bond.list("all")

    assert result.to_dict("records") == [{"symbol": "BAB122032", "type": "corporate"}]
    assert result.attrs["unsupported_types"] == ["government"]
    with pytest.raises(NotImplementedError, match="FU_BOND unsupported"):
        bond.list("government")


def test_bond_all_does_not_hide_malformed_government_response(provider):
    provider.symbols_by_group.side_effect = lambda group: (
        pd.Series(["BAB122032"])
        if group == "BOND"
        else (_ for _ in ()).throw(ValueError("malformed response"))
    )
    with patch("claude_finance_kit.bond.registry.get_stock", return_value=lambda **kwargs: provider):
        bond = Bond()

    with pytest.raises(ValueError, match="malformed response"):
        bond.list("all")
