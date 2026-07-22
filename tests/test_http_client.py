"""Tests for provider HTTP transport hardening."""

from unittest.mock import Mock, patch

import pytest

from claude_finance_kit._internal.http_client import sanitize_url, send_request
from claude_finance_kit._internal.user_agent import get_headers


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


def test_vci_headers_remove_device_identifiers_after_overrides():
    headers = get_headers(
        data_source="VCI",
        override_headers={"Device-ID": "secret", "device_id": "secret-2", "X-Test": "ok"},
    )

    assert "Device-ID" not in headers
    assert "device_id" not in headers
    assert headers["X-Test"] == "ok"
