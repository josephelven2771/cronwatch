# alert_replay

The `alert_replay` module provides utilities for **replaying suppressed or
failed alerts** from the audit log. This is useful when an outage or
misconfiguration caused alerts to be dropped and you want to re-deliver them
once the system is healthy again.

## Key components

| Symbol | Description |
|---|---|
| `ReplayResult` | Dataclass holding replayed entries and skip count. |
| `replay_alerts()` | Functional API — filter and replay entries from an `AuditLog`. |
| `AlertReplayer` | Class wrapper that binds a log and send function together. |

## Usage

```python
from cronwatch.audit_log import AuditLog
from cronwatch.alert_replay import AlertReplayer

log = AuditLog("/var/lib/cronwatch/audit.jsonl")

def my_send(entry):
    # deliver via webhook, email, etc.
    print(f"Replaying alert for {entry.job}: {entry.detail}")
    return True

replayer = AlertReplayer(log, my_send)
result = replayer.run(job_name="backup")
print(f"Replayed {result.count} alert(s), skipped {result.skipped}.")
```

## Filtering options

| Parameter | Type | Description |
|---|---|---|
| `since` | `datetime` (UTC) | Only replay entries at or after this time. |
| `until` | `datetime` (UTC) | Only replay entries at or before this time. |
| `job_name` | `str` | Limit replay to a specific job. |
| `dry_run` | `bool` | Collect candidates without calling the send function. |

## Replayed action types

Only audit entries with the following `action` values are eligible for replay:

- `alert_suppressed` — alert was blocked by a silencer, cooldown, or rate limiter.
- `alert_failed` — the delivery attempt itself raised an exception or returned
  a non-success status.

All other actions (e.g. `alert_sent`, `silence_applied`) are counted as
`skipped` and ignored.

## ReplayResult

```python
result.count        # number of entries replayed
result.skipped      # number of entries skipped
bool(result)        # True when at least one entry was replayed
result.replayed     # list[AuditEntry]
```
