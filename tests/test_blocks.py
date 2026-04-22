"""Unit tests for block-kit builders — pure functions, no I/O."""

from __future__ import annotations

import pytest

from backlight_slack import (
    make_failure_blocks,
    make_incident_blocks,
    make_success_blocks,
)


def _assert_mrkdwn_section(block: dict[str, object]) -> None:
    """Shared assertion for the common `type: section, text: mrkdwn` shape."""
    assert block["type"] == "section"
    text = block["text"]
    assert isinstance(text, dict)
    assert text["type"] == "mrkdwn"
    assert isinstance(text["text"], str) and text["text"]


def test_success_blocks_shape() -> None:
    blocks = make_success_blocks("svc", "Import completed", {"records": "24000"})
    assert len(blocks) == 3  # title, context, details
    _assert_mrkdwn_section(blocks[0])
    assert "Import completed" in blocks[0]["text"]["text"]  # type: ignore[index]
    assert blocks[1]["type"] == "context"
    _assert_mrkdwn_section(blocks[2])
    assert "records" in blocks[2]["text"]["text"]  # type: ignore[index]


def test_success_blocks_no_details() -> None:
    blocks = make_success_blocks("svc", "Done")
    assert len(blocks) == 2  # no details section


def test_failure_blocks_includes_traceback() -> None:
    try:
        raise ValueError("boom")
    except ValueError as exc:
        err = exc
    blocks = make_failure_blocks("svc", "NS API failed", err, {"uid": "abc"})
    assert len(blocks) == 5  # title, context, error+msg, traceback, context
    _assert_mrkdwn_section(blocks[0])
    _assert_mrkdwn_section(blocks[2])
    tb_block = blocks[3]
    _assert_mrkdwn_section(tb_block)
    assert "```" in tb_block["text"]["text"]  # type: ignore[index]
    assert "ValueError" in tb_block["text"]["text"]  # type: ignore[index]


def test_incident_blocks_with_triggered_by() -> None:
    blocks = make_incident_blocks(
        "svc",
        "SAP connection lost",
        "MSSQL over VPN is unreachable.",
        triggered_by="GET /v1/orders",
    )
    assert len(blocks) == 3  # title, context, description
    assert ":warning:" in blocks[0]["text"]["text"]  # type: ignore[index]
    desc = blocks[2]["text"]["text"]  # type: ignore[index]
    assert "MSSQL" in desc
    assert "GET /v1/orders" in desc


def test_incident_blocks_without_triggered_by() -> None:
    blocks = make_incident_blocks("svc", "Title", "Description only.")
    assert "Triggered by" not in blocks[2]["text"]["text"]  # type: ignore[index]


@pytest.mark.parametrize(
    "builder",
    [
        lambda: make_success_blocks("svc", "t"),
        lambda: make_failure_blocks("svc", "t", RuntimeError("x")),
        lambda: make_incident_blocks("svc", "t", "d"),
    ],
)
def test_service_name_in_context(builder: object) -> None:
    blocks = builder()  # type: ignore[operator]
    ctx = blocks[1]
    assert ctx["type"] == "context"
    text = ctx["elements"][0]["text"]
    assert "svc" in text
