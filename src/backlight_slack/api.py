"""Slack Web API helpers for threaded incident messages.

Unlike webhooks, `chat.postMessage` returns a message `ts` we can
later use to post thread replies, so the consumer can track an
incident + its resolution as one Slack thread. The bot identified
by `config.bot_token` must be invited to `config.channel` — create
the app in the Slack admin and grant `chat:write`.
"""

from __future__ import annotations

import logging
from typing import Any

from backlight_slack.config import SlackConfig

logger = logging.getLogger("backlight_slack.api")


async def post_incident_message(
    config: SlackConfig,
    text: str,
    blocks: list[dict[str, Any]],
) -> str | None:
    """Post an incident message and return its Slack `ts`, or None.

    `text` is the fallback plaintext used in push notifications and
    clients without Block Kit support; `blocks` is the rich payload
    rendered in-channel.

    Returns `None` when the config is disabled, the bot token/channel
    are missing, or the API call fails. Never raises — callers
    typically check truthiness and record the `ts` for later
    `post_thread_reply` calls.
    """
    if not config.enabled or not config.bot_token or not config.channel:
        return None
    try:
        from slack_sdk.web.async_client import AsyncWebClient

        client = AsyncWebClient(token=config.bot_token)
        response = await client.chat_postMessage(
            channel=config.channel, text=text, blocks=blocks
        )
        if not response.get("ok"):
            logger.warning("chat.postMessage not ok: %s", response.get("error"))
            return None
        ts = response.get("ts")
        return str(ts) if ts else None
    except Exception as exc:
        logger.warning("failed to post incident message: %s", exc)
        return None


async def post_thread_reply(
    config: SlackConfig,
    thread_ts: str,
    text: str,
    blocks: list[dict[str, Any]],
) -> None:
    """Post a thread reply on the message identified by `thread_ts`.

    Fire-and-forget: always swallows errors so a Slack outage cannot
    break the underlying recovery path.
    """
    if not config.enabled or not config.bot_token or not config.channel:
        return
    try:
        from slack_sdk.web.async_client import AsyncWebClient

        client = AsyncWebClient(token=config.bot_token)
        response = await client.chat_postMessage(
            channel=config.channel,
            thread_ts=thread_ts,
            text=text,
            blocks=blocks,
        )
        if not response.get("ok"):
            logger.warning("thread reply not ok: %s", response.get("error"))
    except Exception as exc:
        logger.warning("failed to post thread reply: %s", exc)
