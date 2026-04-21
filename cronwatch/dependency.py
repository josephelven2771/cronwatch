"""Job dependency tracking — ensure jobs run in order and detect blocked jobs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class DependencyResult:
    job_name: str
    blocked_by: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        """True when the job is clear to run (no blockers, no missing deps)."""
        return not self.blocked_by and not self.missing


class DependencyGraph:
    """Holds a directed graph of job → required-predecessor jobs."""

    def __init__(self) -> None:
        self._deps: Dict[str, List[str]] = {}

    def add(self, job_name: str, depends_on: List[str]) -> None:
        """Register *depends_on* as prerequisites for *job_name*."""
        self._deps[job_name] = list(depends_on)

    def dependencies_for(self, job_name: str) -> List[str]:
        return list(self._deps.get(job_name, []))

    def all_jobs(self) -> Set[str]:
        jobs: Set[str] = set(self._deps.keys())
        for deps in self._deps.values():
            jobs.update(deps)
        return jobs


def check_dependencies(
    graph: DependencyGraph,
    job_name: str,
    completed: Set[str],
) -> DependencyResult:
    """Return a DependencyResult for *job_name* given the set of *completed* jobs."""
    deps = graph.dependencies_for(job_name)
    known = graph.all_jobs()

    blocked_by: List[str] = []
    missing: List[str] = []

    for dep in deps:
        if dep not in known and dep not in completed:
            missing.append(dep)
        elif dep not in completed:
            blocked_by.append(dep)

    return DependencyResult(
        job_name=job_name,
        blocked_by=blocked_by,
        missing=missing,
    )


def topological_order(graph: DependencyGraph) -> Optional[List[str]]:
    """Return jobs in topological order, or None if a cycle is detected."""
    in_degree: Dict[str, int] = {j: 0 for j in graph.all_jobs()}
    adj: Dict[str, List[str]] = {j: [] for j in graph.all_jobs()}

    for job, deps in graph._deps.items():
        for dep in deps:
            adj[dep].append(job)
            in_degree[job] += 1

    queue = [j for j, d in in_degree.items() if d == 0]
    order: List[str] = []

    while queue:
        node = queue.pop(0)
        order.append(node)
        for neighbour in adj.get(node, []):
            in_degree[neighbour] -= 1
            if in_degree[neighbour] == 0:
                queue.append(neighbour)

    if len(order) != len(in_degree):
        return None  # cycle detected
    return order
