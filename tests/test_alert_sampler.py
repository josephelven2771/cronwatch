"""Tests for cronwatch.alert_sampler."""
from __future__ import annotations

import datetime
from typing import List

import pytest

from cronwatch.alert_sampler import AlertSampler, SamplePolicy, SampleResult
from cronwatch.history import HistoryEntry


def _utc(offset: int = 0) -> datetime.datetime:
    return datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=offset)


def _entry(name: str = "backup", success: bool = False) -> HistoryEntry:
    return HistoryEntry(
        job_name=name,
        started_at=_utc(),
        finished_at=_utc(30),
        exit_code=0 if success else 1,
        succeeded=success,
    )


@pytest.fixture()
def policy() -> SamplePolicy:
    return SamplePolicy(rate=0.5, threshold=2, seed=42)


@pytest.fixture()
def sampler(policy: SamplePolicy) -> AlertSampler:
    return AlertSampler(policy=policy)


# ---------------------------------------------------------------------------
# SamplePolicy validation
# ---------------------------------------------------------------------------

def test_policy_rejects_rate_above_one() -> None:
    with pytest.raises(ValueError, match="rate"):
        SamplePolicy(rate=1.1)


def test_policy_rejects_negative_rate() -> None:
    with pytest.raises(ValueError, match="rate"):
        SamplePolicy(rate=-0.1)


def test_policy_rejects_negative_threshold() -> None:
    with pytest.raises(ValueError, match="threshold"):
        SamplePolicy(rate=0.5, threshold=-1)


# ---------------------------------------------------------------------------
# Sampling below threshold – all entries pass
# ---------------------------------------------------------------------------

def test_sample_below_threshold_all_allowed(sampler: AlertSampler) -> None:
    entries = [_entry()]  # 1 entry, threshold=2 → sampling not applied
    results = sampler.sample(entries)
    assert all(r.allowed for r in results)


def test_sample_empty_list_returns_empty(sampler: AlertSampler) -> None:
    assert sampler.sample([]) == []


# ---------------------------------------------------------------------------
# Sampling above threshold – probabilistic
# ---------------------------------------------------------------------------

def test_sample_above_threshold_returns_result_per_entry(sampler: AlertSampler) -> None:
    entries = [_entry() for _ in range(10)]
    results = sampler.sample(entries)
    assert len(results) == 10


def test_sample_above_threshold_not_all_allowed(sampler: AlertSampler) -> None:
    """With seed=42 and rate=0.5, at least one entry should be rejected."""
    entries = [_entry(name=f"job-{i}") for i in range(20)]
    results = sampler.sample(entries)
    allowed = [r for r in results if r.allowed]
    rejected = [r for r in results if not r.allowed]
    assert len(allowed) > 0
    assert len(rejected) > 0


def test_sample_rate_100_percent_all_pass() -> None:
    s = AlertSampler(policy=SamplePolicy(rate=1.0, threshold=0))
    entries = [_entry() for _ in range(10)]
    assert all(r.allowed for r in s.sample(entries))


def test_sample_rate_0_percent_none_pass() -> None:
    s = AlertSampler(policy=SamplePolicy(rate=0.0, threshold=0))
    entries = [_entry() for _ in range(10)]
    assert not any(r.allowed for r in s.sample(entries))


# ---------------------------------------------------------------------------
# SampleResult bool
# ---------------------------------------------------------------------------

def test_sample_result_bool_true() -> None:
    r = SampleResult(entry=_entry(), allowed=True, rate=0.5)
    assert bool(r) is True


def test_sample_result_bool_false() -> None:
    r = SampleResult(entry=_entry(), allowed=False, rate=0.5)
    assert bool(r) is False


# ---------------------------------------------------------------------------
# filter() helper
# ---------------------------------------------------------------------------

def test_filter_returns_only_allowed_entries() -> None:
    s = AlertSampler(policy=SamplePolicy(rate=0.0, threshold=0))
    entries = [_entry() for _ in range(5)]
    assert s.filter(entries) == []


def test_filter_rate_one_returns_all() -> None:
    s = AlertSampler(policy=SamplePolicy(rate=1.0, threshold=0))
    entries = [_entry(name=f"j{i}") for i in range(5)]
    assert s.filter(entries) == entries
