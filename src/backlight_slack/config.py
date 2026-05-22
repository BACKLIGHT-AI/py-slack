"""Configuration model shared by every helper in this package."""

from __future__ import annotations

from pydantic import BaseModel, Field

#: Default broker URL — also used as the OIDC audience.
JASON_BROKER_URL = "https://jason-slack-broker-akk67ufdqa-ew.a.run.app"


class BrokerConfig(BaseModel):
    """Credentials for the Jason Slack broker transport.

    Use this instead of (or in addition to) `bot_token` / `success_channel`
    / `failure_channel` when the consumer wants to post through the central
    Jason broker rather than holding its own bot token.

    The broker authenticates callers via Google OIDC identity tokens minted
    for the broker URL as audience.  On Cloud Run the token is minted
    automatically via the metadata server.  On a local workstation with ADC
    pointing at a human account, minting fails and the transport degrades
    gracefully (returns ``None``, never raises).

    Attributes:
        url: Full base URL of the Jason broker service.  Doubles as the OIDC
            audience.  Defaults to the production instance.
        project: Short project key sent as ``project`` in the broker payload
            (e.g. ``"shad"``, ``"bagelboys"``).  Used for audit logging on
            the broker side.
        caller: Optional free-text audit string.  When empty the transport
            omits the field; the broker uses the OIDC ``email`` claim
            instead.
    """

    url: str = Field(
        default=JASON_BROKER_URL,
        description="Broker base URL (also used as OIDC audience).",
    )
    project: str = Field(
        description="Short project key passed in the broker payload (e.g. 'shad').",
    )
    caller: str = Field(
        default="",
        description=(
            "Optional audit string.  The broker identifies the caller "
            "from the OIDC token's email claim; this field is supplementary."
        ),
    )


class SlackConfig(BaseModel):
    """Container for all Slack credentials + channel routing.

    Every public helper in `backlight_slack` takes a `SlackConfig`
    as its first argument, so the package never reads a consumer's
    `Settings` or environment directly. The consumer is responsible
    for populating this model from its own config system (e.g.
    Pydantic Settings + Secret Manager on GCP).

    **Broker mode** — set ``broker`` to a :class:`BrokerConfig` instance.
    When ``broker`` is set the package-level helpers
    (:func:`~backlight_slack.post_via_broker`) will route through the
    Jason broker instead of calling Slack directly.  The existing
    ``bot_token`` / ``success_channel`` / ``failure_channel`` fields
    remain fully supported and unaffected.
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
    broker: BrokerConfig | None = Field(
        default=None,
        description=(
            "Optional Jason broker transport config.  When set, "
            ":func:`~backlight_slack.post_via_broker` routes through "
            "the broker using Google OIDC auth instead of a raw bot token."
        ),
    )
