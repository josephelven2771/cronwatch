"""Monitor — ties tracker and alerts together; evaluates all jobs."""

import logging
from typing import List

from cronwatch.config import CronwatchConfig
from cronwatch.tracker import JobTracker, JobRun
from cronwatch.alerts import dispatch_alert

logger = logging.getLogger(__name__)


class Monitor:
    """Evaluates job health and fires alerts when jobs miss or fail."""

    def __init__(self, config: CronwatchConfig, tracker: JobTracker) -> None:
        self.config = config
        self.tracker = tracker

    def check_all(self) -> List[str]:
        """Check every configured job. Returns list of alert messages sent."""
        sent: List[str] = []
        for job in self.config.jobs:
            msg = self._check_job(job)
            if msg:
                sent.append(msg)
        return sent

    def _check_job(self, job) -> str | None:
        run: JobRun | None = self.tracker.last_run(job.name)

        if self.tracker.is_overdue(job):
            subject = f"[cronwatch] MISSED: {job.name}"
            body = (
                f"Job '{job.name}' has not run within its expected interval "
                f"({job.max_interval_seconds}s)."
            )
            logger.warning(subject)
            dispatch_alert(self.config.alerts, subject, body)
            return subject

        if run and run.failed:
            subject = f"[cronwatch] FAILED: {job.name}"
            body = (
                f"Job '{job.name}' exited with code {run.exit_code}.\n"
                f"Output:\n{run.output or '(none)'}"
            )
            logger.warning(subject)
            dispatch_alert(self.config.alerts, subject, body)
            return subject

        return None
