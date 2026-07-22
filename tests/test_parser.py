"""Tests for security symbol parsing."""

import pytest

from claude_finance_kit._internal.parser import get_asset_type, get_instrument_type
from claude_finance_kit.core import InstrumentType


@pytest.mark.parametrize(
    "symbol",
    [
        "VNINDEX",
        "vni",
        "HNX",
        "HNXFIN",
        "HNXFINANCIALS",
        "UPCOM",
        "UPCOMLAR",
        "UPCOMMID",
        "UPCOMSML",
    ],
)
def test_get_asset_type_recognizes_index_registry_and_aliases(symbol):
    assert get_asset_type(symbol) == "index"
    assert get_instrument_type(symbol) is InstrumentType.INDEX


@pytest.mark.parametrize(
    ("symbol", "asset_type", "instrument_type"),
    [
        ("FPT", "stock", InstrumentType.STOCK),
        ("VN30F1M", "derivative", InstrumentType.FUTURE),
        ("VN30F2024", "derivative", InstrumentType.FUTURE),
        ("41I1F4000", "derivative", InstrumentType.FUTURE),
        ("GB10F2024", "bond", InstrumentType.FUND_BOND),
        ("BAB122032", "bond", InstrumentType.BOND),
        ("CFPT2401", "coveredWarr", InstrumentType.WARRANT),
        ("E1VFVN30", "stock", InstrumentType.ETF),
        ("FUEVFVND", "stock", InstrumentType.ETF),
        ("FUCVREIT", "stock", InstrumentType.FUND),
    ],
)
def test_get_asset_type_recognizes_security_formats(symbol, asset_type, instrument_type):
    assert get_asset_type(symbol) == asset_type
    assert get_instrument_type(symbol) is instrument_type


@pytest.mark.parametrize("symbol", ["", "ABCD", "ABCDEFGH", "VN30FXX", "TOO-LONG-SYMBOL"])
def test_get_asset_type_rejects_unknown_symbols(symbol):
    with pytest.raises(ValueError):
        get_asset_type(symbol)
