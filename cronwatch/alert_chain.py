"""Alert chain: run a sequence of alert handlers, stopping on first success."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from cronwatch.history import HistoryEntry


AlertHandler = Callable[[HistoryEntry], bool]


@dataclass
class ChainResult:
    """Result from running an alert chain."""
    entry: HistoryEntry
    handler_index: Optional[int]  # index of handler that succeeded, or None
    succeeded: bool
    errors: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.succeeded


@dataclass
class AlertChain:
    """Run handlers in order; stop at first success."""
    handlers: List[AlertHandler] = field(default_factory=list)

    def add(self, handler: AlertHandler) -> "AlertChain":
        self.handlers.append(handler)
        return self

    def run(self, entry: HistoryEntry) -> ChainResult:
        errors: List[str] = []
        for idx, handler in enumerate(self.handlers):
            try:
                ok = handler(entry)
                if ok:
                    return ChainResult(
                        entry=entry,
                        handler_index=idx,
                        succeeded=True,
                        errors=errors,
                    )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"handler[{idx}]: {exc}")
        return ChainResult(
            entry=entry,
            handler_index=None,
            succeeded=False,
            errors=errors,
        )

    def run_all(self, entries: List[HistoryEntry]) -> List[ChainResult]:
        return [self.run(e) for e in entries]
