"""Tests for cronwatch.alert_router."""

import pytest
from unittest.mock import MagicMock

from cronwatch.alert_router import RouteRule, AlertRouter, build_router
from cronwatch.config import AlertConfig


def _entry(failure_count: int = 1, tags=None):
    entry = MagicMock()
    entry.failure_count = failure_count
    entry.tags = tags or []
    return entry


@pytest.fixture()
def router():
    rules = [
        RouteRule(tags=["critical"], min_failures=1, channel="both", label="crit"),
        RouteRule(tags=["low-priority"], min_failures=3, channel="none", label="suppress"),
        RouteRule(tags=[], min_failures=5, channel="email", label="high-fail"),
    ]
    return AlertRouter(rules=rules, default_channel="webhook")


def test_route_matches_tag(router):
    entry = _entry(failure_count=1, tags=["critical"])
    assert router.route(entry) == "both"


def test_route_default_when_no_rule_matches(router):
    entry = _entry(failure_count=1, tags=["other"])
    assert router.route(entry) == "webhook"


def test_route_suppresses_low_priority_above_threshold(router):
    entry = _entry(failure_count=4, tags=["low-priority"])
    assert router.route(entry) == "none"


def test_route_does_not_suppress_below_threshold(router):
    entry = _entry(failure_count=2, tags=["low-priority"])
    # min_failures=3 not met, falls through to default
    assert router.route(entry) == "webhook"


def test_route_high_failure_no_tag(router):
    entry = _entry(failure_count=5, tags=[])
    assert router.route(entry) == "email"


def test_should_suppress_returns_true_for_none_channel(router):
    entry = _entry(failure_count=4, tags=["low-priority"])
    assert router.should_suppress(entry) is True


def test_should_suppress_returns_false_for_active_channel(router):
    entry = _entry(failure_count=1, tags=["critical"])
    assert router.should_suppress(entry) is False


def test_build_router_uses_webhook_when_url_present():
    cfg = AlertConfig(webhook_url="https://hooks.example.com", email_to=None)
    router = build_router(cfg, rules=[])
    assert router.default_channel == "webhook"


def test_build_router_falls_back_to_email_without_webhook():
    cfg = AlertConfig(webhook_url=None, email_to="ops@example.com")
    router = build_router(cfg, rules=[])
    assert router.default_channel == "email"


def test_build_router_parses_rule_dicts():
    cfg = AlertConfig(webhook_url="https://hooks.example.com", email_to=None)
    rules = [{"tags": ["db"], "min_failures": 2, "channel": "email", "label": "db-alert"}]
    router = build_router(cfg, rules=rules)
    assert len(router.rules) == 1
    assert router.rules[0].channel == "email"
    assert router.rules[0].min_failures == 2


def test_route_first_matching_rule_wins():
    """When an entry matches multiple rules, the first rule in order takes precedence."""
    rules = [
        RouteRule(tags=["critical"], min_failures=1, channel="both", label="crit"),
        RouteRule(tags=["critical"], min_failures=1, channel="email", label="crit-email"),
    ]
    router = AlertRouter(rules=rules, default_channel="webhook")
    entry = _entry(failure_count=1, tags=["critical"])
    assert router.route(entry) == "both"
