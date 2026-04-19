"""High-level helper: execute a named job with optional retry support."""
from __future__ import annotations

import logging
from typing import Optional

from cronwatch.config import CronwatchConfig
from cronwatch.history import HistoryStore
from cronwatch.runner import run_job
from cronwatch.retrier import RetryPolicy, retry, RetryResult

logger = logging.getLogger(__name__)


def execute_named_job(
    name: str,
    config: CronwatchConfig,
    store: HistoryStore,
    retry_policy: Optional[RetryPolicy] = None,
) -> RetryResult:
    """Run a named job from config, retrying according to retry_policy.

    Returns a RetryResult summarising all attempts.
    """
    job_cfg = next((j for j in config.jobs if j.name == name), None)
    if job_cfg is None:
        raise ValueError(f"No job named {name!r} found in config.")

    policy = retry_policy or RetryPolicy(max_attempts=1, delay_seconds=0.0)

    def _attempt() -> tuple[bool, str]:
        result = run_job(job_cfg, store)
        return result.succeeded, result.output or ""

    retry_result = retry(_attempt, policy)

    if retry_result.succeeded:
        logger.info("Job %r completed successfully after %d attempt(s).", name, retry_result.attempts)
    else:
        logger.error(
            "Job %r failed after %d attempt(s). Last error: %s",
            name,
            retry_result.attempts,
            retry_result.last_error,
        )

    return retry_result
