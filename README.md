# backlight-slack

Slack notification helpers shared across Backlight customer backends
(SHAD, BagelBoys, HIRSadvies, Mave-Global).

All helpers post via `chat.postMessage` using a **bot token** — one
auth path, one secret per project. Threading (`post_incident_message`
returns the message `ts`, `post_thread_reply` posts on that `ts`) is
the main reason for using the Web API over incoming webhooks.

Block Kit builders (`make_success_blocks`, `make_failure_blocks`,
`make_incident_blocks`) are exported separately so consumers can
compose their own messages.

## Install

```toml
# pyproject.toml (uv / pip)
dependencies = [
    "backlight-slack @ git+https://github.com/BACKLIGHT-AI/py-slack.git@v0.2.0",
]
```

Pin on a tag — the package uses semver and tags are authoritative.

## Quickstart

```python
from backlight_slack import (
    SlackConfig,
    notify_failure,
    post_incident_message,
    post_thread_reply,
    make_incident_blocks,
)

config = SlackConfig(
    enabled=True,
    service_name="shad-backend",
    bot_token="xoxb-...",
    success_channel="#shad-successes",
    failure_channel="#shad-fails",
)

# One-shot failure notification (no threading).
await notify_failure(config, title="NS API unavailable", error=exc)

# Incident + threaded resolution via the Web API.
blocks = make_incident_blocks(
    config.service_name,
    title="SAP connection lost",
    description="MSSQL over VPN is unreachable. Auto-retry in progress.",
    triggered_by="GET /v1/orders",
)
ts = await post_incident_message(
    config, text="SAP connection lost", blocks=blocks
)

# ...later, when the incident resolves:
await post_thread_reply(
    config,
    thread_ts=ts,
    text="SAP restored after 12s",
    blocks=[...],
)
```

## Public API

| Export | Kind | Purpose |
|--------|------|---------|
| `SlackConfig` | Pydantic model | Credentials + channel routing passed to every helper |
| `notify_success(config, title, details=None)` | async | Post to `success_channel` |
| `notify_failure(config, title, error, context=None)` | async | Post to `failure_channel` with traceback |
| `post_incident_message(config, text, blocks)` | async → `str \| None` | Post to `failure_channel`, returns message `ts` |
| `post_thread_reply(config, thread_ts, text, blocks)` | async | Reply on a prior `ts` in `failure_channel` |
| `make_success_blocks(service_name, title, details=None)` | sync | Block Kit builder |
| `make_failure_blocks(service_name, title, error, context=None)` | sync | Block Kit builder (includes traceback) |
| `make_incident_blocks(service_name, title, description, triggered_by=None)` | sync | Block Kit builder |

Every helper is no-op-safe: `config.enabled=False` or an empty
bot token / target channel returns early. Errors talking to Slack are
logged on the `backlight_slack.*` logger namespace and never raised.

## Bot setup

1. Create a Slack app in the Backlight workspace (or reuse the
   existing "Backlight" app).
2. Add the `chat:write` OAuth scope.
3. Install the app to the workspace — copy the bot token (`xoxb-...`).
4. Invite the bot to every channel you configure
   (`/invite @Backlight` in each channel).
5. Store the token per project (e.g. in GCP Secret Manager).

## Versioning

Semver. Tags on the `main` branch are the distribution channel —
consumers pin on a tag, e.g. `@v0.2.0`. Bump the version in
`pyproject.toml` **and** `src/backlight_slack/__init__.py:__version__`
before tagging a release.

### Breaking changes in v0.2.0

- `SlackConfig` no longer accepts `webhook_success`, `webhook_failure`
  or `channel`. Use `success_channel` and `failure_channel` instead
  and populate `bot_token`.
- `backlight_slack.webhook` is removed. `notify_success` and
  `notify_failure` are re-exported from `backlight_slack.api` with
  the same signatures — only the config field names change.

## License

MIT.
