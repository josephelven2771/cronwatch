"""Routes alerts to the appropriate channel based on job tags and severity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwatch.config import AlertConfig
from cronwatch.digest import DigestEntry


@dataclass
class RouteRule:
    """A single routing rule mapping tags/severity to an alert channel."""

    tags: List[str] = field(default_factory=list)
    min_failures: int = 1
    channel: str = "webhook"  # "webhook" | "email" | "both" | "none"
    label: str = ""

    def matches(self, entry: DigestEntry) -> bool:
        """Return True if this rule applies to the given digest entry."""
        if entry.failure_count < self.min_failures:
            return False
        if self.tags:
            entry_tags = set(getattr(entry, "tags", []) or [])
            if not entry_tags.intersection(self.tags):
                return False
        return True


@dataclass
class AlertRouter:
    """Evaluates routing rules and returns the channel to use for an alert."""

    rules: List[RouteRule] = field(default_factory=list)
    default_channel: str = "webhook"

    def route(self, entry: DigestEntry) -> str:
        """Return the channel name for the given entry."""
        for rule in self.rules:
            if rule.matches(entry):
                return rule.channel
        return self.default_channel

    def should_suppress(self, entry: DigestEntry) -> bool:
        """Return True if the routed channel is 'none' (suppress alert)."""
        return self.route(entry) == "none"


def build_router(alert_cfg: AlertConfig, rules: Optional[List[dict]] = None) -> AlertRouter:
    """Construct an AlertRouter from config and an optional list of rule dicts."""
    route_rules: List[RouteRule] = []
    for r in (rules or []):
        route_rules.append(
            RouteRule(
                tags=r.get("tags", []),
                min_failures=r.get("min_failures", 1),
                channel=r.get("channel", "webhook"),
                label=r.get("label", ""),
            )
        )
    default = "webhook" if alert_cfg.webhook_url else "email"
    return AlertRouter(rules=route_rules, default_channel=default)
