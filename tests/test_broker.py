"""Unit tests for the Jason broker transport.

All network and OIDC calls are mocked -- no live services required.
We patch at the module level:
  - ``backlight_slack.broker._mint_oidc_token`` -- avoids fighting
    Python's namespace-package import machinery for google-auth.
  - ``httpx.AsyncClient`` -- async HTTP client used by the transport.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backlight_slack import BrokerConfig, SlackConfig, post_via_broker
from backlight_slack.broker import post_via_broker as _low_level_post

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_TOKEN = "ya29.fake-oidc-token"


def _broker_cfg(**kwargs: Any) -> BrokerConfig:
    return BrokerConfig(project="test-project", **kwargs)


def _slack_cfg(**kwargs: Any) -> SlackConfig:
    return SlackConfig(broker=_broker_cfg(), **kwargs)


def _ok_response(ts: str = "1700000000.000100") -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"ok": True, "ts": ts}
    resp.text = ""
    return resp


def _error_response(status: int = 502, body: str = "bad gateway") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {}
    resp.text = body
    return resp


# ---------------------------------------------------------------------------
# Low-level post_via_broker (backlight_slack.broker)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_low_level_success() -> None:
    """Happy path: OIDC mint succeeds, broker returns 200 ok."""
    with (
        patch("backlight_slack.broker._mint_oidc_token", return_value=_FAKE_TOKEN),
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock(return_value=_ok_response("1700000001.000001"))

        result = await _low_level_post(
            _broker_cfg(),
            channel="#test",
            text="hello",
        )

    assert result == "1700000001.000001"


@pytest.mark.asyncio
async def test_low_level_with_blocks_and_thread_ts() -> None:
    """blocks and thread_ts are forwarded in the payload."""
    captured_payload: dict[str, Any] = {}

    async def fake_post(url: str, **kwargs: Any) -> MagicMock:
        captured_payload.update(kwargs.get("json", {}))
        return _ok_response()

    with (
        patch("backlight_slack.broker._mint_oidc_token", return_value=_FAKE_TOKEN),
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock(side_effect=fake_post)

        await _low_level_post(
            _broker_cfg(),
            channel="#ch",
            text="fallback",
            blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "hi"}}],
            thread_ts="1700000000.000001",
        )

    assert "blocks" in captured_payload
    assert captured_payload["thread_ts"] == "1700000000.000001"
    assert captured_payload["project"] == "test-project"


@pytest.mark.asyncio
async def test_low_level_oidc_mint_failure_returns_none() -> None:
    """When OIDC minting raises (local dev), the transport returns None silently."""
    with patch(
        "backlight_slack.broker._mint_oidc_token",
        side_effect=Exception("no metadata server"),
    ):
        result = await _low_level_post(_broker_cfg(), channel="#ch", text="hi")

    assert result is None


@pytest.mark.asyncio
async def test_low_level_network_error_returns_none() -> None:
    """Network-level exception from httpx is caught and returns None."""
    with (
        patch("backlight_slack.broker._mint_oidc_token", return_value=_FAKE_TOKEN),
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

        result = await _low_level_post(_broker_cfg(), channel="#ch", text="hi")

    assert result is None


@pytest.mark.asyncio
async def test_low_level_broker_http_error_returns_none() -> None:
    """Broker returns 4xx/5xx -- transport returns None."""
    with (
        patch("backlight_slack.broker._mint_oidc_token", return_value=_FAKE_TOKEN),
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock(return_value=_error_response(502))

        result = await _low_level_post(_broker_cfg(), channel="#ch", text="hi")

    assert result is None


@pytest.mark.asyncio
async def test_low_level_broker_ok_false_returns_none() -> None:
    """Broker returns 200 but ok=false -- transport returns None."""
    bad_resp = MagicMock()
    bad_resp.status_code = 200
    bad_resp.json.return_value = {"ok": False, "error": "channel_not_found"}
    bad_resp.text = ""

    with (
        patch("backlight_slack.broker._mint_oidc_token", return_value=_FAKE_TOKEN),
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock(return_value=bad_resp)

        result = await _low_level_post(_broker_cfg(), channel="#ch", text="hi")

    assert result is None


# ---------------------------------------------------------------------------
# High-level post_via_broker (backlight_slack.api -- takes SlackConfig)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_high_level_routes_through_broker() -> None:
    """SlackConfig with broker set routes through the broker transport."""
    with (
        patch("backlight_slack.broker._mint_oidc_token", return_value=_FAKE_TOKEN),
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock(return_value=_ok_response("1700000002.000002"))

        result = await post_via_broker(_slack_cfg(), channel="#test", text="hi")

    assert result == "1700000002.000002"


@pytest.mark.asyncio
async def test_high_level_no_broker_returns_none() -> None:
    """SlackConfig without broker set: post_via_broker is a no-op."""
    config = SlackConfig(broker=None)
    result = await post_via_broker(config, channel="#test", text="hi")
    assert result is None


@pytest.mark.asyncio
async def test_high_level_disabled_returns_none() -> None:
    """config.enabled=False short-circuits immediately."""
    config = SlackConfig(enabled=False, broker=_broker_cfg())
    result = await post_via_broker(config, channel="#test", text="hi")
    assert result is None


@pytest.mark.asyncio
async def test_high_level_caller_field_forwarded() -> None:
    """BrokerConfig.caller is included in the payload when set."""
    captured: dict[str, Any] = {}

    async def fake_post(url: str, **kwargs: Any) -> MagicMock:
        captured.update(kwargs.get("json", {}))
        return _ok_response()

    broker = BrokerConfig(
        project="myproj", caller="myproj-backend@myproj.iam.gserviceaccount.com"
    )
    config = SlackConfig(broker=broker)

    with (
        patch("backlight_slack.broker._mint_oidc_token", return_value=_FAKE_TOKEN),
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock(side_effect=fake_post)

        await post_via_broker(config, channel="#ch", text="hello")

    assert captured.get("caller") == "myproj-backend@myproj.iam.gserviceaccount.com"


@pytest.mark.asyncio
async def test_high_level_no_caller_omits_field() -> None:
    """BrokerConfig with empty caller omits the field from the payload."""
    captured: dict[str, Any] = {}

    async def fake_post(url: str, **kwargs: Any) -> MagicMock:
        captured.update(kwargs.get("json", {}))
        return _ok_response()

    broker = BrokerConfig(project="myproj", caller="")
    config = SlackConfig(broker=broker)

    with (
        patch("backlight_slack.broker._mint_oidc_token", return_value=_FAKE_TOKEN),
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock(side_effect=fake_post)

        await post_via_broker(config, channel="#ch", text="hello")

    assert "caller" not in captured
