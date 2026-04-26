"""alert_fanout.py – broadcast a single alert to multiple destinations.

An AlertFanout accepts a list of send callables and dispatches a payload
to all of them, collecting per-destination results.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


SendFn = Callable[[Dict[str, Any]], bool]


@dataclass
class FanoutResult:
    """Outcome of a single destination within a fanout dispatch."""

    destination: str
    success: bool
    error: Optional[str] = None

    def __bool__(self) -> bool:
        return self.success


@dataclass
class FanoutReport:
    """Aggregated outcome of all destinations for one fanout call."""

    results: List[FanoutResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def sent_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed_count(self) -> int:
        return self.total - self.sent_count

    @property
    def all_succeeded(self) -> bool:
        return self.failed_count == 0 and self.total > 0

    def __bool__(self) -> bool:
        return self.all_succeeded


class AlertFanout:
    """Dispatch a payload to multiple send functions.

    Parameters
    ----------
    destinations:
        Mapping of human-readable name -> send callable.  Each callable
        receives the payload dict and should return ``True`` on success.
    stop_on_first_failure:
        When *True* the fanout halts after the first destination that
        returns ``False`` or raises an exception.
    """

    def __init__(
        self,
        destinations: Dict[str, SendFn],
        *,
        stop_on_first_failure: bool = False,
    ) -> None:
        self._destinations = destinations
        self._stop_on_first_failure = stop_on_first_failure

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def dispatch(self, payload: Dict[str, Any]) -> FanoutReport:
        """Send *payload* to every destination and return a :class:`FanoutReport`."""
        report = FanoutReport()

        for name, send_fn in self._destinations.items():
            result = self._call(name, send_fn, payload)
            report.results.append(result)
            if self._stop_on_first_failure and not result.success:
                break

        return report

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _call(name: str, send_fn: SendFn, payload: Dict[str, Any]) -> FanoutResult:
        try:
            ok = send_fn(payload)
            return FanoutResult(destination=name, success=bool(ok))
        except Exception as exc:  # noqa: BLE001
            return FanoutResult(destination=name, success=False, error=str(exc))
