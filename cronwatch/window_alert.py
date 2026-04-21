"""window_alert.py — dispatch alerts for window violations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from cronwatch.window_checker import WindowResult


AlertFn = Callable[[str, str], None]  # (subject, body)


@dataclass
class WindowAlertConfig:
    """Minimal config controlling how window violations are reported."""
    subject_prefix: str = "[cronwatch] Window violation"
    include_expected_window: bool = True
    include_last_run: bool = True


def _build_body(result: WindowResult, cfg: WindowAlertConfig) -> str:
    lines: List[str] = [result.message]
    if cfg.include_expected_window:
        lines.append(
            f"Expected window: {result.expected_start.strftime('%H:%M')} – "
            f"{result.expected_end.strftime('%H:%M')} UTC"
        )
    if cfg.include_last_run:
        ts = result.last_run.isoformat() if result.last_run else "never"
        lines.append(f"Last run: {ts}")
    return "\n".join(lines)


def alert_on_violations(
    violations: List[WindowResult],
    alert_fn: AlertFn,
    cfg: Optional[WindowAlertConfig] = None,
) -> int:
    """Call *alert_fn* for each violation. Returns the number of alerts sent."""
    if cfg is None:
        cfg = WindowAlertConfig()
    sent = 0
    for result in violations:
        subject = f"{cfg.subject_prefix}: {result.job_name}"
        body = _build_body(result, cfg)
        alert_fn(subject, body)
        sent += 1
    return sent


@dataclass
class WindowAlertPipeline:
    """Combines WindowChecker results with alert dispatch."""
    alert_fn: AlertFn
    alert_cfg: WindowAlertConfig = field(default_factory=WindowAlertConfig)
    _sent: int = field(default=0, init=False)

    def run(self, violations: List[WindowResult]) -> int:
        self._sent = alert_on_violations(violations, self.alert_fn, self.alert_cfg)
        return self._sent

    @property
    def sent(self) -> int:
        return self._sent
