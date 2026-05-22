# Changelog

All notable changes to `backlight-slack` are documented here.
Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) conventions.
Package uses [Semantic Versioning](https://semver.org/).

---

## [0.3.0] - 2026-05-22

### Added

- **Jason broker transport** (`backlight_slack.broker`) -- posts Slack
  messages through the central Jason broker service instead of calling
  Slack directly with a bot token.  The broker holds the @Jason bot token;
  every caller authenticates with a Google OIDC identity token minted for
  its Cloud Run service account.
- **`BrokerConfig`** Pydantic model (new export from the package root) --
  carries the broker URL (defaults to the production instance), project key,
  and optional caller string.
- **`SlackConfig.broker`** optional field -- when set, the new
  `post_via_broker` helper routes through the broker.  The existing
  bot-token fields are unaffected.
- **`post_via_broker(config, channel, text, blocks=None, thread_ts=None)`**
  top-level async helper (exported from the package root) -- accepts a
  `SlackConfig` with a populated `broker` field and posts via the Jason
  broker.  Fail-soft: any error (OIDC mint failure, network error, broker
  4xx/5xx) is logged and returns `None`; no exception is raised.
- New dependencies: `google-auth>=2.28` (OIDC token minting),
  `httpx>=0.27` (async HTTP client for broker requests).
- Unit tests for the broker transport (`tests/test_broker.py`) covering
  success, OIDC mint failure (local dev), network error, broker HTTP errors,
  and `ok=false` responses.

### Changed

- Version bumped to `0.3.0` in `pyproject.toml` and `__init__.py`.

### Notes

- All existing bot-token helpers (`notify_success`, `notify_failure`,
  `post_incident_message`, `post_thread_reply`) are unchanged and
  fully backward compatible.
- On a local workstation with ADC pointing at a human user account,
  `fetch_id_token` raises because human accounts cannot mint Cloud Run
  identity tokens.  `post_via_broker` catches this and returns `None` with
  a `DEBUG` log -- no action required from the caller.

---

## [0.2.1] - earlier

Pin `aiohttp` dependency explicitly (required by `AsyncWebClient` at call
time; `slack_sdk` declares it as optional so we enforce it).

## [0.2.0] - earlier

**Breaking**: drop webhook support.  `SlackConfig` now uses `bot_token`,
`success_channel`, and `failure_channel` instead of the old webhook fields.
`backlight_slack.webhook` module removed.

## [0.1.1] - earlier

Add `py.typed` marker so consumers get static types.

## [0.1.0] - earlier

Initial release.
