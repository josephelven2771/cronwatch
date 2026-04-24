"""Tests for cronwatch.alert_replay."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.audit_log import AuditLog
from cronwatch.alert_replay import AlertReplayer, ReplayResult, replay_alerts


def _utc(offset_seconds: int = 0) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)


@pytest.fixture()
def log(tmp_path: Path) -> AuditLog:
    return AuditLog(tmp_path / "audit.jsonl")


@pytest.fixture()
def replayer(log: AuditLog):
    sent: list = []

    def _send(entry):
        sent.append(entry)
        return True

    replayer = AlertReplayer(log, _send)
    replayer._sent = sent
    return replayer


# ---------------------------------------------------------------------------
# ReplayResult helpers
# ---------------------------------------------------------------------------

def test_replay_result_count_and_bool():
    r = ReplayResult()
    assert r.count == 0
    assert not bool(r)


def test_replay_result_bool_true_when_replayed(log):
    log.append(job="backup", action="alert_suppressed", detail="cooldown")
    sent = []
    r = replay_alerts(log, lambda e: sent.append(e) or True)
    assert bool(r)
    assert r.count == 1


# ---------------------------------------------------------------------------
# Filtering by action
# ---------------------------------------------------------------------------

def test_non_suppressed_entries_are_skipped(log):
    log.append(job="backup", action="alert_sent", detail="ok")
    log.append(job="backup", action="silence_applied", detail="ok")
    sent = []
    r = replay_alerts(log, lambda e: sent.append(e) or True)
    assert r.count == 0
    assert r.skipped == 2


def test_alert_failed_entries_are_replayed(log):
    log.append(job="sync", action="alert_failed", detail="timeout")
    sent = []
    r = replay_alerts(log, lambda e: sent.append(e) or True)
    assert r.count == 1


# ---------------------------------------------------------------------------
# Time-window filtering
# ---------------------------------------------------------------------------

def test_since_filter_excludes_old_entries(log):
    log.append(job="job1", action="alert_suppressed", detail="x")
    future = _utc(offset_seconds=3600)
    sent = []
    r = replay_alerts(log, lambda e: sent.append(e) or True, since=future)
    assert r.count == 0


def test_until_filter_excludes_future_entries(log):
    log.append(job="job1", action="alert_suppressed", detail="x")
    past = _utc(offset_seconds=-3600)
    sent = []
    r = replay_alerts(log, lambda e: sent.append(e) or True, until=past)
    assert r.count == 0


# ---------------------------------------------------------------------------
# job_name filtering
# ---------------------------------------------------------------------------

def test_job_name_filter(log):
    log.append(job="alpha", action="alert_suppressed", detail="x")
    log.append(job="beta", action="alert_suppressed", detail="x")
    sent = []
    r = replay_alerts(log, lambda e: sent.append(e) or True, job_name="alpha")
    assert r.count == 1
    assert r.replayed[0].job == "alpha"


# ---------------------------------------------------------------------------
# dry_run
# ---------------------------------------------------------------------------

def test_dry_run_does_not_call_send_fn(log):
    log.append(job="job1", action="alert_suppressed", detail="x")
    called = []
    r = replay_alerts(log, lambda e: called.append(e) or True, dry_run=True)
    assert r.count == 1
    assert called == []


# ---------------------------------------------------------------------------
# AlertReplayer wrapper
# ---------------------------------------------------------------------------

def test_replayer_run_delegates_correctly(replayer, log):
    log.append(job="cron", action="alert_suppressed", detail="rate_limit")
    r = replayer.run()
    assert r.count == 1
    assert len(replayer._sent) == 1
