# backlight-slack

Slack notification helpers shared across Backlight customer backends
(SHAD, BagelBoys, HIRSadvies, Mave-Global).

Wraps both flavours of the Slack SDK:

- **Incoming webhooks** — fire-and-forget success/failure
  notifications (`notify_success`, `notify_failure`).
- **Web API (`chat.postMessage`)** — returns a message `ts` so the
  caller can post thread replies (`post_incident_message` +
  `post_thread_reply`). Needed for "incident + resolution in one
  Slack thread" flows.

Block Kit builders (`make_success_blocks`, `make_failure_blocks`,
`make_incident_blocks`) are exported separately so consumers can mix
and match with their own renderers.

## Install

```toml
# pyproject.toml (uv / pip)
dependencies = [
    "backlight-slack @ git+https://github.com/BACKLIGHT-AI/py-slack.git@v0.1.0",
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
    webhook_failure="https://hooks.slack.com/services/...",
    bot_token="xoxb-...",
    channel="#shad-fails",
)

# Webhook failure notification (no threading).
await notify_failure(config, title="NS API unavailable", error=exc)

# Incident + threaded resolution via Web API.
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
| `notify_success(config, title, details=None)` | async | Post to `webhook_success` |
| `notify_failure(config, title, error, context=None)` | async | Post to `webhook_failure` with traceback |
| `post_incident_message(config, text, blocks)` | async → `str \| None` | Post via Web API, returns message `ts` |
| `post_thread_reply(config, thread_ts, text, blocks)` | async | Post thread reply on a prior `ts` |
| `make_success_blocks(service_name, title, details=None)` | sync | Block Kit builder |
| `make_failure_blocks(service_name, title, error, context=None)` | sync | Block Kit builder |
| `make_incident_blocks(service_name, title, description, triggered_by=None)` | sync | Block Kit builder |

Every helper is no-op-safe: passing `config.enabled=False` or empty
webhook/token/channel returns early. Errors talking to Slack are
logged on the `backlight_slack.*` logger namespace and never raised.

## Versioning

Semver. Tags on the `main` branch are the distribution channel —
consumers pin on a tag, e.g. `@v0.1.0`. Bump the version in
`pyproject.toml` **and** `src/backlight_slack/__init__.py:__version__`
before tagging a release.

## License

MIT.
