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
    bot_token: str = Field(
        default="",
        description=(
            "Bot token (xoxb-...) used for every API call. The bot "
            "must be invited to both success_channel and failure_channel."
        ),
    )
    success_channel: str = Field(
        default="",
        description=(
            "Channel for success notifications (e.g. '#shad-successes'). "
            "Leave empty to disable success posts without touching "
            "`enabled`."
        ),
    )
    failure_channel: str = Field(
        default="",
        description=(
            "Channel for failure notifications and incident messages "
            "(e.g. '#shad-fails'). Also the target for threaded "
            "recovery replies."
        ),
    )
