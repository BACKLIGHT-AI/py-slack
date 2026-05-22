# backlight-slack

Slack notification helpers shared across Backlight customer backends
(SHAD, BagelBoys, HIRSadvies, Mave-Global).

Two transports are supported:

- **Bot-token transport** (original): posts via `chat.postMessage` using a
  per-project `xoxb-...` bot token.  Good for threading and rich formatting.
- **Jason broker transport** (v0.3.0+): posts through the central Jason Slack
  broker service (`POST /v1/slack/post`).  Each backend authenticates with a
  Google OIDC identity token minted for its Cloud Run service account — no raw
  bot token required in the consumer's Secret Manager.

Block Kit builders (`make_success_blocks`, `make_failure_blocks`,
`make_incident_blocks`) are exported separately so consumers can compose their
own messages regardless of which transport they use.

## Install

```toml
# pyproject.toml (uv / pip)
dependencies = [
    "backlight-slack @ git+https://github.com/BACKLIGHT-AI/py-slack.git@v0.3.0",
]
```

Pin on a tag -- the package uses semver and tags are authoritative.

## Quickstart — bot-token transport

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

## Quickstart — Jason broker transport

The broker transport requires no Slack bot token in the consumer's config.
Instead the consumer's Cloud Run service account is allowlisted in the broker.

```python
from backlight_slack import BrokerConfig, SlackConfig, post_via_broker, make_incident_blocks

config = SlackConfig(
    enabled=True,
    service_name="shad-backend",
    broker=BrokerConfig(
        project="shad",                  # short project key for audit logs
        # url defaults to the production broker; override for testing
    ),
)

# Simple post.
ts = await post_via_broker(config, channel="#shad-fails", text="SAP connection lost")

# Post with Block Kit blocks.
blocks = make_incident_blocks(
    config.service_name,
    title="SAP connection lost",
    description="MSSQL over VPN is unreachable.",
    triggered_by="GET /v1/orders",
)
ts = await post_via_broker(
    config,
    channel="#shad-fails",
    text="SAP connection lost",   # plain-text fallback required by Slack
    blocks=blocks,
)

# Thread reply.
await post_via_broker(
    config,
    channel="#shad-fails",
    text="SAP restored",
    thread_ts=ts,
)
```

### Local dev note

On a local workstation where ADC is a human user account, `fetch_id_token`
raises (human accounts cannot mint Cloud Run identity tokens).  `post_via_broker`
degrades gracefully in that case: it returns `None` and logs a `DEBUG` message.
No exception is raised.  Set `config.enabled = False` to skip the attempt
entirely in local development.

## Public API

### Configuration

| Class | Purpose |
|-------|---------|
| `SlackConfig` | Pydantic model -- credentials + channel routing for the bot-token transport, plus an optional `broker` field |
| `BrokerConfig` | Pydantic model -- broker URL (`url`), project key (`project`), optional caller string (`caller`) |

### Bot-token transport helpers

| Export | Kind | Purpose |
|--------|------|---------|
| `notify_success(config, title, details=None)` | async | Post to `success_channel` |
| `notify_failure(config, title, error, context=None)` | async | Post to `failure_channel` with traceback |
| `post_incident_message(config, text, blocks)` | async -> `str \| None` | Post to `failure_channel`, returns message `ts` |
| `post_thread_reply(config, thread_ts, text, blocks)` | async | Reply on a prior `ts` in `failure_channel` |

### Broker transport helpers

| Export | Kind | Purpose |
|--------|------|---------|
| `post_via_broker(config, channel, text, blocks=None, thread_ts=None)` | async -> `str \| None` | Post via Jason broker; requires `config.broker` to be set |

### Block Kit builders (transport-agnostic)

| Export | Kind | Purpose |
|--------|------|---------|
| `make_success_blocks(service_name, title, details=None)` | sync | Block Kit builder |
| `make_failure_blocks(service_name, title, error, context=None)` | sync | Block Kit builder (includes traceback) |
| `make_incident_blocks(service_name, title, description, triggered_by=None)` | sync | Block Kit builder |

Every helper is no-op-safe: `config.enabled=False`, a missing broker config,
or an empty bot token / target channel returns early.  Errors talking to Slack
or the broker are logged on the `backlight_slack.*` logger namespace and never
raised.

## Bot setup (bot-token transport)

1. Create a Slack app in your workspace (or reuse an existing one --
   Backlight uses "Jason").
2. Add the `chat:write` OAuth scope.
3. Install the app to the workspace -- copy the bot token (`xoxb-...`).
4. Invite the bot to every channel you configure
   (`/invite @<bot-name>` in each channel).
5. Store the token per project (e.g. in GCP Secret Manager).

## Broker setup (broker transport)

1. The broker service is already running at
   `https://jason-slack-broker-akk67ufdqa-ew.a.run.app`.
2. Your Cloud Run service account must be allowlisted in the broker's IAM
   config (contact the Backlight platform team).
3. Set `BrokerConfig(project="<your-project-key>")` in your `SlackConfig`.
4. No Slack token is needed in your consumer's environment.

## Versioning

Semver. Tags on the `main` branch are the distribution channel --
consumers pin on a tag, e.g. `@v0.3.0`. Bump the version in
`pyproject.toml` **and** `src/backlight_slack/__init__.py:__version__`
before tagging a release.

### Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT.
