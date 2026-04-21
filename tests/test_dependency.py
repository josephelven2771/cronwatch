"""Tests for cronwatch.dependency (graph + check logic)."""
import pytest

from cronwatch.dependency import (
    DependencyGraph,
    DependencyResult,
    check_dependencies,
    topological_order,
)


@pytest.fixture()
def linear_graph() -> DependencyGraph:
    """extract → transform → load"""
    g = DependencyGraph()
    g.add("extract", [])
    g.add("transform", ["extract"])
    g.add("load", ["transform"])
    return g


def test_check_no_deps_is_ready(linear_graph):
    result = check_dependencies(linear_graph, "extract", completed=set())
    assert bool(result) is True
    assert result.blocked_by == []
    assert result.missing == []


def test_check_blocked_when_dep_not_completed(linear_graph):
    result = check_dependencies(linear_graph, "transform", completed=set())
    assert bool(result) is False
    assert "extract" in result.blocked_by


def test_check_ready_when_dep_completed(linear_graph):
    result = check_dependencies(linear_graph, "transform", completed={"extract"})
    assert bool(result) is True


def test_check_missing_dep():
    g = DependencyGraph()
    g.add("job_b", ["ghost_job"])
    result = check_dependencies(g, "job_b", completed=set())
    assert bool(result) is False
    assert "ghost_job" in result.missing


def test_check_all_deps_must_complete(linear_graph):
    result = check_dependencies(linear_graph, "load", completed={"extract"})
    assert bool(result) is False
    assert "transform" in result.blocked_by


def test_topological_order_linear(linear_graph):
    order = topological_order(linear_graph)
    assert order is not None
    assert order.index("extract") < order.index("transform")
    assert order.index("transform") < order.index("load")


def test_topological_order_detects_cycle():
    g = DependencyGraph()
    g.add("a", ["b"])
    g.add("b", ["a"])
    assert topological_order(g) is None


def test_dependency_result_bool_false_on_blocked():
    r = DependencyResult(job_name="x", blocked_by=["y"], missing=[])
    assert bool(r) is False


def test_dependency_result_bool_true_when_clear():
    r = DependencyResult(job_name="x", blocked_by=[], missing=[])
    assert bool(r) is True
