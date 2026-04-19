"""Retry logic for failed cron job commands."""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    delay_seconds: float = 5.0
    backoff_factor: float = 2.0
    max_delay_seconds: float = 60.0


@dataclass
class RetryResult:
    succeeded: bool
    attempts: int
    last_error: Optional[str] = None
    outputs: list[str] = field(default_factory=list)


def retry(fn: Callable[[], tuple[bool, str]], policy: RetryPolicy) -> RetryResult:
    """Call fn() up to policy.max_attempts times, backing off between failures.

    fn must return (success: bool, output: str).
    """
    delay = policy.delay_seconds
    outputs: list[str] = []
    last_error: Optional[str] = None

    for attempt in range(1, policy.max_attempts + 1):
        success, output = fn()
        outputs.append(output)
        if success:
            logger.debug("Attempt %d succeeded.", attempt)
            return RetryResult(succeeded=True, attempts=attempt, outputs=outputs)
        last_error = output
        logger.warning("Attempt %d failed: %s", attempt, output)
        if attempt < policy.max_attempts:
            actual_delay = min(delay, policy.max_delay_seconds)
            logger.debug("Waiting %.1fs before next attempt.", actual_delay)
            time.sleep(actual_delay)
            delay *= policy.backoff_factor

    return RetryResult(
        succeeded=False,
        attempts=policy.max_attempts,
        last_error=last_error,
        outputs=outputs,
    )
