"""Configuration model shared by every helper in this package."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SlackConfig(BaseModel):
    """Container for all Slack credentials + channel routing.

    Every public helper in `backlight_slack` takes a `SlackConfig`
    as its first argument, so the package never reads a consumer's
    `Settings` or environment directly. The consumer is responsible
    for populating this model from its own config system (e.g.
    Pydantic Settings + Secret Manager on GCP).
    """

    enabled: bool = Field(
        default=True,
        description=(
            "Master kill-switch. Typically tied to the consumer's "
            "Cloud Run detection — on in production, off in local dev "
            "unless explicitly overridden."
        ),
    )
    service_name: str = Field(
        default="unknown",
        description=(
            "Human-readable service identifier shown in message "
            "headers (e.g. 'shad-backend', 'shad-backend-staging')."
        ),
    )
    webhook_success: str = Field(
        default="",
        description="Incoming webhook URL for success notifications.",
    )
    webhook_failure: str = Field(
        default="",
        description="Incoming webhook URL for failure notifications.",
    )
    bot_token: str = Field(
        default="",
        description=(
            "Bot token (xoxb-...) required for `chat.postMessage` Web "
            "API calls. Needed for threaded incident replies — webhooks "
            "do not return a message `ts`."
        ),
    )
    channel: str = Field(
        default="",
        description=(
            "Target channel for Web API messages (e.g. '#shad-fails'). "
            "The bot must be invited to this channel."
        ),
    )
