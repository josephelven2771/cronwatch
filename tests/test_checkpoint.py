"""Tests for cronwatch.checkpoint."""

import json
from pathlib import Path

import pytest

from cronwatch.checkpoint import CheckpointStore, JobCheckpoint


@pytest.fixture()
def store(tmp_path: Path) -> CheckpointStore:
    return CheckpointStore.load(tmp_path / "checkpoints.json")


def test_get_or_create_returns_empty_checkpoint(store: CheckpointStore) -> None:
    cp = store.get_or_create("backup")
    assert cp.job_name == "backup"
    assert cp.total_runs == 0
    assert cp.consecutive_failures == 0


def test_record_success_increments_total_runs(store: CheckpointStore) -> None:
    cp = store.get_or_create("backup")
    cp.record_success()
    assert cp.total_runs == 1
    assert cp.last_success is not None
    assert cp.consecutive_failures == 0


def test_record_failure_increments_consecutive(store: CheckpointStore) -> None:
    cp = store.get_or_create("backup")
    cp.record_failure()
    cp.record_failure()
    assert cp.consecutive_failures == 2
    assert cp.total_runs == 2


def test_record_success_resets_consecutive_failures(store: CheckpointStore) -> None:
    cp = store.get_or_create("backup")
    cp.record_failure()
    cp.record_failure()
    cp.record_success()
    assert cp.consecutive_failures == 0
    assert cp.total_runs == 3


def test_save_and_reload_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "checkpoints.json"
    store = CheckpointStore.load(path)
    cp = store.get_or_create("nightly")
    cp.record_failure()
    store.save()

    reloaded = CheckpointStore.load(path)
    cp2 = reloaded.get("nightly")
    assert cp2 is not None
    assert cp2.consecutive_failures == 1
    assert cp2.total_runs == 1


def test_save_creates_file(tmp_path: Path) -> None:
    path = tmp_path / "sub" / "checkpoints.json"
    store = CheckpointStore.load(path)
    store.get_or_create("job")
    store.save()
    assert path.exists()


def test_to_dict_from_dict_round_trip() -> None:
    cp = JobCheckpoint(job_name="etl")
    cp.record_success()
    cp.record_failure()
    restored = JobCheckpoint.from_dict(cp.to_dict())
    assert restored.job_name == cp.job_name
    assert restored.consecutive_failures == cp.consecutive_failures
    assert restored.total_runs == cp.total_runs


def test_load_missing_file_returns_empty_store(tmp_path: Path) -> None:
    store = CheckpointStore.load(tmp_path / "missing.json")
    assert store.get("anything") is None
