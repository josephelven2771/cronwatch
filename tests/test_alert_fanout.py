"""Tests for cronwatch.alert_fanout."""
from __future__ import annotations

from typing import Any, Dict, List

import pytest

from cronwatch.alert_fanout import AlertFanout, FanoutReport, FanoutResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_send(return_value: bool = True) -> tuple:
    """Return (send_fn, calls_list) so tests can inspect invocations."""
    calls: List[Dict[str, Any]] = []

    def _send(payload: Dict[str, Any]) -> bool:
        calls.append(payload)
        return return_value

    return _send, calls


def _make_raising_send(exc: Exception):
    def _send(payload):
        raise exc
    return _send


# ---------------------------------------------------------------------------
# FanoutResult
# ---------------------------------------------------------------------------

def test_fanout_result_bool_true():
    r = FanoutResult(destination="slack", success=True)
    assert bool(r) is True


def test_fanout_result_bool_false():
    r = FanoutResult(destination="slack", success=False)
    assert bool(r) is False


# ---------------------------------------------------------------------------
# FanoutReport
# ---------------------------------------------------------------------------

def test_fanout_report_counts():
    report = FanoutReport(results=[
        FanoutResult("a", True),
        FanoutResult("b", False),
        FanoutResult("c", True),
    ])
    assert report.total == 3
    assert report.sent_count == 2
    assert report.failed_count == 1
    assert report.all_succeeded is False
    assert bool(report) is False


def test_fanout_report_all_succeeded():
    report = FanoutReport(results=[FanoutResult("a", True), FanoutResult("b", True)])
    assert report.all_succeeded is True
    assert bool(report) is True


def test_fanout_report_empty_not_all_succeeded():
    report = FanoutReport()
    assert report.all_succeeded is False


# ---------------------------------------------------------------------------
# AlertFanout.dispatch
# ---------------------------------------------------------------------------

def test_dispatch_calls_all_destinations():
    send_a, calls_a = _make_send(True)
    send_b, calls_b = _make_send(True)
    fanout = AlertFanout({"a": send_a, "b": send_b})
    payload = {"job": "backup"}

    report = fanout.dispatch(payload)

    assert len(calls_a) == 1
    assert len(calls_b) == 1
    assert calls_a[0] == payload
    assert report.sent_count == 2


def test_dispatch_records_failure():
    send_ok, _ = _make_send(True)
    send_fail, _ = _make_send(False)
    fanout = AlertFanout({"ok": send_ok, "fail": send_fail})

    report = fanout.dispatch({})

    assert report.sent_count == 1
    assert report.failed_count == 1


def test_dispatch_captures_exception_as_failure():
    send_raise = _make_raising_send(RuntimeError("timeout"))
    fanout = AlertFanout({"broken": send_raise})

    report = fanout.dispatch({})

    assert report.failed_count == 1
    assert report.results[0].error == "timeout"


def test_stop_on_first_failure_halts_early():
    send_fail, _ = _make_send(False)
    send_ok, calls_ok = _make_send(True)
    fanout = AlertFanout({"fail": send_fail, "ok": send_ok}, stop_on_first_failure=True)

    report = fanout.dispatch({})

    assert report.total == 1          # second destination never reached
    assert len(calls_ok) == 0


def test_no_stop_on_failure_by_default():
    send_fail, _ = _make_send(False)
    send_ok, calls_ok = _make_send(True)
    fanout = AlertFanout({"fail": send_fail, "ok": send_ok})

    report = fanout.dispatch({})

    assert report.total == 2
    assert len(calls_ok) == 1
