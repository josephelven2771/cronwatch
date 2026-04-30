"""Runs alert budget checks across all configured jobs before dispatching."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

from cronwatch.alert_budget import AlertBudget, BudgetPolicy, BudgetResult
from cronwatch.history import HistoryEntry


@dataclass
class BudgetRunResult:
    job_name: str
    entry: HistoryEntry
    budget_result: BudgetResult
    dispatched: bool

    def __bool__(self) -> bool:
        return self.dispatched


SendFn = Callable[[HistoryEntry], None]


class AlertBudgetRunner:
    """Wraps a send function with per-job alert budgets.

    Each job gets its own ``AlertBudget`` instance.  A shared *global* budget
    can optionally cap total alerts across all jobs.
    """

    def __init__(
        self,
        policy: BudgetPolicy,
        send: SendFn,
        *,
        global_policy: BudgetPolicy | None = None,
    ) -> None:
        self._policy = policy
        self._send = send
        self._global_policy = global_policy
        self._per_job: Dict[str, AlertBudget] = {}
        self._global: AlertBudget | None = (
            AlertBudget(global_policy) if global_policy else None
        )
        self._results: List[BudgetRunResult] = []

    def _budget_for(self, job_name: str) -> AlertBudget:
        if job_name not in self._per_job:
            self._per_job[job_name] = AlertBudget(self._policy)
        return self._per_job[job_name]

    def run(self, entries: List[HistoryEntry]) -> "AlertBudgetRunner":
        """Process *entries*, dispatching only those within budget."""
        self._results = []
        for entry in entries:
            name = entry.job_name
            job_budget = self._budget_for(name)
            job_check = job_budget.check()
            global_check = self._global.check() if self._global else None

            allowed = job_check.allowed and (
                global_check.allowed if global_check is not None else True
            )

            if allowed:
                job_budget.record()
                if self._global:
                    self._global.record()
                self._send(entry)

            self._results.append(
                BudgetRunResult(
                    job_name=name,
                    entry=entry,
                    budget_result=job_check,
                    dispatched=allowed,
                )
            )
        return self

    @property
    def results(self) -> List[BudgetRunResult]:
        return list(self._results)

    @property
    def sent_count(self) -> int:
        return sum(1 for r in self._results if r.dispatched)

    @property
    def suppressed_count(self) -> int:
        return sum(1 for r in self._results if not r.dispatched)
