"""Regression tests for VCI REST and MSN SecId provider changes."""

import json
from unittest.mock import patch

import pandas as pd
import pytest

from claude_finance_kit import Stock
from claude_finance_kit._provider.kbs.financial import KBSFinancial
from claude_finance_kit._provider.kbs.trading import KBSTrading
from claude_finance_kit._provider.msn.listing import MSNListing
from claude_finance_kit._provider.msn.quote import MSNQuote
from claude_finance_kit._provider.vci.company import VCICompany
from claude_finance_kit._provider.vci.financial import VCIFinancial
from claude_finance_kit._provider.vci.listing import VCIListing
from claude_finance_kit._provider.vci.quote import VCIQuote
from claude_finance_kit.stock.financial import Finance


@patch("claude_finance_kit._provider.vci.listing.send_request")
def test_vci_all_symbols_falls_back_to_rest_industry_search(mock_request):
    mock_request.side_effect = [
        ConnectionError("primary unavailable"),
        {
            "data": [
                {
                    "code": "FPT",
                    "name": "FPT Corp",
                    "floor": "HOSE",
                    "comTypeCode": "CT",
                    "icbLv1": {"code": "9000", "name": "Technology"},
                }
            ]
        },
    ]

    df = VCIListing().all_symbols()

    assert df.to_dict("records") == [{"symbol": "FPT", "organ_name": "FPT Corp"}]
    assert "graphql" not in " ".join(call.kwargs["url"] for call in mock_request.call_args_list).lower()


@patch("claude_finance_kit._provider.vci.listing.send_request")
def test_vci_all_symbols_preserves_exchange_filter_in_rest_fallback(mock_request):
    mock_request.side_effect = [
        ConnectionError("primary unavailable"),
        {
            "data": [
                {
                    "code": "FPT",
                    "name": "FPT Corp",
                    "floor": "HOSE",
                    "icbLv1": {"code": "9000", "name": "Technology"},
                },
                {
                    "code": "SHS",
                    "name": "Saigon Hanoi Securities",
                    "floor": "HNX",
                    "icbLv1": {"code": "8000", "name": "Financials"},
                },
            ]
        },
    ]

    df = VCIListing().all_symbols(exchange="HNX")

    assert df.to_dict("records") == [{"symbol": "SHS", "organ_name": "Saigon Hanoi Securities"}]


@patch("claude_finance_kit._provider.vci.listing.send_request")
def test_vci_all_symbols_falls_back_when_primary_filter_columns_are_missing(mock_request):
    mock_request.side_effect = [
        [{"symbol": "FPT", "organName": "FPT Corp"}],
        {
            "data": [
                {
                    "code": "SHS",
                    "name": "Saigon Hanoi Securities",
                    "floor": "HNX",
                    "icbLv1": {"code": "8000", "name": "Financials"},
                }
            ]
        },
    ]

    df = VCIListing().all_symbols(exchange="HNX")

    assert df.to_dict("records") == [{"symbol": "SHS", "organ_name": "Saigon Hanoi Securities"}]


@patch("claude_finance_kit._provider.vci.listing.send_request")
def test_vci_group_maps_new_hnx_index_alias(mock_request):
    mock_request.return_value = [{"symbol": "SHS"}]

    result = VCIListing().symbols_by_group("hnxfin")

    assert result.tolist() == ["SHS"]
    assert mock_request.call_args.kwargs["params"] == {"group": "HNX Financials Index"}


@pytest.mark.parametrize(
    ("alias", "provider_group"),
    [
        ("VNMidCap", "VNMIDCAP"),
        ("VNSmallCap", "VNSMALLCAP"),
        ("VNAllShare", "VNALLSHARE"),
    ],
)
@patch("claude_finance_kit._provider.vci.listing.send_request")
def test_vci_group_preserves_legacy_index_aliases(mock_request, alias, provider_group):
    mock_request.return_value = [{"symbol": "FPT"}]

    VCIListing().symbols_by_group(alias)

    assert mock_request.call_args.kwargs["params"] == {"group": provider_group}


@patch("claude_finance_kit._provider.vci.quote.send_request")
def test_vci_history_maps_new_hnx_index_before_quote_request(mock_request):
    mock_request.return_value = []

    result = VCIQuote().history("HNXFIN", start="2026-01-01", end="2026-01-02")

    assert result.empty
    assert mock_request.call_args.kwargs["payload"]["symbols"] == ["HNX Financials Index"]


@patch("claude_finance_kit._provider.vci.company.send_request")
def test_vci_company_overview_uses_rest_and_keeps_public_schema(mock_request):
    mock_request.return_value = {
        "data": {
            "ticker": "FPT",
            "viOrganName": "Công ty Cổ phần FPT",
            "profile": "<p>Công nghệ</p>",
            "listingDate": "2006-12-13T00:00:00",
        }
    }

    df = VCICompany().company_overview("fpt")

    assert df.loc[0, "symbol"] == "FPT"
    assert df.loc[0, "organ_name"] == "Công ty Cổ phần FPT"
    assert df.loc[0, "company_profile"] == "Công nghệ"
    assert df.loc[0, "listing_date"] == "2006-12-13"
    assert mock_request.call_args.kwargs["url"].endswith("/v1/company/details")


@patch("claude_finance_kit._provider.vci.company.send_request")
def test_vci_officers_preserve_public_quantity_column(mock_request):
    mock_request.return_value = {
        "data": [
            {
                "ownerName": "Truong Gia Binh",
                "positionName": "Chairman",
                "quantity": 100,
                "percentage": 0.1,
                "ownerType": "INDIVIDUAL",
                "updateDate": "2026-01-01T00:00:00",
            }
        ]
    }

    df = VCICompany().officers("FPT")

    assert df.loc[0, "quantity"] == 100
    assert df.loc[0, "officer_own_percent"] == 10
    assert "officer_own_quantity" not in df.columns


@patch("claude_finance_kit._provider.vci.company.send_request")
def test_vci_officers_reject_unsupported_resigned_filter(mock_request):
    with pytest.raises(NotImplementedError, match="resigned-officer status"):
        VCICompany().officers("FPT", filter_by="resigned")

    mock_request.assert_not_called()


@patch("claude_finance_kit._provider.vci.company.send_request")
def test_vci_shareholder_percentage_is_returned_in_percentage_points(mock_request):
    mock_request.return_value = {
        "data": [
            {
                "ownerName": "Major Holder",
                "quantity": 100,
                "percentage": 0.0689,
                "updateDate": "2026-01-01T00:00:00",
            }
        ]
    }

    df = VCICompany().shareholders("FPT")

    assert df.loc[0, "share_own_percent"] == pytest.approx(6.89)


@patch("claude_finance_kit._provider.vci.company.send_request")
def test_vci_company_endpoints_ignore_malformed_non_record_payloads(mock_request):
    company = VCICompany()
    mock_request.return_value = {"data": [None]}

    shareholders = company.shareholders("FPT")

    mock_request.return_value = {"data": "malformed"}
    news = company.company_news("FPT")

    assert shareholders.empty
    assert list(shareholders.columns) == [
        "symbol",
        "share_holder",
        "quantity",
        "share_own_percent",
        "update_date",
    ]
    assert news.empty
    assert list(news.columns) == ["title", "short_content", "source_link", "public_date"]


def test_vci_rest_paths_reject_invalid_symbols_before_request():
    invalid_symbol = "../../v1/news?x="

    with patch("claude_finance_kit._provider.vci.company.send_request") as company_request:
        with pytest.raises(ValueError):
            VCICompany().shareholders(invalid_symbol)
        company_request.assert_not_called()

    with patch("claude_finance_kit._provider.vci.financial.send_request") as finance_request:
        with pytest.raises(ValueError):
            VCIFinancial().balance_sheet(invalid_symbol)
        finance_request.assert_not_called()


@patch("claude_finance_kit._provider.vci.financial.send_request")
def test_vci_financial_rest_normalizes_period_rows_and_multiplier(mock_request):
    mock_request.side_effect = [
        {
            "data": {
                "quarters": [
                    {"ticker": "FPT", "yearReport": 2026, "lengthReport": 1, "bsa2": 12.5}
                ]
            }
        },
        {
            "data": {
                "BALANCE_SHEET": [
                    {"field": "bsa2", "titleEn": "Cash and cash equivalents"}
                ]
            }
        },
    ]

    df = VCIFinancial().balance_sheet("FPT", unit_multiplier=1000)

    assert list(df.columns) == ["symbol", "year", "period", "cash_and_cash_equivalents"]
    assert df.loc[0, "period"] == "Q1"
    assert df.loc[0, "cash_and_cash_equivalents"] == 12_500
    assert df.attrs["unit_multiplier"] == 1000.0
    assert all("graphql" not in call.kwargs["url"].lower() for call in mock_request.call_args_list)


@patch("claude_finance_kit._provider.vci.financial.send_request")
def test_vci_financial_caches_metric_maps_per_symbol(mock_request):
    mock_request.side_effect = [
        {"data": {"BALANCE_SHEET": [{"field": "fptMetric", "titleEn": "FPT metric"}]}},
        {"data": {"BALANCE_SHEET": [{"field": "vnmMetric", "titleEn": "VNM metric"}]}},
    ]
    financial = VCIFinancial()

    fpt = financial._load_metric_maps("FPT")
    vnm = financial._load_metric_maps("VNM")
    fpt_again = financial._load_metric_maps("FPT")

    assert fpt["BALANCE_SHEET"] == {"fptMetric": "fpt_metric"}
    assert vnm["BALANCE_SHEET"] == {"vnmMetric": "vnm_metric"}
    assert fpt_again is fpt
    assert mock_request.call_count == 2


@patch("claude_finance_kit._provider.vci.financial.send_request")
def test_vci_financial_tolerates_missing_period_metadata(mock_request):
    mock_request.side_effect = [
        {"data": {"quarters": [{"ticker": "FPT", "bsa2": 12.5}, None]}},
        {"data": {"BALANCE_SHEET": [{"field": "bsa2", "titleEn": "Cash"}]}},
    ]

    df = VCIFinancial().balance_sheet("FPT")

    assert pd.isna(df.loc[0, "year"])
    assert pd.isna(df.loc[0, "period"])
    assert df.loc[0, "cash"] == 12.5


@patch("claude_finance_kit._provider.vci.financial.send_request")
def test_vci_financial_rejects_metadata_without_requested_section(mock_request):
    mock_request.side_effect = [
        {"data": {"quarters": [{"ticker": "FPT", "bsa2": 12.5}]}},
        {"data": {"OTHER": [{"field": "bsa2", "titleEn": "Cash"}]}},
    ]

    with pytest.raises(ValueError, match="no 'BALANCE_SHEET' section"):
        VCIFinancial().balance_sheet("FPT")


@patch("claude_finance_kit._provider.vci.financial.send_request")
def test_vci_ratio_tolerates_missing_quarter_metadata(mock_request):
    mock_request.return_value = {"data": [{"ticker": "FPT", "pe": 10.5}, None]}

    df = VCIFinancial().ratio("FPT")

    assert df.empty
    assert list(df.columns[:3]) == ["symbol", "year", "period"]


@patch("claude_finance_kit._provider.kbs.financial.send_request")
def test_kbs_financial_matches_period_rows_and_normalizes_thousand_vnd_units(mock_request):
    mock_request.return_value = {
        "Head": [
            {"YearPeriod": 2026, "TermCode": "Q1"},
            {"YearPeriod": 2025, "TermCode": "Q4"},
        ],
        "Content": {
            "Báo cáo tình hình tài chính": [
                {
                    "ID": 2,
                    "ReportNormID": 2995,
                    "NameEn": "Assets",
                    "Value1": None,
                    "Value2": None,
                },
                {
                    "ID": 3,
                    "ReportNormID": 2996,
                    "NameEn": "Total assets",
                    "Value1": 50,
                    "Value2": 45,
                },
                {
                    "ID": 4,
                    "ReportNormID": 3003,
                    "NameEn": "I. Cash and cash equivalents",
                    "Value1": 12.5,
                    "Value2": 10,
                }
            ]
        },
    }

    df = KBSFinancial().balance_sheet("FPT")

    assert list(df.columns) == [
        "symbol",
        "year",
        "period",
        "total_assets",
        "cash_and_cash_equivalents",
    ]
    assert df[["year", "period"]].to_dict("records") == [
        {"year": 2026, "period": "Q1"},
        {"year": 2025, "period": "Q4"},
    ]
    assert df.loc[0, "cash_and_cash_equivalents"] == 12_500
    assert df.loc[0, "total_assets"] == 50_000
    assert "total_assets__2996" not in df.columns
    assert df.attrs["unit_multiplier"] == 1000.0
    assert mock_request.call_args.kwargs["url"].endswith("/investment/stock/finance-info/FPT")


@patch("claude_finance_kit._provider.kbs.financial.send_request")
def test_kbs_cash_flow_uses_case_sensitive_provider_parameters(mock_request):
    mock_request.return_value = {}

    KBSFinancial().cash_flow("FPT", period="quarter")

    params = mock_request.call_args.kwargs["params"]
    assert params["code"] == "FPT"
    assert params["termType"] == 2
    assert params["termtype"] == 2
    assert "languageid" not in params


@patch("claude_finance_kit._provider.kbs.financial.send_request")
def test_kbs_financial_tolerates_null_head(mock_request):
    mock_request.return_value = {"Head": None, "Content": {}}

    df = KBSFinancial().balance_sheet("FPT")

    assert df.empty
    assert list(df.columns) == ["symbol", "year", "period"]


def test_finance_facade_scales_statements_but_not_year_metadata():
    provider = type(
        "Provider",
        (),
        {
            "balance_sheet": lambda self, symbol, period: pd.DataFrame(
                [
                    {
                        "symbol": symbol,
                        "year": 2026,
                        "year_period": 2026,
                        "period": "Q1",
                        "row_number": 4,
                        "cash": 12.5,
                    }
                ]
            )
        },
    )()

    df = Finance("FPT", provider).balance_sheet(unit_multiplier=1000)

    assert df.loc[0, "year"] == 2026
    assert df.loc[0, "year_period"] == 2026
    assert df.loc[0, "row_number"] == 4
    assert df.loc[0, "cash"] == 12_500
    assert df.attrs["unit_multiplier"] == 1000.0


@pytest.mark.parametrize("multiplier", [float("nan"), float("inf"), float("-inf")])
def test_finance_facade_rejects_non_finite_multiplier(multiplier):
    provider = type(
        "Provider",
        (),
        {"balance_sheet": lambda self, symbol, period: pd.DataFrame([{"cash": 1.0}])},
    )()

    with pytest.raises(ValueError, match="finite"):
        Finance("FPT", provider).balance_sheet(unit_multiplier=multiplier)


def test_finance_facade_preserves_source_and_effective_unit_multipliers():
    raw = pd.DataFrame([{"symbol": "FPT", "year": 2026, "period": "Q1", "cash": 12_500}])
    raw.attrs["unit_multiplier"] = 1000.0
    provider = type(
        "Provider",
        (),
        {"balance_sheet": lambda self, symbol, period: raw},
    )()

    df = Finance("FPT", provider).balance_sheet(unit_multiplier=2)

    assert df.loc[0, "cash"] == 25_000
    assert df.attrs["source_unit_multiplier"] == 1000.0
    assert df.attrs["unit_multiplier"] == 2.0
    assert df.attrs["effective_unit_multiplier"] == 2000.0


@patch("claude_finance_kit._provider.kbs.trading.requests.post")
def test_kbs_price_board_uses_correct_volume_columns(mock_post):
    response = mock_post.return_value
    response.status_code = 200
    response.json.return_value = [{"SB": "FPT", "TT": 1000, "CV": 50, "CP": 100}]

    df = KBSTrading().price_board(["FPT"])

    assert df.loc[0, "volume_accumulated"] == 1000
    assert df.loc[0, "volume_last"] == 50
    assert "total_trades" not in df.columns


def _msn_stock(symbol: str, sec_id: str, locale: str = "vi-vn") -> str:
    return json.dumps({"RT00S": symbol, "SecId": sec_id, "locale": locale})


@patch("claude_finance_kit._provider.msn.listing.send_request")
def test_msn_resolves_exact_vietnam_symbol_to_secid(mock_request):
    mock_request.return_value = {
        "data": {"stocks": [_msn_stock("FPT", "aqji2w"), _msn_stock("FRT", "azrju2")]}
    }

    assert MSNListing().resolve_symbol_id("fpt") == "aqji2w"


@patch("claude_finance_kit._provider.msn.listing.send_request")
def test_msn_rejects_fuzzy_symbol_result(mock_request):
    mock_request.return_value = {"data": {"stocks": [_msn_stock("FRT", "azrju2")]}}

    with pytest.raises(ValueError, match="exact SecId"):
        MSNListing().resolve_symbol_id("FPT")


@patch("claude_finance_kit._provider.msn.listing.send_request")
def test_msn_search_handles_null_data_as_empty_result(mock_request):
    mock_request.return_value = {"data": None}

    df = MSNListing().search_symbol("FPT")

    assert df.empty
    assert {"symbol", "symbol_id"} <= set(df.columns)


@patch("claude_finance_kit._provider.msn.quote.send_request")
def test_msn_history_queries_with_dynamically_resolved_secid(mock_request):
    mock_request.return_value = [
        {
            "series": [
                {
                    "timeStamps": "2026-01-02T00:00:00Z",
                    "openPrices": 100,
                    "pricesHigh": 110,
                    "pricesLow": 95,
                    "prices": 105,
                    "volumes": 1000,
                }
            ]
        }
    ]
    quote = MSNQuote()
    quote._api_key = "test-key"
    with patch.object(quote._listing, "resolve_symbol_id", return_value="aqji2w") as resolve:
        df = quote.history("FPT", "2026-01-01", "2026-01-03")

    resolve.assert_called_once_with("FPT")
    assert mock_request.call_args.kwargs["params"]["ids"] == "aqji2w"
    assert mock_request.call_args.kwargs["params"]["StartTime"] == "2025-12-31T17:00:00.000Z"
    assert mock_request.call_args.kwargs["params"]["EndTime"] == "2026-01-03T16:59:59.999Z"
    assert df.loc[0, "close"] == 105
    assert df.attrs["sec_id"] == "aqji2w"


@patch("claude_finance_kit._provider.msn.quote.send_request")
def test_msn_history_handles_null_series_container_as_empty_frame(mock_request):
    mock_request.return_value = [None]
    quote = MSNQuote()
    quote._api_key = "test-key"
    with patch.object(quote._listing, "resolve_symbol_id", return_value="aqji2w"):
        df = quote.history("FPT", "2026-01-01", "2026-01-03")

    assert df.empty
    assert list(df.columns) == ["time", "open", "high", "low", "close", "volume"]


def test_msn_stock_provider_is_registered_without_network_call():
    stock = Stock("FPT", source="MSN")

    assert stock._source == "MSN"
    assert type(stock._provider).__name__ == "MSNStockProvider"
