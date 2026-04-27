"""Tests for cronwatch.alert_chain_builder."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alert_chain import AlertChain
from cronwatch.alert_chain_builder import build_chain, _dispatch_handler
from cronwatch.config import AlertConfig
from cronwatch.history import HistoryEntry


@pytest.fixture()
def entry() -> HistoryEntry:
    return HistoryEntry(
        job_name="nightly",
        started_at=None,
        finished_at=None,
        exit_code=0,
        succeeded=True,
        duration_seconds=5.0,
        tags=[],
    )


@pytest.fixture()
def minimal_config() -> AlertConfig:
    return AlertConfig(webhook_url=None, email=None)


@pytest.fixture()
def full_config() -> AlertConfig:
    return AlertConfig(webhook_url="https://hooks.example.com/x", email="ops@example.com")


def test_build_chain_returns_alert_chain(minimal_config):
    chain = build_chain(minimal_config)
    assert isinstance(chain, AlertChain)


def test_build_chain_minimal_has_dispatch_handler(minimal_config):
    chain = build_chain(minimal_config)
    assert len(chain.handlers) >= 1


def test_build_chain_full_config_adds_webhook_and_email(full_config):
    chain = build_chain(full_config)
    # webhook + email + dispatch = 3 handlers
    assert len(chain.handlers) == 3


def test_build_chain_extra_handler_appended(minimal_config):
    extra = MagicMock(return_value=True)
    chain = build_chain(minimal_config, extra_handler=extra)
    assert chain.handlers[-1] is extra


def test_dispatch_handler_calls_dispatch_alert(entry):
    alert_config = AlertConfig(webhook_url=None, email=None)
    with patch("cronwatch.alert_chain_builder.dispatch_alert") as mock_dispatch:
        handler = _dispatch_handler(alert_config)
        result = handler(entry)
    mock_dispatch.assert_called_once_with(alert_config, entry)
    assert result is True


def test_chain_runs_successfully_with_dispatch_only(minimal_config, entry):
    with patch("cronwatch.alert_chain_builder.dispatch_alert"):
        chain = build_chain(minimal_config)
        result = chain.run(entry)
    assert result.succeeded
