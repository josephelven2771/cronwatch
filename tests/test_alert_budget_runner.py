"""Tests for cronwatch.alert_budget_runner."""
from datetime import datetime, timezone
from typing import List

import pytest

from cronwatch.alert_budget import BudgetPolicy
from cronwatch.alert_budget_runner import AlertBudgetRunner, BudgetRunResult
from cronwatch.history import HistoryEntry


def _utc() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(job_name: str = "backup", success: bool = True) -> HistoryEntry:
    return HistoryEntry(
        job_name=job_name,
        started_at=_utc(),
        finished_at=_utc(),
        exit_code=0 if success else 1,
        succeeded=success,
        duration_seconds=10.0,
    )


def _collect(sent: List[HistoryEntry]) -> callable:
    def _send(entry: HistoryEntry) -> None:
        sent.append(entry)
    return _send


@pytest.fixture()
def policy() -> BudgetPolicy:
    return BudgetPolicy(max_alerts=2, window_seconds=60)


# --- BudgetRunResult ---

def test_budget_run_result_bool_true():
    e = _entry()
    from cronwatch.alert_budget import BudgetResult
    br = BudgetResult(allowed=True, used=1, remaining=1, limit=2)
    r = BudgetRunResult(job_name="backup", entry=e, budget_result=br, dispatched=True)
    assert bool(r) is True


def test_budget_run_result_bool_false():
    e = _entry()
    from cronwatch.alert_budget import BudgetResult
    br = BudgetResult(allowed=False, used=2, remaining=0, limit=2)
    r = BudgetRunResult(job_name="backup", entry=e, budget_result=br, dispatched=False)
    assert bool(r) is False


# --- AlertBudgetRunner.run ---

def test_run_returns_self(policy: BudgetPolicy):
    sent: List[HistoryEntry] = []
    runner = AlertBudgetRunner(policy, _collect(sent))
    result = runner.run([])
    assert result is runner


def test_run_dispatches_within_budget(policy: BudgetPolicy):
    sent: List[HistoryEntry] = []
    runner = AlertBudgetRunner(policy, _collect(sent))
    entries = [_entry("backup"), _entry("backup")]
    runner.run(entries)
    assert len(sent) == 2
    assert runner.sent_count == 2
    assert runner.suppressed_count == 0


def test_run_suppresses_over_budget(policy: BudgetPolicy):
    sent: List[HistoryEntry] = []
    runner = AlertBudgetRunner(policy, _collect(sent))
    entries = [_entry("backup")] * 3  # limit is 2
    runner.run(entries)
    assert len(sent) == 2
    assert runner.sent_count == 2
    assert runner.suppressed_count == 1


def test_per_job_budgets_are_independent(policy: BudgetPolicy):
    sent: List[HistoryEntry] = []
    runner = AlertBudgetRunner(policy, _collect(sent))
    # 2 alerts for 'backup' and 2 for 'sync' — each within their own budget
    entries = [
        _entry("backup"), _entry("backup"),
        _entry("sync"), _entry("sync"),
    ]
    runner.run(entries)
    assert runner.sent_count == 4


def test_global_budget_caps_across_jobs():
    global_policy = BudgetPolicy(max_alerts=3, window_seconds=60)
    per_job_policy = BudgetPolicy(max_alerts=10, window_seconds=60)
    sent: List[HistoryEntry] = []
    runner = AlertBudgetRunner(per_job_policy, _collect(sent), global_policy=global_policy)
    entries = [_entry("a"), _entry("b"), _entry("c"), _entry("d")]
    runner.run(entries)
    assert runner.sent_count == 3
    assert runner.suppressed_count == 1


def test_results_length_matches_entries(policy: BudgetPolicy):
    sent: List[HistoryEntry] = []
    runner = AlertBudgetRunner(policy, _collect(sent))
    entries = [_entry("backup")] * 5
    runner.run(entries)
    assert len(runner.results) == 5


def test_results_job_name_preserved(policy: BudgetPolicy):
    sent: List[HistoryEntry] = []
    runner = AlertBudgetRunner(policy, _collect(sent))
    runner.run([_entry("my_job")])
    assert runner.results[0].job_name == "my_job"
