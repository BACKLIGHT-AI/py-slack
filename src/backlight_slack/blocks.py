"""Block Kit builders shared by webhook and Web API helpers.

All functions are pure — no I/O — so they're cheap to unit-test and
safe to call anywhere. The returned structure is the `blocks` array
you pass to `chat.postMessage` or an incoming webhook payload.
"""

from __future__ import annotations

import traceback
from datetime import UTC, datetime
from typing import Any

_MAX_TEXT_LENGTH = 2800  # Slack blocks cap at 3000; leave margin


def _truncate(text: str, max_len: int = _MAX_TEXT_LENGTH) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 20] + "\n... (truncated)"


def _header_context(service_name: str) -> dict[str, Any]:
    """Shared `Service: X | Time: Y` context block."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    return {
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": f"*Service:* {service_name}  |  *Time:* {now}"},
        ],
    }


def make_success_blocks(
    service_name: str,
    title: str,
    details: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Build a :white_check_mark: success notification.

    `details` is an optional key/value map rendered as a bulleted
    section under the title (e.g. `{"records": "24000", "duration": "3.2s"}`).
    """
    blocks: list[dict[str, Any]] = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*:white_check_mark: {title}*"},
        },
        _header_context(service_name),
    ]
    if details:
        detail_lines = "\n".join(f"*{k}:* {v}" for k, v in details.items())
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": _truncate(detail_lines)}}
        )
    return blocks


def make_failure_blocks(
    service_name: str,
    title: str,
    error: BaseException,
    context: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Build a :rotating_light: failure notification with a full traceback.

    `context` is an optional key/value map rendered below the traceback
    (e.g. `{"uid": "abc123", "path": "/v1/orders"}`).
    """
    tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    blocks: list[dict[str, Any]] = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*:rotating_light: {title}*"},
        },
        _header_context(service_name),
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Error:* `{type(error).__name__}`\n*Message:* {error}",
            },
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"```{_truncate(tb)}```"},
        },
    ]
    if context:
        ctx_lines = "\n".join(f"*{k}:* {v}" for k, v in context.items())
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": _truncate(ctx_lines)}}
        )
    return blocks


def make_incident_blocks(
    service_name: str,
    title: str,
    description: str,
    triggered_by: str | None = None,
) -> list[dict[str, Any]]:
    """Build a :warning: incident notification for ongoing outages.

    Designed for messages that will receive a thread-reply later when
    the incident resolves (via Web API `chat.postMessage`).

    `description` is the plain-English summary shown in-channel.
    `triggered_by` is an optional short string (e.g. a request path,
    a scheduled-job name) rendered in monospace below the description.
    """
    body = description
    if triggered_by:
        body = f"{description}\n*Triggered by:* `{triggered_by}`"
    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*:warning: {title}*"},
        },
        _header_context(service_name),
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": _truncate(body)},
        },
    ]
