"""Slack notification helpers for Backlight customer backends.

Public API — import from the package root:

    from backlight_slack import (
        SlackConfig,
        notify_success,
        notify_failure,
        post_incident_message,
        post_thread_reply,
        make_success_blocks,
        make_failure_blocks,
        make_incident_blocks,
    )
"""

from backlight_slack.api import (
    notify_failure,
    notify_success,
    post_incident_message,
    post_thread_reply,
)
from backlight_slack.blocks import (
    make_failure_blocks,
    make_incident_blocks,
    make_success_blocks,
)
from backlight_slack.config import SlackConfig

__version__ = "0.2.1"

__all__ = [
    "SlackConfig",
    "__version__",
    "make_failure_blocks",
    "make_incident_blocks",
    "make_success_blocks",
    "notify_failure",
    "notify_success",
    "post_incident_message",
    "post_thread_reply",
]
