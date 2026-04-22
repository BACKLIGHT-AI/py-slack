"""Slack Web API helpers — everything posts via `chat.postMessage`.

Unifies all Slack interactions around the bot token. `notify_success`
and `notify_failure` are convenience wrappers that pick the right
channel and build the right Block Kit payload for you;
`post_incident_message` + `post_thread_reply` expose the raw path
when you need the returned message `ts` for threading.

All helpers are awaitable. Failures are logged and never raised —
posting to Slack must not break the caller's flow.
"""

from __future__ import annotations

import logging
from typing import Any

from backlight_slack.blocks import make_failure_blocks, make_success_blocks
from backlight_slack.config import SlackConfig

logger = logging.getLogger("backlight_slack.api")


async def notify_success(
    config: SlackConfig,
    title: str,
    details: dict[str, str] | None = None,
) -> None:
    """Post a :white_check_mark: success message to `config.success_channel`."""
    if not config.enabled or not config.bot_token or not config.success_channel:
        return
    blocks = make_success_blocks(config.service_name, title, details)
    await _post(config, config.success_channel, title, blocks)


async def notify_failure(
    config: SlackConfig,
    title: str,
    error: BaseException,
    context: dict[str, str] | None = None,
) -> None:
    """Post a :rotating_light: failure (with traceback) to `config.failure_channel`."""
    if not config.enabled or not config.bot_token or not config.failure_channel:
        return
    blocks = make_failure_blocks(config.service_name, title, error, context)
    await _post(config, config.failure_channel, title, blocks)


async def post_incident_message(
    config: SlackConfig,
    text: str,
    blocks: list[dict[str, Any]],
) -> str | None:
    """Post an incident message to `config.failure_channel`; returns its `ts`.

    `text` is the fallback plaintext used in push notifications and
    clients without Block Kit support; `blocks` is the rich payload
    rendered in-channel.

    Returns `None` when the config is disabled, the bot token / channel
    are missing, or the API call fails. Callers typically check
    truthiness and record the `ts` for later `post_thread_reply` calls.
    """
    if not config.enabled or not config.bot_token or not config.failure_channel:
        return None
    return await _post(config, config.failure_channel, text, blocks)


async def post_thread_reply(
    config: SlackConfig,
    thread_ts: str,
    text: str,
    blocks: list[dict[str, Any]],
) -> None:
    """Post a thread reply on the incident message identified by `thread_ts`."""
    if not config.enabled or not config.bot_token or not config.failure_channel:
        return
    await _post(config, config.failure_channel, text, blocks, thread_ts=thread_ts)


async def _post(
    config: SlackConfig,
    channel: str,
    text: str,
    blocks: list[dict[str, Any]],
    thread_ts: str | None = None,
) -> str | None:
    """Shared `chat.postMessage` call — returns message `ts`, or None on error."""
    try:
        from slack_sdk.web.async_client import AsyncWebClient

        client = AsyncWebClient(token=config.bot_token)
        kwargs: dict[str, Any] = {"channel": channel, "text": text, "blocks": blocks}
        if thread_ts is not None:
            kwargs["thread_ts"] = thread_ts
        response = await client.chat_postMessage(**kwargs)
        if not response.get("ok"):
            logger.warning("chat.postMessage not ok: %s", response.get("error"))
            return None
        ts = response.get("ts")
        return str(ts) if ts else None
    except Exception as exc:
        logger.warning("failed to post message to %s: %s", channel, exc)
        return None
