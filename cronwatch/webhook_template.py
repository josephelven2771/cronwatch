"""Webhook payload templating for cronwatch alerts."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from string import Template
from typing import Any

from cronwatch.history import HistoryEntry


_DEFAULT_TEMPLATE = """{
  "job": "${job_name}",
  "status": "${status}",
  "exit_code": ${exit_code},
  "started_at": "${started_at}",
  "finished_at": "${finished_at}",
  "duration_seconds": ${duration_seconds},
  "message": "${message}"
}"""


def _safe_iso(dt: datetime | None) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _duration(entry: HistoryEntry) -> float:
    if entry.started_at is None or entry.finished_at is None:
        return 0.0
    return (entry.finished_at - entry.started_at).total_seconds()


def build_payload(entry: HistoryEntry, template_str: str | None = None) -> str:
    """Render a webhook payload string from a HistoryEntry.

    If *template_str* is None the built-in JSON template is used.
    Supports ``$variable`` / ``${variable}`` substitution via :class:`string.Template`.
    """
    tpl = Template(template_str or _DEFAULT_TEMPLATE)
    status = "success" if entry.succeeded else "failure"
    mapping: dict[str, Any] = {
        "job_name": entry.job_name,
        "status": status,
        "exit_code": entry.exit_code if entry.exit_code is not None else "null",
        "started_at": _safe_iso(entry.started_at),
        "finished_at": _safe_iso(entry.finished_at),
        "duration_seconds": round(_duration(entry), 3),
        "message": f"Job '{entry.job_name}' {status}.",
    }
    return tpl.safe_substitute(mapping)


def build_json_payload(entry: HistoryEntry) -> dict[str, Any]:
    """Return a plain dict payload (useful for libraries that accept dicts)."""
    raw = build_payload(entry)
    return json.loads(raw)
