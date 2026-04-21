"""Tests for cronwatch.window_alert."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Tuple

import pytest

from cronwatch.window_alert import (
    WindowAlertConfig,
    WindowAlertPipeline,
    alert_on_violations,
    _build_body,
)
from cronwatch.window_checker import WindowResult


def _utc(h: int, m: int = 0) -> datetime:
    return datetime(2024, 6, 1, h, m, 0, tzinfo=timezone.utc)


def _violation(name="backup", last_run=None) -> WindowResult:
    return WindowResult(
        job_name=name,
        expected_start=_utc(2),
        expected_end=_utc(4),
        last_run=last_run or _utc(1),
        in_window=False,
        message=f"{name}: outside window",
    )


def _collect() -> Tuple[List[Tuple[str, str]], callable]:
    calls: List[Tuple[str, str]] = []

    def fn(subject: str, body: str) -> None:
        calls.append((subject, body))

    return calls, fn


def test_alert_on_violations_sends_one_per_violation():
    calls, fn = _collect()
    sent = alert_on_violations([_violation("a"), _violation("b")], fn)
    assert sent == 2
    assert len(calls) == 2


def test_alert_on_empty_violations_sends_nothing():
    calls, fn = _collect()
    sent = alert_on_violations([], fn)
    assert sent == 0
    assert calls == []


def test_subject_contains_job_name():
    calls, fn = _collect()
    alert_on_violations([_violation("nightly-backup")], fn)
    subject, _ = calls[0]
    assert "nightly-backup" in subject


def test_subject_uses_prefix():
    calls, fn = _collect()
    cfg = WindowAlertConfig(subject_prefix="[ALERT]")
    alert_on_violations([_violation()], fn, cfg)
    subject, _ = calls[0]
    assert subject.startswith("[ALERT]")


def test_body_includes_expected_window_by_default():
    result = _violation()
    cfg = WindowAlertConfig()
    body = _build_body(result, cfg)
    assert "02:00" in body
    assert "04:00" in body


def test_body_includes_last_run_by_default():
    result = _violation(last_run=_utc(1, 15))
    cfg = WindowAlertConfig()
    body = _build_body(result, cfg)
    assert "01:15" in body


def test_body_no_history_shows_never():
    result = WindowResult(
        job_name="x",
        expected_start=_utc(2),
        expected_end=_utc(4),
        last_run=None,
        in_window=False,
        message="x: no history",
    )
    body = _build_body(result, WindowAlertConfig())
    assert "never" in body


def test_pipeline_run_returns_sent_count():
    calls, fn = _collect()
    pipeline = WindowAlertPipeline(alert_fn=fn)
    count = pipeline.run([_violation(), _violation()])
    assert count == 2
    assert pipeline.sent == 2
