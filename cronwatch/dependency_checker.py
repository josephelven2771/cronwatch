"""High-level checker that evaluates dependency readiness for all configured jobs."""
from __future__ import annotations

from typing import Dict, List, Optional, Set

from cronwatch.config import CronwatchConfig
from cronwatch.dependency import (
    DependencyGraph,
    DependencyResult,
    check_dependencies,
    topological_order,
)


class DependencyChecker:
    """Builds a DependencyGraph from config and checks job readiness."""

    def __init__(self, config: CronwatchConfig) -> None:
        self._config = config
        self._graph = self._build_graph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_job(self, job_name: str, completed: Set[str]) -> DependencyResult:
        """Check whether *job_name* is ready to run given *completed* jobs."""
        return check_dependencies(self._graph, job_name, completed)

    def check_all(self, completed: Set[str]) -> Dict[str, DependencyResult]:
        """Return a mapping of job_name → DependencyResult for every job."""
        return {
            job.name: check_dependencies(self._graph, job.name, completed)
            for job in self._config.jobs
        }

    def blocked(self, completed: Set[str]) -> List[str]:
        """Return names of jobs that cannot yet run."""
        return [
            name
            for name, result in self.check_all(completed).items()
            if not result
        ]

    def execution_order(self) -> Optional[List[str]]:
        """Return a valid topological execution order, or None if a cycle exists."""
        return topological_order(self._graph)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_graph(self) -> DependencyGraph:
        graph = DependencyGraph()
        for job in self._config.jobs:
            deps = getattr(job, "depends_on", None) or []
            graph.add(job.name, deps)
        return graph
