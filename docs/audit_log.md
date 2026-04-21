# Audit Log

The `audit_log` module provides an append-only event log that records significant
cronwatch actions such as alerts dispatched, silences applied, and escalations
triggered.

## Overview

Each event is stored as a newline-delimited JSON record in a file you specify.
The log is human-readable and can be tailed, grepped, or ingested by external
tools.

## Classes

### `AuditEntry`

A single log record.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `str` | ISO-8601 UTC timestamp |
| `event` | `str` | Event type identifier |
| `job_name` | `str` | Name of the affected job |
| `detail` | `str` | Human-readable detail string |
| `tags` | `list[str]` | Optional tags from the job |

### `AuditLog`

Reads and writes audit entries to a file.

```python
from cronwatch.audit_log import AuditLog

log = AuditLog("/var/lib/cronwatch/audit.log")

# Record an event
log.append("alert_sent", "nightly_backup", detail="webhook fired", tags=["infra"])

# Read everything
entries = log.read_all()

# Filter by job
entries = log.read_for_job("nightly_backup")

# Filter by event type
alerts = log.read_by_event("alert_sent")
```

## Event Types

| Event | Emitted by |
|-------|------------|
| `alert_sent` | `alerts.dispatch_alert` |
| `silence_applied` | `silencer.Silencer` |
| `escalation_triggered` | `escalator.Escalator` |
| `rate_limited` | `ratelimiter.RateLimiter` |

## Storage Format

Each line is a JSON object:

```json
{"timestamp": "2024-06-01T12:00:00+00:00", "event": "alert_sent", "job_name": "backup", "detail": "webhook fired", "tags": ["infra"]}
```
