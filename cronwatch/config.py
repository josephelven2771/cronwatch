"""Configuration loader for cronwatch."""

import os
import yaml
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JobConfig:
    name: str
    schedule: str
    timeout: int = 3600  # seconds
    grace_period: int = 300  # seconds
    tags: List[str] = field(default_factory=list)


@dataclass
class AlertConfig:
    webhook_url: Optional[str] = None
    email: Optional[str] = None
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig]
    alerts: AlertConfig
    check_interval: int = 60  # seconds
    state_file: str = ".cronwatch_state.json"


def load_config(path: str = "cronwatch.yml") -> CronwatchConfig:
    """Load and parse configuration from a YAML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    jobs = [
        JobConfig(
            name=j["name"],
            schedule=j["schedule"],
            timeout=j.get("timeout", 3600),
            grace_period=j.get("grace_period", 300),
            tags=j.get("tags", []),
        )
        for j in raw.get("jobs", [])
    ]

    alert_raw = raw.get("alerts", {})
    alerts = AlertConfig(
        webhook_url=alert_raw.get("webhook_url"),
        email=alert_raw.get("email"),
        smtp_host=alert_raw.get("smtp_host", "localhost"),
        smtp_port=alert_raw.get("smtp_port", 587),
        smtp_user=alert_raw.get("smtp_user"),
        smtp_password=alert_raw.get("smtp_password"),
    )

    return CronwatchConfig(
        jobs=jobs,
        alerts=alerts,
        check_interval=raw.get("check_interval", 60),
        state_file=raw.get("state_file", ".cronwatch_state.json"),
    )
