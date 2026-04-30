"""Tests for cronwatch.alert_budget."""
from datetime import datetime, timedelta, timezone

import pytest

from cronwatch.alert_budget import AlertBudget, BudgetPolicy, BudgetResult


def _utc(offset_seconds: float = 0) -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(
        seconds=offset_seconds
    )


@pytest.fixture()
def policy() -> BudgetPolicy:
    return BudgetPolicy(max_alerts=3, window_seconds=60)


@pytest.fixture()
def budget(policy: BudgetPolicy) -> AlertBudget:
    return AlertBudget(policy)


# --- BudgetPolicy validation ---

def test_policy_rejects_zero_max():
    with pytest.raises(ValueError, match="max_alerts"):
        BudgetPolicy(max_alerts=0, window_seconds=60)


def test_policy_rejects_zero_window():
    with pytest.raises(ValueError, match="window_seconds"):
        BudgetPolicy(max_alerts=3, window_seconds=0)


# --- BudgetResult bool ---

def test_budget_result_bool_true():
    r = BudgetResult(allowed=True, used=1, remaining=2, limit=3)
    assert bool(r) is True


def test_budget_result_bool_false():
    r = BudgetResult(allowed=False, used=3, remaining=0, limit=3)
    assert bool(r) is False


# --- check (non-mutating) ---

def test_check_initially_allowed(budget: AlertBudget):
    result = budget.check(now=_utc())
    assert result.allowed is True
    assert result.used == 0
    assert result.remaining == 3
    assert result.limit == 3


def test_check_does_not_record(budget: AlertBudget):
    budget.check(now=_utc())
    result = budget.check(now=_utc())
    assert result.used == 0


# --- record ---

def test_record_decrements_remaining(budget: AlertBudget):
    r = budget.record(now=_utc())
    assert r.used == 1
    assert r.remaining == 2


def test_record_up_to_limit(budget: AlertBudget):
    budget.record(now=_utc(0))
    budget.record(now=_utc(1))
    r = budget.record(now=_utc(2))
    assert r.used == 3
    assert r.remaining == 0
    assert r.allowed is True  # the 3rd was still allowed


def test_record_over_limit_denied(budget: AlertBudget):
    budget.record(now=_utc(0))
    budget.record(now=_utc(1))
    budget.record(now=_utc(2))
    r = budget.record(now=_utc(3))  # 4th — should be denied
    assert r.allowed is False
    assert r.used == 3  # not incremented


# --- rolling window expiry ---

def test_old_entries_expire_from_window(budget: AlertBudget):
    # Record 3 alerts at t=0
    for i in range(3):
        budget.record(now=_utc(i))
    # At t=0 all 3 are used
    assert budget.check(now=_utc(3)).used == 3
    # At t=61 all have expired (window=60s)
    result = budget.check(now=_utc(61))
    assert result.used == 0
    assert result.allowed is True


def test_partial_expiry_allows_new_alert(budget: AlertBudget):
    budget.record(now=_utc(0))
    budget.record(now=_utc(1))
    budget.record(now=_utc(2))
    # At t=62 first two have expired, one remains
    result = budget.check(now=_utc(62))
    assert result.used == 1
    assert result.remaining == 2


# --- reset ---

def test_reset_clears_all(budget: AlertBudget):
    budget.record(now=_utc(0))
    budget.record(now=_utc(1))
    budget.reset()
    result = budget.check(now=_utc(2))
    assert result.used == 0
