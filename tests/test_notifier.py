"""Tests for cronwatch.notifier."""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import AlertConfig
from cronwatch.notifier import Notifier


@pytest.fixture
def alert_config():
    return AlertConfig(webhook_url="https://hooks.example.com/test")


@pytest.fixture
def notifier(alert_config):
    return Notifier(alert_config, cooldown_seconds=60)


@patch("cronwatch.notifier.dispatch_alert")
def test_notify_sends_on_first_call(mock_dispatch, notifier):
    sent = notifier.notify("backup", "subject", "body")
    assert sent is True
    mock_dispatch.assert_called_once()


@patch("cronwatch.notifier.dispatch_alert")
def test_notify_respects_cooldown(mock_dispatch, notifier):
    notifier.notify("backup", "subject", "body")
    sent = notifier.notify("backup", "subject", "body")
    assert sent is False
    assert mock_dispatch.call_count == 1


@patch("cronwatch.notifier.dispatch_alert")
def test_notify_after_cooldown_elapsed(mock_dispatch, alert_config):
    notifier = Notifier(alert_config, cooldown_seconds=0)
    notifier.notify("backup", "s", "b")
    sent = notifier.notify("backup", "s", "b")
    assert sent is True
    assert mock_dispatch.call_count == 2


@patch("cronwatch.notifier.dispatch_alert")
def test_max_repeats_limits_alerts(mock_dispatch, alert_config):
    notifier = Notifier(alert_config, cooldown_seconds=0, max_repeats=2)
    notifier.notify("job", "s", "b")
    notifier.notify("job", "s", "b")
    sent = notifier.notify("job", "s", "b")
    assert sent is False
    assert mock_dispatch.call_count == 2


@patch("cronwatch.notifier.dispatch_alert")
def test_reset_clears_state(mock_dispatch, alert_config):
    notifier = Notifier(alert_config, cooldown_seconds=3600, max_repeats=1)
    notifier.notify("job", "s", "b")
    notifier.reset("job")
    sent = notifier.notify("job", "s", "b")
    assert sent is True
    assert mock_dispatch.call_count == 2


def test_should_notify_true_for_new_job(notifier):
    assert notifier.should_notify("new-job") is True


def test_reset_unknown_job_does_not_raise(notifier):
    notifier.reset("nonexistent")
