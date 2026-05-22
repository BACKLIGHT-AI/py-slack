"""Slack notification helpers for Backlight customer backends.

Public API -- import from the package root:

    from backlight_slack import (
        SlackConfig,
        BrokerConfig,
        notify_success,
        notify_failure,
        post_incident_message,
        post_thread_reply,
        post_via_broker,
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
    post_via_broker,
)
from backlight_slack.blocks import (
    make_failure_blocks,
    make_incident_blocks,
    make_success_blocks,
)
from backlight_slack.config import BrokerConfig, SlackConfig

__version__ = "0.3.0"

__all__ = [
    "BrokerConfig",
    "SlackConfig",
    "__version__",
    "make_failure_blocks",
    "make_incident_blocks",
    "make_success_blocks",
    "notify_failure",
    "notify_success",
    "post_incident_message",
    "post_thread_reply",
    "post_via_broker",
]
