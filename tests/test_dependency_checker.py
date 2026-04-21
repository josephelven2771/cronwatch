"""Tests for cronwatch.dependency_checker (config-level integration)."""
import pytest

from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig
from cronwatch.dependency_checker import DependencyChecker


def _make_job(name: str, depends_on=None) -> JobConfig:
    return JobConfig(
        name=name,
        schedule="0 * * * *",
        command=f"echo {name}",
        depends_on=depends_on or [],
    )


@pytest.fixture()
def config() -> CronwatchConfig:
    return CronwatchConfig(
        jobs=[
            _make_job("extract"),
            _make_job("transform", depends_on=["extract"]),
            _make_job("load", depends_on=["transform"]),
        ],
        alerts=AlertConfig(webhook_url=None, email=None),
    )


@pytest.fixture()
def checker(config) -> DependencyChecker:
    return DependencyChecker(config)


def test_check_all_returns_result_for_every_job(checker):
    results = checker.check_all(completed=set())
    assert set(results.keys()) == {"extract", "transform", "load"}


def test_extract_ready_with_no_completed(checker):
    result = checker.check_job("extract", completed=set())
    assert bool(result) is True


def test_transform_blocked_without_extract(checker):
    result = checker.check_job("transform", completed=set())
    assert bool(result) is False
    assert "extract" in result.blocked_by


def test_transform_ready_after_extract(checker):
    result = checker.check_job("transform", completed={"extract"})
    assert bool(result) is True


def test_blocked_returns_blocked_job_names(checker):
    blocked = checker.blocked(completed=set())
    assert "transform" in blocked
    assert "load" in blocked
    assert "extract" not in blocked


def test_blocked_empty_when_all_completed(checker):
    blocked = checker.blocked(completed={"extract", "transform", "load"})
    assert blocked == []


def test_execution_order_respects_dependencies(checker):
    order = checker.execution_order()
    assert order is not None
    assert order.index("extract") < order.index("transform")
    assert order.index("transform") < order.index("load")


def test_execution_order_none_on_cycle():
    from cronwatch.config import CronwatchConfig, AlertConfig
    cfg = CronwatchConfig(
        jobs=[
            _make_job("a", depends_on=["b"]),
            _make_job("b", depends_on=["a"]),
        ],
        alerts=AlertConfig(webhook_url=None, email=None),
    )
    checker = DependencyChecker(cfg)
    assert checker.execution_order() is None
