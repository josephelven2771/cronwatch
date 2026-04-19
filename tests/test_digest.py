"""Tests for cronwatch.digest."""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import JobConfig, AlertConfig, CronwatchConfig
from cronwatch.digest import build_digest, Digest, DigestEntry
from cronwatch.history import HistoryStore
from cronwatch.reporter import Reporter, JobStatus


@pytest.fixture()
def job_config():
    return JobConfig(name="backup", schedule="0 2 * * *", grace_minutes=30)


@pytest.fixture()
def config(job_config):
    alert = AlertConfig(webhook_url="http://example.com/hook")
    return CronwatchConfig(jobs=[job_config], alerts=alert)


@pytest.fixture()
def store(tmp_path):
    return HistoryStore(path=str(tmp_path / "history.json"))


@pytest.fixture()
def reporter(config, store):
    return Reporter(config=config, store=store)


def test_build_digest_returns_digest(config, reporter):
    digest = build_digest(config, reporter)
    assert isinstance(digest, Digest)
    assert len(digest.entries) == 1


def test_build_digest_entry_fields(config, reporter):
    digest = build_digest(config, reporter)
    entry = digest.entries[0]
    assert entry.job_name == "backup"
    assert entry.status in {"healthy", "missed", "failed"}
    assert isinstance(entry.summary, str)


def test_digest_counts_no_problems_when_healthy(config, reporter):
    with patch.object(reporter, "status", return_value=JobStatus.HEALTHY):
        digest = build_digest(config, reporter)
    assert digest.healthy_count == 1
    assert digest.problem_count == 0


def test_digest_counts_problem_when_missed(config, reporter):
    with patch.object(reporter, "status", return_value=JobStatus.MISSED):
        digest = build_digest(config, reporter)
    assert digest.problem_count == 1
    assert digest.healthy_count == 0


def test_digest_to_dict_structure(config, reporter):
    digest = build_digest(config, reporter)
    d = digest.to_dict()
    assert "generated_at" in d
    assert "healthy" in d
    assert "problems" in d
    assert isinstance(d["jobs"], list)
    assert d["jobs"][0]["job"] == "backup"


def test_digest_last_run_none_when_no_history(config, reporter):
    digest = build_digest(config, reporter)
    assert digest.entries[0].last_run is None
