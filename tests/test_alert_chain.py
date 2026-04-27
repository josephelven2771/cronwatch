"""Tests for cronwatch.alert_chain."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cronwatch.alert_chain import AlertChain, ChainResult
from cronwatch.history import HistoryEntry


@pytest.fixture()
def entry() -> HistoryEntry:
    return HistoryEntry(
        job_name="backup",
        started_at=None,
        finished_at=None,
        exit_code=1,
        succeeded=False,
        duration_seconds=10.0,
        tags=[],
    )


def _handler(returns: bool):
    m = MagicMock(return_value=returns)
    return m


def test_run_returns_chain_result(entry):
    chain = AlertChain()
    chain.add(_handler(True))
    result = chain.run(entry)
    assert isinstance(result, ChainResult)


def test_first_success_stops_chain(entry):
    h1 = _handler(True)
    h2 = _handler(True)
    chain = AlertChain()
    chain.add(h1)
    chain.add(h2)
    result = chain.run(entry)
    assert result.succeeded
    assert result.handler_index == 0
    h2.assert_not_called()


def test_falls_through_to_second_handler(entry):
    h1 = _handler(False)
    h2 = _handler(True)
    chain = AlertChain()
    chain.add(h1)
    chain.add(h2)
    result = chain.run(entry)
    assert result.succeeded
    assert result.handler_index == 1


def test_all_fail_returns_not_succeeded(entry):
    chain = AlertChain()
    chain.add(_handler(False))
    chain.add(_handler(False))
    result = chain.run(entry)
    assert not result.succeeded
    assert result.handler_index is None


def test_exception_is_caught_and_recorded(entry):
    def boom(_e):
        raise RuntimeError("network down")

    h2 = _handler(True)
    chain = AlertChain()
    chain.add(boom)
    chain.add(h2)
    result = chain.run(entry)
    assert result.succeeded
    assert len(result.errors) == 1
    assert "network down" in result.errors[0]


def test_empty_chain_returns_not_succeeded(entry):
    chain = AlertChain()
    result = chain.run(entry)
    assert not result


def test_run_all_returns_one_result_per_entry(entry):
    chain = AlertChain()
    chain.add(_handler(True))
    results = chain.run_all([entry, entry, entry])
    assert len(results) == 3
    assert all(r.succeeded for r in results)


def test_add_returns_chain_for_chaining(entry):
    chain = AlertChain()
    returned = chain.add(_handler(True))
    assert returned is chain
