"""Incoming-webhook helpers for success/failure notifications.

These are awaitable but do not return anything — webhooks do not
give back a message `ts`, so threaded replies require the Web API
(`backlight_slack.api`). Errors are logged and swallowed; posting
to Slack must never break the caller's flow.
"""

from __future__ import annotations

import logging

from backlight_slack.blocks import make_failure_blocks, make_success_blocks
from backlight_slack.config import SlackConfig

logger = logging.getLogger("backlight_slack.webhook")


async def notify_success(
    config: SlackConfig,
    title: str,
    details: dict[str, str] | None = None,
) -> None:
    """Post a success notification to the configured success webhook.

    Returns early (no-op) if the config is disabled or the webhook
    URL is empty — consumer can always call without guarding.
    """
    if not config.enabled or not config.webhook_success:
        return
    blocks = make_success_blocks(config.service_name, title, details)
    await _send_webhook(config.webhook_success, blocks)


async def notify_failure(
    config: SlackConfig,
    title: str,
    error: BaseException,
    context: dict[str, str] | None = None,
) -> None:
    """Post a failure notification (with traceback) to the failure webhook."""
    if not config.enabled or not config.webhook_failure:
        return
    blocks = make_failure_blocks(config.service_name, title, error, context)
    await _send_webhook(config.webhook_failure, blocks)


async def _send_webhook(webhook_url: str, blocks: list[dict[str, object]]) -> None:
    """Send a pre-built block payload to an incoming-webhook URL."""
    try:
        from slack_sdk.webhook.async_client import AsyncWebhookClient

        client = AsyncWebhookClient(webhook_url)
        response = await client.send(blocks=blocks)
        if response.status_code != 200:
            logger.warning(
                "webhook returned %s: %s", response.status_code, response.body
            )
    except Exception as exc:
        logger.warning("failed to send webhook: %s", exc)
