"""Tests for cronwatch.checkpoint_manager."""

from pathlib import Path

import pytest

from cronwatch.checkpoint import CheckpointStore
from cronwatch.checkpoint_manager import CheckpointManager


@pytest.fixture()
def manager(tmp_path: Path) -> CheckpointManager:
    store = CheckpointStore.load(tmp_path / "checkpoints.json")
    return CheckpointManager(store)


def test_record_success_returns_checkpoint(manager: CheckpointManager) -> None:
    cp = manager.record_success("backup")
    assert cp.job_name == "backup"
    assert cp.total_runs == 1
    assert cp.consecutive_failures == 0


def test_record_failure_returns_checkpoint(manager: CheckpointManager) -> None:
    cp = manager.record_failure("backup")
    assert cp.consecutive_failures == 1


def test_consecutive_failures_unknown_job_returns_zero(manager: CheckpointManager) -> None:
    assert manager.consecutive_failures("unknown") == 0


def test_consecutive_failures_after_two_failures(manager: CheckpointManager) -> None:
    manager.record_failure("etl")
    manager.record_failure("etl")
    assert manager.consecutive_failures("etl") == 2


def test_consecutive_failures_reset_after_success(manager: CheckpointManager) -> None:
    manager.record_failure("etl")
    manager.record_success("etl")
    assert manager.consecutive_failures("etl") == 0


def test_all_checkpoints_lists_every_job(manager: CheckpointManager) -> None:
    manager.record_success("job_a")
    manager.record_failure("job_b")
    names = {cp.job_name for cp in manager.all_checkpoints()}
    assert names == {"job_a", "job_b"}


def test_jobs_with_consecutive_failures_filters_correctly(manager: CheckpointManager) -> None:
    manager.record_failure("bad")
    manager.record_failure("bad")
    manager.record_success("good")
    results = manager.jobs_with_consecutive_failures(min_failures=2)
    assert len(results) == 1
    assert results[0].job_name == "bad"


def test_from_path_loads_existing_data(tmp_path: Path) -> None:
    path = tmp_path / "checkpoints.json"
    mgr1 = CheckpointManager.from_path(path)
    mgr1.record_failure("nightly")

    mgr2 = CheckpointManager.from_path(path)
    assert mgr2.consecutive_failures("nightly") == 1
