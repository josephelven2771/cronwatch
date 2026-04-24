"""alert_pipeline.py — End-to-end alert pipeline with suppression, routing, and audit.

Ties together AlertSuppressor, AlertRouter, AuditMiddleware, and the
webhook/email dispatch layer into a single `run()` call.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List, Optional

from cronwatch.alert_suppressor import AlertSuppressor
from cronwatch.alert_router import AlertRouter
from cronwatch.audit_middleware import AuditMiddleware
from cronwatch.history import HistoryEntry


DispatchFn = Callable[[str, str, str], None]  # (channel, subject, body) -> None


@dataclass
class PipelineResult:
    job_name: str
    sent: bool
    suppression_reason: Optional[str]  # None when sent
    channel: Optional[str]             # None when suppressed


@dataclass
class AlertPipeline:
    suppressor: AlertSuppressor
    router: AlertRouter
    audit: AuditMiddleware
    dispatch: DispatchFn
    _results: List[PipelineResult] = field(default_factory=list, init=False)

    def run(
        self,
        entry: HistoryEntry,
        subject: str,
        body: str,
        now: Optional[datetime] = None,
    ) -> PipelineResult:
        """Evaluate suppression, route, dispatch, and audit a single alert."""
        if now is None:
            now = datetime.now(timezone.utc)

        job_name = entry.job_name

        suppression = self.suppressor.check(job_name, body, now=now)
        if not suppression:
            if suppression.reason == "silenced":
                self.audit.record_silence_applied(job_name, body)
            else:
                self.audit.record_alert_suppressed(job_name, body, suppression.reason)
            result = PipelineResult(
                job_name=job_name,
                sent=False,
                suppression_reason=suppression.reason,
                channel=None,
            )
            self._results.append(result)
            return result

        route = self.router.route(entry)
        channel = route.channel if route else "default"

        self.dispatch(channel, subject, body)
        self.suppressor.record(job_name, body, now=now)
        self.audit.record_alert_sent(job_name, channel, body)

        result = PipelineResult(
            job_name=job_name,
            sent=True,
            suppression_reason=None,
            channel=channel,
        )
        self._results.append(result)
        return result

    @property
    def results(self) -> List[PipelineResult]:
        return list(self._results)

    @property
    def sent_count(self) -> int:
        return sum(1 for r in self._results if r.sent)

    @property
    def suppressed_count(self) -> int:
        return sum(1 for r in self._results if not r.sent)
