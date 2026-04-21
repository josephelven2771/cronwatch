# Incident Tracking

`cronwatch.incident` provides lightweight incident management so that a
repeated failure for the same job is grouped into a single *incident* rather
than generating a flood of independent alerts.

## Core types

### `Incident`

| Field | Type | Description |
|---|---|---|
| `job_name` | `str` | Name of the affected job |
| `incident_id` | `str` | UUID assigned at creation |
| `opened_at` | `datetime` | When the first failure was detected |
| `resolved_at` | `datetime \| None` | Set when the job recovers |
| `failure_count` | `int` | Total failures grouped into this incident |
| `last_failure_at` | `datetime \| None` | Timestamp of the most recent failure |
| `notes` | `str` | Free-text annotation |

`Incident.is_open` returns `True` while `resolved_at` is `None`.

### `IncidentTracker`

```python
tracker = IncidentTracker()

# Call on every detected failure:
inc = tracker.open_or_update("backup-db")
print(inc.failure_count)  # increments each call

# Call when the job succeeds again:
resolved = tracker.resolve("backup-db")

# Inspect:
print(tracker.open_incidents())
```

## Persistence

`cronwatch.incident_store` serialises tracker state as newline-delimited JSON:

```python
from pathlib import Path
from cronwatch.incident_store import save_incidents, load_incidents

path = Path("/var/lib/cronwatch/incidents.ndjson")
save_incidents(tracker, path)
tracker2 = load_incidents(path)
```
