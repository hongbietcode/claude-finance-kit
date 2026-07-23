"""Tests for provider HTTP transport hardening."""

from unittest.mock import Mock, patch

import pytest

from claude_finance_kit._internal.http_client import sanitize_url, send_request
from claude_finance_kit._internal.user_agent import get_headers
from claude_finance_kit._provider._market_http import MarketHttpClient
from claude_finance_kit.core.exceptions import AuthenticationError, ProviderError


def test_sanitize_url_normalizes_host_and_preserves_query():
    assert (
        sanitize_url(" https://IQ.VIETCAP.COM.VN/api/data?symbol=FPT ", {"iq.vietcap.com.vn"})
        == "https://iq.vietcap.com.vn/api/data?symbol=FPT"
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://iq.vietcap.com.vn/api/data",
        "https://user:pass@iq.vietcap.com.vn/api/data",
        "https://iq.vietcap.com.vn/api/data#fragment",
        "https://evil.example/api/data",
    ],
)
def test_sanitize_url_rejects_unsafe_provider_urls(url):
    with pytest.raises(ValueError):
        sanitize_url(url, {"iq.vietcap.com.vn"})


@patch("claude_finance_kit._internal.http_client.requests.get")
def test_send_request_uses_fallback_after_transport_failure(mock_get):
    failed = Mock(status_code=503, reason="Unavailable")
    succeeded = Mock(status_code=200)
    succeeded.json.return_value = {"data": [1]}
    mock_get.side_effect = [failed, succeeded]

    result = send_request(
        "https://primary.example/data",
        {},
        fallback_urls=["https://fallback.example/data"],
        allowed_hosts={"primary.example", "fallback.example"},
    )

    assert result == {"data": [1]}
    assert mock_get.call_count == 2


@patch("claude_finance_kit._internal.http_client.requests.get")
def test_send_request_does_not_fallback_on_successful_empty_payload(mock_get):
    response = Mock(status_code=200)
    response.json.return_value = {}
    mock_get.return_value = response

    result = send_request(
        "https://primary.example/data",
        {},
        fallback_urls=["https://fallback.example/data"],
        allowed_hosts={"primary.example", "fallback.example"},
    )

    assert result == {}
    mock_get.assert_called_once()


@patch("claude_finance_kit._internal.http_client.requests.get")
def test_send_request_does_not_fallback_or_expose_key_on_auth_failure(mock_get):
    response = Mock(status_code=401, reason="Unauthorized")
    mock_get.return_value = response
    secret = "do-not-leak-this-key"

    with pytest.raises(AuthenticationError) as captured:
        send_request(
            f"https://primary.example/data?apikey={secret}",
            {},
            fallback_urls=["https://fallback.example/data"],
            allowed_hosts={"primary.example", "fallback.example"},
        )

    assert secret not in str(captured.value)
    mock_get.assert_called_once()


@patch("claude_finance_kit._internal.http_client.requests.get")
def test_send_request_rejects_redirect_without_forwarding_headers(mock_get):
    response = Mock(status_code=302, headers={"Location": "https://evil.example/steal"})
    mock_get.return_value = response

    with pytest.raises(ProviderError, match="Redirect rejected"):
        send_request(
            "https://primary.example/data",
            {"X-API-Key": "secret"},
            allowed_hosts={"primary.example"},
        )

    assert mock_get.call_args.kwargs["allow_redirects"] is False


def test_market_http_client_rejects_redirect_without_forwarding_credentials():
    client = MarketHttpClient(
        "ALPACA",
        {"data.alpaca.markets"},
        {"APCA-API-KEY-ID": "secret"},
    )
    response = Mock(status_code=307, headers={"Location": "https://evil.example/steal"})
    client.session.request = Mock(return_value=response)

    with pytest.raises(ProviderError, match="redirect was rejected"):
        client.request("GET", "https://data.alpaca.markets/v2/stocks/AAPL/bars")

    assert client.session.request.call_args.kwargs["allow_redirects"] is False


def test_vci_headers_remove_device_identifiers_after_overrides():
    headers = get_headers(
        data_source="VCI",
        override_headers={"Device-ID": "secret", "device_id": "secret-2", "X-Test": "ok"},
    )

    assert "Device-ID" not in headers
    assert "device_id" not in headers
    assert headers["X-Test"] == "ok"
