"""Jason Slack broker transport.

Posts Slack messages via the central Jason broker service instead of
calling Slack directly with a bot token.  The broker holds the @Jason bot
token; every caller authenticates with a Google OIDC identity token minted
for the broker URL as audience.

On Cloud Run the token is minted automatically via the GCP metadata server.
On a local workstation where ADC is a human user account, :func:`_mint_oidc_token`
raises (human accounts cannot mint Cloud Run identity tokens).  The entire
transport is **fail-soft**: any failure -- OIDC mint error, network error,
or a non-200 response from the broker -- is logged and returns ``None``.
The caller's flow is never interrupted.

Public API
----------
:func:`post_via_broker` is the only entry point.  Consumers should prefer
using it through the top-level :func:`backlight_slack.post_via_broker`
alias which accepts a :class:`~backlight_slack.config.SlackConfig` (with a
populated ``broker`` field) and handles the ``enabled`` guard.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from backlight_slack.config import BrokerConfig

logger = logging.getLogger("backlight_slack.broker")


def _mint_oidc_token(audience: str) -> str:
    """Mint a Google OIDC identity token for *audience*.

    On Cloud Run uses the metadata server.  On a local workstation with ADC
    pointing at a human user account, ``fetch_id_token`` raises -- the
    caller is responsible for catching the exception and degrading gracefully.

    This function is a thin wrapper extracted to make it easy to patch in
    tests without fighting Python's namespace-package import machinery.
    """
    import google.auth.transport.requests
    import google.oauth2.id_token

    request = google.auth.transport.requests.Request()
    token: str = google.oauth2.id_token.fetch_id_token(  # type: ignore[no-untyped-call]
        request, audience
    )
    return token


async def post_via_broker(
    broker: BrokerConfig,
    channel: str,
    text: str,
    blocks: list[dict[str, Any]] | None = None,
    thread_ts: str | None = None,
) -> str | None:
    """Post a Slack message via the Jason broker.

    Mints a Google OIDC identity token for ``broker.url`` as the audience,
    then POSTs to ``{broker.url}/v1/slack/post``.  Never raises -- all
    failures are logged and returned as ``None`` so callers can decide their
    own error contract.

    Args:
        broker: :class:`~backlight_slack.config.BrokerConfig` containing the
            broker URL, project key, and optional caller string.
        channel: Slack channel name, e.g. ``"#shad-fails"``.
        text: Plain-text fallback (required by Slack even when ``blocks``
            are provided).
        blocks: Optional Block Kit block list.
        thread_ts: Optional parent message timestamp for thread replies.

    Returns:
        Slack message ``ts`` on success, ``None`` on any failure.
    """
    # --- Mint OIDC identity token -----------------------------------------
    try:
        token = _mint_oidc_token(broker.url)
    except Exception as exc:
        # On local dev ADC is a human account -- fetch_id_token raises.
        # Also catches transient metadata server errors on Cloud Run.
        logger.debug(
            "backlight_slack.broker: OIDC mint failed (expected on local dev): %s",
            exc,
            extra={"channel": channel},
        )
        return None

    # --- Build payload -------------------------------------------------------
    payload: dict[str, Any] = {
        "channel": channel,
        "text": text,
        "project": broker.project,
    }
    if broker.caller:
        payload["caller"] = broker.caller
    if blocks is not None:
        payload["blocks"] = blocks
    if thread_ts is not None:
        payload["thread_ts"] = thread_ts

    # --- POST to broker ------------------------------------------------------
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{broker.url.rstrip('/')}/v1/slack/post",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
                json=payload,
                timeout=8.0,
            )
    except Exception as exc:
        logger.error(
            "backlight_slack.broker: request failed: %s",
            exc,
            extra={"channel": channel},
        )
        return None

    if resp.status_code == 200:
        data: dict[str, Any] = resp.json()
        if data.get("ok"):
            ts = data.get("ts")
            return str(ts) if ts else None
        logger.error(
            "backlight_slack.broker: broker returned ok=false: %s",
            resp.text[:200],
            extra={"channel": channel},
        )
        return None

    logger.error(
        "backlight_slack.broker: HTTP %s from broker: %s",
        resp.status_code,
        resp.text[:200],
        extra={"channel": channel},
    )
    return None
